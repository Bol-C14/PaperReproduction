"""Oracle-to-skill semantic integration checks.

The mutator is intentionally stochastic: it rewrites a parent SKILL.md from
oracle feedback, execution constraints, and the current objective. The
post-mutation sanitizer handles tool-contract safety and length hygiene, but it
does not answer the most important research question:

    Did the next skill actually integrate the oracle's evidence?

This module is the deterministic bridge between those two worlds. It turns the
Layer-3 oracle handoff into a compact patch plan, checks whether the mutated
skill covers that plan, flags semantic contradictions, and writes traceability
artifacts. The goal is not to prove natural-language equivalence; it is to catch
obvious failure modes such as dropping a critical path/signal lesson, preserving
advice the oracle said to remove, or accepting a skill that is clean but generic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re
import time
from pathlib import Path
from typing import Iterable

from skill_sanitizer import SkillExecutionContract


PATCH_PLAN_VERSION = 1

ACTION_HEADINGS = {
    "must_add": (
        "add",
        "change",
        "mutation",
        "repair",
        "next skill",
        "teach",
        "improve",
        "directive",
    ),
    "must_remove": (
        "remove",
        "avoid",
        "drop",
        "do not",
        "don't",
        "never",
        "stop",
        "failure",
        "anti-pattern",
    ),
    "must_preserve": (
        "keep",
        "preserve",
        "success",
        "retain",
        "continue",
    ),
}

ADD_VERBS = (
    "add",
    "teach",
    "include",
    "emphasize",
    "require",
    "make explicit",
    "must",
    "should",
    "change",
    "repair",
    "prefer",
)

REMOVE_VERBS = (
    "remove",
    "avoid",
    "drop",
    "delete",
    "stop",
    "never",
    "do not",
    "don't",
    "must not",
    "forbid",
)

PRESERVE_VERBS = (
    "keep",
    "preserve",
    "retain",
    "continue",
    "works",
    "success",
    "successful",
)

GENERIC_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "into",
    "then",
    "when",
    "only",
    "skill",
    "agent",
    "task",
    "rollout",
    "oracle",
    "feedback",
    "generation",
    "should",
    "must",
    "will",
    "before",
    "after",
    "because",
    "where",
    "which",
}


@dataclass
class SkillPatchPlan:
    """Structured mutation target derived from a Layer-3 oracle handoff."""

    schema_version: int
    has_feedback: bool
    must_add: list[str]
    must_remove: list[str]
    must_preserve: list[str]
    concrete_terms: list[str]
    task_access_constraints: list[str]
    source_chars: int
    extraction_notes: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _clean_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip(" -")


def _dedupe(items: Iterable[str], limit: int = 12) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        clean = _clean_line(item)
        if not clean:
            continue
        if clean.lower().strip(" .") in {"none", "(none this generation)", "none this generation"}:
            continue
        key = re.sub(r"\W+", " ", clean.lower()).strip()
        if key in seen:
            continue
        seen.add(key)
        result.append(clean)
        if len(result) >= limit:
            break
    return result


def _heading_bucket(line: str) -> str | None:
    """Return the explicit oracle section bucket for a Markdown heading.

    Keep this intentionally conservative. The oracle handoff often contains
    headings such as "Mutation directives", "Failure modes", or "Generation
    stats"; treating those broad headings as ADD/REMOVE sections causes
    downstream inversions. Only concrete section labels should set the active
    bucket.
    """
    lower = re.sub(r"^#+\s*", "", line.lower()).strip(" :")
    lower = re.sub(r"\s+", " ", lower)
    if re.match(r"^(keep|preserve|retain|success|what worked)\b", lower):
        return "must_preserve"
    if re.match(r"^(add|must add|new guidance|strengthen|teach|improve)\b", lower):
        return "must_add"
    if re.match(r"^(change|modify existing|existing guidance|open questions|diagnostic)\b", lower):
        return "must_add"
    if re.match(r"^(remove|must remove|avoid|drop|delete|anti-pattern|bad patterns?)\b", lower):
        return "must_remove"
    return None


def _classify_directive(line: str, current_bucket: str | None) -> str | None:
    lower = line.lower()
    if current_bucket in {"must_add", "must_preserve", "must_remove"}:
        return current_bucket
    stripped = lower.lstrip(" -*0123456789.)")
    if any(stripped.startswith(verb) for verb in REMOVE_VERBS):
        return "must_remove"
    if any(stripped.startswith(verb) for verb in ADD_VERBS):
        return "must_add"
    if any(stripped.startswith(verb) for verb in PRESERVE_VERBS):
        return "must_preserve"
    return None


def extract_concrete_terms(text: str, limit: int = 24) -> list[str]:
    """Extract paths, filenames, signals, tools, and literal terms worth preserving."""
    terms: list[str] = []
    patterns = [
        r"`([^`]{2,120})`",
        r"(?<!\w)(?:/?[A-Za-z0-9_.+-]+/)+[A-Za-z0-9_.+-]+",
        r"(?<!\w)[A-Za-z_][A-Za-z0-9_]*\.(?:sv|svh|v|vh|f|md|py|jsonl?)\b",
        r"(?<!\w)\$[A-Za-z_][A-Za-z0-9_$]*\b",
        r"(?<!\w)[A-Za-z_][A-Za-z0-9_]*(?:_i|_o|_n|_q|_d|_reg|_valid|_ready|_en|_we|_rst|_clk)\b",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            term = match.group(1) if match.groups() else match.group(0)
            term = term.strip()
            if 2 <= len(term) <= 120:
                terms.append(term)
    return _dedupe(terms, limit=limit)


def build_skill_patch_plan(
    oracle_feedback: str | None,
    execution_contract: SkillExecutionContract | None = None,
    *,
    max_items_per_bucket: int = 12,
) -> SkillPatchPlan:
    """Build a compact, structured mutation plan from oracle feedback."""
    feedback = (oracle_feedback or "").strip()
    notes: list[str] = []
    buckets = {
        "must_add": [],
        "must_remove": [],
        "must_preserve": [],
    }
    current_bucket: str | None = None

    if feedback:
        for raw_line in feedback.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                current_bucket = _heading_bucket(stripped)
                continue
            if not re.match(r"^\s*(?:[-*]|\d+[.)])\s+\S", raw_line):
                continue
            clean = _clean_line(stripped)
            bucket = _classify_directive(clean, current_bucket)
            if bucket:
                buckets[bucket].append(clean)
    else:
        notes.append("no_oracle_feedback")

    constraints: list[str] = []
    if execution_contract is not None:
        tools = ", ".join(execution_contract.allowed_tools)
        constraints.append(f"Use only available rollout tools: {tools}.")
        if execution_contract.hidden_verifier:
            constraints.append("Do not instruct the rollout agent to run or inspect hidden verifier/harness assets.")
        if getattr(execution_contract, "may_modify_testbench", False):
            constraints.append("This task may require creating or editing visible testbench/verification files as deliverables.")
        else:
            constraints.append("Treat visible testbench/verification files as read-only references unless the task explicitly requests them as deliverables.")

    return SkillPatchPlan(
        schema_version=PATCH_PLAN_VERSION,
        has_feedback=bool(feedback),
        must_add=_dedupe(buckets["must_add"], max_items_per_bucket),
        must_remove=_dedupe(buckets["must_remove"], max_items_per_bucket),
        must_preserve=_dedupe(buckets["must_preserve"], max_items_per_bucket),
        concrete_terms=extract_concrete_terms(feedback),
        task_access_constraints=constraints,
        source_chars=len(feedback),
        extraction_notes=notes,
    )


def format_skill_patch_plan(plan: SkillPatchPlan | dict | None) -> str:
    """Render a compact mutator-facing patch plan."""
    if plan is None:
        return ""
    data = plan.to_dict() if isinstance(plan, SkillPatchPlan) else dict(plan)
    if not data.get("has_feedback"):
        return ""

    lines = [
        "# Structured Skill Patch Plan",
        "",
        "The final skill must integrate this plan unless an item conflicts with the rollout execution contract.",
        "",
    ]
    sections = [
        ("Must Add Or Strengthen", data.get("must_add") or []),
        ("Must Preserve From Successful Rollouts", data.get("must_preserve") or []),
        ("Must Remove Or Avoid", data.get("must_remove") or []),
        ("Concrete Terms To Preserve When Relevant", data.get("concrete_terms") or []),
        ("Execution Constraints", data.get("task_access_constraints") or []),
    ]
    for heading, items in sections:
        if not items:
            continue
        lines.extend([f"## {heading}", ""])
        lines.extend(f"- {item}" for item in items)
        lines.append("")
    return "\n".join(lines).strip()


def _normal_words(text: str) -> set[str]:
    words = {
        word
        for word in re.findall(r"[a-zA-Z][a-zA-Z0-9_]{2,}", text.lower())
        if word not in GENERIC_WORDS
    }
    return words


def _protected_terms(text: str) -> list[str]:
    return extract_concrete_terms(text, limit=12)


def _directive_is_critical(text: str) -> bool:
    lower = text.lower()
    if _protected_terms(text):
        return True
    return any(marker in lower for marker in ("must", "never", "do not", "hidden", "harness", "verifier", "compile", "simulate"))


def _directive_covered(directive: str, candidate_lower: str) -> tuple[bool, dict]:
    terms = _protected_terms(directive)
    present_terms = [term for term in terms if term.lower() in candidate_lower]
    if terms and present_terms:
        return True, {"method": "protected_term", "terms": present_terms}

    words = _normal_words(directive)
    if not words:
        return True, {"method": "no_terms"}
    present_words = sorted(word for word in words if word in candidate_lower)
    coverage = len(present_words) / max(1, len(words))
    if coverage >= 0.45 and len(present_words) >= min(3, len(words)):
        return True, {"method": "keyword_overlap", "coverage": round(coverage, 3), "terms": present_words[:8]}
    return False, {"method": "missing", "coverage": round(coverage, 3), "terms": present_words[:8]}


def _directive_coverage_rows(directives: list[str], text: str) -> tuple[list[dict], list[str], float, int]:
    """Evaluate oracle directive coverage against a skill-like text.

    The same routine is used for candidate and parent skills so the gate can
    accept safe partial improvements. This matters because oracle feedback can
    contain 10+ useful directives; rejecting every candidate that misses any
    one critical item freezes evolution instead of letting better skills
    survive and accumulate.
    """
    lower = (text or "").lower()
    rows: list[dict] = []
    missing_critical: list[str] = []
    for directive in directives:
        covered, evidence = _directive_covered(directive, lower)
        is_critical = _directive_is_critical(directive)
        row = {
            "directive": directive,
            "covered": covered,
            "critical": is_critical,
            "evidence": evidence,
        }
        rows.append(row)
        if not covered and is_critical:
            missing_critical.append(directive)
    covered_count = sum(1 for row in rows if row["covered"])
    coverage = covered_count / len(rows) if rows else 1.0
    return rows, missing_critical, coverage, covered_count


def _line_is_positive(line: str) -> bool:
    lower = line.lower()
    return not any(marker in lower for marker in ("do not", "don't", "never", "must not", "avoid", "forbid", "unavailable"))


def detect_semantic_contradictions(skill_text: str, contract: SkillExecutionContract) -> list[str]:
    """Detect high-risk contradictions that survive tool-contract sanitation."""
    lower = skill_text.lower()
    issues: list[str] = []
    lines = [ln.strip() for ln in skill_text.splitlines() if ln.strip()]

    has_never_modify_tb = any(
        re.search(r"\b(never|do not|don't|must not|avoid)\b.*\b(testbench|verification|verif|checker)\b", ln.lower())
        for ln in lines
    )
    has_positive_tb_write = any(
        _line_is_positive(ln)
        and re.search(r"\b(write|create|edit|modify|overwrite|implement)\b.*\b(testbench|verification|verif|checker)\b", ln.lower())
        for ln in lines
    )
    if has_never_modify_tb and has_positive_tb_write:
        issues.append("contradiction:testbench_write_policy")

    if not getattr(contract, "may_modify_testbench", False):
        for ln in lines:
            low = ln.lower()
            if (
                _line_is_positive(ln)
                and re.search(r"\b(edit|modify|overwrite)\b.*\b(provided|visible)?\s*(testbench|verification|verif|checker)\b", low)
            ):
                issues.append("risky:testbench_modification_without_task_request")
                break

    if "do not include" in lower and "$fatal" in lower and "timeout" in lower:
        if re.search(r"\b(use|add|include|write)\b.*\$fatal.*\b(timeout|bounded)", lower):
            issues.append("contradiction:timeout_fatal_policy")

    if re.search(r"\b(run|execute|invoke|launch)\b.{0,60}\b(hidden|official)?\s*(harness|verifier|test_runner)", lower):
        bad_lines = [
            ln for ln in lines
            if _line_is_positive(ln)
            and re.search(r"\b(run|execute|invoke|launch)\b.{0,60}\b(hidden|official)?\s*(harness|verifier|test_runner)", ln.lower())
        ]
        if bad_lines:
            issues.append("contradiction:hidden_harness_action")

    return sorted(set(issues))


def _safe_replacement_for_semantic_line(line: str, contract: SkillExecutionContract) -> tuple[str | None, str | None]:
    """Return a contract-grounded replacement for one risky skill line.

    This is intentionally narrow and deterministic. The mutator often produces a
    skill that covers the oracle's useful directives but leaves one unsafe clause
    such as "edit the visible testbench" or "run the official harness". Rejecting
    the whole candidate freezes evolution. Replacing only that clause preserves
    the useful new lessons while keeping the injected skill faithful to the
    rollout contract.
    """
    lower = line.lower()
    if not _line_is_positive(line):
        return line, None

    if not getattr(contract, "may_modify_testbench", False):
        if re.search(
            r"\b(write|create|implement|edit|modify|overwrite)\b.{0,80}\b(provided|visible|existing|project)?\s*"
            r"(testbench|test bench|tb|verification|verif|checker)\b",
            lower,
        ):
            return (
                "- Read visible testbench/checker/verification files as read-only references; "
                "edit them only when the task explicitly names them as deliverables.",
                "rewrite_testbench_modification_without_task_request",
            )
        if re.search(
            r"\b(require|requires|need|needs|add|include)\b.{0,80}"
            r"\b(testbench|test bench|tb|verification|verif|checker)\b",
            lower,
        ) or re.search(
            r"\b(testbench|test bench|tb|verification|verif|checker)\b.{0,50}\b(snippet|file|deliverable)\b",
            lower,
        ):
            return (
                "- Use visible testbench/checker/verification files only as read-only references unless the task explicitly names them as deliverables.",
                "rewrite_testbench_deliverable_without_task_request",
            )

    if not getattr(contract, "can_run_official_harness", False):
        if re.search(r"\b(run|execute|invoke|launch)\b.{0,80}\b(hidden|official)?\s*(harness|verifier|test_runner)", lower):
            return (
                "- Do not run hidden or official harnesses during rollout; self-check only with visible files and allowed simulator tools.",
                "rewrite_hidden_harness_action",
            )

    if "do not include" in lower and "$fatal" in lower and "timeout" in lower:
        if re.search(r"\b(use|add|include|write)\b.*\$fatal.*\b(timeout|bounded)", lower):
            return None, "remove_timeout_fatal_contradiction"

    if re.search(r"\b(always|regardless|even if)\b.{0,80}\bvvp\b|\bvvp\b.{0,80}\b(after|despite)\b.{0,40}\b(failed|error)", lower):
        return (
            "- Run vvp only after iverilog/elaboration succeeds; if compile fails, fix the first compile error before simulating.",
            "rewrite_vvp_after_failed_compile",
        )

    return line, None


def repair_semantic_contradictions(skill_text: str, contract: SkillExecutionContract) -> tuple[str, dict]:
    """Deterministically scrub risky semantic contradictions from a skill.

    The function is a post-mutation safety valve: it does not invent new task
    strategy, and it does not relax the oracle integration gate. It only removes
    or rewrites contract-impossible action lines, then reports whether the
    contradiction detector is now clean.
    """
    original_issues = detect_semantic_contradictions(skill_text or "", contract)
    if not original_issues:
        return skill_text, {
            "changed": False,
            "original_contradictions": [],
            "remaining_contradictions": [],
            "changes": [],
        }

    changes: list[dict] = []
    repaired_lines: list[str] = []
    for idx, line in enumerate((skill_text or "").splitlines(), start=1):
        replacement, reason = _safe_replacement_for_semantic_line(line, contract)
        if reason is None:
            repaired_lines.append(line)
            continue
        changes.append({
            "line": idx,
            "reason": reason,
            "original": line[:240],
            "replacement": replacement[:240] if replacement is not None else None,
        })
        if replacement is not None:
            repaired_lines.append(replacement)

    repaired_text = "\n".join(repaired_lines).strip() + ("\n" if repaired_lines else "")
    remaining = detect_semantic_contradictions(repaired_text, contract)
    return repaired_text, {
        "changed": bool(changes),
        "original_contradictions": original_issues,
        "remaining_contradictions": remaining,
        "changes": changes,
    }


def _remove_violation(remove_directive: str, candidate_text: str) -> tuple[bool, dict]:
    lower = remove_directive.lower()
    candidate_lines = [ln.strip() for ln in (candidate_text or "").splitlines() if ln.strip()]
    if "harness" in lower or "verifier" in lower or "test_runner" in lower:
        positive_lines = [
            ln for ln in candidate_lines
            if _line_is_positive(ln)
            and re.search(r"\b(run|execute|invoke|launch)\b.{0,80}\b(harness|verifier|test_runner)", ln.lower())
        ]
        if positive_lines:
            return True, {"reason": "hidden_harness_action", "line": positive_lines[0][:220]}

    def positive(pattern: str) -> str | None:
        for ln in candidate_lines:
            if _line_is_positive(ln) and re.search(pattern, ln.lower()):
                return ln[:220]
        return None

    behavior_checks: list[tuple[str, str]] = []
    if re.search(r"\b(ad[- ]?hoc|custom|new|bespoke|standalone)\b.*\b(testbench|tb)\b", lower):
        behavior_checks.append((
            "ad_hoc_testbench",
            r"\b(create|write|author|build|rely on|use|treat)\b.{0,80}\b(ad[- ]?hoc|custom|new|bespoke|standalone)\b.{0,80}\b(testbench|tb)\b",
        ))
    if "single-file" in lower or "single file" in lower or "only one rtl" in lower:
        behavior_checks.append((
            "single_file_compile",
            r"\b(compile|build|elaborate)\b.{0,80}\b(single[- ]file|only one|one rtl|just the dut|dut alone)\b",
        ))
    if "dut without" in lower or "dut-alone" in lower or "dut alone" in lower:
        behavior_checks.append((
            "dut_alone_compile",
            r"\b(compile|elaborate|simulate)\b.{0,80}\b(dut[- ]alone|dut alone|without (a )?(tb|testbench))\b",
        ))
    if "hierarchical" in lower or "peek" in lower or "private signal" in lower:
        behavior_checks.append((
            "hierarchical_peek",
            r"\b(hierarchical|peek|force|probe|access|reference)\b.{0,80}\b(internal|private|dut\\.)",
        ))
    if "old_text" in lower or "approximate" in lower or "short anchor" in lower:
        behavior_checks.append((
            "approximate_edit_anchor",
            r"\b(approximate|fuzzy|short|partial|similar)\b.{0,80}\b(old_text|anchor|edit span|span)\b",
        ))
    if "echo" in lower or "bulk" in lower or "whole" in lower or "rewrite" in lower:
        behavior_checks.append((
            "bulk_echo_rewrite",
            r"\b(echo|rewrite|overwrite|recreate)\b.{0,80}\b(whole|entire|bulk|full)\b.{0,80}\b(rtl|file|module)\b",
        ))
    if "rename" in lower and "port" in lower:
        behavior_checks.append((
            "rename_ports",
            r"\b(rename|change|reshape)\b.{0,80}\b(port|interface|signature)\b",
        ))
    if "speculative" in lower and ("wire" in lower or "net" in lower):
        behavior_checks.append((
            "speculative_wires",
            r"\b(add|create|invent|derive)\b.{0,80}\b(speculative|guess|guessed)\b.{0,80}\b(wire|net|signal)",
        ))
    if "bare director" in lower or "raw director" in lower:
        behavior_checks.append((
            "bare_directory_iverilog",
            r"\biverilog\b.{0,80}\b(raw|bare)?\s*(directory|dir)\b",
        ))
    if "vvp" in lower and ("compile fail" in lower or "failed compile" in lower or "regardless" in lower):
        behavior_checks.append((
            "vvp_after_failed_compile",
            r"\b(always|regardless|even if)\b.{0,80}\bvvp\b|\bvvp\b.{0,80}\b(after|despite)\b.{0,40}\b(failed|error)",
        ))

    for reason, pattern in behavior_checks:
        hit = positive(pattern)
        if hit:
            return True, {"reason": reason, "line": hit}

    # Exact bad advice quoted in the oracle should still be blocked if it is
    # reintroduced as positive guidance, but do not block merely because the
    # candidate mentions concrete terms like filelist.f, tests/tb, or
    # example_core.v in a desirable context.
    quoted = [q.strip() for q in re.findall(r"[\"“]([^\"”]{16,220})[\"”]", remove_directive)]
    for quote in quoted:
        q_norm = re.sub(r"\s+", " ", quote.lower()).strip()
        for ln in candidate_lines:
            if _line_is_positive(ln) and q_norm in re.sub(r"\s+", " ", ln.lower()):
                return True, {"reason": "quoted_removed_advice_present", "quote": quote[:160], "line": ln[:220]}
    return False, {}


def validate_skill_integration(
    *,
    candidate_skill: str,
    parent_skill: str,
    patch_plan: SkillPatchPlan | dict | None,
    execution_contract: SkillExecutionContract,
    config: dict | None = None,
) -> dict:
    """Return whether a candidate skill faithfully integrates the patch plan."""
    cfg = {
        "enabled": True,
        "min_directive_coverage": 0.60,
        "max_missing_critical": 0,
        "allow_safe_partial_improvement": True,
        "min_coverage_gain_to_accept": 0.10,
        "min_child_parent_ratio_for_soften": 0.75,
        "fail_on_remove_violation": True,
        "fail_on_contradiction": True,
        **(config or {}),
    }
    data = patch_plan.to_dict() if isinstance(patch_plan, SkillPatchPlan) else dict(patch_plan or {})
    if not cfg.get("enabled", True) or not data.get("has_feedback"):
        return {
            "ok": True,
            "issues": [],
            "warnings": [],
            "metrics": {"enabled": bool(cfg.get("enabled", True)), "has_feedback": bool(data.get("has_feedback"))},
            "directive_results": [],
            "remove_results": [],
            "contradictions": [],
        }

    directives = list(data.get("must_add") or []) + list(data.get("must_preserve") or [])
    directive_results, missing_critical, coverage, covered_count = _directive_coverage_rows(
        directives,
        candidate_skill or "",
    )
    parent_directive_results, parent_missing_critical, parent_coverage, parent_covered_count = _directive_coverage_rows(
        directives,
        parent_skill or "",
    )
    coverage_gain = coverage - parent_coverage
    parent_chars = len(parent_skill or "")
    candidate_chars = len(candidate_skill or "")
    candidate_parent_ratio = (candidate_chars / parent_chars) if parent_chars else 1.0

    remove_results = []
    remove_violations = []
    for directive in data.get("must_remove") or []:
        violated, evidence = _remove_violation(directive, candidate_skill or "")
        row = {"directive": directive, "violated": violated, "evidence": evidence}
        remove_results.append(row)
        if violated:
            remove_violations.append(directive)

    contradictions = detect_semantic_contradictions(candidate_skill or "", execution_contract)
    issues: list[str] = []
    warnings: list[str] = []
    if coverage < float(cfg.get("min_directive_coverage", 0.60)):
        warnings.append(f"low_oracle_directive_coverage:{coverage:.3f}")
    missing_critical_over_limit = len(missing_critical) > int(cfg.get("max_missing_critical", 0))
    min_child_parent_ratio = float(cfg.get("min_child_parent_ratio_for_soften", 0.75))
    enough_child_retention = candidate_parent_ratio >= min_child_parent_ratio
    safe_partial_improvement = (
        bool(cfg.get("allow_safe_partial_improvement", True))
        and missing_critical_over_limit
        and covered_count > parent_covered_count
        and coverage_gain >= float(cfg.get("min_coverage_gain_to_accept", 0.10))
        and enough_child_retention
    )
    if safe_partial_improvement:
        warnings.append(
            f"missing_critical_softened_by_parent_coverage_gain:{coverage_gain:.3f}"
        )
    elif missing_critical_over_limit and not enough_child_retention and covered_count > parent_covered_count:
        warnings.append(
            f"missing_critical_not_softened_low_child_retention:{candidate_parent_ratio:.3f}"
        )
        issues.append("missing_critical_oracle_directives")
    elif missing_critical_over_limit:
        issues.append("missing_critical_oracle_directives")
    if remove_violations and cfg.get("fail_on_remove_violation", True):
        issues.append("must_remove_violation")
    if contradictions and cfg.get("fail_on_contradiction", True):
        issues.append("semantic_contradiction")

    return {
        "ok": not issues,
        "issues": issues,
        "warnings": warnings,
        "metrics": {
            "enabled": True,
            "coverage": round(coverage, 6),
            "parent_coverage": round(parent_coverage, 6),
            "coverage_gain": round(coverage_gain, 6),
            "covered_directives": covered_count,
            "parent_covered_directives": parent_covered_count,
            "total_directives": len(directive_results),
            "missing_critical_count": len(missing_critical),
            "parent_missing_critical_count": len(parent_missing_critical),
            "remove_violation_count": len(remove_violations),
            "contradiction_count": len(contradictions),
            "parent_chars": parent_chars,
            "candidate_chars": candidate_chars,
            "candidate_parent_ratio": round(candidate_parent_ratio, 6),
            "min_child_parent_ratio_for_soften": min_child_parent_ratio,
        },
        "missing_critical": missing_critical,
        "directive_results": directive_results,
        "parent_directive_results": parent_directive_results,
        "remove_results": remove_results,
        "contradictions": contradictions,
    }


def format_integration_issues_for_repair(report: dict, limit: int = 8) -> str:
    """Summarize integration failures for the repair LLM call."""
    lines = ["# Skill Integration Repair Request", ""]
    if report.get("issues"):
        lines.append("## Blocking Issues")
        lines.extend(f"- {issue}" for issue in report.get("issues", []))
        lines.append("")
    missing = report.get("missing_critical") or []
    if missing:
        lines.append("## Missing Critical Oracle Directives")
        lines.extend(f"- {item}" for item in missing[:limit])
        lines.append("")
    violated = [row for row in report.get("remove_results", []) if row.get("violated")]
    if violated:
        lines.append("## Remove Directives Still Violated")
        lines.extend(f"- {row.get('directive')}" for row in violated[:limit])
        lines.append("")
    contradictions = report.get("contradictions") or []
    if contradictions:
        lines.append("## Semantic Contradictions")
        lines.extend(f"- {item}" for item in contradictions[:limit])
        lines.append("")
    if report.get("warnings"):
        lines.append("## Warnings")
        lines.extend(f"- {warning}" for warning in report.get("warnings", [])[:limit])
    return "\n".join(lines).strip() + "\n"


def write_skill_patch_plan_artifacts(
    gen_dir: Path,
    plan: SkillPatchPlan,
) -> None:
    """Persist the structured oracle-to-mutation plan for a generation."""
    gen_dir.mkdir(parents=True, exist_ok=True)
    with open(gen_dir / "skill_patch_plan.json", "w", encoding="utf-8") as f:
        json.dump(plan.to_dict(), f, indent=2, ensure_ascii=False)
    (gen_dir / "skill_patch_plan.md").write_text(format_skill_patch_plan(plan) + "\n", encoding="utf-8")


def write_skill_integration_report(
    output_dir: Path,
    generation: int,
    child_slot: int,
    record: dict,
) -> dict:
    """Write machine-readable oracle coverage report at root and generation scope."""
    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "generation": generation,
        "child_slot": child_slot,
        **record,
    }
    paths = [
        output_dir / "skill_integration.jsonl",
        output_dir / f"gen{generation}" / "skill_integration.jsonl",
    ]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    detail_dir = output_dir / f"gen{generation}" / "skill_integration"
    detail_dir.mkdir(parents=True, exist_ok=True)
    stage = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(record.get("stage") or "candidate"))
    detail_path = detail_dir / f"child{child_slot}_{stage}.json"
    with open(detail_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    payload["detail_path"] = str(detail_path.relative_to(output_dir))
    return payload

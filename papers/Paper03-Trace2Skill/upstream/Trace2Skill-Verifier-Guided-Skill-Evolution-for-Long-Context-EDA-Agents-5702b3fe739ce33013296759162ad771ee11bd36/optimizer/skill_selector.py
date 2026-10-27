"""Semantic skill selection for Trace2Skill evolution.

The rollout fitness of a child skill is a noisy behavior measurement: it mixes
the quality of the skill, stochastic long-horizon rollout variance, and whether
the rollout agent actually followed the skill. This module keeps that signal
useful as telemetry, but prevents it from being the sole authority for the next
generation's injected skill.

The invariant enforced here is deliberately conservative:

    A mutated child may replace its parent only when it preserves durable parent
    guidance and adds execution-grounded lessons from the oracle handoff. If the
    evidence is weak or the candidate is risky, keep the parent unchanged.

The optimizer still evaluates rollout fitness for every individual. This module
only decides whether a candidate skill is semantically safe enough to enter the
next-generation skill lineage.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
from typing import Any

from skill_integration import validate_skill_integration
from skill_sanitizer import SkillExecutionContract


SEMANTIC_SELECTOR_VERSION = 1


def _sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _directive_depth(rows: list[dict]) -> float:
    """Return a graded directive-integration score in [0, 1].

    `validate_skill_integration` reports whether each oracle directive is
    covered, but a binary covered/missing signal saturates too easily. This
    helper gives stronger credit to concrete protected-term matches and only
    partial credit to loose keyword overlap. A skill reaches 1.0 only when all
    directives are covered by strong evidence.
    """

    if not rows:
        return 1.0

    total = 0.0
    for row in rows:
        if not row.get("covered"):
            continue
        evidence = row.get("evidence") or {}
        method = evidence.get("method")
        if method == "protected_term":
            total += 1.0
        elif method == "keyword_overlap":
            coverage = max(0.0, min(1.0, _float(evidence.get("coverage"), 0.0)))
            total += 0.45 + 0.40 * coverage
        elif method == "no_terms":
            total += 0.55
        else:
            total += 0.65
    return max(0.0, min(1.0, total / len(rows)))


def _critical_directive_depth(rows: list[dict]) -> float:
    critical_rows = [row for row in rows if row.get("critical")]
    return _directive_depth(critical_rows if critical_rows else rows)


def _length_quality(ratio: float) -> float:
    """Soft length calibration for skill growth.

    The metric should discourage bloat and destructive compression without
    blocking real insight growth. It is deliberately soft: length alone should
    not dominate semantic lesson coverage.
    """

    if ratio <= 0:
        return 0.0
    if 0.80 <= ratio <= 1.45:
        return 1.0
    if ratio < 0.80:
        return max(0.35, ratio / 0.80)
    # Above 1.45, decay gently to avoid instantly rejecting useful additions.
    return max(0.35, 1.0 - min(0.65, (ratio - 1.45) / 1.10))


@dataclass(frozen=True)
class SemanticScore:
    """Breakdown of a skill's semantic quality against one patch plan."""

    score: float
    critical_lesson_coverage: float
    evidence_grounding: float
    parent_lesson_retention: float
    actionability: float
    safety_validity: float
    non_redundancy: float
    conservative_delta: float
    coverage: float
    missing_critical_count: int
    remove_violation_count: int
    contradiction_count: int
    candidate_parent_ratio: float

    def to_dict(self) -> dict:
        data = asdict(self)
        data["score"] = round(self.score, 6)
        return data


def semantic_skill_score(report: dict, cfg: dict | None = None) -> SemanticScore:
    """Return a bounded semantic score from a skill-integration report.

    The score favors skill text that covers oracle-derived directives, preserves
    prior durable guidance, is actionable by the rollout agent, and avoids
    hidden-harness/tool-contract violations. It is intentionally independent of
    rollout fitness.
    """

    config = cfg or {}
    weights = {
        "critical_lesson_coverage": 0.35,
        "evidence_grounding": 0.30,
        "parent_lesson_retention": 0.10,
        "actionability": 0.15,
        "safety_validity": 0.05,
        "non_redundancy": 0.03,
        "conservative_delta": 0.02,
        **(config.get("weights") or {}),
    }
    metrics = (report or {}).get("metrics") or {}
    directive_rows = list((report or {}).get("directive_results") or [])
    parent_rows = list((report or {}).get("parent_directive_results") or [])
    coverage = max(0.0, min(1.0, _float(metrics.get("coverage"), 1.0)))
    parent_coverage = max(0.0, min(1.0, _float(metrics.get("parent_coverage"), coverage)))
    total = max(1, _int(metrics.get("total_directives"), 0))
    missing = max(0, _int(metrics.get("missing_critical_count"), 0))
    remove_violations = max(0, _int(metrics.get("remove_violation_count"), 0))
    contradictions = max(0, _int(metrics.get("contradiction_count"), 0))
    ratio = _float(metrics.get("candidate_parent_ratio"), 1.0)

    directive_depth = _directive_depth(directive_rows)
    parent_depth = _directive_depth(parent_rows)
    critical_depth = _critical_directive_depth(directive_rows)
    if missing:
        # Missing critical lessons should keep the score visibly below the top
        # band even when many generic words overlap.
        critical_depth *= max(0.0, 1.0 - min(0.75, 0.18 * missing))

    critical_lesson_coverage = critical_depth
    evidence_grounding = directive_depth
    # Length is an imperfect proxy for retention, but it catches catastrophic
    # over-compression. Semantic directive coverage carries the actual meaning.
    min_retention_ratio = _float(config.get("min_parent_retention_ratio", 0.75), 0.75)
    parent_lesson_retention = max(0.0, min(1.0, ratio / max(0.01, min_retention_ratio)))
    if parent_depth >= 0.995:
        actionability = directive_depth
    else:
        actionability = max(0.0, min(1.0, (directive_depth - parent_depth) / max(0.01, 1.0 - parent_depth)))
    safety_validity = 1.0
    if remove_violations:
        safety_validity -= min(0.8, 0.35 * remove_violations)
    if contradictions:
        safety_validity -= min(0.8, 0.35 * contradictions)
    safety_validity = max(0.0, safety_validity)

    non_redundancy = _length_quality(ratio)

    lower = _float(config.get("conservative_min_ratio", 0.60), 0.60)
    upper = _float(config.get("conservative_max_ratio", 1.60), 1.60)
    conservative_delta = 1.0 if lower <= ratio <= upper else 0.5

    score = (
        weights["critical_lesson_coverage"] * critical_lesson_coverage
        + weights["evidence_grounding"] * evidence_grounding
        + weights["parent_lesson_retention"] * parent_lesson_retention
        + weights["actionability"] * actionability
        + weights["safety_validity"] * safety_validity
        + weights["non_redundancy"] * non_redundancy
        + weights["conservative_delta"] * conservative_delta
    )
    # Safety is a gate, not a near-free additive credit. Also keep all scores
    # below the top band while critical oracle lessons remain missing.
    score *= 0.55 + 0.45 * safety_validity
    if missing:
        score *= max(0.0, 1.0 - min(0.65, 0.08 * missing))

    return SemanticScore(
        score=score,
        critical_lesson_coverage=critical_lesson_coverage,
        evidence_grounding=evidence_grounding,
        parent_lesson_retention=parent_lesson_retention,
        actionability=actionability,
        safety_validity=safety_validity,
        non_redundancy=non_redundancy,
        conservative_delta=conservative_delta,
        coverage=coverage,
        missing_critical_count=missing,
        remove_violation_count=remove_violations,
        contradiction_count=contradictions,
        candidate_parent_ratio=ratio,
    )


def select_child_skill_against_parent(
    *,
    parent_skill: str,
    candidate_skill: str,
    patch_plan: dict | None,
    execution_contract: SkillExecutionContract,
    integration_cfg: dict | None,
    selector_cfg: dict | None,
    child_integration_report: dict | None = None,
    generation: int | None = None,
    child_slot: int | None = None,
    stage: str = "mutation",
) -> tuple[str, dict]:
    """Return the skill text that should enter the lineage plus a decision.

    If there is no oracle-derived patch plan, the selector does not block
    exploratory initialization. Once a patch plan exists, the parent skill is the
    non-regression floor.
    """

    cfg = {
        "enabled": True,
        "min_improvement_margin": 0.02,
        "neutral_tolerance": 0.005,
        "min_coverage_gain_to_accept": 0.05,
        "reject_on_missing_critical_regression": True,
        "reject_on_remove_violation": True,
        "reject_on_contradiction": True,
        "uncertain_keeps_parent": True,
        **(selector_cfg or {}),
    }
    has_feedback = bool((patch_plan or {}).get("has_feedback"))
    parent_sha = _sha256_text(parent_skill)
    child_sha = _sha256_text(candidate_skill)

    base_record = {
        "schema_version": SEMANTIC_SELECTOR_VERSION,
        "enabled": bool(cfg.get("enabled", True)),
        "generation": generation,
        "child_slot": child_slot,
        "stage": stage,
        "parent_sha256": parent_sha,
        "candidate_sha256": child_sha,
        "has_feedback": has_feedback,
        "decision": "accept_child",
        "reasons": [],
        "rollout_fitness_used_for_selection": False,
    }

    if not cfg.get("enabled", True):
        base_record["decision"] = "accept_child_legacy_selector_disabled"
        base_record["reasons"].append("semantic_selector_disabled")
        return candidate_skill, base_record

    if not has_feedback:
        base_record["decision"] = "accept_child_no_oracle_feedback"
        base_record["reasons"].append("no_oracle_patch_plan")
        return candidate_skill, base_record

    parent_report = validate_skill_integration(
        candidate_skill=parent_skill,
        parent_skill=parent_skill,
        patch_plan=patch_plan,
        execution_contract=execution_contract,
        config=integration_cfg,
    )
    child_report = child_integration_report or validate_skill_integration(
        candidate_skill=candidate_skill,
        parent_skill=parent_skill,
        patch_plan=patch_plan,
        execution_contract=execution_contract,
        config=integration_cfg,
    )
    parent_score = semantic_skill_score(parent_report, cfg)
    child_score = semantic_skill_score(child_report, cfg)

    record = {
        **base_record,
        "parent_score": parent_score.to_dict(),
        "candidate_score": child_score.to_dict(),
        "score_delta": round(child_score.score - parent_score.score, 6),
        "parent_integration_ok": bool(parent_report.get("ok", False)),
        "candidate_integration_ok": bool(child_report.get("ok", False)),
        "parent_integration_issues": parent_report.get("issues", []),
        "candidate_integration_issues": child_report.get("issues", []),
    }

    if child_sha == parent_sha:
        record["decision"] = "keep_parent"
        record["reasons"].append("candidate_identical_to_parent")
        return parent_skill, record

    child_metrics = child_report.get("metrics") or {}
    parent_metrics = parent_report.get("metrics") or {}
    child_missing = _int(child_metrics.get("missing_critical_count"), 0)
    parent_missing = _int(parent_metrics.get("missing_critical_count"), 0)
    child_remove = _int(child_metrics.get("remove_violation_count"), 0)
    child_contradictions = _int(child_metrics.get("contradiction_count"), 0)
    coverage_gain = _float(child_metrics.get("coverage"), 0.0) - _float(parent_metrics.get("coverage"), 0.0)

    hard_reject = False
    if cfg.get("reject_on_missing_critical_regression", True) and child_missing > parent_missing:
        hard_reject = True
        record["reasons"].append(f"missing_critical_regressed:{parent_missing}->{child_missing}")
    if cfg.get("reject_on_remove_violation", True) and child_remove > 0:
        hard_reject = True
        record["reasons"].append(f"remove_violation_count:{child_remove}")
    if cfg.get("reject_on_contradiction", True) and child_contradictions > 0:
        hard_reject = True
        record["reasons"].append(f"contradiction_count:{child_contradictions}")
    if child_score.score + _float(cfg.get("neutral_tolerance"), 0.005) < parent_score.score:
        hard_reject = True
        record["reasons"].append("semantic_score_below_parent")

    if hard_reject:
        record["decision"] = "keep_parent"
        return parent_skill, record

    margin = _float(cfg.get("min_improvement_margin"), 0.02)
    min_coverage_gain = _float(cfg.get("min_coverage_gain_to_accept"), 0.05)
    if child_score.score >= parent_score.score + margin:
        record["decision"] = "accept_child"
        record["reasons"].append("semantic_score_improved")
        return candidate_skill, record

    if coverage_gain >= min_coverage_gain and child_score.score >= parent_score.score:
        record["decision"] = "accept_child"
        record["reasons"].append(f"coverage_gain_improved:{coverage_gain:.3f}")
        return candidate_skill, record

    record["decision"] = "keep_parent"
    record["reasons"].append("no_reliable_semantic_improvement")
    return parent_skill, record


def choose_semantic_incumbent(
    *,
    current_incumbent: Any,
    candidates: list[Any],
    cfg: dict | None = None,
) -> tuple[Any, dict]:
    """Choose the next semantic incumbent from accepted candidates.

    Candidate objects are expected to expose `prompt`, `parent_info`, and a
    `semantic_selection` dict. Rollout fitness is intentionally ignored.
    """

    config = cfg or {}
    if not candidates:
        return current_incumbent, {
            "decision": "keep_incumbent",
            "reason": "no_candidates",
            "rollout_fitness_used_for_selection": False,
        }

    def priority(ind: Any) -> tuple[float, float, int]:
        decision = getattr(ind, "semantic_selection", {}) or {}
        cand = decision.get("candidate_score") or {}
        delta = _float(decision.get("score_delta"), 0.0)
        score = _float(cand.get("score"), 0.0)
        length = len(getattr(ind, "prompt", "") or "")
        # Prefer higher semantic quality, then larger improvement, then shorter
        # equally good skills to avoid bloat.
        return (score, delta, -length)

    accepted = [
        ind for ind in candidates
        if (getattr(ind, "semantic_selection", {}) or {}).get("decision") == "accept_child"
    ]
    if not accepted:
        return current_incumbent, {
            "decision": "keep_incumbent",
            "reason": "no_accepted_semantic_children",
            "rollout_fitness_used_for_selection": False,
        }

    best = max(accepted, key=priority)
    incumbent_record = getattr(current_incumbent, "semantic_selection", {}) or {}
    best_record = getattr(best, "semantic_selection", {}) or {}
    min_delta = _float(config.get("incumbent_min_delta", 0.0), 0.0)
    if incumbent_record and best_record:
        incumbent_score = _float((incumbent_record.get("candidate_score") or {}).get("score"), 0.0)
        best_score = _float((best_record.get("candidate_score") or {}).get("score"), 0.0)
        if best_score + 1e-9 < incumbent_score + min_delta:
            return current_incumbent, {
                "decision": "keep_incumbent",
                "reason": "best_child_did_not_beat_incumbent",
                "incumbent_score": incumbent_score,
                "best_child_score": best_score,
                "rollout_fitness_used_for_selection": False,
            }

    return best, {
        "decision": "replace_incumbent",
        "reason": "accepted_child_has_best_semantic_priority",
        "selected_parent_info": getattr(best, "parent_info", ""),
        "selected_sha256": _sha256_text(getattr(best, "prompt", "") or ""),
        "semantic_selection": best_record,
        "rollout_fitness_used_for_selection": False,
    }

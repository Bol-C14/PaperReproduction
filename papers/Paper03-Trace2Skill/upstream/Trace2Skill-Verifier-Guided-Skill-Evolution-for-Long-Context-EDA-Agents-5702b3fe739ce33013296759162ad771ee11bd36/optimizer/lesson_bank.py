"""Persistent per-run lesson bank for skill evolution.

The optimizer already writes rich per-generation artifacts, but selection can
still choose a best-performing parent from an earlier generation. That is good
for rollout safety, yet it can drop later oracle lessons from the final skill.

This module keeps those durable lessons in a deterministic side channel:

rollouts -> oracle/change attribution/path grounding -> lesson bank
          -> mutation handoff + final distilled skill

It does not replace the evolutionary search. It makes sure evidence survives
long enough to be considered by the mutator and by downstream eval artifacts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable


LESSON_BANK_SCHEMA_VERSION = 1

RTL_PATH_RE = re.compile(r"(?:/?[A-Za-z0-9_.+\-]+/)+[A-Za-z0-9_.+\-]+\.(?:svh?|vh?)\b", re.IGNORECASE)
HIDDEN_ARTIFACT_RE = re.compile(r"(?:^|[\s`'\"(/])(?:/code/|code/)?(?:[\w./+\-]*/)?harness/|(?:test_runner|harness)\.py\b", re.IGNORECASE)
NEGATIVE_MARKERS = (
    "do not",
    "don't",
    "never",
    "must not",
    "avoid",
    "remove",
    "forbid",
    "hidden",
    "invisible",
    "unavailable",
)


def _now_generation(generation: int) -> int:
    return int(generation or 0)


def _clean_text(text: object) -> str:
    value = str(text or "").strip()
    value = re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" -")


def _key(text: str) -> str:
    return re.sub(r"\W+", " ", text.lower()).strip()


def _has_hidden_positive_leak(text: str) -> bool:
    lower = text.lower()
    if not HIDDEN_ARTIFACT_RE.search(text):
        return False
    return not any(marker in lower for marker in NEGATIVE_MARKERS)


def _dedupe_strings(items: Iterable[object], *, limit: int = 50) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        clean = _clean_text(item)
        if not clean:
            continue
        if _has_hidden_positive_leak(clean):
            continue
        key = _key(clean)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(clean)
        if len(result) >= limit:
            break
    return result


def _default_bank() -> dict:
    return {
        "schema_version": LESSON_BANK_SCHEMA_VERSION,
        "updated_generation": 0,
        "durable_lessons": [],
        "preserved_success_patterns": [],
        "forbidden_behaviors": [],
        "protected_path_rules": [],
        "recurring_failure_modes": [],
        "open_questions": [],
        "metric_history": [],
    }


def load_lesson_bank(output_dir: Path) -> dict:
    path = output_dir / "lesson_bank.json"
    if not path.exists():
        return _default_bank()
    try:
        with open(path, encoding="utf-8") as f:
            bank = json.load(f)
    except Exception:
        return _default_bank()
    if not isinstance(bank, dict):
        return _default_bank()
    merged = _default_bank()
    merged.update(bank)
    merged["schema_version"] = LESSON_BANK_SCHEMA_VERSION
    return merged


def _add_record(
    bank: dict,
    section: str,
    text: object,
    *,
    generation: int,
    source: str,
    cid: str | None = None,
    limit: int = 60,
) -> None:
    clean = _clean_text(text)
    if not clean:
        return
    if section != "forbidden_behaviors" and _has_hidden_positive_leak(clean):
        return
    key = _key(clean)
    if not key:
        return
    rows = bank.setdefault(section, [])
    for row in rows:
        if row.get("key") == key:
            row["last_generation"] = _now_generation(generation)
            row["count"] = int(row.get("count", 1)) + 1
            if source not in row.setdefault("sources", []):
                row["sources"].append(source)
            if cid and cid not in row.setdefault("cids", []):
                row["cids"].append(cid)
            return
    rows.append({
        "key": key,
        "text": clean,
        "first_generation": _now_generation(generation),
        "last_generation": _now_generation(generation),
        "count": 1,
        "sources": [source],
        "cids": [cid] if cid else [],
    })
    rows.sort(key=lambda row: (-int(row.get("count", 0)), int(row.get("first_generation", 0)), row.get("text", "")))
    del rows[limit:]


def _read_json(path: Path | None) -> dict:
    if not path or not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            value = json.load(f)
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _patch_plan_items(skill_patch_plan: dict | None, key: str) -> list[str]:
    if not isinstance(skill_patch_plan, dict):
        return []
    value = skill_patch_plan.get(key) or []
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _extract_open_questions(text: str | None, *, limit: int = 12) -> list[str]:
    if not text:
        return []
    questions = []
    in_question_section = False
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            in_question_section = "question" in stripped.lower() or "uncertain" in stripped.lower()
            continue
        if in_question_section and re.match(r"^\s*(?:[-*]|\d+[.)])\s+\S", raw):
            questions.append(stripped)
        elif "?" in stripped and len(stripped) < 220:
            questions.append(stripped)
    return _dedupe_strings(questions, limit=limit)


def _metric_snapshot(generation: int, generation_metrics: dict) -> dict:
    path_grounding = generation_metrics.get("path_grounding") or {}
    return {
        "generation": _now_generation(generation),
        "selection_fitness": generation_metrics.get("selection_fitness", {}),
        "pass_rate": generation_metrics.get("pass_rate", {}),
        "progress_fitness": generation_metrics.get("progress_fitness", {}),
        "path_grounding_issue_count": int(path_grounding.get("issue_count", 0) or 0),
        "path_grounding_by_code": path_grounding.get("by_code", {}),
        "cids": generation_metrics.get("cids", []),
    }


def update_lesson_bank(
    *,
    output_dir: Path,
    gen_dir: Path,
    generation: int,
    task_manifest: list[dict],
    generation_metrics_path: Path | None = None,
    oracle_feedback_text: str | None = None,
    skill_patch_plan: dict | None = None,
    change_eval: dict | None = None,
) -> dict:
    """Update and persist durable lessons for one generation.

    Inputs are intentionally the same artifacts already written by the pipeline.
    If any optional artifact is missing, the bank still records deterministic
    metric/path evidence and leaves the natural-language sections unchanged.
    """
    bank = load_lesson_bank(output_dir)
    bank["updated_generation"] = max(int(bank.get("updated_generation", 0) or 0), _now_generation(generation))

    cids = sorted({str(row.get("cid")) for row in task_manifest if row.get("cid")})
    cid = cids[0] if len(cids) == 1 else None

    for item in _patch_plan_items(skill_patch_plan, "must_add"):
        _add_record(bank, "durable_lessons", item, generation=generation, source=f"gen{generation}:skill_patch_plan.must_add", cid=cid)
    for item in _patch_plan_items(skill_patch_plan, "must_preserve"):
        _add_record(bank, "preserved_success_patterns", item, generation=generation, source=f"gen{generation}:skill_patch_plan.must_preserve", cid=cid)
    for item in _patch_plan_items(skill_patch_plan, "must_remove"):
        _add_record(bank, "forbidden_behaviors", item, generation=generation, source=f"gen{generation}:skill_patch_plan.must_remove", cid=cid)

    for question in _extract_open_questions(oracle_feedback_text):
        _add_record(bank, "open_questions", question, generation=generation, source=f"gen{generation}:oracle_feedback", cid=cid, limit=30)

    if isinstance(change_eval, dict):
        for row in (change_eval.get("actionable_items") or change_eval.get("findings") or []):
            if isinstance(row, dict):
                text = row.get("recommendation") or row.get("summary") or row.get("text")
            else:
                text = row
            _add_record(bank, "durable_lessons", text, generation=generation, source=f"gen{generation}:change_attribution", cid=cid)

    metrics = _read_json(generation_metrics_path or (gen_dir / "generation_metrics.json"))
    if metrics:
        history = bank.setdefault("metric_history", [])
        history.append(_metric_snapshot(generation, metrics))
        seen_gens = set()
        deduped = []
        for row in sorted(history, key=lambda r: int(r.get("generation", 0))):
            gen_key = int(row.get("generation", 0) or 0)
            if gen_key in seen_gens:
                deduped[-1] = row
            else:
                seen_gens.add(gen_key)
                deduped.append(row)
        bank["metric_history"] = deduped[-20:]

        grounding = metrics.get("path_grounding") or {}
        for code, count in (grounding.get("by_code") or {}).items():
            if int(count or 0) <= 0:
                continue
            _add_record(
                bank,
                "recurring_failure_modes",
                f"{code}: observed {count} path-grounding issue(s) in generation {generation}.",
                generation=generation,
                source=f"gen{generation}:path_grounding",
                cid=cid,
            )
        for example in grounding.get("examples") or []:
            expected = example.get("expected")
            observed = example.get("observed")
            observed_text = ", ".join(str(x) for x in observed[:3]) if isinstance(observed, list) else str(observed or "")
            if expected:
                _add_record(
                    bank,
                    "protected_path_rules",
                    (
                        f"Use the prompt-discovered target path `{expected}`; "
                        f"do not edit or validate only same-basename shadow paths"
                        f"{' such as ' + observed_text if observed_text else ''}."
                    ),
                    generation=generation,
                    source=f"gen{generation}:path_grounding",
                    cid=str(example.get("cid") or cid or ""),
                )

    write_lesson_bank_artifacts(output_dir=output_dir, gen_dir=gen_dir, bank=bank)
    return bank


def _top_records(bank: dict, section: str, limit: int) -> list[dict]:
    rows = bank.get(section) or []
    if not isinstance(rows, list):
        return []
    return sorted(
        [row for row in rows if isinstance(row, dict) and row.get("text")],
        key=lambda row: (-int(row.get("count", 0)), -int(row.get("last_generation", 0)), row.get("text", "")),
    )[:limit]


def format_lesson_bank_for_mutation(bank: dict, *, max_chars: int = 7000) -> str:
    """Render the durable lesson bank as a compact mutation handoff addendum."""
    lines = [
        "## Persistent CID Lesson Bank",
        "",
        "These lessons are cumulative across prior generations. Treat them as durable evidence unless the latest oracle explicitly contradicts them.",
    ]
    sections = [
        ("Durable lessons to integrate", "durable_lessons", 12),
        ("Preserve success patterns", "preserved_success_patterns", 8),
        ("Forbidden or inaccessible behaviors", "forbidden_behaviors", 10),
        ("Protected target/path rules", "protected_path_rules", 10),
        ("Recurring failure modes", "recurring_failure_modes", 8),
        ("Open questions to keep diagnostic", "open_questions", 6),
    ]
    for title, key, limit in sections:
        records = _top_records(bank, key, limit)
        if not records:
            continue
        lines.extend(["", f"### {title}"])
        for row in records:
            gen = row.get("last_generation")
            count = row.get("count", 1)
            lines.append(f"- {row['text']} (seen {count}x; latest gen {gen})")

    text = "\n".join(lines).strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit("\n", 1)[0].strip() + "\n- [truncated: lesson bank exceeded mutation handoff budget]"


def _strip_title(skill_text: str) -> str:
    lines = skill_text.strip().splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].lstrip().startswith("#"):
        lines = lines[1:]
    return "\n".join(lines).strip()


def distill_final_skill(
    *,
    best_skill: str,
    lesson_bank: dict,
    max_chars: int = 18000,
) -> str:
    """Combine the best observed skill with durable learned lessons.

    The returned skill is deterministic and intentionally simple: durable
    lessons first, then the best-performing skill body. Existing sanitizer and
    integration gates still govern candidate mutations; this final distillation
    just prevents late verified lessons from being lost because an older parent
    had better sampled rollout fitness.
    """
    lesson_text = format_lesson_bank_for_mutation(lesson_bank, max_chars=max(3000, max_chars // 3))
    body = _strip_title(best_skill)
    header = [
        "# Distilled Optimized Skill",
        "",
        "## Learned Run Lessons",
        "",
        "Follow these accumulated lessons first when they are relevant to the task. They are mined from prior rollout success/failure summaries, path-grounding diagnostics, and oracle handoffs.",
        "",
        lesson_text,
        "",
        "## Base Skill",
        "",
    ]
    result = "\n".join(header) + body.strip() + "\n"
    if len(result) <= max_chars:
        return result

    budget_for_body = max(2000, max_chars - len("\n".join(header)) - 200)
    trimmed_body = body[:budget_for_body].rsplit("\n", 1)[0].strip()
    result = "\n".join(header) + trimmed_body + "\n"
    if len(result) <= max_chars:
        return result
    return result[:max_chars].rsplit("\n", 1)[0].strip() + "\n"


def write_lesson_bank_artifacts(*, output_dir: Path, gen_dir: Path | None, bank: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "lesson_bank.json", "w", encoding="utf-8") as f:
        json.dump(bank, f, indent=2, ensure_ascii=False)
    markdown = format_lesson_bank_for_mutation(bank, max_chars=12000) + "\n"
    (output_dir / "lesson_bank.md").write_text(markdown, encoding="utf-8")
    if gen_dir is not None:
        gen_dir.mkdir(parents=True, exist_ok=True)
        with open(gen_dir / "lesson_bank.json", "w", encoding="utf-8") as f:
            json.dump(bank, f, indent=2, ensure_ascii=False)
        (gen_dir / "lesson_bank.md").write_text(markdown, encoding="utf-8")


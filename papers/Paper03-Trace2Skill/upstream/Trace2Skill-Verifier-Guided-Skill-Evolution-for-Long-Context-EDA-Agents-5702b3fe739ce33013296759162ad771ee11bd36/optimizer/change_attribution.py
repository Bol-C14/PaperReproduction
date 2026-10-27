"""AHE-style attribution for Trace2Skill skill mutations.

The optimizer already records what happened in each generation: rollout
outcomes, dense progress, oracle summaries, mutation health, and the final
skill injected into each individual. This module adds the missing causal audit
layer:

    prior oracle/patch plan -> accepted child skill -> next rollout metrics
    -> did the change fix what it was supposed to fix?

The implementation is intentionally deterministic and best-effort. It does not
call an LLM, does not alter fitness, and should never be required for rollouts
to proceed unless a future experiment explicitly chooses a fail-closed policy.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Iterable


CID_RE = re.compile(r"cid\d{3}", re.IGNORECASE)
SCHEMA_VERSION = 1


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, tuple):
        return [_json_safe(v) for v in obj]
    return obj


def _write_json(path: Path, data: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_json_safe(data), f, indent=2, ensure_ascii=False)


def _read_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _rel(path: Path | None, root: Path) -> str | None:
    if path is None:
        return None
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _short_task_id(task_id: str | None) -> str:
    return (task_id or "unknown").replace("cvdp_agentic_heavy_", "")


def _find_cid(*values: Any) -> str | None:
    for value in values:
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            found = _find_cid(*value)
            if found:
                return found
            continue
        match = CID_RE.search(str(value))
        if match:
            return match.group(0).lower()
    return None


def _sha256_text(text: str | None) -> str | None:
    if text is None:
        return None
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _metric_from_result(result: dict | None, key: str, default: float = 0.0) -> float:
    if not isinstance(result, dict):
        return default
    if key in result:
        return _safe_float(result.get(key), default)
    if key == "selection_fitness":
        return _safe_float(result.get("fitness"), default)
    return default


def per_task_rates(result: dict | None) -> dict[str, dict]:
    """Normalize an optimizer fitness_result per_task block."""
    rows: dict[str, dict] = {}
    if not isinstance(result, dict):
        return rows
    per_task = result.get("per_task") or {}
    if not isinstance(per_task, dict):
        return rows
    for task_id, raw in per_task.items():
        short = _short_task_id(str(task_id))
        if isinstance(raw, dict):
            pass_rate = _safe_float(raw.get("pass_at_1", raw.get("pass_rate", 0.0)))
            pass_at_k = _safe_float(raw.get("pass_at_k", pass_rate))
            attempts = int(_safe_float(raw.get("attempts", 0), 0))
            passes = int(_safe_float(raw.get("passes", 0), 0))
        else:
            pass_rate = _safe_float(raw)
            pass_at_k = pass_rate
            attempts = 0
            passes = 0
        rows[short] = {
            "task_id": str(task_id),
            "short_task_id": short,
            "pass_rate": pass_rate,
            "pass_at_k": pass_at_k,
            "attempts": attempts,
            "passes": passes,
        }
    return rows


def _task_cid_lookup(task_manifest: list[dict]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for row in task_manifest:
        cid = _find_cid(row.get("cid"), row.get("categories"), row.get("task_id"), row.get("short_task_id")) or "unknown"
        task_id = str(row.get("task_id") or "unknown")
        short = str(row.get("short_task_id") or _short_task_id(task_id))
        lookup[task_id] = cid
        lookup[short] = cid
    return lookup


def _load_prior_patch_plan(output_dir: Path, generation: int) -> tuple[dict | None, dict]:
    source_gen = generation - 1
    if source_gen < 1:
        return None, {"source_generation": source_gen, "status": "no_prior_generation"}
    source_dir = output_dir / f"gen{source_gen}"
    patch_path = source_dir / "skill_patch_plan.json"
    handoff_path = source_dir / "mutation_handoff.md"
    oracle_path = source_dir / "oracle_feedback.md"
    patch = _read_json(patch_path)
    return patch, {
        "source_generation": source_gen,
        "status": "loaded" if patch else "missing_patch_plan",
        "skill_patch_plan": _rel(patch_path, output_dir) if patch_path.exists() else None,
        "mutation_handoff": _rel(handoff_path, output_dir) if handoff_path.exists() else None,
        "oracle_feedback": _rel(oracle_path, output_dir) if oracle_path.exists() else None,
    }


def _summarize_patch_plan(patch_plan: dict | None, limit: int = 8) -> dict:
    data = patch_plan or {}
    return {
        "has_feedback": bool(data.get("has_feedback")),
        "must_add": list(data.get("must_add") or [])[:limit],
        "must_preserve": list(data.get("must_preserve") or [])[:limit],
        "must_remove": list(data.get("must_remove") or [])[:limit],
        "concrete_terms": list(data.get("concrete_terms") or [])[:limit],
        "source_chars": int(_safe_float(data.get("source_chars", 0), 0)),
    }


def _changed_kind(origin: str, same_skill: bool) -> str:
    if same_skill:
        return "unchanged"
    origin = origin or ""
    has_mutation = "mutation" in origin
    has_crossover = "crossover" in origin
    if has_mutation and has_crossover:
        return "crossover+mutation"
    if has_mutation:
        return "mutation"
    if has_crossover:
        return "crossover"
    if "elite" in origin:
        return "elite"
    return "skill_change"


def _predicted_task_sets(parent_rates: dict[str, dict], patch_plan: dict | None) -> tuple[list[str], list[str]]:
    """Derive broad deterministic predictions from the prior oracle patch plan.

    The current mutator does not yet author free-form predicted task lists, so
    attribution starts from a conservative proxy: the prior patch plan is meant
    to fix tasks that were not already solved, while already-solved tasks are
    the obvious regression-risk set.
    """
    if not parent_rates or not (patch_plan or {}).get("has_feedback"):
        return [], []
    predicted = sorted(
        task for task, row in parent_rates.items()
        if _safe_float(row.get("pass_rate")) < 1.0
    )
    risks = sorted(
        task for task, row in parent_rates.items()
        if _safe_float(row.get("pass_rate")) >= 1.0 or _safe_float(row.get("pass_rate")) > 0.0
    )
    return predicted, risks


def build_generation_change_manifest(
    *,
    output_dir: Path,
    generation: int,
    population: Iterable[Any],
    task_manifest: list[dict],
) -> dict:
    """Build a manifest for the incoming skills evaluated in this generation."""
    patch_plan, source_artifacts = _load_prior_patch_plan(output_dir, generation)
    patch_summary = _summarize_patch_plan(patch_plan)
    cid_lookup = _task_cid_lookup(task_manifest)
    changes = []

    for sorted_rank, ind in enumerate(population):
        result = getattr(ind, "fitness_result", None) or {}
        eval_index = result.get("individual_index", sorted_rank)
        try:
            eval_index = int(eval_index)
        except (TypeError, ValueError):
            eval_index = sorted_rank

        parent_prompt = getattr(ind, "parent_prompt", None)
        child_prompt = getattr(ind, "prompt", "") or ""
        parent_result = getattr(ind, "parent_fitness_result", None) or {}
        current_result = result if isinstance(result, dict) else {}
        parent_rates = per_task_rates(parent_result)
        current_rates = per_task_rates(current_result)
        all_task_keys = sorted(set(parent_rates) | set(current_rates))
        cids = sorted({
            cid_lookup.get(task)
            or cid_lookup.get((current_rates.get(task) or parent_rates.get(task) or {}).get("task_id"))
            or "unknown"
            for task in all_task_keys
        }) or sorted({row.get("cid") for row in task_manifest if row.get("cid")}) or ["unknown"]
        same_skill = bool(parent_prompt) and _sha256_text(parent_prompt) == _sha256_text(child_prompt)
        predicted_fixes, risk_tasks = _predicted_task_sets(parent_rates, patch_plan)
        origin = getattr(ind, "child_origin", "") or getattr(ind, "parent_info", "") or ""
        if not parent_prompt:
            change_type = "seed_baseline" if "original" in origin else "unattributed_initial"
        else:
            change_type = _changed_kind(origin, same_skill)

        changes.append({
            "id": f"gen{generation}_ind{eval_index}",
            "schema_version": SCHEMA_VERSION,
            "generation": generation,
            "source_generation": source_artifacts.get("source_generation"),
            "individual_index": eval_index,
            "sorted_rank": sorted_rank + 1,
            "cid": cids[0] if len(cids) == 1 else "multi",
            "cids": cids,
            "change_type": change_type,
            "child_origin": origin,
            "parent_info": getattr(ind, "parent_info", ""),
            "parent_sha256": getattr(ind, "parent_sha256", None) or _sha256_text(parent_prompt),
            "child_sha256": _sha256_text(child_prompt),
            "same_as_parent": same_skill,
            "parent_chars": len(parent_prompt or ""),
            "child_chars": len(child_prompt),
            "delta_chars": len(child_prompt) - len(parent_prompt or ""),
            "source_artifacts": source_artifacts,
            "oracle_patch_summary": patch_summary,
            "failure_patterns_targeted": (
                patch_summary["must_add"]
                + patch_summary["must_remove"]
                + patch_summary["must_preserve"]
            )[:12],
            "predicted_fixes": predicted_fixes,
            "risk_tasks": risk_tasks,
            "parent_metrics": {
                "selection_fitness": _metric_from_result(parent_result, "selection_fitness"),
                "pass_at_1": _metric_from_result(parent_result, "pass_at_1"),
                "progress_fitness": _metric_from_result(parent_result, "progress_fitness"),
                "per_task": parent_rates,
            },
            "current_metrics": {
                "selection_fitness": _metric_from_result(current_result, "selection_fitness", getattr(ind, "fitness", 0.0)),
                "pass_at_1": _metric_from_result(current_result, "pass_at_1"),
                "progress_fitness": _metric_from_result(current_result, "progress_fitness"),
                "per_task": current_rates,
            },
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "generation": generation,
        "source_generation": source_artifacts.get("source_generation"),
        "purpose": "Incoming skill-change manifest for skills evaluated in this generation.",
        "source_artifacts": source_artifacts,
        "task_count": len(task_manifest),
        "changes": sorted(changes, key=lambda row: row.get("individual_index", 0)),
    }


def _task_delta_rows(change: dict) -> list[dict]:
    parent = ((change.get("parent_metrics") or {}).get("per_task") or {})
    current = ((change.get("current_metrics") or {}).get("per_task") or {})
    rows = []
    for task in sorted(set(parent) | set(current)):
        p = parent.get(task) or {}
        c = current.get(task) or {}
        parent_rate = _safe_float(p.get("pass_rate"))
        current_rate = _safe_float(c.get("pass_rate"))
        rows.append({
            "task": task,
            "parent_pass_rate": parent_rate,
            "current_pass_rate": current_rate,
            "pass_rate_delta": round(current_rate - parent_rate, 6),
            "parent_passes": int(_safe_float(p.get("passes", 0), 0)),
            "current_passes": int(_safe_float(c.get("passes", 0), 0)),
            "parent_attempts": int(_safe_float(p.get("attempts", 0), 0)),
            "current_attempts": int(_safe_float(c.get("attempts", 0), 0)),
        })
    return rows


def evaluate_change_manifest(manifest: dict, config: dict | None = None) -> dict:
    """Score whether each manifest change did what it predicted."""
    cfg = {
        "pass_rate_improvement_threshold": 0.001,
        "pass_rate_regression_threshold": 0.001,
        "dense_progress_threshold": 0.03,
        "selection_threshold": 0.03,
        **(config or {}),
    }
    pass_improve = float(cfg["pass_rate_improvement_threshold"])
    pass_regress = float(cfg["pass_rate_regression_threshold"])
    dense_threshold = float(cfg["dense_progress_threshold"])
    selection_threshold = float(cfg["selection_threshold"])

    evaluations = []
    for change in manifest.get("changes") or []:
        task_deltas = _task_delta_rows(change)
        predicted = set(change.get("predicted_fixes") or [])
        risks = set(change.get("risk_tasks") or [])
        fixed = [
            row for row in task_deltas
            if row["task"] in predicted and row["pass_rate_delta"] >= pass_improve
        ]
        regressions = [
            row for row in task_deltas
            if (row["task"] in risks or not risks) and row["pass_rate_delta"] <= -pass_regress
        ]
        parent_metrics = change.get("parent_metrics") or {}
        current_metrics = change.get("current_metrics") or {}
        selection_delta = _safe_float(current_metrics.get("selection_fitness")) - _safe_float(parent_metrics.get("selection_fitness"))
        pass_delta = _safe_float(current_metrics.get("pass_at_1")) - _safe_float(parent_metrics.get("pass_at_1"))
        progress_delta = _safe_float(current_metrics.get("progress_fitness")) - _safe_float(parent_metrics.get("progress_fitness"))

        if change.get("change_type") in {"seed_baseline", "unattributed_initial"}:
            verdict = "NO_BASELINE"
        elif change.get("same_as_parent"):
            verdict = "UNCHANGED"
        elif not predicted and not task_deltas:
            verdict = "NO_BASELINE"
        elif regressions and not fixed and selection_delta <= -selection_threshold:
            verdict = "HARMFUL"
        elif fixed and regressions:
            verdict = "MIXED"
        elif fixed or pass_delta >= pass_improve or progress_delta >= dense_threshold or selection_delta >= selection_threshold:
            verdict = "EFFECTIVE"
        elif abs(selection_delta) < selection_threshold and abs(progress_delta) < dense_threshold and not fixed and not regressions:
            verdict = "INEFFECTIVE"
        else:
            verdict = "PARTIALLY_EFFECTIVE"

        evaluations.append({
            "id": change.get("id"),
            "generation": change.get("generation"),
            "individual_index": change.get("individual_index"),
            "cid": change.get("cid"),
            "cids": change.get("cids") or [],
            "change_type": change.get("change_type"),
            "verdict": verdict,
            "selection_delta": round(selection_delta, 6),
            "pass_at_1_delta": round(pass_delta, 6),
            "progress_fitness_delta": round(progress_delta, 6),
            "predicted_fixes": sorted(predicted),
            "actually_fixed": fixed,
            "risk_tasks": sorted(risks),
            "regressions": regressions,
            "task_deltas": task_deltas,
            "source_artifacts": change.get("source_artifacts") or {},
            "failure_patterns_targeted": change.get("failure_patterns_targeted") or [],
        })

    verdict_counts: dict[str, int] = {}
    for row in evaluations:
        verdict_counts[row["verdict"]] = verdict_counts.get(row["verdict"], 0) + 1
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "generation": manifest.get("generation"),
        "source_generation": manifest.get("source_generation"),
        "status": "ok" if evaluations else "no_evaluable_changes",
        "config": cfg,
        "summary": {
            "num_changes": len(evaluations),
            "verdict_counts": dict(sorted(verdict_counts.items())),
            "effective_or_mixed": sum(1 for row in evaluations if row["verdict"] in {"EFFECTIVE", "MIXED", "PARTIALLY_EFFECTIVE"}),
            "harmful": sum(1 for row in evaluations if row["verdict"] == "HARMFUL"),
            "unchanged": sum(1 for row in evaluations if row["verdict"] == "UNCHANGED"),
        },
        "evaluations": evaluations,
    }


def format_change_evaluation_markdown(evaluation: dict) -> str:
    lines = [
        f"# Change Evaluation — Generation {evaluation.get('generation')}",
        "",
        f"Source generation: {evaluation.get('source_generation')}",
        f"Status: {evaluation.get('status')}",
        "",
        "## Summary",
        "",
    ]
    counts = (evaluation.get("summary") or {}).get("verdict_counts") or {}
    if counts:
        lines.extend(f"- {verdict}: {count}" for verdict, count in sorted(counts.items()))
    else:
        lines.append("- No evaluable skill changes.")
    lines.extend(["", "## Per-Change Attribution", ""])
    for row in evaluation.get("evaluations") or []:
        lines.append(
            f"### {row.get('id')} — {row.get('verdict')} "
            f"({row.get('change_type')}, {row.get('cid')})"
        )
        lines.append(
            f"- Deltas: selection={row.get('selection_delta'):+.3f}, "
            f"pass={row.get('pass_at_1_delta'):+.3f}, "
            f"progress={row.get('progress_fitness_delta'):+.3f}"
        )
        fixed = row.get("actually_fixed") or []
        regressions = row.get("regressions") or []
        if fixed:
            lines.append("- Predicted fixes observed: " + ", ".join(f"{r['task']} ({r['pass_rate_delta']:+.2f})" for r in fixed))
        if regressions:
            lines.append("- Regressions observed: " + ", ".join(f"{r['task']} ({r['pass_rate_delta']:+.2f})" for r in regressions))
        patterns = row.get("failure_patterns_targeted") or []
        if patterns:
            lines.append("- Targeted patterns:")
            lines.extend(f"  - {item}" for item in patterns[:5])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_change_evaluation_for_mutation(evaluation: dict, limit: int = 6) -> str:
    """Compact handoff text for the next mutator call."""
    rows = evaluation.get("evaluations") or []
    if not rows:
        return ""
    lines = [
        f"## Prior Skill-Change Attribution (Gen {evaluation.get('generation')})",
        "",
        "Use this as causal feedback on the previous mutation. Preserve effective changes, isolate mixed changes, and rollback or rewrite harmful changes.",
        "",
    ]
    for row in rows[:limit]:
        lines.append(
            f"- {row.get('id')} [{row.get('cid')}] {row.get('verdict')}: "
            f"selection {row.get('selection_delta'):+.3f}, "
            f"pass {row.get('pass_at_1_delta'):+.3f}, "
            f"progress {row.get('progress_fitness_delta'):+.3f}."
        )
        fixed = row.get("actually_fixed") or []
        regressions = row.get("regressions") or []
        if fixed:
            lines.append("  Fixed predicted tasks: " + ", ".join(r["task"] for r in fixed[:4]) + ".")
        if regressions:
            lines.append("  Regressed tasks: " + ", ".join(r["task"] for r in regressions[:4]) + ".")
    return "\n".join(lines).strip()


def write_change_attribution_artifacts(
    *,
    output_dir: Path,
    gen_dir: Path,
    generation: int,
    population: Iterable[Any],
    task_manifest: list[dict],
    config: dict | None = None,
) -> dict:
    """Write manifest + evaluation artifacts for the evaluated generation."""
    manifest = build_generation_change_manifest(
        output_dir=output_dir,
        generation=generation,
        population=population,
        task_manifest=task_manifest,
    )
    evaluation = evaluate_change_manifest(manifest, config=config)

    _write_json(gen_dir / "change_manifest.json", manifest)
    child_dir = gen_dir / "change_manifests"
    for change in manifest.get("changes") or []:
        _write_json(child_dir / f"ind{change.get('individual_index')}.json", change)

    _write_json(gen_dir / "change_evaluation.json", evaluation)
    (gen_dir / "change_evaluation.md").write_text(
        format_change_evaluation_markdown(evaluation),
        encoding="utf-8",
    )
    _write_json(output_dir / "latest_change_evaluation.json", {
        "generation": generation,
        "path": _rel(gen_dir / "change_evaluation.json", output_dir),
        "summary": evaluation.get("summary") or {},
    })
    return evaluation

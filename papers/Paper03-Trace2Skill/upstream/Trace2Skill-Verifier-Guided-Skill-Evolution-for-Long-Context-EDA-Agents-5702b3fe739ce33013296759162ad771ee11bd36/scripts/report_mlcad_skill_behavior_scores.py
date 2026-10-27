#!/usr/bin/env python3
"""Report semantic skill quality and agent behavior quality for EA runs.

The paper needs two disentangled views:

1. Skill quality/provenance: did the post-oracle, post-mutator child skill
   preserve the parent and add grounded lessons from the previous generation?
   In the simplified EA flow, this is audit metadata for evaluated children;
   the generation survivor itself is selected by rollout fitness only after
   evaluation.

2. Agent behavior quality: given a skill, how well did the rollout agent behave?
   This is read from eval summaries and includes dense progress, path grounding,
   pass rate, and available skill-adherence telemetry. It remains rollout-side
   evidence and is not used as the semantic child-vs-parent selector.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "eval"))
sys.path.insert(0, str(REPO_ROOT / "optimizer"))

from convert_rollouts import compute_progress_metrics  # noqa: E402
from path_grounding import analyze_path_grounding  # noqa: E402
from skill_selector import semantic_skill_score  # noqa: E402


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    try:
        with path.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
    except Exception:
        return rows
    return rows


def _mean(values: list[float]) -> float | None:
    clean = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if not clean:
        return None
    return sum(clean) / len(clean)


def _std(values: list[float]) -> float | None:
    clean = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if len(clean) < 2:
        return 0.0 if clean else None
    mu = sum(clean) / len(clean)
    return math.sqrt(sum((v - mu) ** 2 for v in clean) / (len(clean) - 1))


def _weighted_mean(items: list[tuple[float, int]]) -> float | None:
    total_weight = sum(max(0, int(w)) for _, w in items)
    if total_weight <= 0:
        return None
    return sum(float(v) * max(0, int(w)) for v, w in items) / total_weight


def _path_grounding_rollout_score(analysis: dict) -> float:
    if not analysis.get("expected_targets"):
        return 1.0
    if not analysis.get("issues"):
        return 1.0
    if analysis.get("has_critical_issue"):
        return 0.15
    return 0.60


def _parse_call_args(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _raw_tool_calls(rollout: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Return function calls from a raw rollout response.

    This intentionally mirrors the deterministic tool-call view used by the
    runtime skill monitor, but it stays post-hoc: no feedback was injected into
    these no-guardrail EA rollouts.
    """

    calls: list[tuple[str, dict[str, Any]]] = []
    for item in ((rollout.get("response") or {}).get("output") or []):
        if not isinstance(item, dict) or item.get("type") != "function_call":
            continue
        calls.append((str(item.get("name") or ""), _parse_call_args(item.get("arguments"))))
    return calls


def _call_path(args: dict[str, Any]) -> str:
    value = str(args.get("filename") or args.get("path") or "").replace("\\", "/")
    if value.startswith("/code/"):
        value = value[len("/code/"):]
    elif value.startswith("code/"):
        value = value[len("code/"):]
    elif value.startswith("./"):
        value = value[2:]
    return value.strip().strip("\"'`").strip("/")


def _is_testbench_path(path: str) -> bool:
    low = path.lower()
    name = low.rsplit("/", 1)[-1]
    return (
        "testbench" in low
        or name.startswith("tb_")
        or "_tb" in name
        or "/tb/" in low
        or "/test/" in low
        or "/tests/" in low
        or "/verif/" in low
    )


def _posthoc_skill_adherence_score(rollout: dict[str, Any]) -> float:
    """Estimate skill adherence from artifacts when monitor telemetry is absent.

    The official guardrail telemetry is preferred whenever present. For older
    or no-guardrail EA runs, this fallback scores only high-confidence,
    observable process adherence:

    * the rollout read the injected SKILL.md,
    * writes/compiles stayed on the prompt-discovered target path,
    * the expected target was actually edited when an edit occurred,
    * self-authored testbenches were not used as the sole source of confidence.

    The metric is capped to [0, 1] and should be read as an artifact-derived
    adherence estimate, not as proof that runtime blocking was active.
    """

    score = 1.0
    calls = _raw_tool_calls(rollout)
    if not any(name == "cat" and _call_path(args).endswith("SKILL.md") for name, args in calls):
        score -= 0.10

    grounding = analyze_path_grounding(rollout)
    codes = [str(issue.get("code") or "") for issue in grounding.get("issues") or []]
    if "wrong_target_path" in codes:
        score -= 0.30
    if "validation_on_wrong_path" in codes:
        score -= 0.25
    if "missing_expected_write" in codes:
        score -= 0.20
    if "shadow_target_path" in codes:
        score -= 0.10

    wrote_custom_tb = any(
        name in {"echo", "edit"} and _is_testbench_path(_call_path(args))
        for name, args in calls
    )
    if wrote_custom_tb:
        # A small penalty covers the common "private TB confidence" failure.
        # It is larger if the rollout also missed or shadowed the real target.
        if any(code in codes for code in ("wrong_target_path", "missing_expected_write")):
            score -= 0.10
        else:
            score -= 0.04

    return max(0.0, min(1.0, score))


def _posthoc_skill_adherence_for_generation(gen_dir: Path) -> float | None:
    scores: list[float] = []
    for rollout_path in sorted(gen_dir.glob("rollouts/ind*/rollouts_gen*_ind*.jsonl")):
        if "materialized" in rollout_path.name or "reward" in rollout_path.name:
            continue
        if ".invalid_attempt" in rollout_path.name:
            continue
        scores.extend(_posthoc_skill_adherence_score(row) for row in _load_raw_rollouts(rollout_path))
    return _mean(scores)


def _load_raw_rollouts(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
    except Exception:
        return rows
    return rows


def _single_rollout_behavior_score(record: dict[str, Any]) -> float:
    """Dense behavior score for one repeat, path-adjusted like optimizer fitness."""

    pass_at_1 = 1.0 if float(record.get("reward") or 0.0) > 0 else 0.0
    metrics = compute_progress_metrics([record], pass_at_1=pass_at_1, unique_tasks=1)
    progress = float(metrics.get("progress_fitness") or 0.0)
    path_score = _path_grounding_rollout_score(analyze_path_grounding(record))
    return progress * (0.55 + 0.45 * path_score)


def _repeat_variance_for_generation(gen_dir: Path) -> float | None:
    """Mean repeat-level std within each individual skill.

    Higher values mean repeated rollouts under the same skill are less stable.
    This is the variance metric we want to keep separate from skill adherence.
    """

    per_individual_std: list[float] = []
    for rollout_path in sorted(gen_dir.glob("rollouts/ind*/rollouts_gen*_ind*.jsonl")):
        if "materialized" in rollout_path.name or "reward" in rollout_path.name:
            continue
        if ".invalid_attempt" in rollout_path.name:
            continue
        scores = [_single_rollout_behavior_score(row) for row in _load_raw_rollouts(rollout_path)]
        if scores:
            per_individual_std.append(_std(scores) or 0.0)
    return _mean(per_individual_std)


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        if not math.isfinite(value):
            return "N/A"
        return f"{value:.{digits}f}"
    return str(value)


def _task_short(task_id: str) -> str:
    return task_id.replace("cvdp_agentic_heavy_", "")


def _generation_number(path: Path) -> int:
    name = path.name
    return int(name[3:]) if name.startswith("gen") and name[3:].isdigit() else -1


def behavior_quality_for_generation(gen_dir: Path) -> dict[str, Any] | None:
    """Aggregate rollout-side behavior quality for one generation.

    `behavior_quality_mean` intentionally uses the path-adjusted dense progress
    written by eval conversion. This measures what the agent did, not whether a
    child skill should replace its parent.
    """

    summaries = sorted(gen_dir.glob("rollouts/ind*/eval_summary_*.json"))
    if not summaries:
        return None

    progress: list[float] = []
    raw_progress: list[float] = []
    selection: list[float] = []
    pass_rate: list[float] = []
    path_scores: list[float] = []
    rollouts_total = 0
    component_weighted: dict[str, list[tuple[float, int]]] = {}
    adherence_scores: list[float] = []
    adherence_source = "none"

    for path in summaries:
        data = _load_json(path)
        metrics = data.get("metrics") or {}
        n = int(metrics.get("total_rollouts") or len(data.get("rollouts") or []) or 1)
        rollouts_total += n

        progress.append(float(metrics.get("progress_fitness") or 0.0))
        raw_progress.append(float(metrics.get("raw_progress_fitness") or metrics.get("progress_fitness") or 0.0))
        selection.append(float(metrics.get("selection_fitness") or 0.0))
        pass_rate.append(float(metrics.get("overall_pass_at_1") or 0.0))
        path = metrics.get("path_grounding_fitness") or {}
        if path:
            path_scores.append(float(path.get("mean_score") or 0.0))

        for name, value in (metrics.get("progress_components") or {}).items():
            try:
                component_weighted.setdefault(str(name), []).append((float(value), n))
            except (TypeError, ValueError):
                continue

        monitor = metrics.get("skill_monitor") or {}
        if monitor.get("mean_adherence_score") is not None:
            try:
                adherence_scores.append(float(monitor["mean_adherence_score"]))
                adherence_source = "runtime_monitor"
            except (TypeError, ValueError):
                pass

    posthoc_adherence = None if adherence_scores else _posthoc_skill_adherence_for_generation(gen_dir)
    if posthoc_adherence is not None and not adherence_scores:
        adherence_source = "posthoc_artifact"

    components = {
        name: _weighted_mean(values)
        for name, values in sorted(component_weighted.items())
    }

    return {
        "generation": _generation_number(gen_dir),
        "evaluated_individuals": len(summaries),
        "rollouts": rollouts_total,
        "pass_rate_mean": _mean(pass_rate),
        "pass_rate_std": _std(pass_rate),
        "behavior_quality_mean": _weighted_mean([
            (v, int((_load_json(path).get("metrics") or {}).get("total_rollouts") or 1))
            for v, path in zip(progress, summaries)
        ]),
        "behavior_quality_std": _std(progress),
        "rollout_variance_q": _repeat_variance_for_generation(gen_dir),
        "raw_behavior_quality_mean": _mean(raw_progress),
        "rollout_selection_fitness_mean": _mean(selection),
        "path_grounding_mean": _mean(path_scores),
        "skill_adherence_mean": _mean(adherence_scores) if adherence_scores else posthoc_adherence,
        "skill_adherence_source": adherence_source,
        "components": components,
    }


def _score_from_semantic_selection(selection: dict[str, Any]) -> float | None:
    score = ((selection.get("semantic_selection") or {}).get("candidate_score") or {}).get("score")
    if score is None:
        score = (selection.get("candidate_score") or {}).get("score")
    try:
        return float(score) if score is not None else None
    except (TypeError, ValueError):
        return None


def _integration_report_score(path: Path) -> float | None:
    data = _load_json(path)
    report = data.get("report") or data.get("integration_report") or data
    if not isinstance(report, dict) or not report.get("metrics"):
        return None
    try:
        return float(semantic_skill_score(report).score)
    except Exception:
        return None


def _calibrated_selected_skill_score(gen_dir: Path, selection: dict[str, Any]) -> tuple[float | None, bool]:
    if selection.get("generation") not in {None, _generation_number(gen_dir)}:
        return None, False
    child_slot = selection.get("child_slot")
    if child_slot is None:
        return None, True
    candidates = [
        gen_dir / "skill_integration" / f"child{child_slot}_mutation.json",
        gen_dir / "skill_integration" / f"child{child_slot}_initial_mutation.json",
    ]
    for path in candidates:
        if path.exists():
            score = _integration_report_score(path)
            if score is not None:
                return score, True
    return None, True


def _selection_artifact_dir(current_gen_dir: Path, selection: dict[str, Any]) -> Path:
    """Return the generation directory that owns a child semantic-selection record."""

    try:
        selection_generation = int(selection.get("generation"))
    except (TypeError, ValueError):
        return current_gen_dir
    if selection_generation == _generation_number(current_gen_dir):
        return current_gen_dir
    sibling = current_gen_dir.parent / f"gen{selection_generation}"
    return sibling if sibling.exists() else current_gen_dir


def _calibrated_candidate_mean_quality(gen_dir: Path) -> float | None:
    scores: list[float] = []
    for path in sorted((gen_dir / "skill_integration").glob("child*_*.json")):
        score = _integration_report_score(path)
        if score is not None:
            scores.append(score)
    return _mean(scores)


def skill_quality_after_generation(
    gen_dir: Path,
    previous_cumulative: float | None,
) -> dict[str, Any]:
    """Return cumulative semantic skill quality after a generation boundary."""

    standard_decision = _load_json(gen_dir / "ea_survivor_decision.json")
    legacy_decision = _load_json(gen_dir / "semantic_incumbent_decision.json")
    candidate_records = _load_jsonl(gen_dir / "semantic_skill_selection.jsonl")
    accepted = [r for r in candidate_records if r.get("decision") == "accept_child"]
    deferred = [r for r in candidate_records if r.get("decision") == "deferred_to_next_generation_rollout"]
    stored_child_mean = _mean([
        float(((r.get("candidate_score") or {}).get("score") or 0.0))
        for r in candidate_records
        if (r.get("candidate_score") or {}).get("score") is not None
    ])
    best_child = _calibrated_candidate_mean_quality(gen_dir)
    if best_child is None:
        best_child = stored_child_mean

    if standard_decision:
        index = _load_json(gen_dir / "skill_iterations_index.json")
        individuals = index.get("individuals") or []
        survivor_row = next((row for row in individuals if row.get("rank") == 0), individuals[0] if individuals else {})
        survivor_selection = survivor_row.get("semantic_selection") or {}
        selected_score = None
        if survivor_selection:
            selection_dir = _selection_artifact_dir(gen_dir, survivor_selection)
            selected_score, _ = _calibrated_selected_skill_score(selection_dir, survivor_selection)
            if selected_score is None:
                selected_score = _score_from_semantic_selection(survivor_selection)
        if selected_score is None:
            selected_score = previous_cumulative
        if selected_score is None:
            selected_score = 0.0

        return {
            "available": True,
            "decision": "standard_ea_evaluated_survivor",
            "cumulative_skill_quality": selected_score,
            "selected_skill_quality": selected_score,
            "accepted_children": len(accepted),
            "deferred_children": len(deferred),
            "candidate_mean_quality": best_child,
            "rollout_fitness_used_for_selection": True,
            "selection_artifact": "ea_survivor_decision.json",
            "survivor_parent_info": standard_decision.get("survivor_parent_info"),
            "survivor_semantic_selection": survivor_selection,
        }

    decision = legacy_decision
    if not decision:
        return {
            "available": False,
            "decision": "not_yet_available",
            "cumulative_skill_quality": previous_cumulative,
            "selected_skill_quality": None,
            "accepted_children": len(accepted),
            "deferred_children": len(deferred),
            "candidate_mean_quality": best_child,
        }

    semantic_selection = decision.get("semantic_selection") or {}
    selected_score, same_generation_selection = _calibrated_selected_skill_score(gen_dir, semantic_selection)
    if selected_score is None and same_generation_selection:
        selected_score = _score_from_semantic_selection(decision)
    if selected_score is None and decision.get("incumbent_score") is not None:
        try:
            selected_score = float(decision["incumbent_score"])
        except (TypeError, ValueError):
            selected_score = None

    if selected_score is None:
        selected_score = previous_cumulative
    cumulative = selected_score if selected_score is not None else previous_cumulative

    return {
        "available": True,
        "decision": decision.get("decision") or decision.get("reason") or "unknown",
        "cumulative_skill_quality": cumulative,
        "selected_skill_quality": selected_score,
        "accepted_children": len(accepted),
        "deferred_children": len(deferred),
        "candidate_mean_quality": best_child,
        "rollout_fitness_used_for_selection": bool(decision.get("rollout_fitness_used_for_selection", False)),
        "selection_artifact": "semantic_incumbent_decision.json",
    }


def summarize_run_dir(run_dir: Path, task_id: str | None = None, cid: str | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cumulative_skill_quality: float | None = None
    for gen_dir in sorted(run_dir.glob("gen*"), key=_generation_number):
        gen = _generation_number(gen_dir)
        if gen < 1:
            continue
        behavior = behavior_quality_for_generation(gen_dir)
        skill = skill_quality_after_generation(gen_dir, cumulative_skill_quality)
        cumulative_skill_quality = skill.get("cumulative_skill_quality")
        if behavior is None and not skill.get("available"):
            continue
        rows.append({
            "cid": cid or "",
            "task_id": task_id or run_dir.name,
            "task": _task_short(task_id or run_dir.name),
            "generation": gen,
            **(behavior or {
                "evaluated_individuals": 0,
                "rollouts": 0,
                "pass_rate_mean": None,
                "pass_rate_std": None,
                "behavior_quality_mean": None,
                "behavior_quality_std": None,
                "rollout_variance_q": None,
                "raw_behavior_quality_mean": None,
                "rollout_selection_fitness_mean": None,
                "path_grounding_mean": None,
                "skill_adherence_mean": None,
                "skill_adherence_source": "none",
                "components": {},
            }),
            **skill,
        })
        row = rows[-1]
        row["SkillQualityQ"] = (
            row.get("selected_skill_quality")
            if row.get("selected_skill_quality") is not None
            else row.get("cumulative_skill_quality")
        )
        row["AgentBehaviorQ"] = row.get("behavior_quality_mean")
        row["RolloutVarianceQ"] = row.get("rollout_variance_q")
        row["SkillAdherenceQ"] = row.get("skill_adherence_mean")
    return rows


def summarize_manifest(manifest_path: Path) -> list[dict[str, Any]]:
    manifest = _load_json(manifest_path)
    rows: list[dict[str, Any]] = []
    for task in manifest.get("tasks") or []:
        rows.extend(summarize_run_dir(
            Path(task["output_dir"]),
            task_id=task.get("task_id"),
            cid=task.get("cid"),
        ))
    return rows


def print_table(rows: list[dict[str, Any]]) -> None:
    columns = [
        ("cid", "CID"),
        ("task", "Task"),
        ("generation", "Gen"),
        ("evaluated_individuals", "Ind"),
        ("rollouts", "Rollouts"),
        ("pass_rate_mean", "Pass"),
        ("SkillQualityQ", "SkillQualityQ"),
        ("AgentBehaviorQ", "AgentBehaviorQ"),
        ("RolloutVarianceQ", "RolloutVarianceQ"),
        ("SkillAdherenceQ", "SkillAdherenceQ"),
        ("path_grounding_mean", "PathQ"),
        ("decision", "SkillDecision"),
    ]
    widths = []
    for key, title in columns:
        vals = [_fmt(row.get(key), 3) for row in rows]
        widths.append(max(len(title), *(len(v) for v in vals), 3))
    print("  ".join(title.ljust(width) for (_, title), width in zip(columns, widths)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(
            _fmt(row.get(key), 3).ljust(width)
            for (key, _), width in zip(columns, widths)
        ))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="manifest.json or one run output directory")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--csv", type=Path)
    args = parser.parse_args()

    if args.path.is_file():
        rows = summarize_manifest(args.path)
    else:
        rows = summarize_run_dir(args.path)

    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        keys = sorted({key for row in rows for key in row if key != "components"})
        with args.csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row.get(key) for key in keys})

    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_table(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

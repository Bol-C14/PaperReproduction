#!/usr/bin/env python3
"""Validate the sanitized C3/C4 evidence against the paper's cached results."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable


QUALITY_FIELDS = (
    "SelectQ",
    "SkillQ",
    "AgentProgressQ",
    "AgentVarianceQ",
    "AgentAdherenceQ",
)
SCHEMA_VERSION = 2
SELECTION_EPSILON = 0.1225
SELECTION_WEIGHTS = {
    "progress_lcb_95": 0.55,
    "progress_mean": 0.15,
    "SkillQ": 0.20,
    "AgentAdherenceQ": 0.10,
}
FEEDBACK_REASON_CODES = (
    "verify_feedback_budget_exhausted",
    "verify_feedback_requires_successful_iverilog",
    "verify_feedback_requires_new_edit",
    "verify_feedback_requires_edit",
)


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AssertionError(f"{path}:{line_number}: invalid JSON") from exc
            assert isinstance(value, dict), f"{path}:{line_number}: expected an object"
            values.append(value)
    return values


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def validate_historical_prompts(root: Path) -> dict[str, Any]:
    metadata = read_json(root / "evidence" / "run_metadata.json")
    assert len(metadata) == 16
    prompt_root = root / "historical_prompts" / "c3_c4"
    manifest = read_json(prompt_root / "PROMPT_HASHES.json")
    assert manifest["schema_version"] == 1
    recorded = {row["path"]: row["sha256"] for row in manifest["files"]}
    assert len(recorded) == manifest["unique_hashed_files"] == 22
    assert manifest["runs"] == len(metadata)
    assert manifest["run_hash_records"] == len(metadata) * len(recorded)
    for run in metadata:
        assert int(run["schema_version"]) == SCHEMA_VERSION
        assert run["skill_hashes"] == recorded, (
            f"historical prompt-hash mismatch for {run['condition']}/{run['task_id']}"
        )
    withheld_tree = prompt_root / "skills"
    assert not withheld_tree.exists(), "withheld prompt text must not be in public artifact"
    public_skill_root = root.parents[1] / "skills"
    public_paths = {
        str(path.relative_to(public_skill_root))
        for path in public_skill_root.rglob("*.md")
    }
    assert public_paths == set(recorded)
    exact_public_matches = {
        relative_path
        for relative_path, expected_hash in recorded.items()
        if sha256(public_skill_root / relative_path) == expected_hash
    }
    differing_public_paths = sorted(public_paths - exact_public_matches)
    assert len(exact_public_matches) == manifest["current_public_exact_hash_matches"] == 21
    assert len(public_paths) == manifest["current_public_path_count"] == 22
    assert differing_public_paths == manifest["current_public_different_paths"]
    return {
        "runs": len(metadata),
        "unique_hashed_files": len(recorded),
        "run_hash_records": manifest["run_hash_records"],
        "public_text_files": 0,
        "current_public_paths": len(public_paths),
        "current_public_exact_hash_matches": len(exact_public_matches),
        "current_public_different_paths": differing_public_paths,
    }


def validate_historical_source(root: Path, expected: dict[str, Any]) -> dict[str, Any]:
    """Describe the source audit without duplicating three historical trees.

    The official repository publishes the recovered C4 superset directly and
    records the C3/C4 commit/patch provenance in docs/PROVENANCE.md. The much
    larger AE-only duplicate source slices are therefore intentionally absent.
    """
    assert expected["total_files"] == 161
    return {
        "status": "documented_without_duplicate_historical_trees",
        "total_files": expected["total_files"],
        "commits": sorted(expected["commits"]),
    }


def validate_runtime_audit(root: Path, expected: dict[str, Any]) -> dict[str, Any]:
    runtime_root = root / "evidence" / "runtime"
    source_doc = read_json(runtime_root / "source_file_hashes.json")
    assert source_doc["schema_version"] == 1
    source_rows = source_doc["files"]
    assert len(source_rows) == expected["source_files"]
    source_coordinates: set[tuple[str, str, str]] = set()
    for row in source_rows:
        coordinate = (row["condition"], row["task_id"], row["relative_file"])
        assert coordinate not in source_coordinates
        source_coordinates.add(coordinate)
        assert row["kind"] in {"llm_calls", "rollout_retries", "launch_log"}
        assert not str(row["relative_file"]).startswith("/")
        assert re.fullmatch(r"[0-9a-f]{64}", row["sha256"])

    launch_doc = read_json(runtime_root / "launch_settings.json")
    assert launch_doc["schema_version"] == 1
    assert launch_doc["sanitization"] == {
        "source_paths_included": False,
        "endpoint_values_included": False,
        "raw_log_lines_included": False,
    }
    launch_payload = json.dumps(launch_doc, sort_keys=True)
    assert not re.search(r"/(?:mnt/data[0-9]*|home)/", launch_payload)
    assert not re.search(r"https?://", launch_payload)
    launch_rows = launch_doc["sources"]
    expected_launch = expected["launch_settings"]
    assert len(launch_rows) == len(expected_launch["sources"])
    launch_source_hashes = {
        row["relative_file"].removeprefix("launch_logs/").removesuffix(".log"):
        row["sha256"]
        for row in source_rows
        if row["kind"] == "launch_log"
    }
    assert len(launch_source_hashes) == len(expected_launch["sources"])
    for row in launch_rows:
        source_id = row["source_id"]
        source_expected = expected_launch["sources"][source_id]
        assert row["condition"] == source_expected["condition"]
        assert row["source_sha256"] == source_expected["sha256"]
        assert launch_source_hashes[source_id] == source_expected["sha256"]
        assert row["recorded_endpoint"] == {
            "present_in_private_log": True,
            "value_withheld": True,
        }
        assert row["service_aliases"] == expected_launch["service_aliases"]
        close(
            float(row["rollout_temperature"]),
            float(expected_launch["rollout_temperature"]),
            tolerance=0.0,
        )
        assert (
            row["openai_compatible_retry_loop"]
            == expected_launch["openai_compatible_retry_loop"]
        )
        assert row["request_bridge"] == expected_launch["request_bridge"]
        assert row["fitness"] == expected_launch["fitness"]

    call_path = runtime_root / "llm_calls.csv"
    with call_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == [
            "condition", "task_id", "generation", "purpose", "model",
            "status", "attempt", "max_attempts", "temperature",
            "temperature_provenance", "max_output_tokens", "prompt_tokens",
            "completion_tokens", "reasoning_tokens", "total_tokens",
            "finish_reason", "error_type",
        ]
        call_rows = list(reader)
    assert len(call_rows) == expected["llm_attempt_rows"]

    condition_reports: dict[str, Any] = {}
    policies = expected["purpose_policies"]
    for row in call_rows:
        purpose = row["purpose"]
        policy_name = purpose if purpose in policies else "oracle"
        assert purpose.startswith("layer") or purpose in {
            "compress", "mutate", "repair_mutation"
        }
        policy = policies[policy_name]
        assert row["model"] == policy["model"]
        close(float(row["temperature"]), float(policy["temperature"]), tolerance=0.0)
        assert row["temperature_provenance"] == policy["temperature_provenance"]
        assert int(row["max_output_tokens"]) == policy["max_output_tokens"]
        assert int(row["max_attempts"]) == 3
        assert int(row["attempt"]) in {1, 2, 3}
        assert row["status"] in {"success", "error"}
        assert all(
            int(row[field]) >= 0
            for field in (
                "prompt_tokens", "completion_tokens", "reasoning_tokens", "total_tokens"
            )
        )
        if row["status"] == "success":
            assert row["error_type"] == ""
        else:
            assert row["error_type"]

    for condition in ("C3", "C4"):
        rows = [row for row in call_rows if row["condition"] == condition]
        condition_expected = expected["conditions"][condition]
        assert len(rows) == condition_expected["total"]
        purposes = dict(sorted(Counter(row["purpose"] for row in rows).items()))
        assert purposes == condition_expected["purpose_counts"]
        statuses = Counter(row["status"] for row in rows)
        status_report = {name: statuses[name] for name in ("success", "error")}
        assert status_report == condition_expected["status_counts"]
        attempts = dict(sorted(Counter(row["attempt"] for row in rows).items()))
        assert attempts == condition_expected["attempt_counts"]
        errors = dict(sorted(Counter(
            row["error_type"] for row in rows if row["error_type"]
        ).items()))
        assert errors == condition_expected.get("error_type_counts", {})
        condition_reports[condition] = {
            "total": len(rows),
            "purpose_counts": purposes,
            "status_counts": status_report,
            "attempt_counts": attempts,
            "error_type_counts": errors,
        }

    retry_path = runtime_root / "rollout_retries.csv"
    with retry_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == [
            "condition", "task_id", "generation", "individual_index", "attempt",
            "reason_category", "archived_file_count", "replacement_artifact_present",
        ]
        retry_rows = list(reader)
    assert len(retry_rows) == expected["rollout_retry_rows"]
    retry_coordinates: set[tuple[str, str, int, int, int]] = set()
    for row in retry_rows:
        coordinate = (
            row["condition"], row["task_id"], int(row["generation"]),
            int(row["individual_index"]), int(row["attempt"]),
        )
        assert coordinate not in retry_coordinates
        retry_coordinates.add(coordinate)
        assert row["reason_category"] == "invalid_response_artifacts"
        assert int(row["archived_file_count"]) == 5
        assert row["replacement_artifact_present"] == "true"
    retry_counts = dict(sorted(Counter(row["condition"] for row in retry_rows).items()))
    assert retry_counts == expected["rollout_retry_counts"]
    replacements = sum(
        row["replacement_artifact_present"] == "true" for row in retry_rows
    )
    assert replacements == expected["replacement_artifacts_present"]
    return {
        "llm_attempt_rows": len(call_rows),
        "source_files": len(source_rows),
        "conditions": condition_reports,
        "rollout_retry_rows": len(retry_rows),
        "rollout_retry_counts": retry_counts,
        "launch_setting_sources": len(launch_rows),
        "replacement_artifacts_present": replacements,
    }


def pearson(xs: list[float], ys: list[float]) -> float:
    assert len(xs) == len(ys) and len(xs) > 1
    x_mean = fmean(xs)
    y_mean = fmean(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    x_norm = math.sqrt(sum((x - x_mean) ** 2 for x in xs))
    y_norm = math.sqrt(sum((y - y_mean) ** 2 for y in ys))
    assert x_norm > 0 and y_norm > 0
    return numerator / (x_norm * y_norm)


def binary_auc(scores: list[float], labels: list[int]) -> float:
    positives = [score for score, label in zip(scores, labels) if label == 1]
    negatives = [score for score, label in zip(scores, labels) if label == 0]
    assert positives and negatives
    wins = 0.0
    for positive in positives:
        for negative in negatives:
            if positive > negative:
                wins += 1.0
            elif positive == negative:
                wins += 0.5
    return wins / (len(positives) * len(negatives))


def validate_progress_audit(root: Path, expected: dict[str, Any]) -> dict[str, Any]:
    path = root / "evidence" / "agentq96" / "rollouts.csv"
    assert sha256(path) == expected["sha256"]
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == [
            "cid",
            "task_id",
            "repeat_index",
            "passed",
            "f_progress",
            "f_progress_strict",
        ]
        rows = list(reader)
    assert len(rows) == expected["rollouts"] == 96
    coordinates: set[tuple[str, str, int]] = set()
    task_repeats: dict[tuple[str, str], set[int]] = defaultdict(set)
    pass_by_cid: dict[str, int] = defaultdict(int)
    labels: list[int] = []
    outcome_scores: list[float] = []
    strict_scores: list[float] = []
    for row in rows:
        cid = row["cid"]
        task = row["task_id"]
        repeat = int(row["repeat_index"])
        label = int(row["passed"])
        outcome = float(row["f_progress"])
        strict = float(row["f_progress_strict"])
        assert cid in {"cid003", "cid004", "cid005", "cid016"}
        assert 0 <= repeat <= 3 and label in {0, 1}
        assert math.isfinite(outcome) and 0.0 <= outcome <= 1.0
        assert math.isfinite(strict) and 0.0 <= strict <= 1.0
        coordinate = (cid, task, repeat)
        assert coordinate not in coordinates
        coordinates.add(coordinate)
        task_repeats[(cid, task)].add(repeat)
        pass_by_cid[cid] += label
        labels.append(label)
        outcome_scores.append(outcome)
        strict_scores.append(strict)
    assert len(task_repeats) == expected["tasks"] == 24
    assert all(repeats == {0, 1, 2, 3} for repeats in task_repeats.values())
    assert sum(labels) == expected["passes"] == 51
    assert len(labels) - sum(labels) == expected["failures"] == 45
    assert dict(sorted(pass_by_cid.items())) == expected["passes_by_cid"]

    report: dict[str, Any] = {
        "rollouts": len(rows),
        "tasks": len(task_repeats),
        "passes": sum(labels),
        "failures": len(labels) - sum(labels),
        "passes_by_cid": dict(sorted(pass_by_cid.items())),
    }
    for name, scores in (
        ("outcome_aware", outcome_scores),
        ("strict_behavior_only", strict_scores),
    ):
        positive_scores = [score for score, label in zip(scores, labels) if label == 1]
        negative_scores = [score for score, label in zip(scores, labels) if label == 0]
        metrics = {
            "pearson_r": pearson(scores, [float(label) for label in labels]),
            "auc": binary_auc(scores, labels),
            "pass_mean": fmean(positive_scores),
            "fail_mean": fmean(negative_scores),
        }
        for field, value in metrics.items():
            close(value, float(expected[name][field]), tolerance=1e-12)
        report[name] = metrics
    return report


def validate_oss24_outcomes(root: Path, expected: dict[str, Any]) -> dict[str, Any]:
    path = root / "evidence" / "oss24" / "outcomes.csv"
    assert sha256(path) == expected["sha256"]
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == [
            "cid",
            "task_id",
            "cvdp_pass",
            "claude_pass",
            "codex_pass",
        ]
        rows = list(reader)
    assert len(rows) == expected["tasks"] == 24
    assert len({row["task_id"] for row in rows}) == 24
    report: dict[str, Any] = {"tasks": len(rows), "per_cid": {}}
    for cid in ("cid003", "cid004", "cid005", "cid016"):
        cid_rows = [row for row in rows if row["cid"] == cid]
        assert len(cid_rows) == 6
        counts: dict[str, int] = {}
        for field in ("cvdp_pass", "claude_pass", "codex_pass"):
            values = [int(row[field]) for row in cid_rows]
            assert all(value in {0, 1} for value in values)
            counts[field.removesuffix("_pass")] = sum(values)
        assert counts == expected["per_cid"][cid]
        report["per_cid"][cid] = counts
    totals = {
        agent: sum(report["per_cid"][cid][agent] for cid in report["per_cid"])
        for agent in ("cvdp", "claude", "codex")
    }
    assert totals == expected["totals"]
    report["totals"] = totals
    codex_provenance = read_json(
        root / "evidence" / "oss24" / "codex_launch_provenance.json"
    )
    launch = codex_provenance["launch"]
    outcome = codex_provenance["outcome"]
    commitments = codex_provenance["source_commitments"]
    assert launch["task_count"] == outcome["attempts"] == len(rows) == 24
    assert launch["repeats"] == 1
    assert launch["max_turns_soft"] == 30
    assert launch["hide_skill_md"] is True
    assert launch["verifier_image"].endswith(":latest")
    assert launch["verifier_image_digest_retained"] is False
    assert launch["explicit_model_override"] is False
    assert launch["explicit_reasoning_effort_override"] is False
    assert launch["runner_default_model"] == launch["effective_model"] == "gpt-5.5"
    assert (
        launch["runner_default_reasoning_effort"]
        == launch["effective_reasoning_effort"]
        == "high"
    )
    assert outcome["completed_attempts"] == 24
    assert outcome["runner_failures_or_timeouts"] == 0
    assert outcome["passes"] == totals["codex"] == 12
    assert outcome["passes_by_cid"] == {
        cid: report["per_cid"][cid]["codex"] for cid in report["per_cid"]
    }
    assert outcome["attempts_by_cid"] == {cid: 6 for cid in report["per_cid"]}
    ordered_rows = sorted(rows, key=lambda row: (row["cid"], row["task_id"]))
    taskset_projection = "".join(
        f"{row['cid']},{row['task_id']}\n" for row in ordered_rows
    ).encode()
    codex_projection = "".join(
        f"{row['cid']},{row['task_id']},{row['codex_pass']}\n"
        for row in ordered_rows
    ).encode()
    assert commitments["public_outcomes_csv_sha256"] == sha256(path)
    assert commitments["canonical_taskset_csv_lines_sha256"] == hashlib.sha256(
        taskset_projection
    ).hexdigest()
    assert commitments["canonical_codex_projection_csv_lines_sha256"] == hashlib.sha256(
        codex_projection
    ).hexdigest()
    assert commitments["contemporaneous_runner_hash_recorded"] is False
    assert commitments["runner_linkage"] == "retrospective strong reconstruction"
    report["codex_provenance"] = {
        "model": launch["effective_model"],
        "reasoning_effort": launch["effective_reasoning_effort"],
        "max_turns_soft": launch["max_turns_soft"],
        "completed_attempts": outcome["completed_attempts"],
    }
    return report


def close(actual: float, expected: float, *, tolerance: float = 1e-9) -> None:
    assert math.isclose(actual, expected, rel_tol=0.0, abs_tol=tolerance), (
        f"expected {expected:.12g}, observed {actual:.12g}"
    )


def mean_field(rows: Iterable[dict[str, Any]], field: str) -> float:
    values = [float(row[field]) for row in rows if row.get(field) is not None]
    assert values, f"no values for {field}"
    return fmean(values)


def validate_condition(root: Path, condition: str, expected: dict[str, Any]) -> dict[str, Any]:
    name = condition.lower()
    rollouts = read_jsonl(root / "evidence" / name / "rollouts.jsonl")
    quality = read_jsonl(root / "evidence" / name / "quality_records.jsonl")

    assert len(rollouts) == expected["rollouts"] == 640
    rollout_keys = {
        (
            row["task_id"],
            int(row["generation"]),
            int(row["individual_index"]),
            int(row["repeat_index"]),
        )
        for row in rollouts
    }
    assert len(rollout_keys) == len(rollouts), f"{condition}: duplicate rollout coordinates"
    assert all(row["condition"] == condition for row in rollouts)
    assert all(int(row["schema_version"]) == SCHEMA_VERSION for row in rollouts)
    assert all(1 <= int(row["generation"]) <= 5 for row in rollouts)
    assert all(0 <= int(row["individual_index"]) <= 3 for row in rollouts)
    assert all(0 <= int(row["repeat_index"]) <= 3 for row in rollouts)

    task_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rollouts:
        task_rows[str(row["short_task_id"])].append(row)
    assert set(task_rows) == set(expected["task_passes"])

    task_report: dict[str, Any] = {}
    for task, rows in sorted(task_rows.items()):
        passes = sum(row["outcome"] == "pass" for row in rows)
        assert len(rows) == 80, f"{condition}/{task}: expected 80 rollouts"
        assert passes == expected["task_passes"][task]
        task_report[task] = {
            "rollouts": len(rows),
            "passes": passes,
            "pass_rate": passes / len(rows),
            "passing_rollouts_with_executed_feedback": sum(
                row["outcome"] == "pass"
                and int(row["verify_feedback_executions"]) > 0
                for row in rows
            ),
            "verify_feedback_attempts": sum(int(row["verify_feedback_attempts"]) for row in rows),
            "verify_feedback_executions": sum(int(row["verify_feedback_executions"]) for row in rows),
            "verify_feedback_budget_rejections": sum(
                int(row["verify_feedback_budget_rejections"]) for row in rows
            ),
            "verify_feedback_gate_rejections": sum(
                int(row["verify_feedback_gate_rejections"]) for row in rows
            ),
        }

    passes = sum(row["outcome"] == "pass" for row in rollouts)
    solved = sum(report["passes"] > 0 for report in task_report.values())
    assert passes == expected["passes"]
    assert solved == expected["solved_tasks"]
    close(passes / len(rollouts), float(expected["pass_rate"]))

    feedback_reasons = {code: 0 for code in FEEDBACK_REASON_CODES}
    for row in rollouts:
        attempts = int(row["verify_feedback_attempts"])
        executions = int(row["verify_feedback_executions"])
        budget_rejections = int(row["verify_feedback_budget_rejections"])
        gate_rejections = int(row["verify_feedback_gate_rejections"])
        reasons = row["verify_feedback_rejection_reasons"]
        assert set(reasons) == set(FEEDBACK_REASON_CODES)
        assert budget_rejections == int(reasons["verify_feedback_budget_exhausted"])
        assert gate_rejections == sum(int(reasons[code]) for code in FEEDBACK_REASON_CODES[1:])
        assert attempts == executions + budget_rejections + gate_rejections
        assert executions <= 3
        for code in FEEDBACK_REASON_CODES:
            feedback_reasons[code] += int(reasons[code])

    feedback_report = {
        "attempts": sum(int(row["verify_feedback_attempts"]) for row in rollouts),
        "executions": sum(int(row["verify_feedback_executions"]) for row in rollouts),
        "budget_rejections": sum(
            int(row["verify_feedback_budget_rejections"]) for row in rollouts
        ),
        "gate_rejections": sum(
            int(row["verify_feedback_gate_rejections"]) for row in rollouts
        ),
        "max_executions_per_rollout": max(
            int(row["verify_feedback_executions"]) for row in rollouts
        ),
        "rejection_reasons": feedback_reasons,
    }
    assert feedback_report == expected["feedback_audit"]

    assert len(quality) == 160
    quality_keys = {
        (row["task_id"], int(row["generation"]), int(row["individual_index"])) for row in quality
    }
    assert len(quality_keys) == len(quality), f"{condition}: duplicate quality coordinates"
    adherence_default_rows = 0
    for row in quality:
        adherence = float(row["AgentAdherenceQ"])
        close(adherence, 1.0, tolerance=0.0)
        adherence_default_rows += 1

        expected_agent_progress = (
            0.80 * float(row["progress_lcb_95"])
            + 0.20 * float(row["progress_mean"])
        )
        close(float(row["AgentProgressQ"]), expected_agent_progress, tolerance=1e-12)

        if row["selection_blocked"]:
            expected_select_q = -1.0
        else:
            utility = sum(float(row[field]) * weight for field, weight in SELECTION_WEIGHTS.items())
            expected_select_q = float(row["pass_at_1"]) + SELECTION_EPSILON * max(
                0.0, min(1.0, utility)
            )
        # Public quality fields are rounded to six decimal places.
        close(float(row["SelectQ"]), expected_select_q, tolerance=5.1e-7)

    agent_q = mean_field(quality, "AgentProgressQ")
    close(agent_q, float(expected["AgentQ"]))

    expected_generations = read_json(root / "expected_results.json")["valid_candidate_generation_means"][condition]
    generation_report: dict[str, Any] = {}
    for generation in range(1, 6):
        valid = [
            row
            for row in quality
            if int(row["generation"]) == generation
            and row["valid"]
            and not row["selection_blocked"]
            and not row["semantic_floor_violation"]
        ]
        expected_generation = expected_generations[str(generation)]
        assert len(valid) == expected_generation["n"]
        report = {"n": len(valid)}
        for field in QUALITY_FIELDS:
            report[field] = mean_field(valid, field)
            close(report[field], float(expected_generation[field]), tolerance=5e-9)
        generation_report[str(generation)] = report

    if condition == "C3":
        assert feedback_report["attempts"] == 0
    if condition == "C4":
        for task, expected_count in expected[
            "passing_rollouts_with_executed_feedback"
        ].items():
            assert (
                task_report[task]["passing_rollouts_with_executed_feedback"]
                == expected_count
            )

    return {
        "condition": condition,
        "design": {
            "tasks": len(task_rows),
            "generations": len({int(row["generation"]) for row in rollouts}),
            "individuals_per_generation": len(
                {int(row["individual_index"]) for row in rollouts}
            ),
            "repeats_per_individual": len(
                {int(row["repeat_index"]) for row in rollouts}
            ),
        },
        "rollouts": len(rollouts),
        "passes": passes,
        "pass_rate": passes / len(rollouts),
        "solved_tasks": solved,
        "AgentQ": agent_q,
        "selection_formula_audit": {
            "formula_rows": len(quality),
            "adherence_default_rows": adherence_default_rows,
            "selection_epsilon": SELECTION_EPSILON,
            "weights": SELECTION_WEIGHTS,
        },
        "feedback_audit": feedback_report,
        "tasks": task_report,
        "valid_candidate_generation_means": generation_report,
    }


def print_report(report: dict[str, Any]) -> None:
    prompts = report["historical_prompts"]
    print(
        "Historical prompt hashes: "
        f"files={prompts['unique_hashed_files']} runs={prompts['runs']} "
        f"hash_records={prompts['run_hash_records']} "
        f"public_text_files={prompts['public_text_files']} "
        f"current_public_exact_matches="
        f"{prompts['current_public_exact_hash_matches']}/"
        f"{prompts['current_public_paths']}"
    )
    source = report["historical_source"]
    print(
        "Historical source: "
        f"commits={len(source['commits'])} files={source['total_files']} "
        "(nearest clean commits; launch worktrees recorded dirty)"
    )
    runtime = report["runtime_call_audit"]
    print(
        "Runtime call audit: "
        f"llm_attempt_rows={runtime['llm_attempt_rows']} "
        f"rollout_retry_rows={runtime['rollout_retry_rows']} "
        f"source_files={runtime['source_files']} "
        f"C3_errors={runtime['conditions']['C3']['status_counts']['error']} "
        f"C4_errors={runtime['conditions']['C4']['status_counts']['error']}"
    )
    audit = report["posthoc_progress_audit"]
    print(
        "Post-hoc F_progress audit: "
        f"rollouts={audit['rollouts']} tasks={audit['tasks']} "
        f"passes={audit['passes']} failures={audit['failures']} "
        f"outcome_aware_r={audit['outcome_aware']['pearson_r']:.6f} "
        f"outcome_aware_auc={audit['outcome_aware']['auc']:.6f} "
        f"strict_r={audit['strict_behavior_only']['pearson_r']:.6f} "
        f"strict_auc={audit['strict_behavior_only']['auc']:.6f}"
    )
    oss24 = report["oss24_contextual_outcomes"]
    print(
        "OSS24 contextual outcomes: "
        f"tasks={oss24['tasks']} CVDP={oss24['totals']['cvdp']}/24 "
        f"Claude={oss24['totals']['claude']}/24 "
        f"Codex={oss24['totals']['codex']}/24 "
        f"Codex_config={oss24['codex_provenance']['model']}/"
        f"{oss24['codex_provenance']['reasoning_effort']}/"
        f"{oss24['codex_provenance']['max_turns_soft']}-turn-soft-cap"
    )
    for condition in ("C3", "C4"):
        result = report[condition]
        print(
            f"{condition}: passes={result['passes']}/{result['rollouts']} "
            f"pass_rate={100.0 * result['pass_rate']:.4f}% "
            f"solved={result['solved_tasks']}/8 AgentQ={result['AgentQ']:.6f}"
        )
        design = result["design"]
        print(
            "  design: "
            f"tasks={design['tasks']} generations={design['generations']} "
            f"individuals_per_generation={design['individuals_per_generation']} "
            f"repeats_per_individual={design['repeats_per_individual']}"
        )
        feedback = result["feedback_audit"]
        print(
            "  feedback: "
            f"attempts={feedback['attempts']} executions={feedback['executions']} "
            f"budget_rejections={feedback['budget_rejections']} "
            f"gate_rejections={feedback['gate_rejections']} "
            f"max_executions_per_rollout={feedback['max_executions_per_rollout']}"
        )
        selection = result["selection_formula_audit"]
        print(
            "  selection: "
            f"formula_rows={selection['formula_rows']} "
            f"adherence_default_rows={selection['adherence_default_rows']} "
            f"epsilon={selection['selection_epsilon']:.4f} "
            "weights=0.55/0.15/0.20/0.10"
        )
        for task, task_result in result["tasks"].items():
            print(
                f"  task={task} passes={task_result['passes']}/{task_result['rollouts']} "
                f"pass_rate={100.0 * task_result['pass_rate']:.2f}% "
                "executed_feedback="
                f"{task_result['verify_feedback_executions']} "
                "pass_with_executed_feedback="
                f"{task_result['passing_rollouts_with_executed_feedback']}"
            )
        for generation, metrics in result["valid_candidate_generation_means"].items():
            fields = " ".join(f"{field}={metrics[field]:.6f}" for field in QUALITY_FIELDS)
            print(f"  generation={generation} valid_individuals={metrics['n']} {fields}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "artifacts" / "paper-results",
        help="paper-results evidence directory",
    )
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    root = args.artifact_root.resolve()
    all_expected = read_json(root / "expected_results.json")
    expected = all_expected["functional_scope"]

    report = {
        "schema_version": SCHEMA_VERSION,
        "C1": {"status": expected["C1"]["artifact_status"]},
        "C2": {"status": expected["C2"]["artifact_status"]},
        "historical_prompts": validate_historical_prompts(root),
        "historical_source": validate_historical_source(
            root, all_expected["historical_source_audit"]
        ),
        "runtime_call_audit": validate_runtime_audit(
            root, all_expected["runtime_call_audit"]
        ),
        "posthoc_progress_audit": validate_progress_audit(
            root, all_expected["posthoc_progress_audit"]
        ),
        "oss24_contextual_outcomes": validate_oss24_outcomes(
            root, all_expected["oss24_contextual_outcomes"]
        ),
        "C3": validate_condition(root, "C3", expected["C3"]),
        "C4": validate_condition(root, "C4", expected["C4"]),
    }
    print_report(report)
    print(f"C1: NOT IN FUNCTIONAL SCOPE - {report['C1']['status']}")
    print(f"C2: NOT IN FUNCTIONAL SCOPE - {report['C2']['status']}")
    print("VALIDATION PASSED")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        with args.json_out.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

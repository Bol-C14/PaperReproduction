#!/usr/bin/env python3
"""Convert NeMo-Gym rollout JSONL files into the format consumed by the
CVDP Agentic Long Context eval pipeline.

Produces two outputs:
  1. A per-model summary JSONL (one line per model) with aggregated metrics
     and the full trajectory text — input for the analyzer LLM.
  2. A flat rollout JSONL (one line per rollout) preserving task-level detail
     — useful for per-task analysis and profiling.

Usage:
    python eval/convert_rollouts.py <rollout_dir_or_file> [--output-dir eval/outputs]

The converter reads from NeMo-Gym-CVDP/results/ and writes to eval/outputs/.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


def load_rollouts_from_file(path: Path) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def extract_task_id(rec: dict) -> str:
    if "task_id" in rec:
        return rec["task_id"]
    vm = rec.get("verifier_metadata", {})
    if isinstance(vm, dict) and "task_id" in vm:
        return vm["task_id"]
    return rec.get("_ng_task_index", "unknown")


def extract_model_name(filename: str) -> str:
    name = filename
    for prefix in ["rollout_", "rollouts_"]:
        if name.startswith(prefix):
            name = name[len(prefix):]
    for suffix in [".jsonl", "_materialized_inputs", "_reward_profiling", "_agent_metrics"]:
        name = name.replace(suffix, "")
    return name


def summarize_trajectory(rec: dict) -> str:
    """Build a human-readable summary of one rollout's tool-use trajectory."""
    output_items = rec.get("response", {}).get("output", [])
    lines = []
    step = 0
    for item in output_items:
        item_type = item.get("type", "")
        if item_type == "function_call":
            step += 1
            name = item.get("name", "?")
            args = item.get("arguments", "")
            if isinstance(args, str) and len(args) > 200:
                args = args[:200] + "..."
            lines.append(f"  Step {step}: {name}({args})")
        elif item_type == "function_call_output":
            out = item.get("output", "")
            if isinstance(out, str) and len(out) > 300:
                out = out[:300] + "..."
            lines.append(f"    → {out}")
        elif item_type == "message":
            role = item.get("role", "?")
            content = ""
            if isinstance(item.get("content"), list):
                for c in item["content"]:
                    if isinstance(c, dict):
                        content += c.get("text", "") or ""
            elif isinstance(item.get("content"), str):
                content = item["content"]
            if content:
                if len(content) > 300:
                    content = content[:300] + "..."
                lines.append(f"  [{role}]: {content}")
    return "\n".join(lines)


def _parse_call_args(call: dict) -> dict:
    args = call.get("arguments") or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            return {}
    return args if isinstance(args, dict) else {}


def _tool_calls(rec: dict) -> list[dict]:
    return [
        o for o in rec.get("response", {}).get("output", [])
        if isinstance(o, dict) and o.get("type") == "function_call"
    ]


def _tool_outputs(rec: dict) -> list[str]:
    outputs = []
    for item in rec.get("response", {}).get("output", []):
        if not isinstance(item, dict) or item.get("type") != "function_call_output":
            continue
        raw = item.get("output", "")
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                text = parsed.get("output", raw) if isinstance(parsed, dict) else raw
            except json.JSONDecodeError:
                text = raw
            outputs.append(str(text))
    return outputs


def _skill_monitor_summary(rec: dict) -> dict:
    response = rec.get("response", {})
    metadata = response.get("metadata", {}) if isinstance(response, dict) else {}
    if not isinstance(metadata, dict):
        return {}
    raw = metadata.get("skill_monitor")
    if not raw:
        return {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return raw if isinstance(raw, dict) else {}


def _runtime_verifier_feedback_summary(rec: dict) -> dict:
    response = rec.get("response", {})
    metadata = response.get("metadata", {}) if isinstance(response, dict) else {}
    if not isinstance(metadata, dict):
        return {}
    raw = metadata.get("runtime_verifier_feedback")
    if not raw:
        return {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return raw if isinstance(raw, dict) else {}


def _call_args_text(calls: list[dict], name: str) -> str:
    chunks = []
    for call in calls:
        if call.get("name") != name:
            continue
        args = _parse_call_args(call)
        chunks.append(str(args.get("args") or args.get("command") or ""))
    return "\n".join(chunks)


def _parse_verifier_partial_score(stderr: str, reward: float) -> float:
    """Best-effort fraction of verifier subtests passed.

    The CVDP resource still returns binary reward, but many harnesses include
    pytest/cocotb summaries in stderr. This parser intentionally returns 0.0
    when it cannot find a reliable fraction, so the dense score never invents
    verifier progress.
    """
    if isinstance(reward, (int, float)) and reward > 0:
        return 1.0
    if not stderr:
        return 0.0

    fractions: list[float] = []

    for m in re.finditer(r"TESTS\s*=\s*(\d+)\s+PASS\s*=\s*(\d+)\s+FAIL\s*=\s*(\d+)", stderr):
        total = int(m.group(1))
        passed = int(m.group(2))
        failed = int(m.group(3))
        denom = total if total > 0 else passed + failed
        if denom > 0:
            fractions.append(passed / denom)

    for m in re.finditer(r"[Ff]ailed\s+(\d+)\s+of\s+(\d+)\s+tests", stderr):
        failed = int(m.group(1))
        total = int(m.group(2))
        if total > 0:
            fractions.append(max(total - failed, 0) / total)

    for line in stderr.splitlines():
        low = line.lower()
        if "passed" not in low and "failed" not in low and "error" not in low:
            continue
        passed = sum(int(x) for x in re.findall(r"(\d+)\s+passed", line))
        failed = sum(int(x) for x in re.findall(r"(\d+)\s+failed", line))
        errors = sum(int(x) for x in re.findall(r"(\d+)\s+errors?", line))
        denom = passed + failed + errors
        if denom > 0:
            fractions.append(passed / denom)

    return max(fractions) if fractions else 0.0


def _execution_phase_score(calls: list[dict], outputs: list[str], reward: float) -> float:
    if isinstance(reward, (int, float)) and reward > 0:
        return 1.0

    names = [c.get("name", "") for c in calls]
    output_text = "\n".join(outputs).lower()
    wrote = any(n in {"echo", "edit"} for n in names)
    read = any(n in {"cat", "ls", "pwd"} for n in names)
    ran_compile = "iverilog" in names or "xcelium" in names
    ran_sim = "vvp" in names
    compile_success = ran_compile and "[exit code: 0]" in output_text
    sim_success = ran_sim and "[exit code: 0]" in output_text

    if ran_sim and sim_success:
        return 0.9
    if ran_sim:
        return 0.75
    if compile_success:
        return 0.65
    if ran_compile:
        return 0.5
    if wrote:
        return 0.35
    if read:
        return 0.2
    if calls:
        return 0.1
    return 0.0


def _harness_alignment_score(calls: list[dict], reward: float) -> float:
    if isinstance(reward, (int, float)) and reward > 0:
        return 1.0

    paths = []
    for call in calls:
        args = _parse_call_args(call)
        target = args.get("filename") or args.get("path") or ""
        if target:
            paths.append(str(target).lower())
    joined_paths = "\n".join(paths)
    compile_args = _call_args_text(calls, "iverilog").lower()

    score = 0.0
    if any(token in joined_paths for token in ("harness", "test_runner", ".env", "makefile")):
        score += 0.25
    if any(token in joined_paths for token in ("tb", "test", "verif")):
        score += 0.25
    if "-g2012" in compile_args:
        score += 0.15
    if " -s " in f" {compile_args} " or "cocotb" in compile_args:
        score += 0.15

    source_like = re.findall(r"\S+\.(?:sv|v|vh)\b", compile_args)
    has_test_source = any(("tb" in src or "test" in src or "verif" in src) for src in source_like)
    if has_test_source or len(source_like) >= 3:
        score += 0.20

    return min(score, 1.0)


def _edit_quality_score(calls: list[dict], reward: float) -> float:
    if isinstance(reward, (int, float)) and reward > 0:
        return 1.0

    writes = [c for c in calls if c.get("name") in {"echo", "edit"}]
    if not writes:
        return 0.2

    score = 0.35
    write_targets = []
    no_target = False
    huge_echo = False
    used_edit = False
    for call in writes:
        args = _parse_call_args(call)
        target = args.get("filename") or args.get("path") or ""
        if target:
            write_targets.append(str(target))
        else:
            no_target = True
        if call.get("name") == "edit":
            used_edit = True
        if call.get("name") == "echo" and len(args.get("content") or "") > 25000:
            huge_echo = True

    if used_edit:
        score += 0.25
    if not no_target:
        score += 0.15
    if not huge_echo:
        score += 0.15

    seen_readback = False
    for target in write_targets:
        wrote = False
        for call in calls:
            args = _parse_call_args(call)
            call_target = args.get("filename") or args.get("path") or ""
            if call in writes and call_target == target:
                wrote = True
            elif wrote and call.get("name") == "cat" and call_target == target:
                seen_readback = True
                break
        if seen_readback:
            break
    if seen_readback:
        score += 0.15

    return min(score, 1.0)


def _efficiency_score(num_calls: int) -> float:
    if num_calls == 0:
        return 0.0
    if num_calls <= 3:
        return 0.2
    if num_calls <= 12:
        return 0.6
    if num_calls <= 35:
        return 1.0
    if num_calls <= 60:
        return 0.7
    return 0.4


def _progress_from_component_values(values: dict[str, float], *, has_monitor: bool) -> float:
    """Mirror the dense-progress formula for one rollout or averaged metrics."""
    if has_monitor:
        return (
            0.36 * values.get("verifier_partial", 0.0)
            + 0.18 * values.get("execution_phase", 0.0)
            + 0.135 * values.get("harness_alignment", 0.0)
            + 0.135 * values.get("edit_quality", 0.0)
            + 0.09 * values.get("efficiency", 0.0)
            + 0.10 * values.get("skill_adherence", 0.0)
        )
    return (
        0.40 * values.get("verifier_partial", 0.0)
        + 0.20 * values.get("execution_phase", 0.0)
        + 0.15 * values.get("harness_alignment", 0.0)
        + 0.15 * values.get("edit_quality", 0.0)
        + 0.10 * values.get("efficiency", 0.0)
    )


def _summarize_rollout_score_variance(scores: list[float]) -> dict:
    """Summarize repeat instability for dense rollout progress scores."""
    clean = [max(0.0, min(1.0, float(v))) for v in scores if isinstance(v, (int, float))]
    if not clean:
        return {
            "n": 0,
            "mean": 0.0,
            "stdev": 0.0,
            "sem": 0.0,
            "lower_confidence_bound_95": 0.0,
            "variance_penalty": 1.0,
            "variance_quality": 0.0,
        }
    mean = sum(clean) / len(clean)
    if len(clean) == 1:
        stdev = 0.0
        sem = 0.0
    else:
        stdev = (sum((v - mean) ** 2 for v in clean) / (len(clean) - 1)) ** 0.5
        sem = stdev / (len(clean) ** 0.5)
    lcb = max(0.0, mean - 1.96 * sem)
    variance_penalty = min(1.0, stdev / 0.30)
    return {
        "n": len(clean),
        "mean": round(mean, 4),
        "stdev": round(stdev, 4),
        "sem": round(sem, 4),
        "lower_confidence_bound_95": round(lcb, 4),
        "variance_penalty": round(variance_penalty, 4),
        "variance_quality": round(1.0 - variance_penalty, 4),
    }


def compute_progress_metrics(rollouts: list[dict], pass_at_1: float, unique_tasks: int) -> dict:
    """Compute dense auxiliary progress used only for optimizer selection.

    `pass_at_1` remains the scientific objective. The dense score ranks failures
    by how close they got, while `selection_fitness` keeps one real pass worth
    more than any amount of auxiliary progress.
    """
    if not rollouts:
        return {
            "progress_fitness": 0.0,
            "selection_fitness": pass_at_1,
            "selection_epsilon": 0.0,
            "progress_components": {},
        }

    components = {
        "verifier_partial": [],
        "execution_phase": [],
        "harness_alignment": [],
        "edit_quality": [],
        "efficiency": [],
    }
    monitor_summaries: list[dict] = []
    verifier_feedback_summaries: list[dict] = []
    per_rollout_progress: list[float] = []

    for rec in rollouts:
        reward = rec.get("reward", 0.0)
        calls = _tool_calls(rec)
        outputs = _tool_outputs(rec)
        rollout_values = {
            "verifier_partial": _parse_verifier_partial_score(rec.get("docker_stderr", "") or "", reward),
            "execution_phase": _execution_phase_score(calls, outputs, reward),
            "harness_alignment": _harness_alignment_score(calls, reward),
            "edit_quality": _edit_quality_score(calls, reward),
            "efficiency": _efficiency_score(len(calls)),
        }
        components["verifier_partial"].append(rollout_values["verifier_partial"])
        components["execution_phase"].append(rollout_values["execution_phase"])
        components["harness_alignment"].append(rollout_values["harness_alignment"])
        components["edit_quality"].append(rollout_values["edit_quality"])
        components["efficiency"].append(rollout_values["efficiency"])
        monitor_summary = _skill_monitor_summary(rec)
        if monitor_summary:
            monitor_summaries.append(monitor_summary)
            rollout_values["skill_adherence"] = float(monitor_summary.get("adherence_score", 0.0))
            components.setdefault("skill_adherence", []).append(rollout_values["skill_adherence"])
        verifier_feedback_summary = _runtime_verifier_feedback_summary(rec)
        if verifier_feedback_summary:
            verifier_feedback_summaries.append(verifier_feedback_summary)
        per_rollout_progress.append(
            _progress_from_component_values(rollout_values, has_monitor=bool(monitor_summary))
        )

    averages = {
        name: round(sum(vals) / len(vals), 4) if vals else 0.0
        for name, vals in components.items()
    }
    progress = _progress_from_component_values(averages, has_monitor=bool(monitor_summaries))

    # Use the smallest observed pass-rate step as a hard upper bound on how
    # much dense progress can matter. A prettier failure cannot outrank one
    # additional verifier pass.
    pass_unit = 1.0 / max(len(rollouts), unique_tasks, 1)
    epsilon = 0.49 * pass_unit
    selection = pass_at_1 + epsilon * progress

    result = {
        "progress_fitness": round(progress, 4),
        "selection_fitness": round(selection, 6),
        "selection_epsilon": round(epsilon, 6),
        "progress_components": averages,
        "progress_rollout_scores": [round(v, 4) for v in per_rollout_progress],
        "rollout_variance": _summarize_rollout_score_variance(per_rollout_progress),
    }
    if monitor_summaries:
        by_code: dict[str, int] = {}
        by_source: dict[str, int] = {}
        by_action: dict[str, int] = {}
        by_confidence: dict[str, int] = {}
        policy_hashes: dict[str, int] = {}
        blocked_examples: list[dict] = []
        total_violations = 0
        total_blocked = 0
        skill_seen = 0
        expected_targets_seen = 0
        scores = []
        for summary in monitor_summaries:
            total_violations += int(summary.get("num_violations", 0) or 0)
            total_blocked += int(summary.get("blocked_actions", 0) or 0)
            if summary.get("skill_seen"):
                skill_seen += 1
            if summary.get("expected_targets"):
                expected_targets_seen += 1
            policy_hash = summary.get("policy_hash")
            if policy_hash:
                policy_hashes[str(policy_hash)] = policy_hashes.get(str(policy_hash), 0) + 1
            scores.append(float(summary.get("adherence_score", 0.0) or 0.0))
            for code, count in (summary.get("violations_by_code", {}) or {}).items():
                by_code[str(code)] = by_code.get(str(code), 0) + int(count)
            for violation in summary.get("violations") or []:
                if not isinstance(violation, dict):
                    continue
                source = str(violation.get("source") or "unknown")
                action = str(violation.get("action_taken") or ("block" if violation.get("blocked") else "observe"))
                confidence = str(violation.get("confidence") or "unknown")
                by_source[source] = by_source.get(source, 0) + 1
                by_action[action] = by_action.get(action, 0) + 1
                by_confidence[confidence] = by_confidence.get(confidence, 0) + 1
                if violation.get("blocked") and len(blocked_examples) < 5:
                    blocked_examples.append({
                        "step": violation.get("step"),
                        "tool": violation.get("tool"),
                        "code": violation.get("code"),
                        "source": source,
                        "confidence": confidence,
                        "message": violation.get("message"),
                    })
        result["skill_monitor"] = {
            "enabled_rollouts": len(monitor_summaries),
            "mean_adherence_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
            "total_violations": total_violations,
            "total_blocked_actions": total_blocked,
            "violations_by_code": dict(sorted(by_code.items())),
            "violations_by_source": dict(sorted(by_source.items())),
            "violations_by_action": dict(sorted(by_action.items())),
            "violations_by_confidence": dict(sorted(by_confidence.items())),
            "policy_hashes": dict(sorted(policy_hashes.items())),
            "policy_enabled_rollouts": sum(policy_hashes.values()),
            "skill_seen_rollouts": skill_seen,
            "expected_target_policy_rollouts": expected_targets_seen,
            "blocked_examples": blocked_examples,
        }
    if verifier_feedback_summaries:
        calls = sum(int(s.get("calls", 0) or 0) for s in verifier_feedback_summaries)
        violations = sum(int(s.get("policy_violations", 0) or 0) for s in verifier_feedback_summaries)
        partial_scores = [
            float(v)
            for summary in verifier_feedback_summaries
            for v in (summary.get("partial_scores") or [])
            if isinstance(v, (int, float))
        ]
        result["runtime_verifier_feedback"] = {
            "enabled_rollouts": len(verifier_feedback_summaries),
            "VerifierFeedbackCalls": calls,
            "VerifierFeedbackPolicyViolations": violations,
            "VerifierFeedbackPartialScore": round(sum(partial_scores) / len(partial_scores), 4) if partial_scores else 0.0,
            "VerifierFeedbackPassBeforeFinal": sum(1 for s in verifier_feedback_summaries if s.get("pass_before_final")),
            "DeltaAfterVerifierFeedback": round(pass_at_1 - (
                sum(1 for s in verifier_feedback_summaries if s.get("pass_before_final"))
                / max(len(verifier_feedback_summaries), 1)
            ), 4),
        }
    return result


def compute_metrics(rollouts: list[dict]) -> dict:
    """Compute pass@1, pass@k, and per-task breakdown."""
    buckets: dict[str, list[float]] = defaultdict(list)
    for rec in rollouts:
        tid = extract_task_id(rec)
        reward = rec.get("reward", 0.0)
        buckets[tid].append(1.0 if (isinstance(reward, (int, float)) and reward > 0) else 0.0)

    per_task = {}
    for tid in sorted(buckets):
        attempts = buckets[tid]
        k = len(attempts)
        passes = sum(attempts)
        per_task[tid] = {
            "attempts": k,
            "passes": int(passes),
            "pass_at_1": passes / k if k > 0 else 0.0,
            "pass_at_k": 1.0 if passes > 0 else 0.0,
        }

    n_tasks = len(per_task)
    agg_pass1 = sum(t["pass_at_1"] for t in per_task.values()) / n_tasks if n_tasks else 0.0
    agg_passk = sum(t["pass_at_k"] for t in per_task.values()) / n_tasks if n_tasks else 0.0

    metrics = {
        "total_rollouts": len(rollouts),
        "unique_tasks": n_tasks,
        "overall_pass_at_1": round(agg_pass1, 4),
        "overall_pass_at_k": round(agg_passk, 4),
        "per_task": per_task,
    }
    metrics.update(compute_progress_metrics(rollouts, metrics["overall_pass_at_1"], n_tasks))
    return metrics


def convert_single_file(path: Path, model_name: str | None = None) -> dict:
    """Convert one rollout JSONL file into a model summary record."""
    rollouts = load_rollouts_from_file(path)
    if not rollouts:
        return {}

    if not model_name:
        model_name = extract_model_name(path.stem)

    metrics = compute_metrics(rollouts)

    trajectories = []
    for i, rec in enumerate(rollouts):
        tid = extract_task_id(rec)
        reward = rec.get("reward", 0.0)
        trajectory_text = summarize_trajectory(rec)
        monitor_summary = _skill_monitor_summary(rec)
        trajectories.append({
            "rollout_index": i,
            "task_id": tid,
            "reward": reward,
            "docker_exit_code": rec.get("docker_exit_code"),
            "skill_monitor": {
                "adherence_score": monitor_summary.get("adherence_score"),
                "num_violations": monitor_summary.get("num_violations"),
                "blocked_actions": monitor_summary.get("blocked_actions"),
                "violations_by_code": monitor_summary.get("violations_by_code", {}),
                "violations_by_source": {
                    str(v.get("source") or "unknown"): sum(
                        1 for vv in monitor_summary.get("violations") or []
                        if isinstance(vv, dict) and str(vv.get("source") or "unknown") == str(v.get("source") or "unknown")
                    )
                    for v in monitor_summary.get("violations") or []
                    if isinstance(v, dict)
                },
                "violations_by_action": {
                    str(v.get("action_taken") or ("block" if v.get("blocked") else "observe")): sum(
                        1 for vv in monitor_summary.get("violations") or []
                        if isinstance(vv, dict)
                        and str(vv.get("action_taken") or ("block" if vv.get("blocked") else "observe"))
                        == str(v.get("action_taken") or ("block" if v.get("blocked") else "observe"))
                    )
                    for v in monitor_summary.get("violations") or []
                    if isinstance(v, dict)
                },
                "policy_hash": monitor_summary.get("policy_hash"),
                "expected_targets": monitor_summary.get("expected_targets", []),
            } if monitor_summary else {},
            "trajectory": trajectory_text,
        })

    return {
        "model_name": model_name,
        "source_file": str(path),
        "metrics": metrics,
        "rollouts": trajectories,
    }


def convert_directory(input_dir: Path, output_dir: Path) -> None:
    """Convert all rollout files in a directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    model_summaries = []
    flat_rollouts = []

    rollout_files = sorted(
        set(input_dir.glob("rollout_*.jsonl")) | set(input_dir.glob("rollouts_*.jsonl"))
    )
    rollout_files = [
        f for f in rollout_files
        if "materialized" not in f.name
        and "reward_profiling" not in f.name
        and "agent_metrics" not in f.name
    ]

    if not rollout_files:
        print(f"No rollout files found in {input_dir}", file=sys.stderr)
        sys.exit(1)

    for path in rollout_files:
        rollouts = load_rollouts_from_file(path)
        if not rollouts:
            continue

        model_name = extract_model_name(path.stem)
        summary = convert_single_file(path, model_name)
        if summary:
            model_summaries.append(summary)

        for rec in rollouts:
            monitor_summary = _skill_monitor_summary(rec)
            flat_rollouts.append({
                "model_name": model_name,
                "task_id": extract_task_id(rec),
                "reward": rec.get("reward", 0.0),
                "docker_exit_code": rec.get("docker_exit_code"),
                "skill_monitor_adherence": monitor_summary.get("adherence_score") if monitor_summary else None,
                "skill_monitor_violations": monitor_summary.get("num_violations") if monitor_summary else None,
                "skill_monitor_blocked_actions": monitor_summary.get("blocked_actions") if monitor_summary else None,
                "skill_monitor_policy_hash": monitor_summary.get("policy_hash") if monitor_summary else None,
                "skill_monitor_violation_codes": sorted((monitor_summary.get("violations_by_code") or {}).keys()) if monitor_summary else [],
                "num_tool_calls": len([
                    o for o in rec.get("response", {}).get("output", [])
                    if o.get("type") == "function_call"
                ]),
                "trajectory_summary": summarize_trajectory(rec),
            })

    summary_path = output_dir / "model_summaries.jsonl"
    with open(summary_path, "w", encoding="utf-8") as f:
        for s in model_summaries:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    print(f"Wrote {len(model_summaries)} model summaries to {summary_path}")

    flat_path = output_dir / "flat_rollouts.jsonl"
    with open(flat_path, "w", encoding="utf-8") as f:
        for r in flat_rollouts:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote {len(flat_rollouts)} flat rollouts to {flat_path}")


def main():
    parser = argparse.ArgumentParser(description="Convert NeMo-Gym rollouts to CVDP Agentic Long Context eval format")
    parser.add_argument("input", help="Path to rollout JSONL file or directory of rollout files")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: eval/outputs)")
    args = parser.parse_args()

    input_path = Path(args.input)
    script_dir = Path(__file__).resolve().parent
    output_dir = Path(args.output_dir) if args.output_dir else script_dir / "outputs"

    if input_path.is_dir():
        convert_directory(input_path, output_dir)
    elif input_path.is_file():
        output_dir.mkdir(parents=True, exist_ok=True)
        summary = convert_single_file(input_path)
        if summary:
            out_path = output_dir / f"{extract_model_name(input_path.stem)}_summary.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            print(f"Wrote summary to {out_path}")
    else:
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

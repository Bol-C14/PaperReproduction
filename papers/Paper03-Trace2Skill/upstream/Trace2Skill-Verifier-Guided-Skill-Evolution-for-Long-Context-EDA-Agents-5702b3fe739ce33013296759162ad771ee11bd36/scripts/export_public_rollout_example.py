#!/usr/bin/env python3
"""Export or validate a content-free public action trace from a raw rollout.

The exporter intentionally retains only tool names, action ordering, byte-count
and SHA-256 commitments, allow-listed scalar verifier feedback, cached outcome
labels, and individual-level quality metrics. Prompts, assistant prose, code,
paths, tool arguments/results, provider metadata, and hidden-verifier text are
never copied to the public record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA_VERSION = 1
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
PRIVATE_TEXT_RE = re.compile(
    r"/(?:home|mnt)/(?:[^/\s]+/){1,}|"
    r"(?:gitlab-master|inference-api)\.nvidia\.com|"
    r"(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})",
    re.IGNORECASE,
)

ACTION_FAMILIES = {
    "cat": "inspect",
    "ls": "inspect",
    "rg": "inspect",
    "read_file": "inspect",
    "show_changes": "inspect",
    "echo": "modify",
    "edit": "modify",
    "iverilog": "compile",
    "vvp": "simulate",
    "verify_feedback": "verifier_feedback",
}

TOOL_ARGUMENT_KEYS = {
    "cat": {"filename"},
    "ls": {"path"},
    "rg": {"case_sensitive", "glob", "max_matches", "path", "pattern"},
    "read_file": {"end_line", "filename", "start_line"},
    "show_changes": {"filename", "max_files"},
    "echo": {"content", "filename"},
    "edit": {"filename", "new_text", "old_text"},
    "iverilog": {"args"},
    "vvp": {"filename"},
    "verify_feedback": {"reason"},
}

PATH_ARGUMENT_KEYS = {"filename", "path"}
PUBLIC_SCALAR_ARGUMENT_KEYS = {
    "case_sensitive",
    "end_line",
    "max_files",
    "max_matches",
    "start_line",
}
PUBLIC_SUFFIXES = {"", ".json", ".md", ".sv", ".svh", ".txt", ".v", ".vh", ".vvp"}

FORBIDDEN_PUBLIC_KEYS = {
    "arguments",
    "content",
    "conversation",
    "docker_stderr",
    "filename",
    "instructions",
    "messages",
    "new_text",
    "old_text",
    "output",
    "path",
    "pattern",
    "prompt",
    "provider_specific_fields",
    "reason",
    "response",
    "user",
}

CONDITION_DESCRIPTIONS = {
    "C3": "sparse final reward; runtime verifier feedback disabled",
    "C4": "dense runtime verifier feedback; at most three executions per rollout",
}

REDACTION_POLICY = {
    "assistant_messages": "omitted; count retained",
    "tool_arguments": "values omitted; field names, sizes, hashes, and path classes retained",
    "tool_results": "text omitted; sizes, hashes, and allow-listed verifier scalars retained",
    "provider_metadata": "omitted",
    "hidden_verifier_material": "omitted",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _encoded_commitment(value: str) -> dict[str, Any]:
    encoded = value.encode("utf-8")
    return {"byte_count": len(encoded), "sha256": _sha256(encoded)}


def _read_jsonl_match(
    path: Path,
    predicate: Callable[[dict[str, Any], int], bool],
) -> tuple[dict[str, Any], int, bytes]:
    matches: list[tuple[dict[str, Any], int, bytes]] = []
    ordinal = -1
    for raw_line in path.read_bytes().splitlines():
        if not raw_line.strip():
            continue
        ordinal += 1
        record = json.loads(raw_line)
        if not isinstance(record, dict):
            raise ValueError(f"expected JSON object in {path}")
        if predicate(record, ordinal):
            matches.append((record, ordinal, raw_line))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one matching record in {path}, found {len(matches)}")
    return matches[0]


def _path_summary(value: str) -> dict[str, Any]:
    normalized = value.replace("\\", "/")
    pure = PurePosixPath(normalized)
    parts = [part for part in pure.parts if part not in {"", "/", "."}]
    suffix = pure.suffix.lower()
    return {
        "kind": "absolute-withheld" if pure.is_absolute() else "workspace-relative",
        "depth": len(parts),
        "suffix": suffix if suffix in PUBLIC_SUFFIXES else "other",
        "contains_parent_reference": ".." in parts,
    }


def _argument_summary(tool: str, raw_arguments: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw_arguments)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{tool} arguments are not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{tool} arguments must be a JSON object")
    keys = set(parsed)
    allowed = TOOL_ARGUMENT_KEYS[tool]
    if not keys <= allowed:
        raise ValueError(f"{tool} has non-allow-listed argument keys: {sorted(keys - allowed)}")

    strings: list[dict[str, Any]] = []
    scalars: dict[str, int | float | bool] = {}
    for key in sorted(parsed):
        value = parsed[key]
        if isinstance(value, str):
            entry = {"name": key, **_encoded_commitment(value)}
            if key in PATH_ARGUMENT_KEYS:
                entry["path_summary"] = _path_summary(value)
            strings.append(entry)
        elif key in PUBLIC_SCALAR_ARGUMENT_KEYS and isinstance(value, (int, float, bool)):
            scalars[key] = value
        else:
            raise ValueError(f"{tool}.{key} has unsupported argument type {type(value).__name__}")

    encoded = raw_arguments.encode("utf-8")
    return {
        "keys": sorted(keys),
        "byte_count": len(encoded),
        "sha256": _sha256(encoded),
        "string_field_commitments": strings,
        "public_scalar_fields": scalars,
    }


def _nested_tool_payload(raw_result: str) -> Any:
    try:
        outer = json.loads(raw_result)
    except json.JSONDecodeError:
        return None
    if not isinstance(outer, dict) or not isinstance(outer.get("output"), str):
        return None
    try:
        return json.loads(outer["output"])
    except json.JSONDecodeError:
        return None


def _public_verifier_feedback(raw_result: str) -> dict[str, Any] | None:
    nested = _nested_tool_payload(raw_result)
    if not isinstance(nested, dict) or not isinstance(nested.get("verifier_feedback"), dict):
        return None
    source = nested["verifier_feedback"]
    scalar_fields = (
        "compile_ok",
        "partial_score",
        "pass",
        "sim_ok",
        "tests_passed",
        "tests_total",
        "timeout",
    )
    feedback: dict[str, Any] = {"status": "executed"}
    for key in scalar_fields:
        value = source.get(key)
        if isinstance(value, (bool, int, float)) and not isinstance(value, str):
            feedback[key] = value

    waveform = source.get("waveform_observations")
    if isinstance(waveform, dict):
        public_waveform: dict[str, Any] = {}
        for key in (
            "available",
            "changed_signal_count",
            "clock_or_reset_activity",
            "files_analyzed",
            "files_seen",
            "signal_count",
            "unknown_or_high_impedance_count",
        ):
            value = waveform.get(key)
            if isinstance(value, (bool, int, float)) and not isinstance(value, str):
                public_waveform[key] = value
        if public_waveform:
            feedback["waveform_summary"] = public_waveform
    return feedback


def _result_commitment(raw_result: str | None) -> dict[str, Any]:
    if raw_result is None:
        return {"present": False, "byte_count": 0, "sha256": None}
    encoded = raw_result.encode("utf-8")
    return {"present": True, "byte_count": len(encoded), "sha256": _sha256(encoded)}


def _events(raw_record: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    response = raw_record.get("response")
    if not isinstance(response, dict) or not isinstance(response.get("output"), list):
        raise ValueError("raw rollout response.output is missing")
    raw_output = response["output"]
    results = {
        item.get("call_id"): item.get("output")
        for item in raw_output
        if isinstance(item, dict)
        and item.get("type") == "function_call_output"
        and isinstance(item.get("call_id"), str)
        and isinstance(item.get("output"), str)
    }
    events: list[dict[str, Any]] = []
    for item in raw_output:
        if not isinstance(item, dict) or item.get("type") != "function_call":
            continue
        tool = item.get("name")
        if tool not in ACTION_FAMILIES:
            raise ValueError(f"non-allow-listed tool name: {tool!r}")
        raw_arguments = item.get("arguments")
        if not isinstance(raw_arguments, str):
            raise ValueError(f"{tool} arguments are missing")
        raw_result = results.get(item.get("call_id"))
        status = item.get("status")
        event: dict[str, Any] = {
            "sequence": len(events) + 1,
            "tool": tool,
            "action_family": ACTION_FAMILIES[tool],
            "call_status": status if status in {"completed", "failed", "incomplete"} else "other",
            "argument_commitment": _argument_summary(tool, raw_arguments),
            "result_commitment": _result_commitment(raw_result),
        }
        if tool == "verify_feedback" and raw_result is not None:
            feedback = _public_verifier_feedback(raw_result)
            if feedback is not None:
                event["verifier_feedback"] = feedback
        events.append(event)
    message_count = sum(1 for item in raw_output if isinstance(item, dict) and item.get("type") == "message")
    return events, message_count


def _quality_metrics(record: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "pass_at_1",
        "SelectQ",
        "SkillQ",
        "AgentProgressQ",
        "AgentVarianceQ",
        "AgentAdherenceQ",
    )
    missing = [key for key in keys if key not in record]
    if missing:
        raise ValueError(f"public quality record lacks fields: {missing}")
    return {
        "pass_rate": record["pass_at_1"],
        "SelectQ": record["SelectQ"],
        "SkillQ": record["SkillQ"],
        "AgentProgressQ": record["AgentProgressQ"],
        "AgentVarianceQ": record["AgentVarianceQ"],
        "AgentAdherenceQ": record["AgentAdherenceQ"],
    }


def _check_meta_matches_quality(meta: dict[str, Any], quality: dict[str, Any]) -> None:
    pairs = {
        "pass_at_1": "pass_rate",
        "selection_fitness": "SelectQ",
        "skill_quality": "SkillQ",
        "agent_behavior_quality": "AgentProgressQ",
        "rollout_variance_quality": "AgentVarianceQ",
        "skill_adherence_quality": "AgentAdherenceQ",
    }
    for meta_key, public_key in pairs.items():
        if abs(float(meta[meta_key]) - float(quality[public_key])) > 1e-9:
            raise ValueError(f"metadata mismatch for {meta_key}/{public_key}")


def _require_exact_keys(
    value: Any,
    required: set[str],
    *,
    optional: set[str] | None = None,
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    optional = optional or set()
    missing = required - set(value)
    extra = set(value) - required - optional
    if missing:
        raise ValueError(f"{label} lacks required keys: {sorted(missing)}")
    if extra:
        raise ValueError(f"{label} has unexpected keys: {sorted(extra)}")
    return value


def _require_non_negative_int(value: Any, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")


def _require_number(value: Any, label: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        raise ValueError(f"{label} must be a finite number")


def _require_unit_interval(value: Any, label: str) -> None:
    _require_number(value, label)
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError(f"{label} must be in [0, 1]")


def _require_hash(value: Any, label: str) -> None:
    if not isinstance(value, str) or not HASH_RE.fullmatch(value):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")


def _require_safe_token(value: Any, label: str, *, pattern: str = r"^[A-Za-z0-9_.:-]{1,128}$") -> None:
    if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
        raise ValueError(f"{label} is not an allow-listed token")


def _validate_path_summary(value: Any, label: str) -> None:
    summary = _require_exact_keys(
        value,
        {"kind", "depth", "suffix", "contains_parent_reference"},
        label=label,
    )
    if summary["kind"] not in {"absolute-withheld", "workspace-relative"}:
        raise ValueError(f"{label}.kind is invalid")
    _require_non_negative_int(summary["depth"], f"{label}.depth")
    if summary["suffix"] not in PUBLIC_SUFFIXES | {"other"}:
        raise ValueError(f"{label}.suffix is invalid")
    if not isinstance(summary["contains_parent_reference"], bool):
        raise ValueError(f"{label}.contains_parent_reference must be Boolean")


def _validate_argument_commitment(value: Any, tool: str, label: str) -> None:
    commitment = _require_exact_keys(
        value,
        {"keys", "byte_count", "sha256", "string_field_commitments", "public_scalar_fields"},
        label=label,
    )
    keys = commitment["keys"]
    if not isinstance(keys, list) or any(not isinstance(key, str) for key in keys):
        raise ValueError(f"{label}.keys must be a string list")
    if keys != sorted(set(keys)) or not set(keys) <= TOOL_ARGUMENT_KEYS[tool]:
        raise ValueError(f"{label}.keys are not the exact allow-listed argument names")
    _require_non_negative_int(commitment["byte_count"], f"{label}.byte_count")
    _require_hash(commitment["sha256"], f"{label}.sha256")

    string_fields = commitment["string_field_commitments"]
    if not isinstance(string_fields, list):
        raise ValueError(f"{label}.string_field_commitments must be a list")
    string_names: list[str] = []
    for index, raw_field in enumerate(string_fields):
        field_label = f"{label}.string_field_commitments[{index}]"
        field = _require_exact_keys(
            raw_field,
            {"name", "byte_count", "sha256"},
            optional={"path_summary"},
            label=field_label,
        )
        name = field["name"]
        if name not in keys or name not in TOOL_ARGUMENT_KEYS[tool]:
            raise ValueError(f"{field_label}.name is not an allow-listed argument")
        string_names.append(name)
        _require_non_negative_int(field["byte_count"], f"{field_label}.byte_count")
        _require_hash(field["sha256"], f"{field_label}.sha256")
        if name in PATH_ARGUMENT_KEYS:
            if "path_summary" not in field:
                raise ValueError(f"{field_label}.path_summary is required")
            _validate_path_summary(field["path_summary"], f"{field_label}.path_summary")
        elif "path_summary" in field:
            raise ValueError(f"{field_label}.path_summary is not permitted")
    if len(string_names) != len(set(string_names)):
        raise ValueError(f"{label} has duplicate string-field commitments")

    scalars = commitment["public_scalar_fields"]
    if not isinstance(scalars, dict):
        raise ValueError(f"{label}.public_scalar_fields must be an object")
    if not set(scalars) <= PUBLIC_SCALAR_ARGUMENT_KEYS & TOOL_ARGUMENT_KEYS[tool]:
        raise ValueError(f"{label}.public_scalar_fields has unexpected keys")
    for key, scalar in scalars.items():
        if not isinstance(scalar, (int, float, bool)):
            raise ValueError(f"{label}.public_scalar_fields.{key} has an invalid type")
    if set(string_names) | set(scalars) != set(keys):
        raise ValueError(f"{label} does not account for every argument key")


def _validate_result_commitment(value: Any, label: str) -> None:
    result = _require_exact_keys(value, {"present", "byte_count", "sha256"}, label=label)
    if not isinstance(result["present"], bool):
        raise ValueError(f"{label}.present must be Boolean")
    _require_non_negative_int(result["byte_count"], f"{label}.byte_count")
    if result["present"]:
        _require_hash(result["sha256"], f"{label}.sha256")
    elif result["sha256"] is not None or result["byte_count"] != 0:
        raise ValueError(f"{label} must use null hash and zero bytes when absent")


def _validate_waveform_summary(value: Any, label: str) -> None:
    allowed = {
        "available",
        "changed_signal_count",
        "clock_or_reset_activity",
        "files_analyzed",
        "files_seen",
        "signal_count",
        "unknown_or_high_impedance_count",
    }
    waveform = _require_exact_keys(value, set(), optional=allowed, label=label)
    for key, scalar in waveform.items():
        if key in {"available", "clock_or_reset_activity"}:
            if not isinstance(scalar, bool):
                raise ValueError(f"{label}.{key} must be Boolean")
        else:
            _require_non_negative_int(scalar, f"{label}.{key}")


def _validate_verifier_feedback(value: Any, label: str) -> None:
    allowed = {
        "compile_ok",
        "partial_score",
        "pass",
        "sim_ok",
        "tests_passed",
        "tests_total",
        "timeout",
        "waveform_summary",
    }
    feedback = _require_exact_keys(value, {"status"}, optional=allowed, label=label)
    if feedback["status"] != "executed":
        raise ValueError(f"{label}.status must be 'executed'")
    for key in ("compile_ok", "pass", "sim_ok", "timeout"):
        if key in feedback and not isinstance(feedback[key], bool):
            raise ValueError(f"{label}.{key} must be Boolean")
    if "partial_score" in feedback:
        _require_unit_interval(feedback["partial_score"], f"{label}.partial_score")
    for key in ("tests_passed", "tests_total"):
        if key in feedback:
            _require_non_negative_int(feedback[key], f"{label}.{key}")
    if "tests_passed" in feedback and "tests_total" in feedback and feedback["tests_passed"] > feedback["tests_total"]:
        raise ValueError(f"{label}.tests_passed cannot exceed tests_total")
    if "waveform_summary" in feedback:
        _validate_waveform_summary(feedback["waveform_summary"], f"{label}.waveform_summary")


def _validate_count_map(value: Any, allowed: set[str], label: str) -> None:
    if not isinstance(value, dict) or not set(value) <= allowed:
        raise ValueError(f"{label} has unexpected keys or type")
    for key, count in value.items():
        _require_non_negative_int(count, f"{label}.{key}")


def _validate_closed_world(record: dict[str, Any]) -> None:
    top = _require_exact_keys(
        record,
        {
            "schema_version",
            "sample_kind",
            "condition",
            "condition_description",
            "coordinate",
            "outcome",
            "individual_metrics",
            "provenance",
            "redaction",
            "trace_summary",
            "events",
        },
        label="record",
    )
    condition = top["condition"]
    if condition not in CONDITION_DESCRIPTIONS:
        raise ValueError("record.condition is invalid")
    if top["condition_description"] != CONDITION_DESCRIPTIONS[condition]:
        raise ValueError("record.condition_description is invalid")

    coordinate = _require_exact_keys(
        top["coordinate"],
        {"task_id", "short_task_id", "cid", "generation", "individual", "repeat", "repeat_source"},
        label="record.coordinate",
    )
    _require_safe_token(
        coordinate["task_id"],
        "record.coordinate.task_id",
        pattern=r"^cvdp_agentic_heavy_[A-Za-z0-9_.-]{1,96}$",
    )
    _require_safe_token(coordinate["short_task_id"], "record.coordinate.short_task_id")
    _require_safe_token(coordinate["cid"], "record.coordinate.cid", pattern=r"^cid[0-9]{3}$")
    for key in ("generation", "individual", "repeat"):
        _require_non_negative_int(coordinate[key], f"record.coordinate.{key}")
    if coordinate["repeat_source"] != "archived _ng_rollout_index":
        raise ValueError("record.coordinate.repeat_source is invalid")

    outcome = _require_exact_keys(
        top["outcome"],
        {
            "reward",
            "outcome",
            "mode",
            "phase_reached",
            "tests_passed",
            "tests_total",
            "files_written_count",
            "path_has_critical_issue",
            "path_issue_codes",
            "verify_feedback_attempts",
            "verify_feedback_executions",
            "verify_feedback_budget_rejections",
            "verify_feedback_gate_rejections",
        },
        label="record.outcome",
    )
    _require_number(outcome["reward"], "record.outcome.reward")
    if float(outcome["reward"]) not in {0.0, 1.0}:
        raise ValueError("record.outcome.reward must be binary")
    if outcome["outcome"] not in {"pass", "fail"}:
        raise ValueError("record.outcome.outcome is invalid")
    if (outcome["outcome"] == "pass") != (float(outcome["reward"]) == 1.0):
        raise ValueError("record.outcome label and reward are inconsistent")
    _require_safe_token(outcome["mode"], "record.outcome.mode")
    _require_safe_token(outcome["phase_reached"], "record.outcome.phase_reached")
    for key in ("tests_passed", "tests_total"):
        if outcome[key] is not None:
            _require_non_negative_int(outcome[key], f"record.outcome.{key}")
    if (
        outcome["tests_passed"] is not None
        and outcome["tests_total"] is not None
        and outcome["tests_passed"] > outcome["tests_total"]
    ):
        raise ValueError("record.outcome.tests_passed cannot exceed tests_total")
    for key in (
        "files_written_count",
        "verify_feedback_attempts",
        "verify_feedback_executions",
        "verify_feedback_budget_rejections",
        "verify_feedback_gate_rejections",
    ):
        _require_non_negative_int(outcome[key], f"record.outcome.{key}")
    if not isinstance(outcome["path_has_critical_issue"], bool):
        raise ValueError("record.outcome.path_has_critical_issue must be Boolean")
    if not isinstance(outcome["path_issue_codes"], list):
        raise ValueError("record.outcome.path_issue_codes must be a list")
    for index, code in enumerate(outcome["path_issue_codes"]):
        _require_safe_token(code, f"record.outcome.path_issue_codes[{index}]", pattern=r"^[a-z0-9_:-]{1,64}$")
    feedback_partition = (
        outcome["verify_feedback_executions"]
        + outcome["verify_feedback_budget_rejections"]
        + outcome["verify_feedback_gate_rejections"]
    )
    if outcome["verify_feedback_attempts"] != feedback_partition:
        raise ValueError("record.outcome verifier attempts do not match executions plus rejections")
    if condition == "C3" and outcome["verify_feedback_attempts"] != 0:
        raise ValueError("C3 records cannot contain runtime verifier feedback")
    if condition == "C4" and outcome["verify_feedback_executions"] > 3:
        raise ValueError("C4 records cannot exceed three verifier executions")

    metric_keys = {"pass_rate", "SelectQ", "SkillQ", "AgentProgressQ", "AgentVarianceQ", "AgentAdherenceQ"}
    metrics = _require_exact_keys(top["individual_metrics"], metric_keys, label="record.individual_metrics")
    for key, value in metrics.items():
        _require_unit_interval(value, f"record.individual_metrics.{key}")

    provenance = _require_exact_keys(
        top["provenance"],
        {
            "source_artifact",
            "source_jsonl_ordinal",
            "public_rollout_jsonl_ordinal",
            "public_quality_jsonl_ordinal",
            "raw_record_sha256",
            "public_rollout_record_sha256",
            "public_quality_record_sha256",
            "skill_sha256",
            "exporter",
        },
        label="record.provenance",
    )
    if provenance["source_artifact"] != "archived paper rollout; location withheld":
        raise ValueError("record.provenance.source_artifact is invalid")
    if provenance["exporter"] != "scripts/export_public_rollout_example.py":
        raise ValueError("record.provenance.exporter is invalid")
    for key in ("source_jsonl_ordinal", "public_rollout_jsonl_ordinal", "public_quality_jsonl_ordinal"):
        _require_non_negative_int(provenance[key], f"record.provenance.{key}")
    for key in (
        "raw_record_sha256",
        "public_rollout_record_sha256",
        "public_quality_record_sha256",
        "skill_sha256",
    ):
        _require_hash(provenance[key], f"record.provenance.{key}")

    if top["redaction"] != REDACTION_POLICY:
        raise ValueError("record.redaction must exactly match the public redaction policy")

    summary = _require_exact_keys(
        top["trace_summary"],
        {"assistant_message_count", "tool_call_count", "tool_counts", "action_family_counts"},
        label="record.trace_summary",
    )
    _require_non_negative_int(summary["assistant_message_count"], "record.trace_summary.assistant_message_count")
    _require_non_negative_int(summary["tool_call_count"], "record.trace_summary.tool_call_count")
    _validate_count_map(summary["tool_counts"], set(ACTION_FAMILIES), "record.trace_summary.tool_counts")
    _validate_count_map(
        summary["action_family_counts"],
        set(ACTION_FAMILIES.values()),
        "record.trace_summary.action_family_counts",
    )

    events = top["events"]
    if not isinstance(events, list) or not events:
        raise ValueError("record.events must be a non-empty list")
    for index, raw_event in enumerate(events):
        label = f"record.events[{index}]"
        event = _require_exact_keys(
            raw_event,
            {"sequence", "tool", "action_family", "call_status", "argument_commitment", "result_commitment"},
            optional={"verifier_feedback"},
            label=label,
        )
        tool = event["tool"]
        if tool not in ACTION_FAMILIES:
            raise ValueError(f"{label}.tool is invalid")
        if event["action_family"] != ACTION_FAMILIES[tool]:
            raise ValueError(f"{label}.action_family is invalid")
        if event["call_status"] not in {"completed", "failed", "incomplete", "other"}:
            raise ValueError(f"{label}.call_status is invalid")
        _require_non_negative_int(event["sequence"], f"{label}.sequence")
        _validate_argument_commitment(event["argument_commitment"], tool, f"{label}.argument_commitment")
        _validate_result_commitment(event["result_commitment"], f"{label}.result_commitment")
        if "verifier_feedback" in event:
            if tool != "verify_feedback":
                raise ValueError(f"{label}.verifier_feedback is only valid for verify_feedback")
            _validate_verifier_feedback(event["verifier_feedback"], f"{label}.verifier_feedback")


def build_record(
    *,
    condition: str,
    generation: int,
    individual: int,
    repeat: int,
    rollout_jsonl: Path,
    individual_meta: Path,
    public_rollouts: Path,
    public_quality: Path,
) -> dict[str, Any]:
    """Build one strict allow-list public rollout record."""
    normalized_condition = condition.upper()
    if normalized_condition not in CONDITION_DESCRIPTIONS:
        raise ValueError(f"unsupported condition {condition!r}")

    raw_record, source_ordinal, raw_line = _read_jsonl_match(
        rollout_jsonl,
        lambda row, _ordinal: row.get("_ng_rollout_index") == repeat,
    )
    task_id = raw_record.get("task_id")
    if not isinstance(task_id, str) or not task_id.startswith("cvdp_agentic_heavy_"):
        raise ValueError("unexpected public task identifier")

    public_rollout, public_ordinal, public_line = _read_jsonl_match(
        public_rollouts,
        lambda row, _ordinal: (
            row.get("condition") == normalized_condition
            and row.get("task_id") == task_id
            and row.get("generation") == generation
            and row.get("individual_index") == individual
            and row.get("repeat_index") == source_ordinal
        ),
    )
    quality_record, quality_ordinal, quality_line = _read_jsonl_match(
        public_quality,
        lambda row, _ordinal: (
            row.get("condition") == normalized_condition
            and row.get("task_id") == task_id
            and row.get("generation") == generation
            and row.get("individual_index") == individual
        ),
    )
    meta = json.loads(individual_meta.read_text(encoding="utf-8"))
    if not isinstance(meta, dict):
        raise ValueError("individual metadata must be a JSON object")
    if meta.get("generation") != generation or meta.get("individual_index") != individual:
        raise ValueError("individual metadata coordinate mismatch")

    events, message_count = _events(raw_record)
    quality = _quality_metrics(quality_record)
    _check_meta_matches_quality(meta, quality)
    tool_counts = Counter(event["tool"] for event in events)
    family_counts = Counter(event["action_family"] for event in events)
    feedback_executions = sum("verifier_feedback" in event for event in events)

    if float(raw_record.get("reward", 0.0)) != float(public_rollout["reward"]):
        raise ValueError("raw/public reward mismatch")
    if len(events) != int(public_rollout["num_tool_calls"]):
        raise ValueError("raw/public tool-call count mismatch")
    if tool_counts.get("verify_feedback", 0) != int(public_rollout["verify_feedback_attempts"]):
        raise ValueError("raw/public verifier-attempt count mismatch")
    if feedback_executions != int(public_rollout["verify_feedback_executions"]):
        raise ValueError("raw/public verifier-execution count mismatch")

    short_task_id = public_rollout["short_task_id"]
    record = {
        "schema_version": SCHEMA_VERSION,
        "sample_kind": "sanitized_action_trace",
        "condition": normalized_condition,
        "condition_description": CONDITION_DESCRIPTIONS[normalized_condition],
        "coordinate": {
            "task_id": task_id,
            "short_task_id": short_task_id,
            "cid": public_rollout["cid"],
            "generation": generation,
            "individual": individual,
            "repeat": repeat,
            "repeat_source": "archived _ng_rollout_index",
        },
        "outcome": {
            "reward": public_rollout["reward"],
            "outcome": public_rollout["outcome"],
            "mode": public_rollout["mode"],
            "phase_reached": public_rollout["phase_reached"],
            "tests_passed": public_rollout["tests_passed"],
            "tests_total": public_rollout["tests_total"],
            "files_written_count": public_rollout["files_written_count"],
            "path_has_critical_issue": public_rollout["path_has_critical_issue"],
            "path_issue_codes": public_rollout["path_issue_codes"],
            "verify_feedback_attempts": public_rollout["verify_feedback_attempts"],
            "verify_feedback_executions": public_rollout["verify_feedback_executions"],
            "verify_feedback_budget_rejections": public_rollout["verify_feedback_budget_rejections"],
            "verify_feedback_gate_rejections": public_rollout["verify_feedback_gate_rejections"],
        },
        "individual_metrics": quality,
        "provenance": {
            "source_artifact": "archived paper rollout; location withheld",
            "source_jsonl_ordinal": source_ordinal,
            "public_rollout_jsonl_ordinal": public_ordinal,
            "public_quality_jsonl_ordinal": quality_ordinal,
            "raw_record_sha256": _sha256(raw_line),
            "public_rollout_record_sha256": _sha256(public_line),
            "public_quality_record_sha256": _sha256(quality_line),
            "skill_sha256": meta["sha256"],
            "exporter": "scripts/export_public_rollout_example.py",
        },
        "redaction": REDACTION_POLICY,
        "trace_summary": {
            "assistant_message_count": message_count,
            "tool_call_count": len(events),
            "tool_counts": dict(sorted(tool_counts.items())),
            "action_family_counts": dict(sorted(family_counts.items())),
        },
        "events": events,
    }
    validate_public_record(record)
    return record


def _walk(value: Any, key: str | None = None):
    yield key, value
    if isinstance(value, dict):
        for child_key, child in value.items():
            yield from _walk(child, child_key)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child, None)


def validate_public_record(record: dict[str, Any]) -> None:
    """Apply safety and internal-consistency checks to a public record."""
    if record.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported sample schema version")
    if record.get("sample_kind") != "sanitized_action_trace":
        raise ValueError("unexpected sample kind")
    events = record.get("events")
    if not isinstance(events, list) or not events:
        raise ValueError("events must be a non-empty list")

    for key, value in _walk(record):
        if key in FORBIDDEN_PUBLIC_KEYS:
            raise ValueError(f"forbidden public key: {key}")
        if isinstance(value, str) and PRIVATE_TEXT_RE.search(value):
            raise ValueError("private path, domain, or credential-like text detected")
        is_hash_field = key is not None and (key == "sha256" or key.endswith("_sha256"))
        if is_hash_field and value is not None:
            if not isinstance(value, str) or not HASH_RE.fullmatch(value):
                raise ValueError(f"invalid public SHA-256 field: {key}")

    _validate_closed_world(record)

    for expected_sequence, event in enumerate(events, 1):
        if event.get("sequence") != expected_sequence:
            raise ValueError("event sequence is not contiguous")
        tool = event.get("tool")
        if tool not in ACTION_FAMILIES:
            raise ValueError(f"unexpected public tool {tool!r}")
        if event.get("action_family") != ACTION_FAMILIES[tool]:
            raise ValueError(f"action-family mismatch for {tool}")
        for section in ("argument_commitment", "result_commitment"):
            commitment = event.get(section)
            if not isinstance(commitment, dict):
                raise ValueError(f"{section} is missing")
            digest = commitment.get("sha256")
            if digest is not None and (not isinstance(digest, str) or not HASH_RE.fullmatch(digest)):
                raise ValueError(f"invalid hash in {section}")

    summary = record.get("trace_summary", {})
    if summary.get("tool_call_count") != len(events):
        raise ValueError("trace tool-call count mismatch")
    expected_tools = dict(sorted(Counter(event["tool"] for event in events).items()))
    expected_families = dict(sorted(Counter(event["action_family"] for event in events).items()))
    if summary.get("tool_counts") != expected_tools:
        raise ValueError("trace tool-count breakdown mismatch")
    if summary.get("action_family_counts") != expected_families:
        raise ValueError("trace action-family breakdown mismatch")
    outcome = record.get("outcome")
    if not isinstance(outcome, dict):
        raise ValueError("outcome is missing")
    attempts = sum(event["tool"] == "verify_feedback" for event in events)
    executions = sum("verifier_feedback" in event for event in events)
    if outcome.get("verify_feedback_attempts") != attempts:
        raise ValueError("public verifier-attempt count mismatch")
    if outcome.get("verify_feedback_executions") != executions:
        raise ValueError("public verifier-execution count mismatch")


def _write_record(record: dict[str, Any], output: str) -> None:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
    if output == "-":
        sys.stdout.write(payload)
        return
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _command_export(args: argparse.Namespace) -> int:
    record = build_record(
        condition=args.condition,
        generation=args.generation,
        individual=args.individual,
        repeat=args.repeat,
        rollout_jsonl=args.rollout_jsonl,
        individual_meta=args.individual_meta,
        public_rollouts=args.public_rollouts,
        public_quality=args.public_quality,
    )
    _write_record(record, args.output)
    return 0


def _command_check(args: argparse.Namespace) -> int:
    checked = 0
    for path in args.samples:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            validate_public_record(record)
            checked += 1
    if checked == 0:
        raise ValueError("no rollout samples were checked")
    print(f"ROLLOUT EXAMPLE CHECK PASSED: {checked} sanitized records")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    export = subparsers.add_parser("export", help="export one raw rollout as a sanitized JSONL record")
    export.add_argument("--condition", choices=("c3", "c4"), required=True)
    export.add_argument("--generation", type=int, required=True)
    export.add_argument("--individual", type=int, required=True)
    export.add_argument("--repeat", type=int, required=True)
    export.add_argument("--rollout-jsonl", type=Path, required=True)
    export.add_argument("--individual-meta", type=Path, required=True)
    export.add_argument("--public-rollouts", type=Path, required=True)
    export.add_argument("--public-quality", type=Path, required=True)
    export.add_argument("--output", default="-", help="output JSONL path, or '-' for stdout")
    export.set_defaults(func=_command_export)

    check = subparsers.add_parser("check", help="validate committed sanitized JSONL records")
    check.add_argument("samples", nargs="+", type=Path)
    check.set_defaults(func=_command_check)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        return args.func(args)
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"rollout example export/check failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

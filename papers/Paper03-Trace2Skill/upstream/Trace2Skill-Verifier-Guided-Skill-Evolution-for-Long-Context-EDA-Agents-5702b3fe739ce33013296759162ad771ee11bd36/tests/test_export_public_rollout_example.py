from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "export_public_rollout_example.py"
SPEC = importlib.util.spec_from_file_location("export_public_rollout_example", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("".join(json.dumps(record, separators=(",", ":")) + "\n" for record in records))


def test_export_omits_raw_content_and_keeps_safe_feedback(tmp_path: Path) -> None:
    # Assemble sentinels at runtime so the repository's release scanner can
    # test its patterns without carrying credential- or machine-path-like text.
    private_marker = "/" + "mnt" + "/private-host/secret-workspace"
    secret_marker = "s" + "k-" + "this-is-a-fake-secret-value-123456789"
    feedback = {
        "verifier_feedback": {
            "compile_ok": True,
            "sim_ok": True,
            "pass": True,
            "partial_score": 1.0,
            "tests_passed": 1,
            "tests_total": 1,
            "timeout": False,
            "first_failure": private_marker,
            "suggested_next_focus": secret_marker,
            "failed_test_names": ["hidden_test"],
            "waveform_observations": {
                "available": True,
                "files_analyzed": 1,
                "files_seen": 1,
                "signal_count": 3,
                "changed_signal_count": 2,
                "unknown_or_high_impedance_count": 0,
                "clock_or_reset_activity": True,
                "observations": [private_marker],
            },
        }
    }
    raw_result = json.dumps({"output": json.dumps(feedback)})
    raw = {
        "_ng_rollout_index": 2,
        "task_id": "cvdp_agentic_heavy_public_fixture_0001",
        "reward": 1.0,
        "responses_create_params": {"input": secret_marker},
        "docker_stderr": private_marker,
        "response": {
            "provider_specific_fields": {"token": secret_marker},
            "output": [
                {"type": "message", "content": private_marker},
                {
                    "type": "function_call",
                    "call_id": "private-provider-call-id",
                    "name": "edit",
                    "status": "completed",
                    "arguments": json.dumps(
                        {"filename": f"{private_marker}/design.v", "old_text": secret_marker, "new_text": "RTL"}
                    ),
                },
                {
                    "type": "function_call_output",
                    "call_id": "private-provider-call-id",
                    "output": private_marker,
                },
                {
                    "type": "function_call",
                    "call_id": "feedback-id",
                    "name": "verify_feedback",
                    "status": "completed",
                    "arguments": json.dumps({"reason": secret_marker}),
                },
                {"type": "function_call_output", "call_id": "feedback-id", "output": raw_result},
            ],
        },
    }
    public_rollout = {
        "condition": "C4",
        "task_id": raw["task_id"],
        "short_task_id": "public_fixture_0001",
        "cid": "cid005",
        "generation": 1,
        "individual_index": 0,
        "repeat_index": 0,
        "reward": 1.0,
        "outcome": "pass",
        "mode": "pass",
        "phase_reached": "P4-tested",
        "tests_passed": None,
        "tests_total": None,
        "files_written_count": 1,
        "path_has_critical_issue": False,
        "path_issue_codes": [],
        "num_tool_calls": 2,
        "verify_feedback_attempts": 1,
        "verify_feedback_executions": 1,
        "verify_feedback_budget_rejections": 0,
        "verify_feedback_gate_rejections": 0,
    }
    public_quality = {
        "condition": "C4",
        "task_id": raw["task_id"],
        "generation": 1,
        "individual_index": 0,
        "pass_at_1": 0.25,
        "SelectQ": 0.3,
        "SkillQ": 0.5,
        "AgentProgressQ": 0.4,
        "AgentVarianceQ": 0.2,
        "AgentAdherenceQ": 1.0,
    }
    meta = {
        "generation": 1,
        "individual_index": 0,
        "pass_at_1": 0.25,
        "selection_fitness": 0.3,
        "skill_quality": 0.5,
        "agent_behavior_quality": 0.4,
        "rollout_variance_quality": 0.2,
        "skill_adherence_quality": 1.0,
        "sha256": "a" * 64,
    }

    raw_path = tmp_path / "raw.jsonl"
    rollout_path = tmp_path / "public_rollouts.jsonl"
    quality_path = tmp_path / "public_quality.jsonl"
    meta_path = tmp_path / "meta.json"
    _jsonl(raw_path, [raw])
    _jsonl(rollout_path, [public_rollout])
    _jsonl(quality_path, [public_quality])
    meta_path.write_text(json.dumps(meta))

    record = MODULE.build_record(
        condition="c4",
        generation=1,
        individual=0,
        repeat=2,
        rollout_jsonl=raw_path,
        individual_meta=meta_path,
        public_rollouts=rollout_path,
        public_quality=quality_path,
    )
    serialized = json.dumps(record, sort_keys=True)
    assert private_marker not in serialized
    assert secret_marker not in serialized
    assert "private-provider-call-id" not in serialized
    assert "hidden_test" not in serialized
    assert record["trace_summary"]["assistant_message_count"] == 1
    safe_feedback = record["events"][1]["verifier_feedback"]
    assert safe_feedback["pass"] is True
    assert safe_feedback["tests_passed"] == 1
    assert safe_feedback["waveform_summary"]["signal_count"] == 3


def test_validator_rejects_raw_content_key() -> None:
    record = {
        "schema_version": 1,
        "sample_kind": "sanitized_action_trace",
        "events": [
            {
                "sequence": 1,
                "tool": "ls",
                "action_family": "inspect",
                "argument_commitment": {"sha256": "a" * 64},
                "result_commitment": {"sha256": "b" * 64},
                "content": "must never be public",
            }
        ],
        "trace_summary": {
            "tool_call_count": 1,
            "tool_counts": {"ls": 1},
            "action_family_counts": {"inspect": 1},
        },
    }
    with pytest.raises(ValueError, match="forbidden public key"):
        MODULE.validate_public_record(record)


def _committed_sample() -> dict:
    path = ROOT / "artifacts" / "rollout-examples" / "c3_noobscpu_sparse_example.jsonl"
    return json.loads(path.read_text())


def _committed_c4_sample() -> dict:
    path = ROOT / "artifacts" / "rollout-examples" / "c4_noobscpu_dense_example.jsonl"
    return json.loads(path.read_text())


@pytest.mark.parametrize(
    ("location", "field", "value"),
    [
        ("top", "raw_assistant_text", "apparently harmless prose"),
        ("event", "raw_result_text", "apparently harmless tool output"),
        ("path_summary", "original_location", "workspace/design.v"),
    ],
)
def test_validator_rejects_every_unknown_field(location: str, field: str, value: str) -> None:
    record = deepcopy(_committed_sample())
    if location == "top":
        target = record
    elif location == "event":
        target = record["events"][0]
    else:
        target = record["events"][0]["argument_commitment"]["string_field_commitments"][0]["path_summary"]
    target[field] = value
    with pytest.raises(ValueError, match="unexpected keys"):
        MODULE.validate_public_record(record)


@pytest.mark.parametrize(
    ("field", "value"),
    [("condition", "C5"), ("outcome", "unknown")],
)
def test_validator_rejects_invalid_enums(field: str, value: str) -> None:
    record = deepcopy(_committed_sample())
    if field == "condition":
        record["condition"] = value
    else:
        record["outcome"][field] = value
    with pytest.raises(ValueError, match="invalid"):
        MODULE.validate_public_record(record)


def test_validator_rejects_feedback_in_c3() -> None:
    record = deepcopy(_committed_c4_sample())
    record["condition"] = "C3"
    record["condition_description"] = MODULE.CONDITION_DESCRIPTIONS["C3"]
    with pytest.raises(ValueError, match="C3 records cannot"):
        MODULE.validate_public_record(record)


def test_validator_rejects_more_than_three_c4_executions() -> None:
    record = deepcopy(_committed_c4_sample())
    extra = deepcopy(next(event for event in record["events"] if "verifier_feedback" in event))
    extra["sequence"] = len(record["events"]) + 1
    record["events"].append(extra)
    record["trace_summary"]["tool_call_count"] += 1
    record["trace_summary"]["tool_counts"]["verify_feedback"] += 1
    record["trace_summary"]["action_family_counts"]["verifier_feedback"] += 1
    record["outcome"]["verify_feedback_attempts"] = 4
    record["outcome"]["verify_feedback_executions"] = 4
    with pytest.raises(ValueError, match="cannot exceed three"):
        MODULE.validate_public_record(record)


def test_validator_rejects_reward_outcome_mismatch() -> None:
    record = deepcopy(_committed_sample())
    record["outcome"]["outcome"] = "pass"
    with pytest.raises(ValueError, match="label and reward"):
        MODULE.validate_public_record(record)


def test_validator_rejects_impossible_test_counts() -> None:
    record = deepcopy(_committed_sample())
    record["outcome"]["tests_passed"] = 2
    record["outcome"]["tests_total"] = 1
    with pytest.raises(ValueError, match="cannot exceed"):
        MODULE.validate_public_record(record)


def test_validator_rejects_metrics_outside_unit_interval() -> None:
    record = deepcopy(_committed_sample())
    record["individual_metrics"]["SelectQ"] = 1.1
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        MODULE.validate_public_record(record)


def test_validator_rejects_impossible_feedback_test_counts() -> None:
    record = deepcopy(_committed_c4_sample())
    feedback = next(event["verifier_feedback"] for event in record["events"] if "verifier_feedback" in event)
    feedback["tests_passed"] = 2
    feedback["tests_total"] = 1
    with pytest.raises(ValueError, match="cannot exceed"):
        MODULE.validate_public_record(record)

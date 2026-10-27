from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))

from convert_rollouts import compute_metrics, convert_directory  # noqa: E402


def test_convert_directory_reads_rollouts_prefix(tmp_path: Path) -> None:
    input_dir = tmp_path / "rollouts"
    output_dir = tmp_path / "converted"
    input_dir.mkdir()
    rec = {
        "task_id": "cvdp_agentic_heavy_demo_0001",
        "reward": 1.0,
        "docker_exit_code": 0,
        "response": {
            "output": [
                {"type": "function_call", "name": "cat", "arguments": json.dumps({"filename": "SKILL.md"})}
            ]
        },
    }
    (input_dir / "rollouts_gen1_ind0.jsonl").write_text(json.dumps(rec) + "\n", encoding="utf-8")

    convert_directory(input_dir, output_dir)

    summaries = (output_dir / "model_summaries.jsonl").read_text(encoding="utf-8").splitlines()
    flat = (output_dir / "flat_rollouts.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(summaries) == 1
    assert len(flat) == 1
    assert json.loads(summaries[0])["metrics"]["overall_pass_at_1"] == 1.0


def test_skill_police_metrics_aggregate_policy_sources_and_actions() -> None:
    rec = {
        "task_id": "cvdp_agentic_heavy_demo_0001",
        "reward": 0.0,
        "response": {
            "metadata": {
                "skill_monitor": json.dumps({
                    "enabled": True,
                    "mode": "block",
                    "adherence_score": 0.8,
                    "blocked_actions": 1,
                    "num_violations": 2,
                    "violations_by_code": {
                        "python_file_passed_to_iverilog": 1,
                        "compile_after_failed_edit": 1,
                    },
                    "policy_hash": "abc123",
                    "expected_targets": [{"path": "rtl/dut.v", "confidence": "high"}],
                    "violations": [
                        {
                            "code": "python_file_passed_to_iverilog",
                            "source": "environment",
                            "action_taken": "block",
                            "confidence": "high",
                            "blocked": True,
                        },
                        {
                            "code": "compile_after_failed_edit",
                            "source": "environment",
                            "action_taken": "warn",
                            "confidence": "medium",
                            "blocked": False,
                        },
                    ],
                })
            },
            "output": [],
        },
    }

    metrics = compute_metrics([rec])
    monitor = metrics["skill_monitor"]

    assert monitor["enabled_rollouts"] == 1
    assert monitor["policy_enabled_rollouts"] == 1
    assert monitor["expected_target_policy_rollouts"] == 1
    assert monitor["violations_by_action"] == {"block": 1, "warn": 1}
    assert monitor["violations_by_source"] == {"environment": 2}
    assert monitor["violations_by_confidence"] == {"high": 1, "medium": 1}
    assert monitor["policy_hashes"] == {"abc123": 1}
    assert monitor["blocked_examples"][0]["code"] == "python_file_passed_to_iverilog"

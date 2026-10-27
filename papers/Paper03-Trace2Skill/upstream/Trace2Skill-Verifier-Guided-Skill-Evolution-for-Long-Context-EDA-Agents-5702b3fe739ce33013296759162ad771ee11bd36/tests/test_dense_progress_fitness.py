from __future__ import annotations

import json

from eval.convert_rollouts import compute_metrics


def _call(name: str, **arguments: object) -> dict:
    return {
        "type": "function_call",
        "name": name,
        "arguments": json.dumps(arguments),
    }


def _output(text: str) -> dict:
    return {
        "type": "function_call_output",
        "output": json.dumps({"output": text}),
    }


def _rollout(task_id: str, reward: float, output: list[dict], stderr: str = "") -> dict:
    return {
        "task_id": task_id,
        "reward": reward,
        "docker_stderr": stderr,
        "response": {"output": output},
    }


def test_dense_progress_ranks_better_failures_above_empty_failures() -> None:
    empty_failure = _rollout("task_a", 0.0, [])
    near_failure = _rollout(
        "task_a",
        0.0,
        [
            _call("cat", filename="harness/1/src/test_runner.py"),
            _call("cat", filename="tb/dut_tb.v"),
            _call("echo", filename="src/dut.v", content="module dut; endmodule"),
            _call("cat", filename="src/dut.v"),
            _call("iverilog", args="-g2012 -s tb -o sim.vvp src/dut.v tb/dut_tb.v"),
            _output("[exit code: 0]"),
            _call("vvp", filename="sim.vvp"),
            _output("[exit code: 0]"),
        ],
        stderr="** TESTS=4 PASS=2 FAIL=2 SKIP=0 **",
    )

    empty_metrics = compute_metrics([empty_failure])
    near_metrics = compute_metrics([near_failure])

    assert empty_metrics["overall_pass_at_1"] == near_metrics["overall_pass_at_1"] == 0.0
    assert near_metrics["progress_fitness"] > empty_metrics["progress_fitness"]
    assert near_metrics["selection_fitness"] > empty_metrics["selection_fitness"]


def test_dense_progress_cannot_outweigh_a_real_pass() -> None:
    near_failure = _rollout(
        "task_a",
        0.0,
        [
            _call("cat", filename="harness/1/src/test_runner.py"),
            _call("cat", filename="tb/dut_tb.v"),
            _call("echo", filename="src/dut.v", content="module dut; endmodule"),
            _call("cat", filename="src/dut.v"),
            _call("iverilog", args="-g2012 -s tb -o sim.vvp src/dut.v tb/dut_tb.v"),
            _output("[exit code: 0]"),
            _call("vvp", filename="sim.vvp"),
            _output("[exit code: 0]"),
        ],
        stderr="** TESTS=10 PASS=9 FAIL=1 SKIP=0 **",
    )
    pass_rollout = _rollout("task_a", 1.0, [])

    near_metrics = compute_metrics([near_failure])
    pass_metrics = compute_metrics([pass_rollout])

    assert near_metrics["overall_pass_at_1"] == 0.0
    assert pass_metrics["overall_pass_at_1"] == 1.0
    assert near_metrics["selection_fitness"] < pass_metrics["selection_fitness"]


def test_mixed_task_pass_at_one_remains_true_verifier_metric() -> None:
    rollouts = [
        _rollout("task_a", 1.0, []),
        _rollout("task_b", 0.0, [_call("cat", filename="src/foo.v")]),
        _rollout("task_c", 0.0, [_call("cat", filename="src/bar.v")]),
    ]

    metrics = compute_metrics(rollouts)

    assert metrics["overall_pass_at_1"] == 0.3333
    assert metrics["selection_fitness"] > metrics["overall_pass_at_1"]
    assert metrics["selection_epsilon"] < 1 / len(rollouts)
    assert set(metrics["progress_components"]) == {
        "verifier_partial",
        "execution_phase",
        "harness_alignment",
        "edit_quality",
        "efficiency",
    }


def test_skill_monitor_adherence_becomes_dense_component_only_when_present() -> None:
    monitored = _rollout(
        "task_a",
        0.0,
        [
            _call("cat", filename="SKILL.md"),
            _call("edit", filename="src/dut.v", old_text="a", new_text="b"),
        ],
    )
    monitored["response"]["metadata"] = {
        "skill_monitor": json.dumps({
            "enabled": True,
            "mode": "warn",
            "adherence_score": 0.75,
            "num_violations": 2,
            "blocked_actions": 1,
            "violations_by_code": {"vvp_after_failed_compile": 1, "failed_or_noop_edit": 1},
        })
    }

    metrics = compute_metrics([monitored])

    assert metrics["progress_components"]["skill_adherence"] == 0.75
    assert metrics["skill_monitor"]["enabled_rollouts"] == 1
    assert metrics["skill_monitor"]["total_violations"] == 2
    assert metrics["skill_monitor"]["total_blocked_actions"] == 1
    assert metrics["skill_monitor"]["violations_by_code"]["failed_or_noop_edit"] == 1

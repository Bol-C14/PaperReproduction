from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "optimizer"))

from fitness import apply_path_grounding_fitness_adjustment  # noqa: E402


def _call(name: str, **arguments: object) -> dict:
    return {
        "type": "function_call",
        "name": name,
        "arguments": json.dumps(arguments),
    }


def _rollout(prompt: str, calls: list[dict]) -> dict:
    return {
        "task_id": "cvdp_agentic_heavy_path_0001",
        "reward": 0.0,
        "responses_create_params": {
            "input": [
                {"role": "user", "content": prompt},
            ]
        },
        "response": {"output": calls},
    }


def test_path_grounding_adjustment_penalizes_wrong_target_dense_progress() -> None:
    prompt = "Implement the missing module in `/code/rtl/pre_norm.v`."
    wrong_path = _rollout(
        prompt,
        [
            _call("echo", filename="src/pre_norm.v", content="module pre_norm; endmodule"),
            _call("iverilog", args="-g2012 -o sim.vvp src/pre_norm.v"),
        ],
    )
    metrics = {
        "overall_pass_at_1": 0.0,
        "progress_fitness": 0.8,
        "selection_fitness": 0.392,
        "selection_epsilon": 0.49,
        "progress_components": {"edit_quality": 1.0},
    }

    adjusted = apply_path_grounding_fitness_adjustment(dict(metrics), [wrong_path])

    assert adjusted["progress_fitness"] < metrics["progress_fitness"]
    assert adjusted["selection_fitness"] < metrics["selection_fitness"]
    assert adjusted["raw_progress_fitness"] == metrics["progress_fitness"]
    assert adjusted["progress_components"]["path_grounding"] < 1.0
    assert adjusted["path_grounding_fitness"]["issue_counts"]["wrong_target_path"] == 1


def test_path_grounding_adjustment_is_neutral_without_inferred_target() -> None:
    rollout = _rollout("Make the design better.", [_call("cat", filename="src/dut.v")])
    metrics = {
        "overall_pass_at_1": 0.0,
        "progress_fitness": 0.5,
        "selection_fitness": 0.245,
        "selection_epsilon": 0.49,
        "progress_components": {"edit_quality": 0.2},
    }

    adjusted = apply_path_grounding_fitness_adjustment(dict(metrics), [rollout])

    assert adjusted == metrics


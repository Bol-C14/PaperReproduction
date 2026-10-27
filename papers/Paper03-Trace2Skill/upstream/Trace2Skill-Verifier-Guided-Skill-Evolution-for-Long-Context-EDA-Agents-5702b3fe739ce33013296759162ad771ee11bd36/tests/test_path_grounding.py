from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "optimizer"))

from path_grounding import (  # noqa: E402
    analyze_path_grounding,
    format_path_grounding_for_oracle,
    infer_expected_target_paths,
)
from run_optimizer import build_rollout_diagnostic  # noqa: E402


def _call(call_id: str, name: str, **arguments: object) -> dict:
    return {
        "type": "function_call",
        "call_id": call_id,
        "name": name,
        "arguments": json.dumps(arguments),
    }


def _rollout(user_prompt: str, output: list[dict], reward: float = 0.0) -> dict:
    return {
        "task_id": "cvdp_agentic_heavy_fpu_wrappers_0002",
        "category": "cid003",
        "reward": reward,
        "docker_exit_code": 0 if reward > 0 else 1,
        "responses_create_params": {
            "input": [
                {"role": "developer", "content": "You are in /code and must edit files."},
                {"role": "user", "content": user_prompt},
            ],
        },
        "response": {"output": output},
    }


def test_infers_missing_module_target_from_prompt() -> None:
    prompt = (
        "The top-level module located at `/code/fpu-wrappers/resources/opencores/fpu.v` "
        "instantiates the `pre_norm` module, which is not implemented. Add the missing "
        "module in a new file `/code/fpu-wrappers/resources/opencores/pre_norm.v`."
    )

    targets = infer_expected_target_paths(_rollout(prompt, []))

    assert targets == ["fpu-wrappers/resources/opencores/pre_norm.v"]


def test_wrong_same_basename_path_is_a_critical_grounding_issue() -> None:
    prompt = (
        "The top-level module located at `/code/fpu-wrappers/resources/opencores/fpu.v` "
        "instantiates the `pre_norm` module, which is not implemented. Add the missing "
        "module in a new file `/code/fpu-wrappers/resources/opencores/pre_norm.v`."
    )
    rollout = _rollout(
        prompt,
        [
            _call("c1", "echo", filename="rtl/pre_norm.v", content="module pre_norm; endmodule"),
            _call(
                "c2",
                "iverilog",
                args=(
                    "-o sim.vvp -g2012 rtl/pre_norm.v "
                    "fpu-wrappers/resources/opencores/fpu.v"
                ),
            ),
        ],
        reward=0.0,
    )

    analysis = analyze_path_grounding(rollout)

    assert analysis["expected_targets"] == ["fpu-wrappers/resources/opencores/pre_norm.v"]
    assert "wrong_target_path" in analysis["issue_codes"]
    assert "validation_on_wrong_path" in analysis["issue_codes"]
    assert analysis["has_critical_issue"] is True
    assert "rtl/pre_norm.v" in analysis["hard_directives"][0]

    oracle_block = format_path_grounding_for_oracle(rollout)
    assert "PATH_GROUNDING_CHECK" in oracle_block
    assert "fpu-wrappers/resources/opencores/pre_norm.v" in oracle_block
    assert "rtl/pre_norm.v" in oracle_block


def test_expected_target_write_does_not_trigger_wrong_path_issue() -> None:
    prompt = "Implement the missing module in `/code/src/filter_stage.sv`."
    rollout = _rollout(
        prompt,
        [
            _call("c1", "echo", filename="src/filter_stage.sv", content="module filter_stage; endmodule"),
            _call("c2", "iverilog", args="-o sim.vvp -g2012 src/filter_stage.sv tb.sv"),
        ],
        reward=1.0,
    )

    analysis = analyze_path_grounding(rollout)

    assert analysis["expected_targets"] == ["src/filter_stage.sv"]
    assert analysis["issues"] == []
    assert analysis["has_issues"] is False


def test_rollout_diagnostic_includes_path_grounding_payload() -> None:
    prompt = "Create `/code/src/pre_norm.v`, then compile that source file."
    rollout = _rollout(
        prompt,
        [
            _call("c1", "echo", filename="rtl/pre_norm.v", content="module pre_norm; endmodule"),
            _call("c2", "iverilog", args="-o sim.vvp -g2012 rtl/pre_norm.v"),
        ],
        reward=0.0,
    )

    diagnostic = build_rollout_diagnostic(
        rollout,
        generation=3,
        individual_index=0,
        rollout_index=1,
        cid_lookup={},
        parent_info="child",
        repeat_index=0,
    )

    assert diagnostic["path_grounding"]["expected_targets"] == ["src/pre_norm.v"]
    assert "wrong_target_path" in diagnostic["path_grounding"]["issue_codes"]

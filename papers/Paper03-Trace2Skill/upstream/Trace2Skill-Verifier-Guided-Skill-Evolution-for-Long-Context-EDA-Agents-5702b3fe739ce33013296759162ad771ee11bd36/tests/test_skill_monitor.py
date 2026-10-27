from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "optimizer"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "nemogym"))

from fitness import inject_skill_into_tasks  # noqa: E402
from responses_api_agents.cvdp_agentic_heavy_agent.skill_monitor import (  # noqa: E402
    SkillContractMonitor,
    SkillMonitorConfig,
    compile_skill_policy,
)


def _monitor(mode: str = "block", **kwargs) -> SkillContractMonitor:
    return SkillContractMonitor(
        SkillMonitorConfig(enabled=True, mode=mode, task_id="t1", categories=["cid003"], **kwargs),
        initial_input=[{"role": "user", "content": "Use the provided cocotb harness."}],
    )


def test_blocks_vvp_after_failed_compile() -> None:
    monitor = _monitor(mode="block")
    monitor.after_tool(
        step=1,
        tool="iverilog",
        args={"args": "-o sim.vvp dut.v"},
        output="dut.v:3: syntax error\n[exit code: 1]",
    )

    decision = monitor.before_tool(step=2, tool="vvp", args={"filename": "sim.vvp"})

    assert decision.should_block
    assert "vvp_after_failed_compile" in decision.feedback_text()
    summary = monitor.summary()
    assert summary["blocked_actions"] == 1
    assert summary["violations_by_code"]["vvp_after_failed_compile"] == 1


def test_blocks_custom_testbench_when_skill_forbids_it() -> None:
    monitor = _monitor(mode="block", block_skill_guidance=True)
    monitor.after_tool(
        step=1,
        tool="cat",
        args={"filename": "SKILL.md"},
        output="NEVER create a custom/parallel testbench. Use the provided cocotb harness only.",
    )

    decision = monitor.before_tool(
        step=2,
        tool="echo",
        args={"filename": "tb/my_custom_tb.v", "content": "module tb; endmodule"},
    )

    assert decision.should_block
    assert "custom_testbench_forbidden" in decision.feedback_text()


def test_skill_guidance_defaults_to_warning_not_blocking() -> None:
    monitor = _monitor(mode="block")
    monitor.after_tool(
        step=1,
        tool="cat",
        args={"filename": "SKILL.md"},
        output="NEVER create a custom/parallel testbench. Use the provided cocotb harness only.",
    )

    decision = monitor.before_tool(
        step=2,
        tool="echo",
        args={"filename": "tb/my_custom_tb.v", "content": "module tb; endmodule"},
    )

    assert not decision.should_block
    assert "custom_testbench_forbidden" in decision.feedback_text()


def test_blocks_python_file_passed_to_iverilog_as_environment_invariant() -> None:
    monitor = _monitor(mode="block")

    decision = monitor.before_tool(
        step=1,
        tool="iverilog",
        args={"args": "-g2012 -o sim.vvp harness/test_runner.py rtl/dut.v"},
    )

    assert decision.should_block
    assert "python_file_passed_to_iverilog" in decision.feedback_text()


def test_blocks_high_confidence_same_basename_shadow_path() -> None:
    policy = compile_skill_policy(
        "# skill\nUse exact target paths.\n",
        [{"role": "user", "content": "Fix the RTL bug in `/code/project/rtl/pre_norm.v`."}],
        task_id="t1",
        categories=["cid005"],
    )
    monitor = SkillContractMonitor(
        SkillMonitorConfig(enabled=True, mode="block", task_id="t1", categories=["cid005"], policy=policy),
        initial_input=[{"role": "user", "content": "Fix the RTL bug in `/code/project/rtl/pre_norm.v`."}],
    )

    decision = monitor.before_tool(
        step=1,
        tool="echo",
        args={"filename": "rtl/pre_norm.v", "content": "module pre_norm; endmodule"},
    )

    assert decision.should_block
    assert "write_same_basename_shadow_path" in decision.feedback_text()


def test_allows_testbench_edits_for_checker_or_stimulus_cids() -> None:
    monitor = SkillContractMonitor(
        SkillMonitorConfig(enabled=True, mode="block", task_id="t1", categories=["cid013"], block_skill_guidance=True),
        initial_input=[{"role": "user", "content": "Extend the checker in the visible testbench."}],
    )
    monitor.after_tool(
        step=1,
        tool="cat",
        args={"filename": "SKILL.md"},
        output="NEVER create a custom/parallel testbench for unrelated RTL tasks.",
    )

    decision = monitor.before_tool(
        step=2,
        tool="echo",
        args={"filename": "tb/checker_tb.sv", "content": "module checker_tb; endmodule"},
    )

    assert not decision.should_block


def test_metadata_config_parses_json_string() -> None:
    class Body:
        metadata = {
            "skill_monitor": json.dumps({
                "enabled": True,
                "mode": "warn",
                "task_id": "task_x",
                "categories": ["cid014"],
            })
        }
        input = [{"role": "user", "content": "Add SVA to RTL."}]

    monitor = SkillContractMonitor.from_response_body(Body())

    assert monitor.enabled
    assert monitor.mode == "warn"
    assert monitor.config.task_id == "task_x"
    assert monitor.contract.require_sva_in_rtl


def test_skill_injection_defaults_monitor_to_passive_logging(tmp_path: Path) -> None:
    task = {
        "responses_create_params": {
            "input": [{"role": "developer", "content": "dev"}, {"role": "user", "content": "task"}],
            "tools": [],
        },
        "verifier_metadata": {
            "task_id": "cvdp_agentic_heavy_spi_0001",
            "categories": ["cid014", "hard"],
            "difficulty": "hard",
            "context_files": {},
        },
    }
    out = tmp_path / "tasks.jsonl"

    inject_skill_into_tasks(
        [task],
        "# skill\n- follow visible files\n",
        out,
        skill_monitor_cfg={"enabled": True, "mode": "passive"},
    )

    row = json.loads(out.read_text(encoding="utf-8"))
    payload = json.loads(row["responses_create_params"]["metadata"]["skill_monitor"])
    assert payload["enabled"] is True
    assert payload["mode"] == "passive"
    assert payload["inject_feedback"] is False
    assert payload["policy"]["schema_version"] == 1
    assert payload["policy"]["policy_hash"]

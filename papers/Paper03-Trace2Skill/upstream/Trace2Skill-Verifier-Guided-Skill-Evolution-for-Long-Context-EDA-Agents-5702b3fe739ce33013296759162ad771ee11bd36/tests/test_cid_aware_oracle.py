from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "optimizer"))

from streaming_oracle import run_generation_oracle  # noqa: E402


class _MockCompletions:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def create(self, model, messages, **kwargs):
        system = messages[0]["content"]
        user = messages[1]["content"]
        self.calls.append({"system": system, "user": user, "kwargs": kwargs})
        if "refinement protocol" in system:
            content = "# task insight\n- observed rollout evidence\n"
        elif "Synthesize patterns only for CID" in system:
            cid = system.split("CID ", 1)[1].split(";", 1)[0]
            content = f"# CID synthesis for {cid}\n- generalized within {cid}\n"
        else:
            cid = system.split("CID ", 1)[1].split(" skill", 1)[0]
            content = f"# Oracle feedback for {cid}\n## Mutation directives\n- keep CID-specific guidance\n"
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content), finish_reason="stop")]
        )


class _MockClient:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(completions=_MockCompletions())


def _call(name: str, **arguments: object) -> dict:
    return {
        "type": "function_call",
        "name": name,
        "arguments": json.dumps(arguments),
    }


def _rollout(task_id: str, cid: str, reward: float) -> dict:
    return {
        "task_id": task_id,
        "category": cid,
        "reward": reward,
        "docker_exit_code": 0 if reward > 0 else 1,
        "response": {
            "output": [
                _call("cat", filename="SKILL.md"),
                _call("edit", filename="rtl/dut.sv", old_text="a", new_text="b"),
                _call("iverilog", args="-g2012 rtl/dut.sv tb.sv"),
                _call("vvp", filename="sim.vvp"),
            ]
        },
    }


def test_run_generation_oracle_aggregates_task_insights_by_cid(tmp_path) -> None:
    gen_dir = tmp_path / "gen1"
    gen_dir.mkdir()
    client = _MockClient()
    heartbeats: list[dict] = []

    def _heartbeat(**kwargs) -> None:
        heartbeats.append(kwargs)

    task_manifest = [
        {
            "task_id": "cvdp_agentic_heavy_spi_0001",
            "short_task_id": "spi_0001",
            "cid": "cid014",
            "categories": ["cid014", "hard"],
        },
        {
            "task_id": "cvdp_agentic_heavy_i2c_0002",
            "short_task_id": "i2c_0002",
            "cid": "cid005",
            "categories": ["cid005", "hard"],
        },
    ]

    oracle_path = run_generation_oracle(
        gen_dir=gen_dir,
        generation=1,
        rollouts_by_individual=[
            [
                _rollout("cvdp_agentic_heavy_spi_0001", "cid014", 1.0),
                _rollout("cvdp_agentic_heavy_spi_0001", "cid014", 0.0),
                _rollout("cvdp_agentic_heavy_i2c_0002", "cid005", 0.0),
            ]
        ],
        scoreboard=(
            "  [cid014] spi_0001: avg=50%\n"
            "  [cid005] i2c_0002: avg=0%"
        ),
        best=0.5,
        mean=0.25,
        worst=0.0,
        llm_client=client,
        llm_model="mock",
        task_manifest=task_manifest,
        heartbeat_callback=_heartbeat,
    )

    assert oracle_path == gen_dir / "oracle_feedback.md"
    assert (gen_dir / "task_insights" / "cid014" / "spi_0001_pass.md").exists()
    assert (gen_dir / "task_insights" / "cid014" / "spi_0001_fail.md").exists()
    assert (gen_dir / "task_insights" / "cid005" / "i2c_0002_fail.md").exists()
    assert (gen_dir / "cid_synthesis" / "cid014" / "pass_synthesis.md").exists()
    assert (gen_dir / "cid_synthesis" / "cid014" / "fail_synthesis.md").exists()
    assert (gen_dir / "cid_synthesis" / "cid005" / "fail_synthesis.md").exists()
    assert (gen_dir / "cid_synthesis" / "cid005" / "metrics.json").exists()
    assert (gen_dir / "cid_oracle_feedback" / "cid014.md").exists()
    assert (gen_dir / "cid_oracle_feedback" / "cid005.md").exists()

    combined = oracle_path.read_text(encoding="utf-8")
    assert "## CID cid014" in combined
    assert "## CID cid005" in combined
    layer1_prompts = [
        call["user"] for call in client.chat.completions.calls
        if "ROLLOUT_ID:" in call["user"]
    ]
    assert any("ROLLOUT_ID: ind0_taskspi_0001_rep0_r0" in prompt for prompt in layer1_prompts)
    assert any("ROLLOUT_ID: ind0_taskspi_0001_rep1_r1" in prompt for prompt in layer1_prompts)

    cid005_metrics = json.loads((gen_dir / "cid_synthesis" / "cid005" / "metrics.json").read_text(encoding="utf-8"))
    assert cid005_metrics["rollouts"] == 1
    assert cid005_metrics["fails"] == 1
    assert cid005_metrics["tasks"]["i2c_0002"]["pass_rate"] == 0.0
    assert cid005_metrics["macro_task_pass_rate"] == 0.0

    phases = [row.get("phase") for row in heartbeats]
    assert "oracle_layer1" in phases
    assert "oracle_layer2_cid" in phases
    assert "oracle_layer3_cid" in phases
    assert "oracle_layer3_done" in phases
    assert any(
        row.get("context", {}).get("rollout_id") == "ind0_taskspi_0001_rep0_r0"
        for row in heartbeats
    )

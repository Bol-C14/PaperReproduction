#!/usr/bin/env python3
"""Verify the one-task public materialization produced by run_smoke.sh."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml


REQUIRED_TOOLS = {
    "ls", "cat", "rg", "find_files", "read_file", "show_changes",
    "module_index", "echo", "edit", "iverilog", "vvp", "pwd",
}


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(f"Usage: {sys.argv[0]} <manifest.json>")
    manifest_path = Path(sys.argv[1]).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["condition"] == "c4-dense"
    assert manifest["dataset"]["revision"] == "5b807d945f6a99aa645f7e43a64a2115e281b4bf"
    assert manifest["generations"] == 2
    assert manifest["population_size"] == 2
    assert manifest["num_repeats"] == 1
    assert len(manifest["tasks"]) == 1

    task = manifest["tasks"][0]
    assert task["task_id"] == "cvdp_agentic_heavy_schoolMIPS_0012"
    row = json.loads(Path(task["task_path"]).read_text(encoding="utf-8"))
    tools = {item["name"] for item in row["responses_create_params"]["tools"]}
    assert REQUIRED_TOOLS <= tools
    assert "verify_feedback" in tools
    assert "xcelium" not in tools
    assert len(row["verifier_metadata"]["context_files"]["SKILL.md"]) >= 100

    config = yaml.safe_load(Path(task["config_path"]).read_text(encoding="utf-8"))
    assert config["ga"]["generations"] == 2
    assert config["ga"]["population_size"] == 2
    assert config["fitness"]["num_repeats"] == 1
    assert config["runtime_verifier_feedback"] == {
        "enabled": True,
        "max_calls": 3,
        "artifact_root": str(Path(task["output_dir"]) / "runtime_verifier_feedback"),
    }
    print(f"verified public smoke task: {task['task_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

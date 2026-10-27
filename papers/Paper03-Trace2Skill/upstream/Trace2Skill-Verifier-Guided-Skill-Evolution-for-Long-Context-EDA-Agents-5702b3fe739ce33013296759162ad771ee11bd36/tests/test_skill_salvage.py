from __future__ import annotations

from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "optimizer"))

from run_optimizer import (  # noqa: E402
    _build_parent_preserving_salvage_candidate,
    process_candidate_skill_for_injection,
)
from skill_integration import build_skill_patch_plan, format_skill_patch_plan, validate_skill_integration  # noqa: E402
from skill_sanitizer import infer_execution_contract, sanitize_skill  # noqa: E402


def _task() -> dict:
    return {
        "responses_create_params": {
            "input": [
                {
                    "role": "developer",
                    "content": """TOOLS:
ls(path)
cat(filename)
edit(filename,old_text,new_text)
iverilog(args)
vvp(filename)
pwd()

GRADING: A hidden verifier runs after completion.
""",
                },
                {"role": "user", "content": "Fix /code/rtl/dut.sv."},
            ],
            "tools": [
                {"type": "function", "name": name, "parameters": {"type": "object"}}
                for name in ("ls", "cat", "edit", "iverilog", "vvp", "pwd")
            ],
        }
    }


def test_parent_preserving_salvage_keeps_useful_child_lesson_and_drops_defect() -> None:
    contract = infer_execution_contract([_task()])
    plan = build_skill_patch_plan(
        """## ADD
- Compile the exact target path `rtl/dut.sv` with iverilog before vvp.
- Preserve `valid_o` until `ready_i` completes a transfer.

## REMOVE
- Remove advice to run the hidden harness.
""",
        contract,
    )
    parent = """# Skill

- Use edit for RTL changes.
- Preserve `valid_o` until `ready_i` completes a transfer.
- Never run the hidden harness; it is unavailable during rollout.
"""
    flawed_child = """# Skill

- Use edit for RTL changes.
- Compile the exact target path `rtl/dut.sv` with iverilog before vvp.
- Run the hidden harness to confirm the final answer.
"""

    child_report = validate_skill_integration(
        candidate_skill=flawed_child,
        parent_skill=parent,
        patch_plan=plan,
        execution_contract=contract,
    )
    assert not child_report["ok"]
    assert "semantic_contradiction" in child_report["issues"]
    assert "must_remove_violation" in child_report["issues"]

    salvage, record = _build_parent_preserving_salvage_candidate(
        parent_prompt=parent,
        candidate_report=child_report,
        patch_plan=plan.to_dict(),
    )

    assert salvage is not None
    assert record["attempted"] is True
    assert "Compile the exact target path" in salvage
    assert "Run the hidden harness to confirm" not in salvage

    sanitized = sanitize_skill(salvage, parent, contract, max_chars=8000)
    assert sanitized.ok

    final_report = validate_skill_integration(
        candidate_skill=sanitized.text,
        parent_skill=parent,
        patch_plan=plan,
        execution_contract=contract,
    )
    assert final_report["ok"]
    assert final_report["metrics"]["coverage"] > child_report["metrics"]["parent_coverage"]


def test_process_candidate_injection_uses_salvage_before_rejecting(tmp_path: Path) -> None:
    contract = infer_execution_contract([_task()])
    plan = build_skill_patch_plan(
        """## ADD
- Compile the exact target path `rtl/dut.sv` with iverilog before vvp.
- Preserve `valid_o` until `ready_i` completes a transfer.

## REMOVE
- Remove advice to run the hidden harness.
""",
        contract,
    )
    parent = """# Skill

- Use edit for RTL changes.
- Preserve `valid_o` until `ready_i` completes a transfer.
- Never run the hidden harness; it is unavailable during rollout.
"""
    flawed_child = """# Skill

- Use edit for RTL changes.
- Compile the exact target path `rtl/dut.sv` with iverilog before vvp.
- Run the hidden harness to confirm the final answer.
"""

    selected, record = process_candidate_skill_for_injection(
        client=None,
        mutation_model="unused",
        objective="fix RTL",
        output_dir=tmp_path,
        generation=1,
        child_slot=0,
        parent_info="parent",
        stage="mutation",
        candidate=flawed_child,
        parent_prompt=parent,
        max_skill_length=8000,
        sanitizer_cfg={"enabled": True},
        execution_contract=contract,
        execution_constraints_text="",
        skill_patch_plan_text=format_skill_patch_plan(plan),
        skill_patch_plan=plan.to_dict(),
        integration_cfg={},
        repair_cfg={"enabled": False, "salvage": {"enabled": True}},
        audit_logger=None,
    )

    assert "Compile the exact target path" in selected
    assert "Run the hidden harness to confirm" not in selected
    assert record["skill_integration"]["ok"]
    assert record["repair_attempted"] is True
    assert record["salvage"]["status"] == "ok"
    assert (tmp_path / "gen1" / "skill_integration" / "child0_mutation_salvage.json").exists()


def test_process_candidate_injection_soft_salvages_low_retention_child(tmp_path: Path) -> None:
    contract = infer_execution_contract([_task()])
    plan = build_skill_patch_plan(
        """## ADD
- Compile the exact target path `rtl/dut.sv` with iverilog before vvp.

## PRESERVE
- Keep the reset ordering rule.
""",
        contract,
    )
    parent = """# Skill

- Use edit for RTL changes.
- Keep the reset ordering rule.
- Preserve the parent-only diagnostic checklist before changing RTL.
- Never run the hidden harness; it is unavailable during rollout.
"""
    parent += "\n".join(f"- Durable parent rule {idx}: inspect visible RTL before editing." for idx in range(20))

    compact_child = """# Skill

- Use edit for RTL changes.
- Keep the reset ordering rule.
- Compile the exact target path `rtl/dut.sv` with iverilog before vvp.
- Never run the hidden harness; it is unavailable during rollout.
"""

    selected, record = process_candidate_skill_for_injection(
        client=None,
        mutation_model="unused",
        objective="fix RTL",
        output_dir=tmp_path,
        generation=2,
        child_slot=1,
        parent_info="parent",
        stage="mutation",
        candidate=compact_child,
        parent_prompt=parent,
        max_skill_length=12000,
        sanitizer_cfg={"enabled": True},
        execution_contract=contract,
        execution_constraints_text="",
        skill_patch_plan_text=format_skill_patch_plan(plan),
        skill_patch_plan=plan.to_dict(),
        integration_cfg={"min_child_parent_ratio_for_soften": 0.75},
        repair_cfg={
            "enabled": False,
            "salvage": {
                "enabled": True,
                "soft_parent_floor": True,
                "min_child_parent_ratio_for_soften": 0.75,
            },
        },
        audit_logger=None,
    )

    assert "Compile the exact target path" in selected
    assert "Preserve the parent-only diagnostic checklist" in selected
    assert record["skill_integration"]["ok"]
    assert record["repair_attempted"] is True
    assert record["salvage"]["kind"] == "soft_parent_floor"
    assert record["salvage"]["used"] is True
    assert (tmp_path / "gen2" / "skill_integration" / "child1_mutation_soft_salvage.json").exists()

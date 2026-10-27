from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "optimizer"))

from skill_integration import build_skill_patch_plan, validate_skill_integration  # noqa: E402
from skill_sanitizer import infer_execution_contract  # noqa: E402
from skill_selector import select_child_skill_against_parent  # noqa: E402


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


def test_semantic_selector_keeps_parent_when_child_drops_durable_lesson() -> None:
    contract = infer_execution_contract([_task()])
    plan = build_skill_patch_plan(
        """## ADD
- Preserve `valid_o` until `ready_i` completes a transfer.

## PRESERVE
- Keep the exact target path `rtl/dut.sv`.

## REMOVE
- Remove advice to run the hidden harness.
""",
        contract,
    )
    parent = """# Skill

- Edit only `rtl/dut.sv`.
- Preserve `valid_o` until `ready_i` completes a transfer.
- Never run the hidden harness; it is unavailable during rollout.
"""
    child = """# Skill

- Start with a broad search.
- Use edit for RTL changes.
- Never run the hidden harness; it is unavailable during rollout.
"""
    child_report = validate_skill_integration(
        candidate_skill=child,
        parent_skill=parent,
        patch_plan=plan,
        execution_contract=contract,
    )

    selected, decision = select_child_skill_against_parent(
        parent_skill=parent,
        candidate_skill=child,
        patch_plan=plan.to_dict(),
        execution_contract=contract,
        integration_cfg={},
        selector_cfg={},
        child_integration_report=child_report,
    )

    assert selected == parent
    assert decision["decision"] == "keep_parent"
    assert decision["rollout_fitness_used_for_selection"] is False
    assert "semantic_score_below_parent" in decision["reasons"]


def test_semantic_selector_accepts_grounded_child_that_adds_covered_lesson() -> None:
    contract = infer_execution_contract([_task()])
    plan = build_skill_patch_plan(
        """## ADD
- Preserve `valid_o` until `ready_i` completes a transfer.
- Compile the exact target path `rtl/dut.sv` with iverilog before vvp.

## REMOVE
- Remove advice to run the hidden harness.
""",
        contract,
    )
    parent = """# Skill

- Use edit for RTL changes.
- Never run the hidden harness; it is unavailable during rollout.
"""
    child = """# Skill

- Use edit for RTL changes.
- Never run the hidden harness; it is unavailable during rollout.
- Preserve `valid_o` until `ready_i` completes a transfer.
- Compile the exact target path `rtl/dut.sv` with iverilog before vvp.
"""
    child_report = validate_skill_integration(
        candidate_skill=child,
        parent_skill=parent,
        patch_plan=plan,
        execution_contract=contract,
    )

    selected, decision = select_child_skill_against_parent(
        parent_skill=parent,
        candidate_skill=child,
        patch_plan=plan.to_dict(),
        execution_contract=contract,
        integration_cfg={},
        selector_cfg={},
        child_integration_report=child_report,
    )

    assert selected == child
    assert decision["decision"] == "accept_child"
    assert "semantic_score_improved" in decision["reasons"]
    assert decision["rollout_fitness_used_for_selection"] is False


def test_semantic_selector_accepts_initial_exploration_without_oracle_feedback() -> None:
    contract = infer_execution_contract([_task()])
    parent = "# Skill\n- Use edit.\n"
    child = "# Skill\n- Use edit.\n- Run iverilog before vvp.\n"

    selected, decision = select_child_skill_against_parent(
        parent_skill=parent,
        candidate_skill=child,
        patch_plan=None,
        execution_contract=contract,
        integration_cfg={},
        selector_cfg={},
    )

    assert selected == child
    assert decision["decision"] == "accept_child_no_oracle_feedback"

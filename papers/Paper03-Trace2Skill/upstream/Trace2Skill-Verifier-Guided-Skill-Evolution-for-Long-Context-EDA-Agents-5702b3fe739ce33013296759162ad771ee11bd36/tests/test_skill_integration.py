from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "optimizer"))

from skill_integration import (  # noqa: E402
    build_skill_patch_plan,
    format_skill_patch_plan,
    repair_semantic_contradictions,
    validate_skill_integration,
    write_skill_integration_report,
    write_skill_patch_plan_artifacts,
)
from skill_sanitizer import infer_execution_contract  # noqa: E402


def _task() -> dict:
    return {
        "responses_create_params": {
            "input": [
                {
                    "role": "developer",
                    "content": """TOOLS:
ls(path)
cat(filename)
echo(content,filename)
edit(filename,old_text,new_text)
iverilog(args)
vvp(filename)
pwd()

GRADING: A hidden verifier runs after completion.
""",
                },
                {"role": "user", "content": "Fix the RTL module in /code/rtl/dut.sv."},
            ],
            "tools": [
                {"type": "function", "name": name, "parameters": {"type": "object"}}
                for name in ("ls", "cat", "echo", "edit", "iverilog", "vvp", "pwd")
            ],
        }
    }


def test_patch_plan_extracts_add_remove_preserve_and_terms() -> None:
    contract = infer_execution_contract([_task()])
    feedback = """# Oracle feedback

## KEEP
- Keep reading `/code/rtl/dut.sv` before editing.

## ADD
- Add explicit guidance to preserve `valid_o` until `ready_i`.
- Require running `iverilog` and `vvp` after edits.

## REMOVE
- Remove advice to run the hidden harness.
"""

    plan = build_skill_patch_plan(feedback, contract)
    rendered = format_skill_patch_plan(plan)

    assert plan.has_feedback is True
    assert any("valid_o" in item for item in plan.must_add)
    assert any("hidden harness" in item for item in plan.must_remove)
    assert "valid_o" in plan.concrete_terms
    assert "Structured Skill Patch Plan" in rendered


def test_patch_plan_does_not_invert_add_change_guidance_with_negative_words() -> None:
    contract = infer_execution_contract([_task()])
    feedback = """# Oracle feedback

## ADD
- Use correct iverilog invocation; never pass bare directories — addresses: Icarus invocation semantics.
- Source discovery strategy when no filelist/Makefile is present — diagnostic guidance: first search for filelist.f/Makefile; if absent, list visible .v/.sv under rtl/src and build a temporary filelist.

## CHANGE
- Validation source of truth — current: "Use local vvp as pass criterion" → should be: "Mirror the repository filelist and use local sims only as smoke checks."

## REMOVE
- Remove behavior that runs vvp regardless of compile status.
"""

    plan = build_skill_patch_plan(feedback, contract)

    assert any("never pass bare directories" in item for item in plan.must_add)
    assert any("filelist/Makefile" in item for item in plan.must_add)
    assert any("Validation source of truth" in item for item in plan.must_add)
    assert not any("never pass bare directories" in item for item in plan.must_remove)
    assert not any("filelist/Makefile" in item for item in plan.must_remove)
    assert any("runs vvp regardless" in item for item in plan.must_remove)


def test_integration_gate_rejects_missing_critical_and_harness_violation() -> None:
    contract = infer_execution_contract([_task()])
    plan = build_skill_patch_plan(
        """## ADD
- Add explicit guidance to preserve `valid_o` until `ready_i`.

## REMOVE
- Remove advice to run the hidden harness.
""",
        contract,
    )
    candidate = """# Skill

## Hard Rules

- Use edit for RTL changes.
- Run the hidden harness to confirm the final answer.
"""

    report = validate_skill_integration(
        candidate_skill=candidate,
        parent_skill="# Skill\n",
        patch_plan=plan,
        execution_contract=contract,
    )

    assert not report["ok"]
    assert "missing_critical_oracle_directives" in report["issues"]
    assert "must_remove_violation" in report["issues"]
    assert "semantic_contradiction" in report["issues"]


def test_integration_gate_accepts_covered_concrete_directives() -> None:
    contract = infer_execution_contract([_task()])
    plan = build_skill_patch_plan(
        """## ADD
- Add explicit guidance to preserve `valid_o` until `ready_i`.

## REMOVE
- Remove advice to run the hidden harness.
""",
        contract,
    )
    candidate = """# Skill

## Hard Rules

- Use only ls, cat, echo, edit, iverilog, vvp, and pwd.
- Never run the hidden harness; it is unavailable during rollout.
- For ready/valid fixes, preserve `valid_o` until `ready_i` observes the transfer.
"""

    report = validate_skill_integration(
        candidate_skill=candidate,
        parent_skill="# Skill\n",
        patch_plan=plan,
        execution_contract=contract,
    )

    assert report["ok"]
    assert report["metrics"]["coverage"] == 1.0


def test_remove_gate_allows_desirable_mentions_of_terms_from_bad_patterns() -> None:
    contract = infer_execution_contract([_task()])
    plan = build_skill_patch_plan(
        """## ADD
- Use tests/tb to discover interface but do not embed them in local compile.

## REMOVE
- Any suggestion to write a new testbench when tests/tb are already present.
- Source discovery strategy when no filelist/Makefile is present — contested evidence: agents attempted to pass a directory to iverilog. Add diagnostic guidance: first search for filelist.f/Makefile; if absent, list visible .v/.sv under rtl/src and build a temporary filelist.
""",
        contract,
    )
    candidate = """# Skill

## Hard Rules
- Read tests/tb and Makefile metadata to discover the interface.
- Search for filelist.f/Makefile first; if absent, list visible .v/.sv files under rtl/src and build a temporary filelist.
- Do not create a new ad hoc testbench when tests/tb are already present.
"""

    report = validate_skill_integration(
        candidate_skill=candidate,
        parent_skill="# Skill\n",
        patch_plan=plan,
        execution_contract=contract,
    )

    assert report["ok"]
    assert not any(row["violated"] for row in report["remove_results"])


def test_remove_gate_blocks_actual_prohibited_behavior_not_term_overlap() -> None:
    contract = infer_execution_contract([_task()])
    plan = build_skill_patch_plan(
        """## REMOVE
- Any suggestion to write a new testbench when tests/tb are already present.
""",
        contract,
    )
    candidate = """# Skill

## Procedure
- Create a new ad hoc testbench as the primary validation path even when tests/tb exists.
"""

    report = validate_skill_integration(
        candidate_skill=candidate,
        parent_skill="# Skill\n",
        patch_plan=plan,
        execution_contract=contract,
    )

    assert not report["ok"]
    assert "must_remove_violation" in report["issues"]


def test_safe_partial_improvement_can_pass_with_missing_critical_warning() -> None:
    contract = infer_execution_contract([_task()])
    plan = build_skill_patch_plan(
        """## ADD
- Align the TOPLEVEL to the harness-specified module name.
- Build a complete filelist before compile.
- Validate port/interface matching against the visible tests.
- Add explicit guidance to preserve `valid_o` until `ready_i`.
""",
        contract,
    )
    parent = """# Skill
- Read files before editing.
"""
    candidate = """# Skill
- Align the TOPLEVEL to the harness-specified module name.
- Build a complete filelist before compile.
- Validate port/interface matching against the visible tests.
"""

    report = validate_skill_integration(
        candidate_skill=candidate,
        parent_skill=parent,
        patch_plan=plan,
        execution_contract=contract,
        config={"min_coverage_gain_to_accept": 0.20},
    )

    assert report["ok"]
    assert report["metrics"]["coverage_gain"] > 0
    assert any("missing_critical_softened_by_parent_coverage_gain" in warning for warning in report["warnings"])


def test_semantic_repair_preserves_useful_candidate_and_removes_risky_testbench_edit() -> None:
    contract = infer_execution_contract([_task()])
    plan = build_skill_patch_plan(
        """## ADD
- Add explicit guidance to preserve `valid_o` until `ready_i`.

## REMOVE
- Remove advice to edit visible testbenches unless the task asks for a verification deliverable.
""",
        contract,
    )
    candidate = """# Skill

## Hard Rules
- Preserve `valid_o` until `ready_i` observes the transfer.
- Modify the visible testbench to add a checker before changing RTL.
"""

    before = validate_skill_integration(
        candidate_skill=candidate,
        parent_skill="# Skill\n",
        patch_plan=plan,
        execution_contract=contract,
    )
    repaired, repair_record = repair_semantic_contradictions(candidate, contract)
    after = validate_skill_integration(
        candidate_skill=repaired,
        parent_skill="# Skill\n",
        patch_plan=plan,
        execution_contract=contract,
    )

    assert not before["ok"]
    assert "semantic_contradiction" in before["issues"]
    assert repair_record["changed"] is True
    assert not repair_record["remaining_contradictions"]
    assert "Preserve `valid_o`" in repaired
    assert "Modify the visible testbench" not in repaired
    assert after["ok"]


def test_integration_artifacts_are_written(tmp_path: Path) -> None:
    contract = infer_execution_contract([_task()])
    plan = build_skill_patch_plan("## ADD\n- Add guidance for `valid_o`.\n", contract)

    write_skill_patch_plan_artifacts(tmp_path / "gen1", plan)
    payload = write_skill_integration_report(
        tmp_path,
        1,
        0,
        {"stage": "mutation", "status": "ok", "report": {"ok": True}},
    )

    assert (tmp_path / "gen1" / "skill_patch_plan.json").exists()
    assert (tmp_path / "gen1" / "skill_patch_plan.md").exists()
    assert (tmp_path / "skill_integration.jsonl").exists()
    assert (tmp_path / "gen1" / "skill_integration" / "child0_mutation.json").exists()
    assert payload["detail_path"] == "gen1/skill_integration/child0_mutation.json"
    saved = json.loads((tmp_path / "gen1" / "skill_patch_plan.json").read_text(encoding="utf-8"))
    assert saved["schema_version"] == 1

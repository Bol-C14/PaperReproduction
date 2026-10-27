from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "optimizer"))

from skill_sanitizer import (  # noqa: E402
    build_execution_constraints_text,
    condense_skill,
    infer_execution_contract,
    risky_added_lines,
    sanitize_feedback_for_execution_contract,
    sanitize_skill,
    skill_length_budget,
)
from run_optimizer import Individual, _breeding_pool_with_survivor, _single_lineage_parent  # noqa: E402


def _task_with_tools() -> dict:
    return {
        "responses_create_params": {
            "input": [
                {
                    "role": "developer",
                    "content": """TOOLS -- these are the ONLY tools:
  ls(path)              -- list directory
  cat(filename)         -- read file
  echo(content,filename)-- write file
  iverilog(args)        -- compile Verilog
  vvp(filename)         -- run simulation
  pwd()                 -- print directory

GRADING: A hidden test harness checks FILES after you finish.
""",
                }
            ]
        }
    }


def _task_with_schema_edit() -> dict:
    task = _task_with_tools()
    task["responses_create_params"]["tools"] = [
        {"type": "function", "name": name, "strict": True, "parameters": {"type": "object"}}
        for name in ("ls", "cat", "echo", "edit", "iverilog", "vvp", "pwd")
    ]
    return task


def _testbench_task_with_schema_edit() -> dict:
    task = _task_with_schema_edit()
    task["responses_create_params"]["input"].append({
        "role": "user",
        "content": "Create a SystemVerilog testbench and checker for the requested RTL behavior.",
    })
    return task


def test_infers_actual_tool_contract_not_static_default() -> None:
    contract = infer_execution_contract([_task_with_tools()])

    assert contract.allowed_tools == ("ls", "cat", "echo", "iverilog", "vvp", "pwd")
    assert contract.hidden_verifier is True
    assert contract.can_run_official_harness is False

    constraints = build_execution_constraints_text(contract)
    assert "edit" in constraints
    assert "must NOT tell the agent to run the official harness" in constraints


def test_tool_schema_takes_precedence_over_prompt_text() -> None:
    contract = infer_execution_contract([_task_with_schema_edit()])

    assert contract.allowed_tools == ("ls", "cat", "echo", "edit", "iverilog", "vvp", "pwd")
    assert contract.write_tool == "edit"

    constraints = build_execution_constraints_text(contract)
    assert "Prefer edit() for surgical changes" in constraints
    assert "do not recommend edit" not in constraints


def test_contract_distinguishes_testbench_deliverable_tasks() -> None:
    rtl_contract = infer_execution_contract([_task_with_schema_edit()])
    tb_contract = infer_execution_contract([_testbench_task_with_schema_edit()])

    assert rtl_contract.may_modify_testbench is False
    assert rtl_contract.task_type == "rtl_or_design"
    assert tb_contract.may_modify_testbench is True
    assert tb_contract.task_type == "testbench_or_verification"

    rtl_constraints = build_execution_constraints_text(rtl_contract)
    tb_constraints = build_execution_constraints_text(tb_contract)
    assert "read-only references" in rtl_constraints
    assert "may be created or edited" in tb_constraints


def test_sanitizer_rewrites_testbench_editing_when_not_requested() -> None:
    contract = infer_execution_contract([_task_with_schema_edit()])
    candidate = """# Skill

- Edit the provided testbench to make the assertion pass.
- Use edit(filename, old_text, new_text) for the RTL fix.
"""

    result = sanitize_skill(candidate, "# Parent\n\n- Keep edits small.\n", contract, max_chars=5000)

    assert result.ok
    assert "Edit the provided testbench" not in result.text
    assert "read-only references" in result.text
    assert "rewrote_testbench_modification_without_task_request" in result.issues


def test_sanitizer_removes_unavailable_harness_and_edit_guidance() -> None:
    contract = infer_execution_contract([_task_with_tools()])
    parent = "# Skill\n\n## Strategy\n\n- Use echo to write the target.\n"
    candidate = """# Skill

## Strategy

- Run the official harness early and repeatedly.
- Prefer edit(filename, old_text, new_text) over echo.
- Use echo(content, filename) to write the complete file.
"""

    result = sanitize_skill(candidate, parent, contract, max_chars=4000)

    assert result.ok
    assert "Run the official harness" not in result.text
    assert "edit(filename" not in result.text
    assert "## Hard Rules" in result.text
    assert "self-check only with allowed simulator tools" in result.text
    assert "removed_impossible_harness_run" in result.issues
    assert "removed_unavailable_edit_tool" in result.issues


def test_sanitizer_rejects_excessive_growth() -> None:
    contract = infer_execution_contract([_task_with_tools()])
    parent = "# Skill\n\n" + ("- concrete rule\n" * 20)
    candidate = "# Skill\n\n" + "".join(
        f"- extra process ceremony that is not integrated {i}\n" for i in range(400)
    )

    result = sanitize_skill(
        candidate,
        parent,
        contract,
        max_chars=12000,
        sanitizer_cfg={
            "enabled": True,
            "max_growth_ratio": 1.1,
            "max_growth_chars": 200,
            "min_budget_chars": 500,
            "absolute_max_chars": 600,
            "condense": {"enabled": False},
        },
    )

    assert not result.ok
    assert "excessive_length_growth" in result.issues
    assert "exceeds_absolute_max_chars" in result.issues
    assert result.metrics["absolute_max_chars"] < result.metrics["sanitized_chars"]


def test_tiny_parent_gets_usable_budget_floor() -> None:
    parent = "# Skill\n\n- Write the required files.\n"

    budget = skill_length_budget(
        parent,
        max_chars=12000,
        sanitizer_cfg={"enabled": True, "min_budget_chars": 3500},
    )

    assert budget == 3500


def test_length_over_soft_budget_is_warning_not_rejection() -> None:
    contract = infer_execution_contract([_task_with_schema_edit()])
    parent = "# Skill\n\n" + ("- concrete rule\n" * 20)
    candidate = "# Skill\n\n" + "".join(
        f"- Read the visible spec and testbench, then edit the exact RTL target {i}.\n" for i in range(60)
    )

    result = sanitize_skill(
        candidate,
        parent,
        contract,
        max_chars=12000,
        sanitizer_cfg={
            "enabled": True,
            "min_budget_chars": 1200,
            "absolute_max_chars": 8000,
            "condense": {"enabled": False},
        },
    )

    assert result.ok
    assert "excessive_length_growth" in result.issues
    assert "exceeds_absolute_max_chars" not in result.issues


def test_command_scanner_ignores_english_and_negative_tool_mentions() -> None:
    contract = infer_execution_contract([_task_with_schema_edit()])
    candidate = """# Skill

- Find DUT top, testbench, and dependencies from visible files.
- Confirm diff by catting the edited file after edit().
- No bash/grep/make/pytest/python.
- Use edit(filename, old_text, new_text) for surgical changes.
"""

    result = sanitize_skill(candidate, "# Parent\n\n- Keep edits small.\n", contract, max_chars=5000)

    assert result.ok
    assert not any(issue.startswith("removed_unavailable_command:find") for issue in result.issues)
    assert not any(issue.startswith("removed_unavailable_command:diff") for issue in result.issues)
    assert "removed_impossible_pytest_or_test_runner" not in result.issues


def test_feedback_sanitizer_rewrites_oracle_harness_and_unavailable_tools() -> None:
    task = _task_with_schema_edit()
    task["responses_create_params"]["tools"].append(
        {"type": "function", "name": "xcelium", "strict": True, "parameters": {"type": "object"}}
    )
    contract = infer_execution_contract([task])
    feedback = """# Oracle feedback

## ADD
- Run the repository harness before stopping; use pytest/Makefiles/cmds.f as the source of truth.
- Invoke xcelium/xrun for the final validation.
- Preserve exact target path guidance: use dsp.v, not rtl/dsp.v.
- Do not run the official hidden harness.
"""

    result = sanitize_feedback_for_execution_contract(
        feedback,
        contract,
        source="test_oracle_feedback",
    )

    assert result.changed
    assert "Run the repository harness" not in result.text
    assert "use pytest/Makefiles/cmds.f" not in result.text
    assert "Invoke xcelium/xrun" not in result.text
    assert "Read visible specs" in result.text
    assert "unavailable commands such as pytest, make, or docker" in result.text
    assert "Use xcelium only after confirming" in result.text
    assert "use dsp.v, not rtl/dsp.v" in result.text
    assert "Do not run the official hidden harness" in result.text
    assert "rewrite_unavailable_harness_run" in result.issues
    assert "make_xcelium_guidance_conditional" in result.issues


def test_skill_sanitizer_rewrites_generic_harness_execution_line() -> None:
    contract = infer_execution_contract([_task_with_schema_edit()])
    parent = "# Skill\n\n- Read visible specs and self-check with iverilog/vvp.\n"
    candidate = """# Skill

## Procedure

- Parse visible filelists and top-level testbench names before editing.
- Invoke: iverilog -g2012 -s <top> -o sim.vvp <expanded_sources>. Run with vvp sim.vvp and use the harness TB top if provided.
"""

    result = sanitize_skill(candidate, parent, contract, max_chars=6000)

    assert result.ok
    assert "Run with vvp sim.vvp and use the harness TB top" not in result.text
    assert "harness metadata if present" in result.text
    assert "rewrote_harness_execution_to_visible_metadata" in result.issues
    assert "remaining_impossible_harness_run" not in result.issues


def test_command_scanner_still_removes_command_like_unavailable_tools() -> None:
    contract = infer_execution_contract([_task_with_schema_edit()])
    candidate = """# Skill

- Use `find /code -name '*.sv'` to discover sources.
- Run grep reset across the repository.
- Use edit(filename, old_text, new_text) for surgical changes.
"""

    result = sanitize_skill(candidate, "# Parent\n\n- Keep edits small.\n", contract, max_chars=5000)

    assert result.ok
    assert "removed_unavailable_command:find" in result.issues
    assert "removed_unavailable_command:grep" in result.issues


def test_condenser_rewrites_verbose_skill_into_canonical_schema() -> None:
    contract = infer_execution_contract([_task_with_schema_edit()])
    verbose = """# RTL Agent Skill - cid003

## Strategy

- Use only allowed rollout tools.
- Use only allowed rollout tools.
- Consider being careful about the implementation.
- Read the visible spec before writing RTL.
- Read the visible testbench before writing RTL.
- Match the exact module name, port names, widths, reset polarity, and parameters.
- Prefer edit for surgical changes and echo for brand-new files.
- Run iverilog on the target RTL and visible Verilog/SystemVerilog testbench.
- Run vvp after a successful compile.
- If compile fails, fix the first compiler error before touching later cascaded errors.
- If simulation fails, read the mismatch message and map it back to the named signal.
- Never run the hidden harness.
- Never compile board/vendor/example IP unless the prompt explicitly requires it.

```verilog
module oversized_example;
endmodule
```
""" + "\n".join(f"- repeated generic workflow note {i}" for i in range(80))

    condensed, metrics = condense_skill(
        verbose,
        contract,
        sanitizer_cfg={"condense": {"enabled": True, "over_chars": 500, "target_chars": 1800}},
        budget_chars=1800,
    )

    assert metrics["changed"] is True
    assert len(condensed) < len(verbose)
    assert "## Hard Rules" in condensed
    assert "## Procedure" in condensed
    assert "## Do Not" in condensed
    assert "oversized_example" not in condensed
    assert condensed.count("Use only allowed rollout tools") <= 1


def test_risky_added_lines_flags_harness_dependency_overcorrection() -> None:
    contract = infer_execution_contract([_task_with_tools()])
    previous = "# Skill\n\n- Write the target module and run iverilog/vvp.\n"
    current = """# Skill

- Write the target module and run iverilog/vvp.
- Run the official harness early to discover behavior.
- Create files.f and manage dependency chains before implementation.
"""

    risky = risky_added_lines(previous, current, contract)

    assert any("official harness" in line for line in risky)
    assert any("dependency chains" in line for line in risky)


def test_survival_pool_keeps_best_ever_when_current_generation_regresses() -> None:
    current = Individual("# weaker", generation=2, parent_info="child")
    current.fitness = 0.2
    best = Individual("# best", generation=1, parent_info="original")
    best.fitness = 0.8

    pool = _breeding_pool_with_survivor([current], best, enabled=True)

    assert len(pool) == 2
    assert max(ind.fitness for ind in pool) == 0.8


def test_single_lineage_parent_keeps_current_when_within_margin() -> None:
    current = Individual("# current", generation=2, parent_info="child")
    current.fitness = 0.76
    best = Individual("# best", generation=1, parent_info="best")
    best.fitness = 0.80

    chosen, reason = _single_lineage_parent(current, best, margin=0.05)
    assert chosen is current
    assert reason == "current_within_best_ever_margin"

    chosen, reason = _single_lineage_parent(current, best, margin=0.01)
    assert chosen is best
    assert reason == "best_ever_after_regression"

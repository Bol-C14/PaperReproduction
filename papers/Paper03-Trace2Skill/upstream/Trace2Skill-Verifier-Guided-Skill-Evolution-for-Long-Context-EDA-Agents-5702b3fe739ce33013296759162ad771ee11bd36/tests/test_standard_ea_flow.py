from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "optimizer"))

from run_optimizer import (  # noqa: E402
    Individual,
    _apply_combined_selection_fitness,
    _carry_prompt_for_reevaluation,
    defer_child_semantic_selection,
    make_standard_ea_survivor_record,
)


def test_standard_ea_survivor_record_uses_evaluated_population_member() -> None:
    survivor = Individual("# Skill\n- Keep this evaluated survivor.\n", generation=2, parent_info="child_gen2_1")
    survivor.fitness = 0.73
    survivor.fitness_result = {
        "selection_fitness": 0.73,
        "pass_at_1": 0.2,
        "progress_fitness": 0.61,
    }

    record = make_standard_ea_survivor_record(generation=2, survivor=survivor)

    assert record["decision"] == "evaluated_population_survivor"
    assert record["selection_metric"] == "combined_selection_fitness"
    assert record["selection_fitness"] == 0.73
    assert record["pass_at_1"] == 0.2
    assert "not eligible" in record["note"]


def test_standard_ea_defers_child_semantic_selection_until_rollout(tmp_path: Path) -> None:
    parent = "# Skill\n- Parent rule.\n"
    child = "# Skill\n- Parent rule.\n- New oracle-grounded lesson.\n"
    process_record = {
        "skill_integration": {
            "ok": True,
            "issues": [],
            "metrics": {
                "coverage": 0.9,
                "coverage_gain": 0.2,
            },
        }
    }

    decision = defer_child_semantic_selection(
        parent_prompt=parent,
        candidate_prompt=child,
        process_record=process_record,
        output_dir=tmp_path,
        gen_dir=tmp_path / "gen1",
        generation=1,
        child_slot=1,
        stage="mutation",
        parent_info="ea_survivor_from_gen1",
        skill_patch_plan={"has_feedback": True},
    )

    assert decision["decision"] == "deferred_to_next_generation_rollout"
    assert decision["selected_parent_or_child"] == "child"
    assert decision["rollout_fitness_used_for_selection"] is False
    assert decision["skill_integration_metrics"]["coverage_gain"] == 0.2

    run_records = [
        json.loads(line)
        for line in (tmp_path / "semantic_skill_selection.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    gen_records = [
        json.loads(line)
        for line in (tmp_path / "gen1" / "semantic_skill_selection.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert run_records == gen_records == [decision]


def test_standard_ea_carried_survivor_is_reevaluated_not_pre_scored() -> None:
    survivor = Individual("# Skill\n- Survivor prompt.\n", generation=1, parent_info="elite")
    survivor.fitness = 0.88
    survivor.fitness_result = {"selection_fitness": 0.88, "pass_at_1": 0.4}

    carried = _carry_prompt_for_reevaluation(survivor, generation=2, parent_info="ea_survivor_from_gen1")

    assert carried.prompt == survivor.prompt
    assert carried.fitness == 0.0
    assert carried.fitness_result == {}
    assert carried.parent_fitness == 0.88
    assert carried.parent_fitness_result == survivor.fitness_result
    assert carried.child_origin == "ea_survivor"


def test_combined_selection_keeps_parent_when_child_semantic_quality_regresses(tmp_path: Path) -> None:
    parent = Individual("# Skill\n- Durable parent lesson.\n", generation=2, parent_info="ea_survivor")
    parent.fitness_result = {
        "selection_fitness": 0.01,
        "pass_at_1": 0.0,
        "progress_fitness": 0.20,
        "selection_epsilon": 0.10,
        "rollout_variance": {"mean": 0.20, "lower_confidence_bound_95": 0.18, "variance_quality": 0.90},
    }
    parent.semantic_retention = {"skill_quality_score": 0.70}

    child = Individual("# Skill\n- Lucky but semantically worse.\n", generation=2, parent_info="child")
    child.fitness_result = {
        "selection_fitness": 0.09,
        "pass_at_1": 0.0,
        "progress_fitness": 0.90,
        "selection_epsilon": 0.10,
        "rollout_variance": {"mean": 0.90, "lower_confidence_bound_95": 0.88, "variance_quality": 0.80},
    }
    child.semantic_retention = {
        "skill_quality_score": 0.40,
        "skill_integration_ok": True,
        "skill_integration_metrics": {"coverage": 0.40, "parent_coverage": 0.70},
    }

    _apply_combined_selection_fitness(
        population=[parent, child],
        generation=2,
        gen_dir=tmp_path / "gen2",
        cfg={"enabled": True, "enforce_semantic_floor": True, "enforce_validity": True},
    )

    assert parent.fitness > child.fitness
    assert child.fitness_result["selection_fitness_breakdown"]["semantic_floor_violation"] is True
    assert child.fitness_result["selection_fitness_breakdown"]["selection_blocked"] is True
    assert child.fitness == -1.0


def test_combined_selection_blocks_invalid_child_on_equal_pass_rate(tmp_path: Path) -> None:
    parent = Individual("# Skill\n- Valid parent lesson.\n", generation=2, parent_info="ea_survivor")
    parent.fitness_result = {
        "selection_fitness": 0.01,
        "pass_at_1": 0.0,
        "progress_fitness": 0.10,
        "selection_epsilon": 0.10,
        "rollout_variance": {"mean": 0.10, "lower_confidence_bound_95": 0.10, "variance_quality": 1.0},
    }
    parent.semantic_retention = {"skill_quality_score": 0.60}

    child = Individual("# Skill\n- Run hidden harness.\n", generation=2, parent_info="child")
    child.fitness_result = {
        "selection_fitness": 0.09,
        "pass_at_1": 0.0,
        "progress_fitness": 0.90,
        "selection_epsilon": 0.10,
        "rollout_variance": {"mean": 0.90, "lower_confidence_bound_95": 0.90, "variance_quality": 1.0},
    }
    child.semantic_retention = {
        "skill_quality_score": 0.70,
        "skill_integration_ok": True,
        "skill_integration_metrics": {
            "coverage": 0.95,
            "parent_coverage": 0.60,
            "remove_violation_count": 1,
        },
    }

    _apply_combined_selection_fitness(
        population=[parent, child],
        generation=2,
        gen_dir=tmp_path / "gen2",
        cfg={"enabled": True, "enforce_semantic_floor": True, "enforce_validity": True},
    )

    assert parent.fitness > child.fitness
    validity = child.fitness_result["selection_fitness_breakdown"]["validity"]
    assert validity["valid"] is False
    assert "remove_violation_count:1" in validity["invalid_reasons"]
    assert child.fitness_result["selection_fitness_breakdown"]["selection_blocked"] is True
    assert child.fitness == -1.0

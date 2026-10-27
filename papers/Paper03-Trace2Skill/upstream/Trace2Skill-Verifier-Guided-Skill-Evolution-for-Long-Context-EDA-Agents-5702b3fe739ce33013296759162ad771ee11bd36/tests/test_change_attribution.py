from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "optimizer"))

from change_attribution import (  # noqa: E402
    evaluate_change_manifest,
    format_change_evaluation_for_mutation,
    write_change_attribution_artifacts,
)


def _ind(
    *,
    idx: int,
    parent_rate: float,
    current_rate: float,
    parent_selection: float = 0.2,
    current_selection: float = 0.4,
    parent_progress: float = 0.2,
    current_progress: float = 0.4,
    task: str = "cvdp_agentic_heavy_spi_0001",
) -> SimpleNamespace:
    return SimpleNamespace(
        prompt="# child\n" + "Use visible files.\n" * 20,
        parent_prompt="# parent\n" + "Use tools.\n" * 20,
        parent_sha256="parent-sha",
        parent_info="child_gen2_0",
        child_origin="parent+mutation",
        fitness=current_selection,
        parent_fitness_result={
            "selection_fitness": parent_selection,
            "pass_at_1": parent_rate,
            "progress_fitness": parent_progress,
            "per_task": {
                task: {
                    "pass_at_1": parent_rate,
                    "attempts": 5,
                    "passes": int(parent_rate * 5),
                }
            },
        },
        fitness_result={
            "individual_index": idx,
            "selection_fitness": current_selection,
            "pass_at_1": current_rate,
            "progress_fitness": current_progress,
            "per_task": {
                task: {
                    "pass_at_1": current_rate,
                    "attempts": 5,
                    "passes": int(current_rate * 5),
                }
            },
        },
    )


def _task_manifest() -> list[dict]:
    return [{
        "index": 0,
        "task_id": "cvdp_agentic_heavy_spi_0001",
        "short_task_id": "spi_0001",
        "cid": "cid014",
        "categories": ["cid014"],
        "difficulty": "hard",
    }]


def _write_prior_patch_plan(output_dir: Path) -> None:
    gen1 = output_dir / "gen1"
    gen1.mkdir()
    (gen1 / "oracle_feedback.md").write_text("oracle says fix compile flow", encoding="utf-8")
    (gen1 / "mutation_handoff.md").write_text("handoff", encoding="utf-8")
    (gen1 / "skill_patch_plan.json").write_text(json.dumps({
        "schema_version": 1,
        "has_feedback": True,
        "must_add": ["Require filelist-aware compile before simulation."],
        "must_preserve": ["Keep visible file inspection before editing."],
        "must_remove": ["Avoid compiling a single DUT file in isolation."],
        "concrete_terms": ["filelist.f", "iverilog"],
        "source_chars": 1234,
    }), encoding="utf-8")


def test_change_attribution_marks_predicted_fix_effective(tmp_path) -> None:
    _write_prior_patch_plan(tmp_path)

    evaluation = write_change_attribution_artifacts(
        output_dir=tmp_path,
        gen_dir=tmp_path / "gen2",
        generation=2,
        population=[_ind(idx=0, parent_rate=0.0, current_rate=0.4)],
        task_manifest=_task_manifest(),
        config={"pass_rate_improvement_threshold": 0.001},
    )

    assert (tmp_path / "gen2" / "change_manifest.json").exists()
    assert (tmp_path / "gen2" / "change_manifests" / "ind0.json").exists()
    assert (tmp_path / "gen2" / "change_evaluation.md").exists()
    row = evaluation["evaluations"][0]
    assert row["verdict"] == "EFFECTIVE"
    assert row["actually_fixed"][0]["task"] == "spi_0001"
    assert row["source_artifacts"]["skill_patch_plan"] == "gen1/skill_patch_plan.json"


def test_change_attribution_marks_regression_harmful(tmp_path) -> None:
    _write_prior_patch_plan(tmp_path)

    evaluation = write_change_attribution_artifacts(
        output_dir=tmp_path,
        gen_dir=tmp_path / "gen2",
        generation=2,
        population=[_ind(idx=1, parent_rate=1.0, current_rate=0.0, parent_selection=0.8, current_selection=0.2)],
        task_manifest=_task_manifest(),
        config={"selection_threshold": 0.03},
    )

    row = evaluation["evaluations"][0]
    assert row["verdict"] == "HARMFUL"
    assert row["regressions"][0]["task"] == "spi_0001"
    handoff = format_change_evaluation_for_mutation(evaluation)
    assert "HARMFUL" in handoff
    assert "Regressed tasks: spi_0001" in handoff


def test_change_attribution_does_not_overclaim_seed_baseline(tmp_path) -> None:
    seed = SimpleNamespace(
        prompt="# seed\n" + "Use tools.\n" * 20,
        parent_prompt=None,
        parent_info="original",
        child_origin="",
        fitness=1.0,
        fitness_result={
            "individual_index": 0,
            "selection_fitness": 1.0,
            "pass_at_1": 1.0,
            "progress_fitness": 1.0,
            "per_task": {"cvdp_agentic_heavy_spi_0001": {"pass_at_1": 1.0}},
        },
    )

    manifest_eval = write_change_attribution_artifacts(
        output_dir=tmp_path,
        gen_dir=tmp_path / "gen1",
        generation=1,
        population=[seed],
        task_manifest=_task_manifest(),
        config={},
    )

    assert manifest_eval["evaluations"][0]["verdict"] == "NO_BASELINE"
    manifest = json.loads((tmp_path / "gen1" / "change_manifest.json").read_text(encoding="utf-8"))
    assert manifest["changes"][0]["change_type"] == "seed_baseline"


def test_evaluate_change_manifest_labels_unchanged_skills() -> None:
    manifest = {
        "generation": 3,
        "source_generation": 2,
        "changes": [{
            "id": "gen3_ind0",
            "same_as_parent": True,
            "change_type": "unchanged",
            "parent_metrics": {"selection_fitness": 0.2, "pass_at_1": 0.0, "progress_fitness": 0.1, "per_task": {}},
            "current_metrics": {"selection_fitness": 0.2, "pass_at_1": 0.0, "progress_fitness": 0.1, "per_task": {}},
        }],
    }

    evaluation = evaluate_change_manifest(manifest)

    assert evaluation["evaluations"][0]["verdict"] == "UNCHANGED"
    assert evaluation["summary"]["verdict_counts"] == {"UNCHANGED": 1}

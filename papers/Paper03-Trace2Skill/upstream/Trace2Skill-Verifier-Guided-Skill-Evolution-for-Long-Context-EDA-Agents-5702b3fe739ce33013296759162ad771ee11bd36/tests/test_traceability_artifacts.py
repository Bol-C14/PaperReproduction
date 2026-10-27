from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "optimizer"))

from run_optimizer import (  # noqa: E402
    Individual,
    _checkpoint_needs_breeding,
    _metric_summary,
    _should_challenge_child,
    _wilson_ci_95,
    build_rollout_diagnostic,
    build_task_manifest,
    load_checkpoint,
    run_preflight_checks,
    save_checkpoint,
    write_initial_skill_artifacts,
    write_generation_traceability_artifacts,
    write_oracle_feedback_index,
)


def _call(call_id: str, name: str, **arguments: object) -> dict:
    return {
        "type": "function_call",
        "call_id": call_id,
        "name": name,
        "arguments": json.dumps(arguments),
    }


def _output(call_id: str, text: str) -> dict:
    return {
        "type": "function_call_output",
        "call_id": call_id,
        "output": json.dumps({"output": text}),
    }


def test_build_rollout_diagnostic_classifies_compile_failure() -> None:
    rollout = {
        "task_id": "cvdp_agentic_heavy_spi_0001",
        "category": "cid014",
        "reward": 0.0,
        "docker_exit_code": 1,
        "response": {
            "output": [
                _call("c1", "cat", filename="SKILL.md"),
                _output("c1", "This skill says FAIL in examples, but this should not be treated as an error."),
                _call("c2", "edit", filename="hardware/spi.sv", old_text="endmodule", new_text="// assertions\nendmodule"),
                _call("c3", "iverilog", args="-g2012 hardware/spi.sv"),
                _output("c3", "hardware/spi.sv:10: syntax error"),
            ],
        },
    }

    diagnostic = build_rollout_diagnostic(
        rollout,
        generation=2,
        individual_index=1,
        rollout_index=3,
        cid_lookup={},
        parent_info="mutated",
        repeat_index=2,
    )

    assert diagnostic["cid"] == "cid014"
    assert diagnostic["rollout_id"] == "ind1_r3"
    assert diagnostic["repeat_index"] == 2
    assert diagnostic["task_repeat_id"] == "spi_0001#repeat2"
    assert diagnostic["phase_reached"] == "P3-compiled"
    assert diagnostic["mode"] == "fail:compile_error"
    assert diagnostic["files_written"] == ["hardware/spi.sv"]
    assert diagnostic["error_signatures"] == ["hardware/spi.sv:10: syntax error"]


def test_initial_skill_artifacts_snapshot_seed_and_cid_mapping(tmp_path) -> None:
    tasks = [
        {
            "verifier_metadata": {
                "task_id": "cvdp_agentic_heavy_spi_0001",
                "categories": ["cid014", "hard"],
                "difficulty": "hard",
                "context_files": {"large.v": "omitted from manifest"},
            }
        }
    ]
    seed = "# skill\nDo the thing.\n"
    seed_path = tmp_path / "skills" / "cid014_sva.md"
    tasks_path = tmp_path / "data" / "cid014_sva" / "train.jsonl"
    manifest = build_task_manifest(tasks, tasks_path)

    write_initial_skill_artifacts(tmp_path, seed_path, seed, tasks_path, manifest)

    assert (tmp_path / "initial_skill.md").read_text(encoding="utf-8") == seed
    meta = json.loads((tmp_path / "initial_skill_meta.json").read_text(encoding="utf-8"))
    assert meta["skill_scope"] == "per_task"
    assert meta["cids"] == ["cid014"]
    assert meta["scope"]["lineage"] == "common CID seed skill -> task-specific evolved skill"
    assert meta["tasks"][0] == {
        "index": 0,
        "task_id": "cvdp_agentic_heavy_spi_0001",
        "short_task_id": "spi_0001",
        "cid": "cid014",
        "categories": ["cid014", "hard"],
        "difficulty": "hard",
    }


def test_oracle_feedback_index_groups_layer1_docs_by_cid(tmp_path) -> None:
    gen_dir = tmp_path / "gen1"
    (gen_dir / "task_insights").mkdir(parents=True)
    (gen_dir / "cross_task").mkdir()
    (gen_dir / "task_insights" / "spi_0001_fail.md").write_text("fail insight", encoding="utf-8")
    (gen_dir / "cross_task" / "fail_synthesis.md").write_text("cross insight", encoding="utf-8")
    handoff = gen_dir / "oracle_feedback.md"
    handoff.write_text("oracle handoff", encoding="utf-8")
    manifest = [
        {
            "index": 0,
            "task_id": "cvdp_agentic_heavy_spi_0001",
            "short_task_id": "spi_0001",
            "cid": "cid014",
            "categories": ["cid014", "hard"],
            "difficulty": "hard",
        }
    ]

    write_oracle_feedback_index(
        gen_dir=gen_dir,
        output_dir=tmp_path,
        generation=1,
        task_manifest=manifest,
        status="completed",
        oracle_feedback_path=handoff,
    )

    by_cid = json.loads((gen_dir / "oracle_feedback_by_cid.json").read_text(encoding="utf-8"))
    assert by_cid["per_cid"]["cid014"]["layer1_task_insights"] == [
        "gen1/task_insights/spi_0001_fail.md"
    ]
    index = json.loads((gen_dir / "oracle_feedback_index.json").read_text(encoding="utf-8"))
    assert index["per_cid_index"] == "gen1/oracle_feedback_by_cid.json"


def test_post_fitness_checkpoint_resumes_breeding_even_when_all_zero(tmp_path) -> None:
    ind = Individual("# skill\n- use tools\n", generation=1, parent_info="original")
    ind.fitness = 0.0
    ind.fitness_result = {"pass_at_1": 0.0, "num_rollouts": 15, "per_task": {"t": {"pass_at_1": 0.0}}}
    best = Individual("# skill\n- use tools\n", generation=1, parent_info="original")
    best.fitness = 0.0
    best.fitness_result = dict(ind.fitness_result)

    save_checkpoint(
        tmp_path,
        last_completed_gen=1,
        population=[ind],
        best_ever=best,
        history=[{"generation": 1, "best_fitness": 0.0}],
        checkpoint_stage="post_fitness",
    )

    ckpt = load_checkpoint(tmp_path)
    assert ckpt is not None
    resumed_population = [Individual.from_checkpoint_dict(d) for d in ckpt["population"]]
    assert ckpt["needs_breeding"] is True
    assert _checkpoint_needs_breeding(ckpt, resumed_population) is True

    legacy_ckpt = dict(ckpt)
    legacy_ckpt.pop("needs_breeding")
    legacy_ckpt.pop("checkpoint_stage")
    assert _checkpoint_needs_breeding(legacy_ckpt, resumed_population) is True


def test_preflight_rejects_hidden_harness_prompt_and_missing_edit(tmp_path) -> None:
    task = {
        "responses_create_params": {
            "input": [
                {"role": "developer", "content": "Run /code/harness/test_runner.py after editing."},
                {"role": "user", "content": "Fix /code/rtl/top.v"},
            ],
            "tools": [
                {"type": "function", "name": name, "strict": True, "parameters": {"type": "object"}}
                for name in ["ls", "cat", "echo", "iverilog", "vvp", "pwd"]
            ],
        },
        "verifier_metadata": {
            "task_id": "cvdp_agentic_heavy_spi_0001",
            "categories": ["cid014", "hard"],
            "difficulty": "hard",
            "context_files": {"SKILL.md": "# skill\n" + "Use tools.\n" * 20, "rtl/top.v": "module top; endmodule"},
            "harness_files": {"docker-compose.yml": "services: {verif: {image: test}}"},
        },
    }

    with pytest.raises(RuntimeError):
        run_preflight_checks(
            output_dir=tmp_path,
            seed_skill_path=tmp_path / "seed.md",
            seed_skill="# seed\n" + "Read visible files.\n" * 20,
            tasks_path=tmp_path / "tasks.jsonl",
            tasks_data=[task],
            task_manifest=build_task_manifest([task], tmp_path / "tasks.jsonl"),
            config={},
        )

    report = json.loads((tmp_path / "preflight_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "failed"
    assert any("hidden harness" in err or "test_runner" in err for err in report["errors"])
    assert any("missing required rollout tools" in err for err in report["errors"])


def test_generation_metrics_report_confidence_intervals(tmp_path) -> None:
    ind = Individual("# skill\n- edit files\n", generation=1, parent_info="child")
    ind.fitness = 0.55
    ind.fitness_result = {
        "pass_at_1": 0.4,
        "progress_fitness": 0.5,
        "selection_fitness": 0.55,
        "per_task": {
            "cvdp_agentic_heavy_spi_0001": {
                "pass_at_1": 0.4,
                "pass_at_k": 1.0,
                "attempts": 5,
                "passes": 2,
            }
        },
        "num_rollouts": 5,
    }
    manifest = [{
        "index": 0,
        "task_id": "cvdp_agentic_heavy_spi_0001",
        "short_task_id": "spi_0001",
        "cid": "cid014",
        "categories": ["cid014", "hard"],
        "difficulty": "hard",
    }]

    write_generation_traceability_artifacts(
        gen_dir=tmp_path / "gen1",
        output_dir=tmp_path,
        generation=1,
        population=[ind],
        task_manifest=manifest,
        skill_scope="per_cid",
    )

    metrics = json.loads((tmp_path / "gen1" / "generation_metrics.json").read_text(encoding="utf-8"))
    assert metrics["confidence_intervals"]["rollout_pass_rate_ci_95"]["attempts"] == 5
    assert metrics["per_task"]["spi_0001"]["rollout_pass_rate_ci_95"]["passes"] == 2
    assert _metric_summary([0.2, 0.8])["mean_ci_95"]["n"] == 2
    assert _wilson_ci_95(2, 5)["method"] == "wilson_95"


def test_child_challenger_triggers_only_on_regression() -> None:
    parent_result = {"pass_at_1": 0.4, "selection_fitness": 0.45}
    child = Individual("# child skill\n" + "Use tools.\n" * 20, generation=2, parent_info="child")
    child.fitness = 0.2
    child.fitness_result = {"pass_at_1": 0.0, "selection_fitness": 0.2}
    child.parent_prompt = "# parent skill\n" + "Use tools.\n" * 20
    child.parent_fitness = 0.45
    child.parent_fitness_result = parent_result
    child.parent_sha256 = "parent"

    should, reason = _should_challenge_child(child, {"enabled": True, "selection_drop": 0.02, "pass_drop": 0.001})

    assert should
    assert "regression" in reason

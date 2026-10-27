from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "optimizer"))

from lesson_bank import (  # noqa: E402
    distill_final_skill,
    format_lesson_bank_for_mutation,
    update_lesson_bank,
)


def test_lesson_bank_preserves_patch_plan_and_path_rules(tmp_path: Path) -> None:
    gen_dir = tmp_path / "gen1"
    gen_dir.mkdir()
    metrics = {
        "generation": 1,
        "cids": ["cid005"],
        "selection_fitness": {"mean": 0.1},
        "pass_rate": {"mean": 0.0},
        "progress_fitness": {"mean": 0.6},
        "path_grounding": {
            "issue_count": 2,
            "by_code": {"wrong_target_path": 1, "validation_on_wrong_path": 1},
            "examples": [
                {
                    "cid": "cid005",
                    "expected": "rtl/i2c_simple_interface.v",
                    "observed": ["src/i2c_simple_interface.v"],
                }
            ],
        },
    }
    (gen_dir / "generation_metrics.json").write_text(json.dumps(metrics), encoding="utf-8")

    bank = update_lesson_bank(
        output_dir=tmp_path,
        gen_dir=gen_dir,
        generation=1,
        task_manifest=[{"cid": "cid005", "short_task_id": "i2c_0001"}],
        generation_metrics_path=gen_dir / "generation_metrics.json",
        oracle_feedback_text="## Open questions\n- Which exact target file should be edited?",
        skill_patch_plan={
            "must_add": ["Require a target-path audit before editing."],
            "must_preserve": ["Keep using edit for small RTL changes."],
            "must_remove": ["Remove advice to run the hidden harness."],
        },
        change_eval=None,
    )

    rendered = format_lesson_bank_for_mutation(bank)

    assert "Require a target-path audit" in rendered
    assert "hidden harness" in rendered
    assert "rtl/i2c_simple_interface.v" in rendered
    assert (tmp_path / "lesson_bank.json").exists()
    assert (gen_dir / "lesson_bank.md").exists()


def test_final_distillation_keeps_best_skill_and_durable_lessons() -> None:
    bank = {
        "durable_lessons": [
            {"text": "Lock edits to the exact requested RTL target path.", "count": 2, "last_generation": 3}
        ],
        "preserved_success_patterns": [],
        "forbidden_behaviors": [],
        "protected_path_rules": [],
        "recurring_failure_modes": [],
        "open_questions": [],
    }
    skill = "# Skill\n\n## Hard Rules\n\n- Use edit for RTL changes.\n"

    distilled = distill_final_skill(best_skill=skill, lesson_bank=bank, max_chars=5000)

    assert distilled.startswith("# Distilled Optimized Skill")
    assert "Lock edits to the exact requested RTL target path" in distilled
    assert "Use edit for RTL changes" in distilled


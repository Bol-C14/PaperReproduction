from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from report_mlcad_skill_behavior_scores import skill_quality_after_generation  # noqa: E402


def test_standard_ea_reporting_uses_evaluated_survivor_artifact(tmp_path: Path) -> None:
    gen_dir = tmp_path / "gen1"
    gen_dir.mkdir()
    (gen_dir / "ea_survivor_decision.json").write_text(
        json.dumps(
            {
                "generation": 1,
                "decision": "evaluated_population_survivor",
                "selection_metric": "selection_fitness",
                "survivor_parent_info": "child_gen1_1",
            }
        ),
        encoding="utf-8",
    )
    (gen_dir / "skill_iterations_index.json").write_text(
        json.dumps(
            {
                "individuals": [
                    {
                        "rank": 0,
                        "individual_index": 1,
                        "semantic_selection": {
                            "generation": 0,
                            "child_slot": 1,
                            "decision": "deferred_to_next_generation_rollout",
                            "candidate_score": {"score": 0.42},
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (gen_dir / "semantic_skill_selection.jsonl").write_text(
        json.dumps({"decision": "deferred_to_next_generation_rollout"}) + "\n",
        encoding="utf-8",
    )

    row = skill_quality_after_generation(gen_dir, previous_cumulative=None)

    assert row["available"] is True
    assert row["decision"] == "standard_ea_evaluated_survivor"
    assert row["selection_artifact"] == "ea_survivor_decision.json"
    assert row["rollout_fitness_used_for_selection"] is True
    assert row["selected_skill_quality"] == 0.42
    assert row["deferred_children"] == 1


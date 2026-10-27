#!/usr/bin/env python3
"""Emit per-repeat Trace2Skill run metrics as public-schema CSV."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


FIELDS = [
    "task", "generation", "individual", "repeat", "reward", "pass_rate",
    "SelectQ", "SkillQ", "AgentProgressQ", "AgentVarianceQ", "AgentAdherenceQ",
]


def rows(run_root: Path):
    for meta_path in sorted(run_root.glob("**/gen*/individuals/ind*_meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        generation = int(meta["generation"])
        individual = int(meta["individual_index"])
        task = str(meta.get("task_alias") or next(iter(meta.get("per_task", {"unknown": {}}))))
        common = {
            "task": task,
            "generation": generation,
            "individual": individual,
            "pass_rate": meta.get("pass_at_1"),
            "SelectQ": meta.get("selection_fitness"),
            "SkillQ": meta.get("skill_quality"),
            "AgentProgressQ": meta.get("agent_behavior_quality"),
            "AgentVarianceQ": meta.get("rollout_variance_quality"),
            "AgentAdherenceQ": meta.get("skill_adherence_quality"),
        }
        gen_dir = meta_path.parents[1]
        rollout_path = gen_dir / "rollouts" / f"ind{individual}" / f"rollouts_gen{generation}_ind{individual}.jsonl"
        emitted = False
        if rollout_path.is_file():
            with rollout_path.open(encoding="utf-8") as stream:
                for ordinal, line in enumerate(stream):
                    if not line.strip():
                        continue
                    rollout = json.loads(line)
                    reward = rollout.get("reward")
                    yield {
                        **common,
                        "repeat": rollout.get("_ng_rollout_index", ordinal),
                        "reward": reward,
                    }
                    emitted = True
        if not emitted:
            yield {**common, "repeat": "all", "reward": ""}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", type=Path)
    args = parser.parse_args()
    writer = csv.DictWriter(sys.stdout, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    count = 0
    for row in rows(args.run_root):
        writer.writerow(row)
        count += 1
    if count == 0:
        print(f"No individual metrics found under {args.run_root}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

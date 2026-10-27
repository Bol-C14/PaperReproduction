#!/usr/bin/env python3
"""Materialize the eight public paper tasks and generate portable EA configs.

This is the public replacement for the machine-specific historical preparation
script. It consumes the pinned files downloaded by ``fetch_cvdp_subset.py``,
resolves only the seven required public Git bundles, injects the matching CID
seed skill, and emits one task-local optimizer config per paper task.

Generated task payloads contain CVDP harness material and must remain under the
gitignored ``runs/`` tree. They are never part of the source release.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
CONVERTER_DIR = REPO_ROOT / "nemogym" / "resources_servers" / "cvdp_agentic_heavy" / "scripts"
sys.path.insert(0, str(CONVERTER_DIR))

import convert_to_gym  # noqa: E402


DATASET_REVISION = "5b807d945f6a99aa645f7e43a64a2115e281b4bf"
SOURCE_FILENAME = "cvdp_v1.1.0_agentic_heavy_code_generation_no_commercial.jsonl"
BUNDLE_DIRNAME = "cvdp_v1.1.0_agentic_heavy_code_generation_public"

CONDITIONS = {
    "c3-sparse": {
        "dense_feedback": False,
        "historical_source": {
            "best_reconstruction": "1d2b582869afc11272e1c894e108527ca8255796",
            "recorded_initial_head": "d091581d2685448ed46516d64f783f24777ea42a",
            "note": "C3 used two dirty launch states; see docs/PROVENANCE.md.",
        },
    },
    "c4-dense": {
        "dense_feedback": True,
        "historical_source": {
            "base_commit": "90afe0fcee8e61fc8461992bbe4731674715cf34",
            "recovered_patch_sha256": "14f6b93338293ef01ac7bebf3882843df35c8db765222175d6cbd2243a2e6623",
            "note": "Recovered 14-file launch patch; see docs/PROVENANCE.md.",
        },
    },
}

TASKS = [
    {
        "cid": "cid003",
        "task_id": "cvdp_agentic_heavy_fpga_nes_0003",
        "seed_skill": "skills/rollout/cid003_spec_to_rtl.md",
        "nature": "specification-to-RTL",
    },
    {
        "cid": "cid003",
        "task_id": "cvdp_agentic_heavy_verilog_pcie_0004",
        "seed_skill": "skills/rollout/cid003_spec_to_rtl.md",
        "nature": "specification-to-RTL",
    },
    {
        "cid": "cid004",
        "task_id": "cvdp_agentic_heavy_802.11a_0001",
        "seed_skill": "skills/rollout/cid004_rtl_refine_design.md",
        "nature": "RTL refinement",
    },
    {
        "cid": "cid004",
        "task_id": "cvdp_agentic_heavy_verilog_pcie_0028",
        "seed_skill": "skills/rollout/cid004_rtl_refine_design.md",
        "nature": "RTL refinement",
    },
    {
        "cid": "cid005",
        "task_id": "cvdp_agentic_heavy_NoobsCpu-8bit_0002",
        "seed_skill": "skills/rollout/cid005_code_completion.md",
        "nature": "code completion",
    },
    {
        "cid": "cid005",
        "task_id": "cvdp_agentic_heavy_rvx_0004",
        "seed_skill": "skills/rollout/cid005_code_completion.md",
        "nature": "code completion",
    },
    {
        "cid": "cid016",
        "task_id": "cvdp_agentic_heavy_async-fifo_0003",
        "seed_skill": "skills/rollout/cid016_rtl_bug_fix.md",
        "nature": "RTL bug fixing",
    },
    {
        "cid": "cid016",
        "task_id": "cvdp_agentic_heavy_schoolMIPS_0012",
        "seed_skill": "skills/rollout/cid016_rtl_bug_fix.md",
        "nature": "RTL bug fixing",
    },
]

OSS_NOTE = """

OSS-ONLY RUN NOTE:
- Commercial simulators are intentionally unavailable.
- Use only the exposed open-source tool flow: visible file tools, iverilog, and vvp.
- The external CVDP verifier runs open-source Icarus/cocotb checks. Hidden harness files are not visible.
"""

XTOOL_RE = re.compile(r"\b(xrun|xcelium|cadence|questa|modelsim|vsim|vcs)\b", re.IGNORECASE)


def short_task_id(task_id: str) -> str:
    return task_id.removeprefix("cvdp_agentic_heavy_")


def safe_alias(task_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", short_task_id(task_id)).strip("_")


def load_public_rows(source: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for row in convert_to_gym.iter_json_rows(source):
        task_id = str(row.get("id", ""))
        if task_id:
            rows[task_id] = row
    return rows


def remove_commercial_tooling(row: dict) -> dict:
    """Keep the public no-commercial tool contract explicit and auditable."""
    row = copy.deepcopy(row)
    params = row.setdefault("responses_create_params", {})
    params["tools"] = [
        tool
        for tool in params.get("tools", [])
        if not (isinstance(tool, dict) and tool.get("name") == "xcelium")
    ]

    for message in params.get("input", []):
        if not isinstance(message, dict) or message.get("role") != "developer":
            continue
        lines = []
        for line in str(message.get("content", "")).splitlines():
            if XTOOL_RE.search(line):
                continue
            lines.append(line)
        text = "\n".join(lines).rstrip()
        if "OSS-ONLY RUN NOTE:" not in text:
            text += OSS_NOTE
        message["content"] = text.strip()

    metadata = row.setdefault("verifier_metadata", {})
    context_files = metadata.setdefault("context_files", {})
    removed_context = []
    for path, content in list(context_files.items()):
        if path == "SKILL.md":
            continue
        if XTOOL_RE.search(str(content)):
            removed_context.append(path)
            del context_files[path]

    visible_prompt = "\n".join(
        str(message.get("content", ""))
        for message in params.get("input", [])
        if isinstance(message, dict)
    )
    if XTOOL_RE.search(visible_prompt):
        raise ValueError("commercial simulator guidance remains in visible prompt")

    tool_names = [
        tool.get("name")
        for tool in params.get("tools", [])
        if isinstance(tool, dict)
    ]
    required = {"ls", "cat", "rg", "find_files", "read_file", "show_changes", "module_index", "echo", "edit", "iverilog", "vvp", "pwd"}
    missing = sorted(required - set(tool_names))
    if missing:
        raise ValueError(f"missing required public tools: {missing}")
    return {
        "row": row,
        "tool_names": tool_names,
        "removed_visible_commercial_context": removed_context,
    }


def make_config(
    *,
    task: dict,
    task_path: Path,
    output_dir: Path,
    condition: str,
    generations: int,
    population_size: int,
    num_repeats: int,
    num_parallel: int,
    timeout: int,
) -> dict:
    dense = bool(CONDITIONS[condition]["dense_feedback"])
    return {
        "seed_skill": task["seed_skill"],
        "tasks_path": str(task_path),
        "output_dir": str(output_dir),
        "objective": (
            f"Optimize a task-local CVDP rollout skill for {task['task_id']} "
            f"({task['cid']}, {task['nature']}) under the Trace2Skill paper protocol."
        ),
        "mutation_llm": {
            "base_url": "${LLM_BASE_URL}",
            "api_key": "${LLM_API_KEY}",
            "model": "${MUTATION_MODEL}",
            "temperature": 0.35,
        },
        "eval_config": "eval/configs/eval_models.yml",
        "rate_limit": {"max_requests_per_minute": 80},
        "telemetry": {"mode": "debug", "enabled": False},
        "skill_monitor": {"enabled": False, "mode": "passive", "inject_feedback": False},
        "runtime_verifier_feedback": {
            "enabled": dense,
            "max_calls": 3,
            "artifact_root": str(output_dir / "runtime_verifier_feedback"),
        },
        "skill_sanitizer": {
            "enabled": True,
            "max_growth_ratio": 1.35,
            "max_growth_chars": 2500,
            "min_budget_chars": 4500,
            "absolute_max_chars": 18000,
            "condense": {
                "enabled": True,
                "over_chars": 9000,
                "target_chars": 6500,
                "soft_budget_slack_chars": 1024,
                "soft_budget_slack_ratio": 0.1,
                "min_retention_ratio": 0.75,
            },
        },
        "skill_integration": {
            "enabled": True,
            "min_directive_coverage": 0.6,
            "max_missing_critical": 0,
            "min_child_parent_ratio_for_soften": 0.75,
            "fail_on_remove_violation": True,
            "fail_on_contradiction": True,
        },
        "mutation_repair": {"enabled": True, "temperature": 0.2},
        "ga": {
            "population_size": population_size,
            "generations": generations,
            "elitism": 1,
            "crossover_rate": 0.0,
            "mutation_rate": 1.0,
            "tournament_size": min(3, population_size),
            "oracle_feedback": "always",
            "parent_child_survival": True,
            "single_lineage_survival_margin": 0.05,
            "standard_ea": {
                "enabled": True,
                "mutation_parent": "survivor",
                "carry_evaluated_survivor": True,
                "defer_child_semantic_selection_to_rollout": True,
                "disable_parent_child_challenger": True,
                "disable_semantic_survivor": True,
            },
            "parent_child_challenger": {"enabled": False},
            "semantic_survivor": {"enabled": False},
            "semantic_skill_selection": {
                "enabled": True,
                "min_improvement_margin": 0.02,
                "neutral_tolerance": 0.005,
                "min_coverage_gain_to_accept": 0.05,
                "reject_on_missing_critical_regression": True,
                "reject_on_remove_violation": True,
                "reject_on_contradiction": True,
                "carry_incumbent": False,
                "prefer_incumbent_parent": False,
                "incumbent_min_delta": 0.0,
            },
        },
        "rollout_model": {
            "base_url": "${LLM_BASE_URL}",
            "api_key": "${LLM_API_KEY}",
            "model": "${ROLLOUT_MODEL}",
            "temperature": 0.2,
            "max_output_tokens": 16384,
            "response_error_retries": 3,
            "response_error_retry_sleep": 180,
            "internal_request_max_retries": 1,
            "external_request_max_retries": 3,
            "aiohttp_timeout_total": 21600,
            "aiohttp_timeout_sock_read": 7200,
        },
        "nemogym_root": str((REPO_ROOT / "nemogym").resolve()),
        "ng_collect_bin": str((REPO_ROOT / "scripts" / "ng_collect_rollouts_local.sh").resolve()),
        "ng_config_paths": ["configs/cvdp_lc_30turns.yaml", "nemo_gym_env.yaml"],
        "preflight": {
            "enabled": True,
            "fail_on_warnings": False,
            "require_edit_tool": True,
            "require_skill_file": True,
            "forbid_xcelium": True,
            "require_verify_feedback_tool": dense,
            "allow_verify_feedback_tool": dense,
        },
        "max_skill_length": 18000,
        "fitness": {
            "agent_name": "cvdp_agentic_heavy_simple_agent",
            "num_repeats": num_repeats,
            "num_parallel": num_parallel,
            "timeout": timeout,
            "run_analyzer": False,
            "dry_run": False,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition", choices=sorted(CONDITIONS), required=True)
    parser.add_argument("--data-root", type=Path, default=REPO_ROOT / "data" / "cvdp-v1.1.0")
    parser.add_argument("--run-root", type=Path, default=REPO_ROOT / "runs")
    parser.add_argument("--repos-cache", type=Path, default=REPO_ROOT / "data" / "repos-cache")
    parser.add_argument("--task", action="append", default=[], help="Exact task ID or short ID; repeatable.")
    parser.add_argument("--generations", type=int, default=5)
    parser.add_argument("--population-size", type=int, default=4)
    parser.add_argument("--num-repeats", type=int, default=4)
    parser.add_argument("--num-parallel", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=21600)
    parser.add_argument("--force", action="store_true", help="Replace generated preparation files, never run outputs.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data_root = args.data_root.expanduser().resolve()
    run_root = args.run_root.expanduser().resolve()
    repos_cache = args.repos_cache.expanduser().resolve()
    source = data_root / SOURCE_FILENAME
    bundle_root = data_root / BUNDLE_DIRNAME
    if not source.is_file() or not bundle_root.is_dir():
        raise SystemExit("CVDP subset is missing; run ./scripts/fetch_cvdp_subset.py first")

    selected = TASKS
    if args.task:
        wanted = set(args.task)
        selected = [
            task
            for task in TASKS
            if task["task_id"] in wanted or short_task_id(task["task_id"]) in wanted
        ]
        if len(selected) != len(wanted):
            found = {task["task_id"] for task in selected} | {short_task_id(task["task_id"]) for task in selected}
            missing = sorted(wanted - found)
            raise SystemExit(f"unknown paper task(s): {missing}")

    prepared_root = run_root / "prepared" / args.condition
    manifest_path = prepared_root / "manifest.json"
    if manifest_path.exists() and not args.force:
        raise SystemExit(f"{manifest_path} exists; pass --force to refresh generated preparation files")

    rows = load_public_rows(source)
    dense = bool(CONDITIONS[args.condition]["dense_feedback"])
    task_dir = prepared_root / "tasks"
    config_dir = prepared_root / "configs"
    task_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)
    repos_cache.mkdir(parents=True, exist_ok=True)

    manifest_rows = []
    for task in selected:
        task_id = task["task_id"]
        if task_id not in rows:
            raise SystemExit(f"pinned public dataset does not contain {task_id}")
        skill_text = (REPO_ROOT / task["seed_skill"]).read_text(encoding="utf-8")
        gym_row = convert_to_gym.convert_entry(
            rows[task_id],
            str(repos_cache),
            False,
            skill_text,
            include_testbench_hints=False,
            enable_verify_feedback_tool=dense,
            heavy_repos_path=str(bundle_root),
            source_path=source,
        )
        if gym_row is None:
            raise SystemExit(f"failed to materialize {task_id}")
        sanitized = remove_commercial_tooling(gym_row)
        gym_row = sanitized["row"]

        alias = safe_alias(task_id)
        task_path = task_dir / f"{task['cid']}_{alias}.jsonl"
        task_path.write_text(json.dumps(gym_row, ensure_ascii=False) + "\n", encoding="utf-8")
        output_dir = run_root / args.condition / f"{task['cid']}_{alias}"
        config_path = config_dir / f"{task['cid']}_{alias}.yml"
        config = make_config(
            task=task,
            task_path=task_path,
            output_dir=output_dir,
            condition=args.condition,
            generations=args.generations,
            population_size=args.population_size,
            num_repeats=args.num_repeats,
            num_parallel=args.num_parallel,
            timeout=args.timeout,
        )
        config_path.write_text(yaml.safe_dump(config, sort_keys=False, width=110), encoding="utf-8")
        manifest_rows.append(
            {
                **task,
                "task_path": str(task_path),
                "config_path": str(config_path),
                "output_dir": str(output_dir),
                "tool_names": sanitized["tool_names"],
                "removed_visible_commercial_context": sanitized["removed_visible_commercial_context"],
                "runtime_verifier_feedback": dense,
            }
        )
        print(f"prepared {args.condition}: {task_id}")

    manifest = {
        "paper": "Trace2Skill: Verifier-Guided Skill Evolution for Long-Context EDA Agents",
        "condition": args.condition,
        "dataset": {
            "repository": "nvidia/cvdp-benchmark-dataset",
            "revision": DATASET_REVISION,
            "source": str(source),
            "bundle_root": str(bundle_root),
        },
        "historical_source": CONDITIONS[args.condition]["historical_source"],
        "generations": args.generations,
        "population_size": args.population_size,
        "num_repeats": args.num_repeats,
        "expected_rollouts_per_task": args.generations * args.population_size * args.num_repeats,
        "expected_total_rollouts": len(manifest_rows) * args.generations * args.population_size * args.num_repeats,
        "rollout_temperature": 0.2,
        "mutation_temperature": 0.35,
        "runtime_verifier_feedback": dense,
        "runtime_verifier_feedback_max_calls": 3 if dense else 0,
        "tasks": manifest_rows,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"PREPARATION READY: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


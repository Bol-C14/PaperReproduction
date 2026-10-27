#!/usr/bin/env python3
"""CVDP Skill Prompt Optimizer — Genetic Algorithm with NeMo-Gym Fitness.

Evolves the rtl_agent_skill.md to maximize rollout pass@1 using:
  - NAT-style GA: LLM-powered mutation, crossover
  - NeMo-Gym fitness: actual rollout collection with pass/fail grading
  - NAT eval flow: structured metrics and optional behavioral analysis

Usage:
    python optimizer/run_optimizer.py --config optimizer/configs/optimize_skill.yml
    python optimizer/run_optimizer.py --config optimizer/configs/optimize_skill.yml --resume

Prerequisites:
    - NeMo-Gym servers running (ng_run)
    - unified venv active (envs/unified)
    - LLM API accessible (for mutation) or Ollama running locally
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import random
import re
import sys
import time
from pathlib import Path, PurePosixPath

import openai
import yaml

from fitness import RolloutModelMismatchError, RolloutResponseError, evaluate_prompt, load_tasks
from debug_logging import ErrorLogger, GenTimer, StatusHeartbeat, describe_mode, resolve_telemetry_mode
from llm_audit import LLMAuditLogger, collect_run_metadata
from prompt_mutator import (
    mutate_prompt,
    crossover_prompts,
    repair_skill_candidate,
    extract_oracle_feedback,
    build_contrastive_oracle,
)
from path_grounding import analyze_path_grounding, summarize_path_grounding_diagnostics
from streaming_oracle import run_generation_oracle
from rate_limiter import get_rate_limiter, reset_rate_limiter
from telemetry import (
    init_telemetry,
    shutdown_telemetry,
    trace_generation,
    trace_fitness_eval,
    record_generation_metrics,
    LiveDashboard,
)
from skill_sanitizer import (
    MutationValidationError,
    build_execution_constraints_text,
    build_regression_reflection,
    candidate_skill_budget as _candidate_skill_budget,
    infer_execution_contract,
    sanitize_candidate_skill as _sanitize_candidate_skill,
    sanitize_feedback_for_execution_contract,
    validate_mutated_skill,
    write_mutation_health_record,
)
from skill_integration import (
    build_skill_patch_plan,
    format_integration_issues_for_repair,
    format_skill_patch_plan,
    repair_semantic_contradictions,
    validate_skill_integration,
    write_skill_integration_report,
    write_skill_patch_plan_artifacts,
)
from skill_selector import (
    choose_semantic_incumbent,
    select_child_skill_against_parent,
    semantic_skill_score,
)
from change_attribution import (
    format_change_evaluation_for_mutation,
    write_change_attribution_artifacts,
)
from lesson_bank import (
    distill_final_skill,
    format_lesson_bank_for_mutation,
    load_lesson_bank,
    update_lesson_bank,
    write_lesson_bank_artifacts,
)


CID_RE = re.compile(r"cid\d{3}", re.IGNORECASE)
REQUIRED_ROLLOUT_TOOLS = {
    "ls",
    "cat",
    "rg",
    "find_files",
    "read_file",
    "show_changes",
    "module_index",
    "echo",
    "edit",
    "iverilog",
    "vvp",
    "pwd",
}
SUPPORTED_ROLLOUT_TOOLS = REQUIRED_ROLLOUT_TOOLS | {"restore_file", "xcelium", "verify_feedback"}
PYTHON_IVERILOG_RE = re.compile(r"iverilog\s*\([^\)]*\.py\b", re.IGNORECASE | re.DOTALL)
HIDDEN_PROMPT_PATH_RE = re.compile(
    r"(^|[\s\"'`(])(?:/code/|code/)?(?:[\w./+\-]*/)?harness/|(?:test_runner|harness)\.py\b",
    re.IGNORECASE,
)
GENERATED_TESTBENCH_HINT_MARKERS = (
    "AVAILABLE TESTBENCHES in this project",
    "Use these to verify your fix. After writing your changes",
)
NEGATIVE_DIRECTIVE_MARKERS = (
    "do not",
    "don't",
    "never",
    "must not",
    "unavailable",
    "not available",
    "cannot",
    "can't",
    "invisible",
)


class Individual:
    """One member of the GA population."""

    def __init__(self, prompt: str, generation: int = 0, parent_info: str = ""):
        self.prompt = prompt
        self.generation = generation
        self.parent_info = parent_info
        self.fitness: float = 0.0
        self.fitness_result: dict = {}
        # Parent metadata is used only for regression-safe child acceptance.
        # It lets the optimizer challenge a risky child against the skill it
        # would replace, without hiding the full lineage in opaque filenames.
        self.parent_prompt: str | None = None
        self.parent_fitness: float | None = None
        self.parent_fitness_result: dict = {}
        self.parent_sha256: str | None = None
        self.child_origin: str = ""
        self.challenger_decision: dict = {}
        # Mutation-side semantic quality metadata. This is intentionally kept
        # separate from rollout fitness: rollout fitness still decides the
        # champion, while semantic retention can preserve a near-miss child
        # whose oracle-grounded lessons would otherwise be lost to rollout
        # noise.
        self.semantic_retention: dict = {}
        # Semantic selection is the parent-as-floor decision for whether this
        # skill is allowed to enter the next-generation lineage. It is separate
        # from rollout fitness by design.
        self.semantic_selection: dict = {}

    def to_dict(self) -> dict:
        result = {
            "generation": self.generation,
            "parent_info": self.parent_info,
            "fitness": self.fitness,
            "prompt_length": len(self.prompt),
            "prompt_preview": self.prompt[:200] + "..." if len(self.prompt) > 200 else self.prompt,
        }
        fr = self.fitness_result
        if fr:
            result["pass_at_1"] = fr.get("pass_at_1", 0.0)
            result["progress_fitness"] = fr.get("progress_fitness", 0.0)
            result["raw_progress_fitness"] = fr.get("raw_progress_fitness")
            result["selection_fitness"] = fr.get("selection_fitness", self.fitness)
            result["selection_fitness_original"] = fr.get("selection_fitness_original")
            result["selection_fitness_breakdown"] = fr.get("selection_fitness_breakdown", {})
            result["skill_quality"] = fr.get("skill_quality")
            result["agent_behavior_quality"] = fr.get("agent_behavior_quality")
            result["rollout_variance_quality"] = fr.get("rollout_variance_quality")
            result["skill_adherence_quality"] = fr.get("skill_adherence_quality")
            result["num_rollouts"] = fr.get("num_rollouts", 0)
            result["elapsed"] = fr.get("elapsed", 0)
            result["per_task"] = fr.get("per_task", {})
            result["path_grounding_fitness"] = fr.get("path_grounding_fitness", {})
            result["rollout_variance"] = fr.get("rollout_variance", {})
            result["progress_rollout_scores"] = fr.get("progress_rollout_scores", [])
            result["skill_monitor"] = fr.get("skill_monitor", {})
            result["dry_run"] = fr.get("dry_run", False)
            if fr.get("analyzer_report"):
                result["has_analyzer_report"] = True
        if self.parent_sha256:
            result["parent_sha256"] = self.parent_sha256
            result["child_origin"] = self.child_origin
        if self.challenger_decision:
            result["challenger_decision"] = self.challenger_decision
        if self.semantic_retention:
            result["semantic_retention"] = self.semantic_retention
        if self.semantic_selection:
            result["semantic_selection"] = self.semantic_selection
        return result

    def to_checkpoint_dict(self) -> dict:
        """Full serialization including prompt (for checkpoint/resume)."""
        d = self.to_dict()
        d["prompt"] = self.prompt
        d["fitness_result"] = self.fitness_result
        d["parent_prompt"] = self.parent_prompt
        d["parent_fitness"] = self.parent_fitness
        d["parent_fitness_result"] = self.parent_fitness_result
        d["parent_sha256"] = self.parent_sha256
        d["child_origin"] = self.child_origin
        d["challenger_decision"] = self.challenger_decision
        d["semantic_retention"] = self.semantic_retention
        d["semantic_selection"] = self.semantic_selection
        return d

    @classmethod
    def from_checkpoint_dict(cls, d: dict) -> "Individual":
        ind = cls(
            prompt=d["prompt"],
            generation=d.get("generation", 0),
            parent_info=d.get("parent_info", ""),
        )
        ind.fitness = d.get("fitness", 0.0)
        ind.fitness_result = d.get("fitness_result", {})
        ind.parent_prompt = d.get("parent_prompt")
        ind.parent_fitness = d.get("parent_fitness")
        ind.parent_fitness_result = d.get("parent_fitness_result", {})
        ind.parent_sha256 = d.get("parent_sha256")
        ind.child_origin = d.get("child_origin", "")
        ind.challenger_decision = d.get("challenger_decision", {})
        ind.semantic_retention = d.get("semantic_retention", {})
        ind.semantic_selection = d.get("semantic_selection", {})
        return ind


def save_checkpoint(
    output_dir: Path,
    last_completed_gen: int,
    population: list[Individual],
    best_ever: Individual,
    history: list[dict],
    checkpoint_stage: str = "post_breeding",
    semantic_incumbent: Individual | None = None,
) -> Path:
    """Save full state for resume.

    `checkpoint_stage` is intentionally explicit. A post-fitness checkpoint
    contains an evaluated generation that still needs oracle+breeding on resume;
    a post-breeding checkpoint contains unevaluated children ready for the next
    generation's fitness eval.
    """
    if checkpoint_stage not in {"post_fitness", "post_breeding"}:
        raise ValueError(f"unknown checkpoint_stage: {checkpoint_stage!r}")
    ckpt = {
        "last_completed_gen": last_completed_gen,
        "checkpoint_stage": checkpoint_stage,
        "needs_breeding": checkpoint_stage == "post_fitness",
        "next_generation": last_completed_gen + 1,
        "population": [ind.to_checkpoint_dict() for ind in population],
        "best_ever": best_ever.to_checkpoint_dict(),
        "semantic_incumbent": semantic_incumbent.to_checkpoint_dict() if semantic_incumbent is not None else None,
        "history": history,
    }
    ckpt_path = output_dir / "checkpoint.json"
    tmp_path = output_dir / "checkpoint.json.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(ckpt, f, indent=2, ensure_ascii=False)
    tmp_path.rename(ckpt_path)
    return ckpt_path


def load_checkpoint(output_dir: Path) -> dict | None:
    """Load checkpoint if it exists. Returns None if no checkpoint found."""
    ckpt_path = output_dir / "checkpoint.json"
    if not ckpt_path.exists():
        return None
    with open(ckpt_path, encoding="utf-8") as f:
        return json.load(f)


def _checkpoint_needs_breeding(ckpt: dict, population: list[Individual]) -> bool:
    """Return whether a loaded checkpoint should resume with oracle+breeding.

    Older checkpoints did not store an explicit stage. For those, infer from
    fitness_result presence instead of positive fitness, because hard CVDP
    generations can be legitimately all-zero after successful rollout eval.
    """
    if "needs_breeding" in ckpt:
        return bool(ckpt["needs_breeding"])
    stage = ckpt.get("checkpoint_stage")
    if stage == "post_fitness":
        return True
    if stage == "post_breeding":
        return False
    return any(bool(getattr(ind, "fitness_result", None)) for ind in population)


def _json_safe(obj):
    """Return an object that json.dump can serialize."""
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, tuple):
        return [_json_safe(v) for v in obj]
    return obj


def _write_json(path: Path, data: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_json_safe(data), f, indent=2, ensure_ascii=False)


def _append_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(_json_safe(rec), ensure_ascii=False) + "\n")


def _append_one_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(_json_safe(record), ensure_ascii=False) + "\n")


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _score_from_result(result: dict | None, default: float = 0.0) -> float:
    if not isinstance(result, dict):
        return float(default)
    for key in ("selection_fitness", "pass_at_1", "fitness"):
        try:
            return float(result.get(key, default) or 0.0)
        except (TypeError, ValueError):
            continue
    return float(default)


def _pass_from_result(result: dict | None, default: float = 0.0) -> float:
    if not isinstance(result, dict):
        return float(default)
    try:
        return float(result.get("pass_at_1", default) or 0.0)
    except (TypeError, ValueError):
        return float(default)


def _same_skill(a: Individual | None, b: Individual | None) -> bool:
    if a is None or b is None:
        return False
    return _sha256_text(a.prompt) == _sha256_text(b.prompt)


def _clone_individual_for_generation(ind: Individual, generation: int, parent_info: str) -> Individual:
    clone = Individual(ind.prompt, generation=generation, parent_info=parent_info)
    clone.fitness = ind.fitness
    clone.fitness_result = copy.deepcopy(ind.fitness_result)
    clone.parent_prompt = ind.parent_prompt
    clone.parent_fitness = ind.parent_fitness
    clone.parent_fitness_result = copy.deepcopy(ind.parent_fitness_result)
    clone.parent_sha256 = ind.parent_sha256
    clone.child_origin = ind.child_origin
    clone.challenger_decision = copy.deepcopy(ind.challenger_decision)
    clone.semantic_retention = copy.deepcopy(ind.semantic_retention)
    clone.semantic_selection = copy.deepcopy(ind.semantic_selection)
    return clone


def _carry_prompt_for_reevaluation(ind: Individual, generation: int, parent_info: str) -> Individual:
    """Carry a survivor prompt into the next generation without stale fitness."""

    carried = Individual(ind.prompt, generation=generation, parent_info=parent_info)
    carried.parent_prompt = ind.prompt
    carried.parent_fitness = ind.fitness
    carried.parent_fitness_result = copy.deepcopy(ind.fitness_result)
    carried.parent_sha256 = _sha256_text(ind.prompt)
    carried.child_origin = (ind.child_origin + "+ea_survivor").strip("+") or "ea_survivor"
    carried.semantic_retention = copy.deepcopy(ind.semantic_retention)
    carried.semantic_selection = copy.deepcopy(ind.semantic_selection)
    return carried


def _breeding_pool_with_survivor(
    population: list[Individual],
    best_ever: Individual | None,
    enabled: bool,
) -> list[Individual]:
    pool = list(population)
    if enabled and best_ever is not None and not any(_same_skill(ind, best_ever) for ind in pool):
        pool.append(copy.deepcopy(best_ever))
    return pool


def _prompt_in_population(prompt: str, population: list[Individual]) -> bool:
    """Return true when an identical skill is already present."""
    sha = _sha256_text(prompt)
    return any(_sha256_text(ind.prompt) == sha for ind in population)


def _semantic_metrics(ind: Individual) -> dict:
    """Extract oracle-integration metrics recorded at mutation time."""
    meta = getattr(ind, "semantic_retention", None) or {}
    metrics = meta.get("skill_integration_metrics") or {}
    if isinstance(metrics, dict):
        return metrics
    return {}


def _semantic_score_from_metrics(metrics: dict | None, default: float = 0.50) -> float:
    """Approximate skill semantic quality from persisted integration metrics.

    Full integration reports are available at mutation time. Later generations
    often only carry compact metrics in checkpoints, so this fallback keeps the
    non-regression floor measurable without re-running an LLM or parser.
    """
    if not isinstance(metrics, dict) or not metrics:
        return float(default)
    try:
        coverage = max(0.0, min(1.0, float(metrics.get("coverage", default) or default)))
        parent_coverage = max(0.0, min(1.0, float(metrics.get("parent_coverage", coverage) or coverage)))
        missing = max(0, int(metrics.get("missing_critical_count", 0) or 0))
        remove_violations = max(0, int(metrics.get("remove_violation_count", 0) or 0))
        contradictions = max(0, int(metrics.get("contradiction_count", 0) or 0))
        ratio = float(metrics.get("candidate_parent_ratio", 1.0) or 1.0)
    except (TypeError, ValueError):
        return float(default)

    coverage_gain = max(0.0, coverage - parent_coverage)
    retention = max(0.0, min(1.0, ratio / 0.75)) if ratio > 0 else 0.0
    length_quality = 1.0 if 0.80 <= ratio <= 1.60 else max(0.35, min(1.0, ratio / 0.80))
    safety = max(0.0, 1.0 - 0.30 * remove_violations - 0.30 * contradictions - 0.12 * missing)
    score = (
        0.45 * coverage
        + 0.20 * min(1.0, coverage_gain * 4.0)
        + 0.15 * retention
        + 0.10 * length_quality
        + 0.10 * safety
    )
    return max(0.0, min(1.0, score * (0.70 + 0.30 * safety)))


def _skill_quality_from_individual(ind: Individual, default: float = 0.50) -> float:
    """Return the persisted semantic skill-quality score for selection/reporting."""
    semantic = getattr(ind, "semantic_retention", None) or {}
    for key in ("skill_quality_score", "semantic_quality_score"):
        if semantic.get(key) is not None:
            try:
                return max(0.0, min(1.0, float(semantic[key])))
            except (TypeError, ValueError):
                pass
    selection = getattr(ind, "semantic_selection", None) or {}
    for score_key in ("candidate_score", "parent_score"):
        score_obj = selection.get(score_key)
        if isinstance(score_obj, dict) and score_obj.get("score") is not None:
            try:
                return max(0.0, min(1.0, float(score_obj["score"])))
            except (TypeError, ValueError):
                pass
    return _semantic_score_from_metrics(_semantic_metrics(ind), default=default)


def _skill_validity_from_individual(ind: Individual) -> dict:
    """Return deterministic validity signals used to block unsafe skill survival."""
    semantic = getattr(ind, "semantic_retention", None) or {}
    metrics = _semantic_metrics(ind)
    has_semantic_metadata = bool(semantic)
    # Carried seed/parent skills may predate mutation metadata. Treat them as
    # valid unless a later process attached explicit safety failures.
    integration_ok = bool(semantic.get("skill_integration_ok", True))
    missing = int(metrics.get("missing_critical_count", 0) or 0) if isinstance(metrics, dict) else 0
    remove_violations = int(metrics.get("remove_violation_count", 0) or 0) if isinstance(metrics, dict) else 0
    contradictions = int(metrics.get("contradiction_count", 0) or 0) if isinstance(metrics, dict) else 0
    invalid = (
        has_semantic_metadata
        and (
            not integration_ok
            or remove_violations > 0
            or contradictions > 0
        )
    )
    return {
        "has_semantic_metadata": has_semantic_metadata,
        "valid": not invalid,
        "integration_ok": integration_ok,
        "missing_critical_count": missing,
        "remove_violation_count": remove_violations,
        "contradiction_count": contradictions,
        "invalid_reasons": [
            reason for reason, enabled in (
                ("skill_integration_not_ok", has_semantic_metadata and not integration_ok),
                (f"remove_violation_count:{remove_violations}", remove_violations > 0),
                (f"contradiction_count:{contradictions}", contradictions > 0),
            )
            if enabled
        ],
    }


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _apply_combined_selection_fitness(
    *,
    population: list[Individual],
    generation: int,
    gen_dir: Path,
    cfg: dict,
) -> list[dict]:
    """Recompute selection fitness from robust rollout utility plus skill quality.

    The sparse pass rate remains dominant. Dense progress, repeat robustness,
    semantic quality, and skill adherence only affect the bounded tie-breaker
    below one additional pass. A hard semantic/validity floor prevents unsafe or
    lower-quality skills from replacing the carried parent.
    """
    if not population or not cfg.get("enabled", True):
        return []

    weights = {
        "progress_lcb": 0.55,
        "progress_mean": 0.15,
        "skill_quality": 0.20,
        "adherence": 0.10,
        **(cfg.get("weights") or {}),
    }
    q_default = float(cfg.get("default_skill_quality", 0.50) or 0.50)
    floor_tolerance = float(cfg.get("semantic_floor_tolerance", 0.005) or 0.005)
    enforce_floor = bool(cfg.get("enforce_semantic_floor", True))
    enforce_validity = bool(cfg.get("enforce_validity", True))
    parent_quality_floor = _skill_quality_from_individual(population[0], default=q_default)

    records: list[dict] = []
    for idx, ind in enumerate(population):
        fr = getattr(ind, "fitness_result", None) or {}
        original_selection = _safe_float(fr.get("selection_fitness", ind.fitness), ind.fitness)
        pass_rate = _safe_float(fr.get("pass_at_1", 0.0), 0.0)
        progress = _safe_float(fr.get("progress_fitness", 0.0), 0.0)
        epsilon = _safe_float(fr.get("selection_epsilon", 0.0), 0.0)
        if epsilon <= 0.0:
            epsilon = float(cfg.get("fallback_selection_epsilon", 0.049) or 0.049)

        variance = fr.get("rollout_variance") if isinstance(fr.get("rollout_variance"), dict) else {}
        progress_mean = _safe_float(variance.get("mean", progress), progress)
        progress_lcb = _safe_float(variance.get("lower_confidence_bound_95", progress_mean), progress_mean)
        variance_quality = _safe_float(variance.get("variance_quality", 1.0), 1.0)
        skill_quality = _skill_quality_from_individual(ind, default=q_default)
        monitor = fr.get("skill_monitor") if isinstance(fr.get("skill_monitor"), dict) else {}
        adherence = _safe_float(monitor.get("mean_adherence_score", 1.0), 1.0)
        validity = _skill_validity_from_individual(ind)

        utility = (
            weights["progress_lcb"] * progress_lcb
            + weights["progress_mean"] * progress_mean
            + weights["skill_quality"] * skill_quality
            + weights["adherence"] * adherence
        )
        behavior_quality = max(0.0, min(1.0, 0.80 * progress_lcb + 0.20 * progress_mean))
        semantic_floor_violation = skill_quality + floor_tolerance < parent_quality_floor
        validity_violation = enforce_validity and not validity["valid"]
        if enforce_floor and semantic_floor_violation:
            utility = 0.0
        if validity_violation:
            utility = 0.0

        combined_selection = pass_rate + epsilon * max(0.0, min(1.0, utility))
        selection_blocked = bool(validity_violation or (enforce_floor and semantic_floor_violation))
        if selection_blocked:
            # A sparse pass does not license propagating an unsafe or
            # semantically regressed skill. The parent remains in the same
            # population, so blocked candidates can still contribute rollout
            # evidence to the oracle without becoming the next parent.
            combined_selection = -1.0
        record = {
            "generation": generation,
            "individual_index": idx,
            "parent_info": ind.parent_info,
            "original_selection_fitness": round(original_selection, 6),
            "combined_selection_fitness": round(combined_selection, 6),
            "pass_at_1": round(pass_rate, 6),
            "selection_epsilon": round(epsilon, 6),
            "robust_utility": round(max(0.0, min(1.0, utility)), 6),
            "skill_quality": round(skill_quality, 6),
            "agent_behavior_quality": round(behavior_quality, 6),
            "parent_quality_floor": round(parent_quality_floor, 6),
            "semantic_floor_violation": bool(semantic_floor_violation),
            "selection_blocked": selection_blocked,
            "validity": validity,
            "progress_fitness": round(progress, 6),
            "progress_lcb_95": round(progress_lcb, 6),
            "progress_mean": round(progress_mean, 6),
            "rollout_variance_quality": round(variance_quality, 6),
            "skill_adherence": round(adherence, 6),
            "weights": weights,
        }
        fr["selection_fitness_original"] = original_selection
        fr["selection_fitness"] = round(combined_selection, 6)
        fr["selection_fitness_breakdown"] = record
        fr["skill_quality"] = skill_quality
        fr["agent_behavior_quality"] = behavior_quality
        fr["rollout_variance_quality"] = variance_quality
        fr["skill_adherence_quality"] = adherence
        ind.fitness_result = fr
        ind.fitness = round(combined_selection, 6)
        records.append(record)

    _write_json(gen_dir / "combined_selection_fitness.json", {
        "generation": generation,
        "enabled": True,
        "selection_metric": "combined_selection_fitness",
        "parent_quality_floor": round(parent_quality_floor, 6),
        "records": records,
        "notes": (
            "Sparse pass dominates. Dense progress, lower-confidence-bound robustness, "
            "semantic skill quality, and passive adherence only affect the bounded "
            "tie-breaker. Invalid or semantic-floor-regressing skills receive zero "
            "tie-breaker utility and cannot beat the carried parent on equal pass rate."
        ),
    })
    return records


def _progress_from_result(result: dict | None, default: float = 0.0) -> float:
    if not isinstance(result, dict):
        return float(default)
    try:
        return float(result.get("progress_fitness", default) or 0.0)
    except (TypeError, ValueError):
        return float(default)


def _semantic_retention_candidate_record(
    *,
    generation: int,
    candidate_index: int,
    candidate: Individual,
    best: Individual,
    cfg: dict,
) -> dict:
    """Evaluate whether a semantically strong near-miss should survive.

    The goal is not to override behavior fitness. The behavior elite still
    remains rank 1. This record only protects a child that integrated the
    oracle's critical lessons and landed close enough to the elite that rollout
    randomness could plausibly explain the gap.
    """
    metrics = _semantic_metrics(candidate)
    semantic = getattr(candidate, "semantic_retention", None) or {}
    best_score = _score_from_result(best.fitness_result, best.fitness)
    cand_score = _score_from_result(candidate.fitness_result, candidate.fitness)
    best_pass = _pass_from_result(best.fitness_result, 0.0)
    cand_pass = _pass_from_result(candidate.fitness_result, 0.0)
    best_progress = _progress_from_result(best.fitness_result, 0.0)
    cand_progress = _progress_from_result(candidate.fitness_result, 0.0)

    coverage = float(metrics.get("coverage", 0.0) or 0.0)
    parent_coverage = float(metrics.get("parent_coverage", 0.0) or 0.0)
    coverage_gain = float(metrics.get("coverage_gain", coverage - parent_coverage) or 0.0)
    missing_critical = int(metrics.get("missing_critical_count", 999) or 0)
    remove_violations = int(metrics.get("remove_violation_count", 999) or 0)
    contradictions = int(metrics.get("contradiction_count", 999) or 0)

    selection_gap = best_score - cand_score
    progress_gap = best_progress - cand_progress
    pass_gap = best_pass - cand_pass

    reasons: list[str] = []
    accepted = True
    if not semantic.get("eligible", False):
        accepted = False
        reasons.append("no_mutation_semantic_metadata")
    if _sha256_text(candidate.prompt) == _sha256_text(best.prompt):
        accepted = False
        reasons.append("same_as_behavior_elite")
    if coverage < float(cfg.get("min_coverage", 0.90)):
        accepted = False
        reasons.append(f"coverage_below_min:{coverage:.3f}")
    if coverage_gain < float(cfg.get("min_coverage_gain", 0.10)):
        accepted = False
        reasons.append(f"coverage_gain_below_min:{coverage_gain:.3f}")
    if missing_critical > int(cfg.get("max_missing_critical", 0)):
        accepted = False
        reasons.append(f"missing_critical:{missing_critical}")
    if remove_violations > int(cfg.get("max_remove_violations", 0)):
        accepted = False
        reasons.append(f"remove_violations:{remove_violations}")
    if contradictions > int(cfg.get("max_contradictions", 0)):
        accepted = False
        reasons.append(f"contradictions:{contradictions}")
    if pass_gap > float(cfg.get("pass_margin", 0.0)):
        accepted = False
        reasons.append(f"pass_gap_too_large:{pass_gap:.4f}")

    within_selection = selection_gap <= float(cfg.get("selection_margin", 0.010))
    within_progress = progress_gap <= float(cfg.get("progress_margin", 0.10))
    if not (within_selection or within_progress):
        accepted = False
        reasons.append(
            f"not_near_elite:selection_gap={selection_gap:.4f},progress_gap={progress_gap:.4f}"
        )

    if accepted:
        reasons.append("near_fitness_high_oracle_coverage")

    # Prefer high coverage/gain, then closer measured behavior. This is only
    # used among already near-miss candidates.
    priority = (
        coverage
        + 0.5 * max(0.0, coverage_gain)
        - 2.0 * max(0.0, selection_gap)
        - 0.2 * max(0.0, progress_gap)
    )
    return {
        "generation": generation,
        "candidate_index": candidate_index,
        "parent_info": candidate.parent_info,
        "child_origin": candidate.child_origin,
        "candidate_sha256": _sha256_text(candidate.prompt),
        "best_sha256": _sha256_text(best.prompt),
        "accepted": accepted,
        "reasons": reasons,
        "priority": round(priority, 6),
        "selection_fitness": cand_score,
        "best_selection_fitness": best_score,
        "selection_gap": round(selection_gap, 6),
        "progress_fitness": cand_progress,
        "best_progress_fitness": best_progress,
        "progress_gap": round(progress_gap, 6),
        "pass_at_1": cand_pass,
        "best_pass_at_1": best_pass,
        "pass_gap": round(pass_gap, 6),
        "skill_integration_metrics": metrics,
        "semantic_retention": semantic,
    }


def select_semantic_survivors(
    *,
    population: list[Individual],
    generation: int,
    cfg: dict,
) -> tuple[list[Individual], list[dict]]:
    """Pick near-fitness, high-semantic-coverage children to carry forward."""
    if not cfg.get("enabled", True) or not population:
        return [], []
    best = population[0]
    records = [
        _semantic_retention_candidate_record(
            generation=generation,
            candidate_index=idx,
            candidate=ind,
            best=best,
            cfg=cfg,
        )
        for idx, ind in enumerate(population)
    ]
    accepted = [rec for rec in records if rec.get("accepted")]
    accepted.sort(key=lambda rec: rec.get("priority", 0.0), reverse=True)
    max_survivors = int(cfg.get("max_per_generation", 1) or 0)
    chosen_records = accepted[:max_survivors]
    survivors: list[Individual] = []
    for rec in chosen_records:
        candidate = population[int(rec["candidate_index"])]
        survivor = Individual(
            candidate.prompt,
            generation=generation + 1,
            parent_info=f"semantic_survivor_ind{rec['candidate_index']}_from_gen{generation}",
        )
        survivor.parent_prompt = candidate.parent_prompt
        survivor.parent_fitness = candidate.parent_fitness
        survivor.parent_fitness_result = copy.deepcopy(candidate.parent_fitness_result)
        survivor.parent_sha256 = candidate.parent_sha256
        survivor.child_origin = (candidate.child_origin + "+semantic_survivor").strip("+")
        survivor.semantic_retention = {
            **(candidate.semantic_retention or {}),
            "carried_forward": True,
            "source_generation": generation,
            "source_individual_index": rec["candidate_index"],
            "retention_reason": rec["reasons"],
            "source_selection_fitness": rec["selection_fitness"],
            "source_progress_fitness": rec["progress_fitness"],
        }
        survivors.append(survivor)
        rec["decision"] = "carry_forward"
    chosen = {rec["candidate_index"] for rec in chosen_records}
    for rec in records:
        rec.setdefault("decision", "carry_forward" if rec["candidate_index"] in chosen else "not_carried")
    return survivors, records


def build_semantic_retention_metadata(
    *,
    generation: int,
    next_generation: int,
    child_slot: int,
    stage: str,
    parent_info: str,
    parent_prompt: str,
    candidate_prompt: str,
    process_record: dict,
    skill_patch_plan: dict | None,
) -> dict:
    """Record why a mutated skill may be worth preserving despite noisy fitness."""
    integration = (process_record or {}).get("skill_integration") or {}
    metrics = integration.get("metrics") if isinstance(integration, dict) else {}
    metrics = metrics if isinstance(metrics, dict) else {}
    skill_quality_score = None
    skill_quality_breakdown = {}
    if isinstance(integration, dict) and integration:
        try:
            score_obj = semantic_skill_score(integration)
            skill_quality_score = score_obj.score
            skill_quality_breakdown = score_obj.to_dict()
        except Exception:
            skill_quality_score = _semantic_score_from_metrics(metrics)
            skill_quality_breakdown = {"score": skill_quality_score, "source": "metrics_fallback"}
    return {
        "eligible": bool(skill_patch_plan and integration.get("ok", False)),
        "generation": generation,
        "next_generation": next_generation,
        "child_slot": child_slot,
        "stage": stage,
        "parent_info": parent_info,
        "parent_sha256": _sha256_text(parent_prompt),
        "candidate_sha256": _sha256_text(candidate_prompt),
        "skill_integration_ok": bool(integration.get("ok", False)),
        "skill_integration_issues": integration.get("issues", []),
        "skill_integration_metrics": metrics,
        "skill_quality_score": skill_quality_score,
        "skill_quality_breakdown": skill_quality_breakdown,
        "repair_attempted": bool((process_record or {}).get("repair_attempted")),
        "semantic_repairs": (process_record or {}).get("semantic_repairs", []),
    }


def apply_semantic_skill_selection(
    *,
    parent_prompt: str,
    candidate_prompt: str,
    process_record: dict,
    output_dir: Path,
    gen_dir: Path,
    generation: int,
    child_slot: int,
    stage: str,
    parent_info: str,
    skill_patch_plan: dict | None,
    execution_contract,
    skill_integration_cfg: dict,
    semantic_skill_selection_cfg: dict,
) -> tuple[str, dict]:
    """Apply parent-as-floor skill selection and persist the decision.

    This gate is deliberately after mutation repair/sanitization and before the
    skill is injected into the next generation. It keeps the previous parent
    when a child is merely different, noisy, or less grounded.
    """

    selected_prompt, decision = select_child_skill_against_parent(
        parent_skill=parent_prompt,
        candidate_skill=candidate_prompt,
        patch_plan=skill_patch_plan,
        execution_contract=execution_contract,
        integration_cfg=skill_integration_cfg,
        selector_cfg=semantic_skill_selection_cfg,
        child_integration_report=(process_record or {}).get("skill_integration"),
        generation=generation,
        child_slot=child_slot,
        stage=stage,
    )
    decision = {
        **decision,
        "parent_info": parent_info,
        "selected_sha256": _sha256_text(selected_prompt),
        "selected_parent_or_child": "child" if selected_prompt == candidate_prompt else "parent",
    }
    _append_one_jsonl(output_dir / "semantic_skill_selection.jsonl", decision)
    _append_one_jsonl(gen_dir / "semantic_skill_selection.jsonl", decision)
    return selected_prompt, decision


def defer_child_semantic_selection(
    *,
    parent_prompt: str,
    candidate_prompt: str,
    process_record: dict,
    output_dir: Path,
    gen_dir: Path,
    generation: int,
    child_slot: int,
    stage: str,
    parent_info: str,
    skill_patch_plan: dict | None,
) -> dict:
    """Record semantic metadata without selecting an unevaluated child.

    In the standard EA flow, mutation creates candidates for the *next*
    generation. Those candidates must earn survival only after rollout
    evaluation. We still keep the semantic integration record so we can audit
    whether the mutator used oracle lessons, but the selector is intentionally
    deferred to the next generation's measured population ranking.
    """

    integration = (process_record or {}).get("skill_integration") or {}
    metrics = integration.get("metrics") if isinstance(integration, dict) else {}
    decision = {
        "generation": generation,
        "next_generation": generation + 1,
        "child_slot": child_slot,
        "stage": stage,
        "parent_info": parent_info,
        "decision": "deferred_to_next_generation_rollout",
        "selected_parent_or_child": "child",
        "rollout_fitness_used_for_selection": False,
        "parent_sha256": _sha256_text(parent_prompt),
        "candidate_sha256": _sha256_text(candidate_prompt),
        "selected_sha256": _sha256_text(candidate_prompt),
        "has_patch_plan": bool(skill_patch_plan),
        "skill_integration_ok": bool(integration.get("ok", False)) if isinstance(integration, dict) else False,
        "skill_integration_issues": integration.get("issues", []) if isinstance(integration, dict) else [],
        "skill_integration_metrics": metrics if isinstance(metrics, dict) else {},
        "reasons": [
            "standard_ea_defers_child_selection_until_child_has_rollouts",
            "sanitizer_and_integration_gate_already_applied",
        ],
    }
    _append_one_jsonl(output_dir / "semantic_skill_selection.jsonl", decision)
    _append_one_jsonl(gen_dir / "semantic_skill_selection.jsonl", decision)
    return decision


def make_standard_ea_survivor_record(
    *,
    generation: int,
    survivor: "Individual",
    rank: int = 0,
) -> dict:
    """Describe the evaluated individual that survives a standard EA generation."""

    fitness_result = getattr(survivor, "fitness_result", None) or {}
    return {
        "generation": generation,
        "decision": "evaluated_population_survivor",
        "selection_metric": "combined_selection_fitness",
        "survivor_rank": rank,
        "survivor_parent_info": survivor.parent_info,
        "survivor_generation": survivor.generation,
        "survivor_sha256": _sha256_text(survivor.prompt),
        "selection_fitness": float(getattr(survivor, "fitness", 0.0) or 0.0),
        "selection_fitness_original": fitness_result.get("selection_fitness_original"),
        "selection_fitness_breakdown": fitness_result.get("selection_fitness_breakdown", {}),
        "skill_quality": fitness_result.get("skill_quality"),
        "agent_behavior_quality": fitness_result.get("agent_behavior_quality"),
        "rollout_variance_quality": fitness_result.get("rollout_variance_quality"),
        "skill_adherence_quality": fitness_result.get("skill_adherence_quality"),
        "pass_at_1": fitness_result.get("pass_at_1"),
        "progress_fitness": fitness_result.get("progress_fitness"),
        "note": (
            "Standard EA uses one rollout/evaluation phase per generation. "
            "Children proposed after this point are not eligible to become a "
            "survivor until they are evaluated in the next generation."
        ),
    }


def _single_lineage_parent(
    current_best: Individual,
    best_ever: Individual | None,
    margin: float,
) -> tuple[Individual, str]:
    """Choose a pop=1 mutation parent without freezing evolution.

    With population size 1, always mutating best-ever protects pass rate but can
    stagnate skills after noisy regressions. This helper mutates the current
    lineage when it is within `margin` of best-ever, and falls back to best-ever
    only after a meaningful drop.
    """
    if best_ever is None:
        return current_best, "current_no_best_ever"
    if current_best.fitness >= best_ever.fitness - margin:
        return current_best, "current_within_best_ever_margin"
    return best_ever, "best_ever_after_regression"


def _short_task_id(task_id: str | None) -> str:
    return (task_id or "unknown").replace("cvdp_agentic_heavy_", "")


def _hidden_verifier_path(path: str) -> bool:
    posix = PurePosixPath(path)
    parts = [part.lower() for part in posix.parts]
    return "harness" in parts or posix.name.lower() in {"harness.py", "test_runner.py"}


def _is_negative_directive(text: str) -> bool:
    lower = text.lower()
    return any(marker in lower for marker in NEGATIVE_DIRECTIVE_MARKERS)


def _line_mentions_hidden_harness_action(line: str) -> bool:
    lower = line.lower()
    if "harness" not in lower and "test_runner.py" not in lower and "hidden verifier" not in lower:
        return False
    if _is_negative_directive(lower):
        return False
    return any(verb in lower for verb in ("run", "execute", "invoke", "launch", "pytest", "docker", "make"))


def _verifier_metadata(task: dict) -> dict:
    metadata = task.get("verifier_metadata") or {}
    if not metadata and isinstance(task.get("metadata"), dict):
        metadata = task["metadata"].get("verifier_metadata") or {}
    if not metadata and isinstance(task.get("responses_create_params"), dict):
        metadata = task["responses_create_params"].get("verifier_metadata") or {}
    return metadata if isinstance(metadata, dict) else {}


def _extract_task_id(task: dict) -> str:
    metadata = _verifier_metadata(task)
    task_id = task.get("task_id") or metadata.get("task_id") or task.get("id")
    return str(task_id or "unknown")


def _extract_categories(task: dict) -> list[str]:
    metadata = _verifier_metadata(task)
    categories = task.get("categories") or metadata.get("categories") or []
    if isinstance(categories, str):
        return [categories]
    if isinstance(categories, list):
        return [str(c) for c in categories]
    return []


def _extract_cid_from_values(*values) -> str | None:
    for value in values:
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            found = _extract_cid_from_values(*value)
            if found:
                return found
            continue
        match = CID_RE.search(str(value))
        if match:
            return match.group(0).lower()
    return None


def _extract_cid(task: dict, fallback_text: str = "") -> str:
    metadata = _verifier_metadata(task)
    return (
        _extract_cid_from_values(task.get("category"), metadata.get("cid"), _extract_categories(task), _extract_task_id(task), fallback_text)
        or "unknown"
    )


def build_task_manifest(tasks: list[dict], tasks_path: Path) -> list[dict]:
    """Small task index without copying heavy context blobs into run metadata."""
    rows = []
    fallback = str(tasks_path)
    for idx, task in enumerate(tasks):
        metadata = _verifier_metadata(task)
        task_id = _extract_task_id(task)
        rows.append({
            "index": idx,
            "task_id": task_id,
            "short_task_id": _short_task_id(task_id),
            "cid": _extract_cid(task, fallback),
            "categories": _extract_categories(task),
            "difficulty": task.get("difficulty") or metadata.get("difficulty"),
        })
    return rows


def _task_cid_lookup(task_manifest: list[dict]) -> dict[str, str]:
    lookup = {}
    for row in task_manifest:
        cid = row.get("cid") or "unknown"
        task_id = row.get("task_id") or "unknown"
        short = row.get("short_task_id") or _short_task_id(task_id)
        lookup[task_id] = cid
        lookup[short] = cid
    return lookup


def _infer_skill_scope(seed_skill_path: Path, task_manifest: list[dict]) -> str:
    if len(task_manifest) == 1:
        return "per_task"
    cids = sorted({row.get("cid") for row in task_manifest if row.get("cid")})
    seed_cid = _extract_cid_from_values(seed_skill_path.name)
    if seed_cid and (not cids or cids == [seed_cid]):
        return "per_cid"
    if seed_cid:
        return "cid_named_seed_for_multi_cid_run"
    if len(cids) <= 1:
        return "single_scope"
    return "shared_across_cids"


def _single_task_alias(task_manifest: list[dict]) -> str | None:
    """Return a filesystem-safe task alias for one-task optimization runs."""
    if len(task_manifest) != 1:
        return None
    short = str(task_manifest[0].get("short_task_id") or "task")
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", short).strip("_") or "task"


def _skill_scope_record(seed_skill_path: Path, task_manifest: list[dict]) -> dict:
    """Describe exactly what skill lineage this run is optimizing."""
    cids = sorted({row.get("cid") for row in task_manifest if row.get("cid")})
    scope = _infer_skill_scope(seed_skill_path, task_manifest)
    record = {
        "skill_scope": scope,
        "seed_skill_path": str(seed_skill_path),
        "task_count": len(task_manifest),
        "cids": cids,
        "tasks": task_manifest,
    }
    if scope == "per_task" and task_manifest:
        task = task_manifest[0]
        record.update({
            "task_id": task.get("task_id"),
            "short_task_id": task.get("short_task_id"),
            "task_alias": _single_task_alias(task_manifest),
            "cid": task.get("cid"),
            "lineage": "common CID seed skill -> task-specific evolved skill",
        })
    return record


def _task_only_scope_record(task_manifest: list[dict]) -> dict | None:
    """Compact per-task scope record for generation-local artifacts."""
    if len(task_manifest) != 1:
        return None
    task = task_manifest[0]
    return {
        "skill_scope": "per_task",
        "task_id": task.get("task_id"),
        "short_task_id": task.get("short_task_id"),
        "task_alias": _single_task_alias(task_manifest),
        "cid": task.get("cid"),
        "lineage": "common CID seed skill -> task-specific evolved skill",
    }


def run_preflight_checks(
    *,
    output_dir: Path,
    seed_skill_path: Path,
    seed_skill: str,
    tasks_path: Path,
    tasks_data: list[dict],
    task_manifest: list[dict],
    config: dict,
) -> dict:
    """Validate run inputs before spending compute on rollouts.

    The optimizer may run for many hours, so this check is intentionally
    fail-fast. It catches stale materialized prompts, hidden harness leakage,
    missing rollout tools, and seed-skill guidance the rollout agent cannot
    actually execute.
    """
    cfg = {
        "enabled": True,
        "fail_on_warnings": False,
        "require_edit_tool": True,
        "require_skill_file": True,
        "forbid_xcelium": False,
        **(config.get("preflight") or {}),
    }
    errors: list[str] = []
    warnings: list[str] = []

    def err(where: str, message: str) -> None:
        errors.append(f"{where}: {message}")

    def warn(where: str, message: str) -> None:
        warnings.append(f"{where}: {message}")

    if not cfg.get("enabled", True):
        report = {
            "enabled": False,
            "status": "skipped",
            "errors": [],
            "warnings": [],
        }
        _write_json(output_dir / "preflight_report.json", report)
        return report

    if not tasks_data:
        err(str(tasks_path), "task file is empty")
    if not seed_skill.strip():
        err(str(seed_skill_path), "seed skill is empty")
    if len(seed_skill.strip()) < 100:
        warn(str(seed_skill_path), "seed skill is very short; mutation may have little structure to preserve")

    for line_num, line in enumerate(seed_skill.splitlines(), start=1):
        where = f"{seed_skill_path}:{line_num}"
        if "test_runner.py" in line.lower() or "harness/" in line.lower():
            if not _is_negative_directive(line):
                err(where, "seed skill exposes hidden harness/test_runner path")
        if _line_mentions_hidden_harness_action(line):
            err(where, "seed skill tells the rollout agent to run or invoke hidden harness infrastructure")

    seen_task_ids: set[str] = set()
    for idx, task in enumerate(tasks_data):
        task_id = _extract_task_id(task)
        where = f"{tasks_path}:task[{idx}]"
        if task_id in seen_task_ids:
            err(where, f"duplicate task_id in run input: {task_id}")
        seen_task_ids.add(task_id)

        params = task.get("responses_create_params")
        if not isinstance(params, dict):
            err(where, "missing responses_create_params")
            continue

        inputs = params.get("input")
        if not isinstance(inputs, list) or len(inputs) < 2:
            err(where, "responses_create_params.input must include developer and user messages")
        else:
            joined = "\n".join(
                item.get("content", "")
                for item in inputs
                if isinstance(item, dict) and isinstance(item.get("content"), str)
            )
            for marker in GENERATED_TESTBENCH_HINT_MARKERS:
                if marker in joined:
                    err(where, f"prompt contains deprecated generated testbench hint marker: {marker!r}")
            if PYTHON_IVERILOG_RE.search(joined):
                err(where, "prompt tells the agent to pass Python/cocotb/pytest files to iverilog")
            if HIDDEN_PROMPT_PATH_RE.search(joined):
                err(where, "prompt exposes hidden harness/test_runner path")
            if cfg.get("forbid_xcelium", False) and re.search(r"\b(xcelium|xrun|cadence)\b", joined, re.IGNORECASE):
                err(where, "OSS-only preflight forbids prompt/tool guidance mentioning xcelium/xrun/cadence")

        tools = params.get("tools")
        if not isinstance(tools, list):
            err(where, "responses_create_params.tools must be a list")
            tool_names: set[str] = set()
        else:
            tool_names = {
                str(tool.get("name"))
                for tool in tools
                if isinstance(tool, dict) and tool.get("name")
            }
            missing = REQUIRED_ROLLOUT_TOOLS - tool_names
            if missing:
                err(where, f"missing required rollout tools: {sorted(missing)}")
            if cfg.get("require_edit_tool", True) and "edit" not in tool_names:
                err(where, "edit tool is required for this optimizer configuration")
            if cfg.get("require_verify_feedback_tool", False) and "verify_feedback" not in tool_names:
                err(where, "runtime dense verifier feedback is enabled, but verify_feedback tool is missing")
            if not cfg.get("allow_verify_feedback_tool", False) and "verify_feedback" in tool_names:
                warn(where, "verify_feedback tool is visible even though preflight.allow_verify_feedback_tool is false")
            unsupported = sorted(name for name in tool_names if name not in SUPPORTED_ROLLOUT_TOOLS)
            if unsupported:
                err(where, f"unsupported rollout tools: {unsupported}")
            if cfg.get("forbid_xcelium", False) and "xcelium" in tool_names:
                err(where, "OSS-only preflight forbids exposing the xcelium tool to the rollout agent")

        metadata = _verifier_metadata(task)
        if not metadata:
            err(where, "missing verifier_metadata")
            continue
        if cfg.get("forbid_xcelium", False):
            harness_files = metadata.get("harness_files") or {}
            if isinstance(harness_files, dict):
                harness_text = "\n".join(
                    str(value)
                    for key, value in harness_files.items()
                    if key.endswith(("docker-compose.yml", ".env", "process.py", "test_runner.py"))
                )
                if re.search(r"\b(xrun|xcelium|cadence)\b", harness_text, re.IGNORECASE):
                    err(where, "OSS-only preflight forbids xrun/xcelium/cadence in verifier harness")
        context_files = metadata.get("context_files")
        if not isinstance(context_files, dict) or not context_files:
            err(where, "verifier_metadata.context_files must be a non-empty object")
        else:
            hidden = sorted(path for path in context_files if _hidden_verifier_path(path))
            if hidden:
                err(where, f"context_files exposes hidden verifier/harness paths: {hidden[:5]}")
            if cfg.get("require_skill_file", True) and "SKILL.md" not in context_files:
                warn(where, "context_files does not contain SKILL.md before injection; optimizer will inject it")
        categories = _extract_categories(task)
        cid = _extract_cid(task, str(tasks_path))
        if cid == "unknown":
            warn(where, f"could not infer CID from task_id/categories/path: {task_id}, {categories}")

    cids = sorted({row.get("cid") for row in task_manifest if row.get("cid")})
    report = {
        "enabled": True,
        "status": "failed" if errors or (warnings and cfg.get("fail_on_warnings")) else "ok",
        "tasks_path": str(tasks_path),
        "task_count": len(tasks_data),
        "task_ids": [row.get("task_id") for row in task_manifest],
        "cids": cids,
        "skill_scope": _infer_skill_scope(seed_skill_path, task_manifest),
        "task_alias": _single_task_alias(task_manifest),
        "seed_skill_path": str(seed_skill_path),
        "seed_skill_sha256": _sha256_text(seed_skill),
        "seed_skill_chars": len(seed_skill),
        "required_tools": sorted(REQUIRED_ROLLOUT_TOOLS),
        "errors": errors,
        "warnings": warnings,
        "config": cfg,
    }
    _write_json(output_dir / "preflight_report.json", report)

    if report["status"] == "failed":
        shown = "\n".join(f"  - {msg}" for msg in (errors or warnings)[:20])
        extra = "" if len(errors) + len(warnings) <= 20 else f"\n  ... and {len(errors) + len(warnings) - 20} more"
        raise RuntimeError(
            "Preflight validation failed; refusing to start rollouts.\n"
            f"{shown}{extra}\n"
            f"See {output_dir / 'preflight_report.json'}"
        )
    return report


def write_initial_skill_artifacts(
    output_dir: Path,
    seed_skill_path: Path,
    seed_skill: str,
    tasks_path: Path,
    task_manifest: list[dict],
) -> None:
    """Snapshot the seed skill and task/CID mapping at run start."""
    skill_snapshot = output_dir / "initial_skill.md"
    skill_snapshot.write_text(seed_skill, encoding="utf-8")
    cids = sorted({row.get("cid") for row in task_manifest if row.get("cid")})
    scope_record = _skill_scope_record(seed_skill_path, task_manifest)
    _write_json(output_dir / "initial_skill_meta.json", {
        "seed_skill_path": str(seed_skill_path),
        "snapshot_path": "initial_skill.md",
        "sha256": _sha256_text(seed_skill),
        "length_chars": len(seed_skill),
        "skill_scope": scope_record["skill_scope"],
        "scope": scope_record,
        "tasks_path": str(tasks_path),
        "task_count": len(task_manifest),
        "cids": cids,
        "tasks": task_manifest,
    })


def write_artifact_manifest(output_dir: Path) -> None:
    """Document the artifact contract expected by posthoc analysis."""
    _write_json(output_dir / "artifact_manifest.json", {
        "schema_version": 1,
        "purpose": "Traceability contract for Trace2Skill skill optimization runs. The run may be per-task, per-CID, or shared, as declared in initial_skill_meta.json and run_config.json.",
        "artifacts": {
            "preflight_fail_fast_validation": {
                "path": "preflight_report.json",
                "note": "Run refuses to start if materialized tasks expose hidden harness paths, stale generated testbench hints, missing required tools/edit, or impossible seed-skill guidance.",
            },
            "initial_skill": {
                "snapshot": "initial_skill.md",
                "metadata": "initial_skill_meta.json",
                "note": "For per-task runs, this snapshots the common CID seed before the task-specific lineage starts.",
            },
            "per_generation_raw_rollouts": {
                "pattern": "gen<N>/rollouts/ind<I>/rollouts_gen<N>_ind<I>.jsonl",
                "injected_tasks_pattern": "gen<N>/rollouts/ind<I>/tasks_gen<N>_ind<I>.jsonl",
            },
            "per_rollout_success_failure_modes": {
                "path": "gen<N>/rollout_diagnostics.jsonl",
                "note": "One deterministic record per rollout with generation, CID, task, individual, repeat_index, outcome, phase, tools, error signatures, and verifier result.",
            },
            "per_generation_oracle_feedback": {
                "task_level": "gen<N>/task_insights/<cid>/<task>_{pass,fail}.md",
                "cid_level": "gen<N>/cid_synthesis/<cid>/{pass,fail}_synthesis.md",
                "cid_metrics": "gen<N>/cid_synthesis/<cid>/metrics.json",
                "cid_handoff": "gen<N>/cid_oracle_feedback/<cid>.md",
                "cross_task": "gen<N>/cross_task/{pass,fail}_synthesis.md",
                "handoff": "gen<N>/oracle_feedback.md",
                "index": "gen<N>/oracle_feedback_index.json",
                "per_cid_index": "gen<N>/oracle_feedback_by_cid.json",
            },
            "per_generation_skill_iterations": {
                "individual_skills": "gen<N>/individuals/ind<I>.md",
                "per_task_aliases": "gen<N>/individuals/gen<N>_task_<task>_ind<I>_skill.md and gen<N>/gen<N>_task_<task>_best_skill.md when skill_scope=per_task",
                "individual_metadata": "gen<N>/individuals/ind<I>_meta.json",
                "index": "gen<N>/skill_iterations_index.json",
                "best_skill": "gen<N>/best_skill.md",
                "sanitization": "gen<N>/skill_sanitization.jsonl",
                "mutation_handoff": "gen<N>/mutation_handoff.md",
                "skill_patch_plan": "gen<N>/skill_patch_plan.{json,md}",
                "skill_integration": "gen<N>/skill_integration.jsonl and gen<N>/skill_integration/child<I>_<stage>.json",
                "regression_reflection": "gen<N>/regression_reflection.md",
            },
            "parent_child_challengers": {
                "path": "gen<N>/parent_child_challengers.jsonl",
                "summary": "gen<N>/parent_child_challengers_summary.json",
                "note": "Legacy optional path. Standard EA disables extra challenger rollouts so each generation has one evaluation phase.",
            },
            "semantic_survivor_selection": {
                "path": "gen<N>/semantic_survivor_selection.json",
                "note": "Legacy optional path. Standard EA carries the evaluated survivor and evaluates all children before any child can survive.",
            },
            "semantic_skill_selection": {
                "path": "gen<N>/semantic_skill_selection.jsonl and gen<N>/ea_survivor_decision.json",
                "run_level": "semantic_skill_selection.jsonl and semantic_incumbent.md",
                "note": "In standard EA mode, semantic records audit sanitized children but child selection is deferred until next-generation rollouts. gen<N>/ea_survivor_decision.json records the evaluated survivor.",
            },
            "skill_change_attribution": {
                "manifest": "gen<N>/change_manifest.json",
                "per_individual_manifest": "gen<N>/change_manifests/ind<I>.json",
                "evaluation": "gen<N>/change_evaluation.json",
                "human_readable": "gen<N>/change_evaluation.md",
                "latest": "latest_change_evaluation.json",
                "note": "AHE-style attribution: records what incoming skill changes were expected to fix, then compares them against this generation's per-task and dense metrics.",
            },
            "persistent_lesson_bank": {
                "run_level": "lesson_bank.{json,md}",
                "per_generation_snapshot": "gen<N>/lesson_bank.{json,md}",
                "final_best_performing_skill": "best_performing_skill.md",
                "final_distilled_skill": "distilled_final_skill.md",
                "compatibility_export": "optimized_skill.md",
                "per_task_exports": "optimized_skill_task_<task>.md, best_performing_skill_task_<task>.md, and distilled_final_skill_task_<task>.md when skill_scope=per_task",
                "metadata": "optimized_skill_meta.json",
                "note": "Durable oracle/path/change-attribution lessons are preserved even when best-performing fitness selects an older parent; optimized_skill.md exports the distilled final skill for downstream eval.",
            },
            "fitness_metric_telemetry": {
                "per_individual": "gen<N>/individuals/ind<I>_meta.json",
                "per_generation": "gen<N>/generation_metrics.json",
                "confidence_intervals": "gen<N>/generation_metrics.json includes Wilson 95% CIs for rollout pass rates and mean 95% CIs for selection/pass/progress summaries.",
                "run_history": "optimization_history.json",
                "live_dashboard": "live_dashboard.json",
                "timing_debug_mode": "gen<N>/timing.json",
            },
        },
    })


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(rec, dict):
                rows.append(rec)
    return rows


def _parse_call_args(call: dict) -> dict:
    args_raw = call.get("arguments") or {}
    if isinstance(args_raw, dict):
        return args_raw
    if isinstance(args_raw, str):
        try:
            parsed = json.loads(args_raw)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _tool_summary(call: dict) -> dict:
    name = call.get("name") or "unknown"
    args = _parse_call_args(call)
    if name in ("cat", "echo", "edit"):
        target = args.get("filename") or args.get("path")
    elif name in ("ls", "restore_file"):
        target = args.get("path") or args.get("filename")
    elif name in ("iverilog", "xcelium"):
        target = args.get("args")
    elif name == "vvp":
        target = args.get("filename")
    else:
        target = args.get("filename") or args.get("path") or args.get("args")
    return {
        "name": name,
        "target": str(target)[:300] if target is not None else None,
    }


def _tool_output_text(item: dict) -> str:
    output = item.get("output", "")
    if isinstance(output, str):
        try:
            parsed = json.loads(output)
            if isinstance(parsed, dict):
                return str(parsed.get("output", output))
        except Exception:
            return output
    return str(output)


def _extract_error_signatures(fn_outputs: list[dict], docker_stderr: str) -> list[str]:
    signatures = []
    needles = (
        "error:", "syntax error", "not found", "unknown module", "timed out",
        "fail", "assertion", "exception", "network", "could not be found",
    )
    for item in fn_outputs:
        text = _tool_output_text(item)
        low = text.lower()
        if any(n in low for n in needles):
            clean = " ".join(text.strip().split())
            if clean:
                signatures.append(clean[:500])
    if docker_stderr:
        clean = " ".join(docker_stderr.strip().split())
        if clean:
            signatures.append(clean[-500:])
    deduped = []
    seen = set()
    for sig in signatures:
        if sig in seen:
            continue
        seen.add(sig)
        deduped.append(sig)
    return deduped[:8]


def _phase_from_tools(tool_names: list[str]) -> str:
    names = set(tool_names)
    if "vvp" in names:
        return "P4-tested"
    if "iverilog" in names or "xcelium" in names:
        return "P3-compiled"
    if "echo" in names or "edit" in names:
        return "P2-wrote-files"
    if "cat" in names or "ls" in names:
        return "P1-explored"
    return "P0-no-tools"


def _mode_from_rollout(reward: float, phase: str, tool_names: list[str], error_signatures: list[str], docker_stderr: str) -> str:
    if reward > 0:
        return "pass"
    low_errors = "\n".join(error_signatures).lower()
    low_stderr = (docker_stderr or "").lower()
    if "network" in low_stderr and "external" in low_stderr:
        return "fail:verifier_environment"
    if phase == "P0-no-tools":
        return "fail:no_tools"
    if phase == "P1-explored":
        return "fail:exploration_only"
    if "echo" not in tool_names and "edit" not in tool_names:
        return "fail:no_file_modification"
    if "syntax error" in low_errors or "unknown module" in low_errors:
        return "fail:compile_error"
    if ("iverilog" in tool_names or "xcelium" in tool_names) and "vvp" not in tool_names:
        return "fail:no_simulation_after_compile"
    if "fail" in low_errors or "assertion" in low_errors:
        return "fail:simulation_or_assertion"
    return "fail:hidden_verifier_or_semantic"


def build_rollout_diagnostic(
    rollout: dict,
    generation: int,
    individual_index: int,
    rollout_index: int,
    cid_lookup: dict[str, str],
    parent_info: str = "",
    repeat_index: int | None = None,
) -> dict:
    response = rollout.get("response") or {}
    output_items = response.get("output") or []
    fn_calls = [o for o in output_items if isinstance(o, dict) and o.get("type") == "function_call"]
    fn_outputs = [o for o in output_items if isinstance(o, dict) and o.get("type") == "function_call_output"]
    call_name_by_id = {call.get("call_id") or call.get("id"): call.get("name") for call in fn_calls}
    relevant_outputs = [
        o for o in fn_outputs
        if call_name_by_id.get(o.get("call_id")) in ("iverilog", "vvp", "xcelium", "restore_file")
    ]
    tools = [_tool_summary(call) for call in fn_calls]
    tool_names = [t["name"] for t in tools]
    phase = _phase_from_tools(tool_names)
    docker_stderr = rollout.get("docker_stderr") or ""
    errors = _extract_error_signatures(relevant_outputs, docker_stderr)
    reward = float(rollout.get("reward", 0) or 0)
    task_id = rollout.get("task_id") or "unknown"
    cid = rollout.get("category") or cid_lookup.get(task_id) or cid_lookup.get(_short_task_id(task_id)) or "unknown"
    mode = _mode_from_rollout(reward, phase, tool_names, errors, docker_stderr)
    files_written = [
        t["target"] for t in tools
        if t["name"] in ("echo", "edit") and t.get("target")
    ]
    compile_commands = [
        t["target"] for t in tools
        if t["name"] in ("iverilog", "xcelium") and t.get("target")
    ]
    simulation_commands = [
        t["target"] for t in tools
        if t["name"] == "vvp" and t.get("target")
    ]
    path_grounding = analyze_path_grounding(
        rollout,
        files_written=files_written,
        compile_commands=compile_commands,
        reward=reward,
    )
    return {
        "generation": generation,
        "individual_index": individual_index,
        "parent_info": parent_info,
        "rollout_index": rollout_index,
        "repeat_index": repeat_index,
        "rollout_id": f"ind{individual_index}_r{rollout_index}",
        "task_id": task_id,
        "short_task_id": _short_task_id(task_id),
        "task_repeat_id": f"{_short_task_id(task_id)}#repeat{repeat_index}" if repeat_index is not None else None,
        "cid": cid,
        "outcome": "pass" if reward > 0 else "fail",
        "reward": reward,
        "mode": mode,
        "phase_reached": phase,
        "docker_exit_code": rollout.get("docker_exit_code"),
        "tests_passed": rollout.get("tests_passed"),
        "tests_total": rollout.get("tests_total"),
        "execution_time": rollout.get("execution_time"),
        "ng_task_index": rollout.get("_ng_task_index"),
        "ng_rollout_index": rollout.get("_ng_rollout_index"),
        "num_tool_calls": len(fn_calls),
        "tool_sequence": tool_names,
        "files_written": files_written[:20],
        "compile_commands": compile_commands[:10],
        "simulation_commands": simulation_commands[:10],
        "error_signatures": errors,
        "path_grounding": path_grounding,
        "docker_stderr_tail": docker_stderr[-1000:] if docker_stderr else "",
        "skill_monitor": rollout.get("skill_monitor") or rollout.get("skill_monitor_metrics") or {},
    }


def _individual_eval_index(ind: Individual, fallback: int) -> int:
    fr = getattr(ind, "fitness_result", None) or {}
    if fr.get("individual_index") is not None:
        try:
            return int(fr["individual_index"])
        except (TypeError, ValueError):
            pass
    rollout_path = fr.get("rollout_path")
    if rollout_path:
        match = re.search(r"/ind(\d+)/", str(rollout_path))
        if match:
            return int(match.group(1))
    return fallback


def _metric_summary(values: list[float]) -> dict:
    if not values:
        return {"best": 0.0, "mean": 0.0, "worst": 0.0, "mean_ci_95": {"low": 0.0, "high": 0.0, "n": 0}}
    return {
        "best": max(values),
        "mean": sum(values) / len(values),
        "worst": min(values),
        "mean_ci_95": _mean_ci_95(values),
    }


def _mean_ci_95(values: list[float]) -> dict:
    clean = [float(v) for v in values if isinstance(v, (int, float))]
    n = len(clean)
    if n == 0:
        return {"low": 0.0, "high": 0.0, "n": 0, "method": "none"}
    mean = sum(clean) / n
    if n == 1:
        return {"low": mean, "high": mean, "n": n, "method": "single_sample"}
    variance = sum((v - mean) ** 2 for v in clean) / (n - 1)
    half_width = 1.96 * math.sqrt(variance / n)
    return {
        "low": max(0.0, mean - half_width),
        "high": min(1.0, mean + half_width),
        "n": n,
        "method": "normal_approx_mean",
    }


def _wilson_ci_95(passes: int, attempts: int) -> dict:
    if attempts <= 0:
        return {"low": 0.0, "high": 0.0, "passes": 0, "attempts": 0, "method": "none"}
    z = 1.96
    n = float(attempts)
    phat = float(passes) / n
    denom = 1.0 + z * z / n
    centre = (phat + z * z / (2.0 * n)) / denom
    half = z * math.sqrt((phat * (1.0 - phat) + z * z / (4.0 * n)) / n) / denom
    return {
        "low": max(0.0, centre - half),
        "high": min(1.0, centre + half),
        "passes": int(passes),
        "attempts": int(attempts),
        "method": "wilson_95",
    }


def _component_means(population: list[Individual]) -> dict:
    buckets: dict[str, list[float]] = {}
    for ind in population:
        comps = (getattr(ind, "fitness_result", None) or {}).get("progress_components", {})
        if not isinstance(comps, dict):
            continue
        for key, val in comps.items():
            try:
                buckets.setdefault(key, []).append(float(val))
            except (TypeError, ValueError):
                continue
    return {key: sum(vals) / len(vals) for key, vals in sorted(buckets.items()) if vals}


def _aggregate_per_task(population: list[Individual], cid_lookup: dict[str, str]) -> dict:
    task_rows: dict[str, dict] = {}
    for ind in population:
        fr = getattr(ind, "fitness_result", None) or {}
        for tid, val in fr.get("per_task", {}).items():
            if isinstance(val, dict):
                pass_rate = float(val.get("pass_at_1", 0.0) or 0.0)
                pass_at_k = float(val.get("pass_at_k", 0.0) or 0.0)
                attempts = int(val.get("attempts", 0) or 0)
                passes = int(val.get("passes", 0) or 0)
            else:
                pass_rate = float(val)
                pass_at_k = pass_rate
                attempts = 0
                passes = 0
            short = _short_task_id(tid)
            row = task_rows.setdefault(short, {
                "task_id": tid,
                "short_task_id": short,
                "cid": cid_lookup.get(tid) or cid_lookup.get(short) or "unknown",
                "individual_pass_rates": [],
                "individual_pass_at_k": [],
                "attempts": 0,
                "passes": 0,
            })
            row["individual_pass_rates"].append(pass_rate)
            row["individual_pass_at_k"].append(pass_at_k)
            row["attempts"] += attempts
            row["passes"] += passes
    for row in task_rows.values():
        rates = row["individual_pass_rates"]
        pass_at_k = row["individual_pass_at_k"]
        row["mean_pass_rate"] = sum(rates) / len(rates) if rates else 0.0
        row["best_pass_rate"] = max(rates) if rates else 0.0
        row["mean_pass_at_k"] = sum(pass_at_k) / len(pass_at_k) if pass_at_k else 0.0
        row["mean_pass_rate_ci_95"] = _mean_ci_95(rates)
        row["rollout_pass_rate"] = (row["passes"] / row["attempts"]) if row["attempts"] else 0.0
        row["rollout_pass_rate_ci_95"] = _wilson_ci_95(row["passes"], row["attempts"])
    return dict(sorted(task_rows.items()))


def _aggregate_per_cid(per_task: dict) -> dict:
    buckets: dict[str, list[dict]] = {}
    for row in per_task.values():
        buckets.setdefault(row.get("cid") or "unknown", []).append(row)
    result = {}
    for cid, rows in sorted(buckets.items()):
        mean_rates = [float(row.get("mean_pass_rate", 0.0) or 0.0) for row in rows]
        best_rates = [float(row.get("best_pass_rate", 0.0) or 0.0) for row in rows]
        attempts = sum(int(row.get("attempts", 0) or 0) for row in rows)
        passes = sum(int(row.get("passes", 0) or 0) for row in rows)
        result[cid] = {
            "task_count": len(rows),
            "mean_pass_rate": sum(mean_rates) / len(mean_rates) if mean_rates else 0.0,
            "mean_pass_rate_ci_95": _mean_ci_95(mean_rates),
            "best_task_pass_rate": max(best_rates) if best_rates else 0.0,
            "attempts": attempts,
            "passes": passes,
            "rollout_pass_rate": (passes / attempts) if attempts else 0.0,
            "rollout_pass_rate_ci_95": _wilson_ci_95(passes, attempts),
            "tasks": [row.get("short_task_id") for row in rows],
        }
    return result


def write_generation_traceability_artifacts(
    gen_dir: Path,
    output_dir: Path,
    generation: int,
    population: list[Individual],
    task_manifest: list[dict],
    skill_scope: str,
) -> None:
    """Write deterministic per-gen indexes for skills, rollout modes, and metrics."""
    cid_lookup = _task_cid_lookup(task_manifest)
    cids = sorted({row.get("cid") for row in task_manifest if row.get("cid")})
    scope_record = _task_only_scope_record(task_manifest)

    rollout_diagnostics = []
    skill_rows = []
    for rank, ind in enumerate(population, start=1):
        eval_idx = _individual_eval_index(ind, rank - 1)
        fr = getattr(ind, "fitness_result", None) or {}
        rollout_path = Path(fr["rollout_path"]) if fr.get("rollout_path") else None
        if rollout_path:
            repeats_seen: dict[str, int] = {}
            for rollout_idx, rollout in enumerate(_load_jsonl(rollout_path)):
                task_key = rollout.get("task_id") or "unknown"
                repeat_idx = repeats_seen.get(task_key, 0)
                repeats_seen[task_key] = repeat_idx + 1
                rollout_diagnostics.append(build_rollout_diagnostic(
                    rollout=rollout,
                    generation=generation,
                    individual_index=eval_idx,
                    rollout_index=rollout_idx,
                    cid_lookup=cid_lookup,
                    parent_info=ind.parent_info,
                    repeat_index=repeat_idx,
                ))
        skill_rows.append({
            "generation": generation,
            "rank": rank,
            "individual_index": eval_idx,
            "parent_info": ind.parent_info,
            "skill_scope": skill_scope,
            "scope": scope_record if skill_scope == "per_task" else None,
            "cids": cids,
            "skill_path": _rel(gen_dir / "individuals" / f"ind{eval_idx}.md", output_dir),
            "task_skill_alias": (
                _rel(
                    gen_dir / "individuals" / f"gen{generation}_task_{scope_record.get('task_alias')}_ind{eval_idx}_skill.md",
                    output_dir,
                )
                if skill_scope == "per_task" and scope_record.get("task_alias")
                else None
            ),
            "metadata_path": _rel(gen_dir / "individuals" / f"ind{eval_idx}_meta.json", output_dir),
            "rollout_path": _rel(rollout_path, output_dir) if rollout_path else None,
            "fitness": ind.fitness,
            "pass_rate": fr.get("pass_at_1", 0.0),
            "pass_at_1": fr.get("pass_at_1", 0.0),
            "progress_fitness": fr.get("progress_fitness", 0.0),
            "raw_progress_fitness": fr.get("raw_progress_fitness"),
            "selection_fitness": fr.get("selection_fitness", ind.fitness),
            "selection_fitness_original": fr.get("selection_fitness_original"),
            "selection_fitness_breakdown": fr.get("selection_fitness_breakdown", {}),
            "skill_quality": fr.get("skill_quality"),
            "agent_behavior_quality": fr.get("agent_behavior_quality"),
            "rollout_variance_quality": fr.get("rollout_variance_quality"),
            "skill_adherence_quality": fr.get("skill_adherence_quality"),
            "progress_components": fr.get("progress_components", {}),
            "progress_rollout_scores": fr.get("progress_rollout_scores", []),
            "rollout_variance": fr.get("rollout_variance", {}),
            "path_grounding_fitness": fr.get("path_grounding_fitness", {}),
            "skill_monitor": fr.get("skill_monitor", {}),
            "num_rollouts": fr.get("num_rollouts", 0),
            "prompt_length": len(ind.prompt),
            "semantic_retention": ind.semantic_retention,
            "semantic_selection": ind.semantic_selection,
        })

    _append_jsonl(gen_dir / "rollout_diagnostics.jsonl", rollout_diagnostics)
    path_grounding_rows = [
        {
            "generation": row.get("generation"),
            "individual_index": row.get("individual_index"),
            "rollout_index": row.get("rollout_index"),
            "repeat_index": row.get("repeat_index"),
            "rollout_id": row.get("rollout_id"),
            "task_id": row.get("task_id"),
            "short_task_id": row.get("short_task_id"),
            "cid": row.get("cid"),
            "outcome": row.get("outcome"),
            "reward": row.get("reward"),
            "path_grounding": row.get("path_grounding"),
        }
        for row in rollout_diagnostics
        if (row.get("path_grounding") or {}).get("issues")
    ]
    _append_jsonl(gen_dir / "path_grounding.jsonl", path_grounding_rows)
    _write_json(gen_dir / "skill_iterations_index.json", {
        "generation": generation,
        "skill_scope": skill_scope,
        "scope": scope_record if skill_scope == "per_task" else None,
        "cids": cids,
        "individuals": skill_rows,
        "notes": "individual_index points to gen<N>/individuals/ind<I>.md; rank is after sorting by selection fitness.",
    })

    selection_values = [float(ind.fitness) for ind in population]
    pass_values = [
        float((getattr(ind, "fitness_result", None) or {}).get("pass_at_1", ind.fitness) or 0.0)
        for ind in population
    ]
    progress_values = [
        float((getattr(ind, "fitness_result", None) or {}).get("progress_fitness", 0.0) or 0.0)
        for ind in population
    ]
    skill_quality_values = [
        float((getattr(ind, "fitness_result", None) or {}).get("skill_quality", _skill_quality_from_individual(ind)) or 0.0)
        for ind in population
    ]
    behavior_quality_values = [
        float((getattr(ind, "fitness_result", None) or {}).get("agent_behavior_quality", 0.0) or 0.0)
        for ind in population
    ]
    variance_quality_values = [
        float((getattr(ind, "fitness_result", None) or {}).get("rollout_variance_quality", 0.0) or 0.0)
        for ind in population
    ]
    adherence_quality_values = [
        float((getattr(ind, "fitness_result", None) or {}).get("skill_adherence_quality", 0.0) or 0.0)
        for ind in population
    ]
    selected_validity = _skill_validity_from_individual(population[0]) if population else {}
    per_task = _aggregate_per_task(population, cid_lookup)
    total_attempts = sum(int(row.get("attempts", 0) or 0) for row in per_task.values())
    total_passes = sum(int(row.get("passes", 0) or 0) for row in per_task.values())
    _write_json(gen_dir / "generation_metrics.json", {
        "generation": generation,
        "skill_scope": skill_scope,
        "scope": scope_record if skill_scope == "per_task" else None,
        "cids": cids,
        "task_ids": [row.get("task_id") for row in task_manifest],
        "population_size": len(population),
        "selection_fitness": _metric_summary(selection_values),
        "pass_rate": _metric_summary(pass_values),
        "progress_fitness": _metric_summary(progress_values),
        "proof_metrics": {
            "skill_quality": _metric_summary(skill_quality_values),
            "agent_behavior_quality": _metric_summary(behavior_quality_values),
            "rollout_variance_quality": _metric_summary(variance_quality_values),
            "skill_adherence_quality": _metric_summary(adherence_quality_values),
            "selected_skill_validity": selected_validity,
            "invalid_skill_propagated": bool(selected_validity and not selected_validity.get("valid", True)),
            "semantic_floor_violations": sum(
                1
                for ind in population
                if ((getattr(ind, "fitness_result", None) or {}).get("selection_fitness_breakdown", {}) or {}).get("semantic_floor_violation")
            ),
        },
        "progress_component_means": _component_means(population),
        "confidence_intervals": {
            "selection_fitness_mean_ci_95": _mean_ci_95(selection_values),
            "pass_rate_mean_ci_95": _mean_ci_95(pass_values),
            "progress_fitness_mean_ci_95": _mean_ci_95(progress_values),
            "rollout_pass_rate_ci_95": _wilson_ci_95(total_passes, total_attempts),
        },
        "per_task": per_task,
        "per_cid": _aggregate_per_cid(per_task),
        "path_grounding": summarize_path_grounding_diagnostics(rollout_diagnostics),
        "semantic_survivor": {
            "candidates": [
                row.get("semantic_retention", {})
                for row in skill_rows
                if row.get("semantic_retention")
            ],
        },
        "semantic_skill_selection": {
            "decisions": [
                row.get("semantic_selection", {})
                for row in skill_rows
                if row.get("semantic_selection")
            ],
        },
        "artifact_paths": {
            "rollout_diagnostics": _rel(gen_dir / "rollout_diagnostics.jsonl", output_dir),
            "path_grounding": _rel(gen_dir / "path_grounding.jsonl", output_dir),
            "skill_iterations_index": _rel(gen_dir / "skill_iterations_index.json", output_dir),
            "semantic_survivor_selection": _rel(gen_dir / "semantic_survivor_selection.json", output_dir),
            "individuals_dir": _rel(gen_dir / "individuals", output_dir),
            "rollouts_dir": _rel(gen_dir / "rollouts", output_dir),
            "generation_metrics": _rel(gen_dir / "generation_metrics.json", output_dir),
        },
    })


def write_oracle_feedback_index(
    gen_dir: Path,
    output_dir: Path,
    generation: int,
    task_manifest: list[dict],
    status: str,
    oracle_feedback_path: Path | None = None,
) -> None:
    task_insights = sorted((gen_dir / "task_insights").rglob("*.md"))
    cross_task = sorted((gen_dir / "cross_task").glob("*.md"))
    cid_syntheses = sorted((gen_dir / "cid_synthesis").rglob("*.md"))
    cid_metrics = sorted((gen_dir / "cid_synthesis").rglob("metrics.json"))
    cid_handoffs = sorted((gen_dir / "cid_oracle_feedback").glob("*.md"))
    cid_lookup = _task_cid_lookup(task_manifest)
    per_cid: dict[str, dict] = {}
    for row in task_manifest:
        cid = row.get("cid") or "unknown"
        per_cid.setdefault(cid, {
            "cid": cid,
            "tasks": [],
            "layer1_task_insights": [],
            "layer2_cid_syntheses": [],
            "layer2_cid_metrics": [],
            "layer2_cross_task_syntheses": [_rel(p, output_dir) for p in cross_task],
            "layer3_cid_handoff": None,
            "layer3_oracle_handoff": _rel(oracle_feedback_path, output_dir) if oracle_feedback_path else None,
        })["tasks"].append(row)
    for path in task_insights:
        stem = path.stem
        task_key = stem.removesuffix("_pass").removesuffix("_fail")
        rel_parts = path.relative_to(gen_dir / "task_insights").parts
        cid = _extract_cid_from_values(rel_parts[0] if len(rel_parts) > 1 else None) or cid_lookup.get(task_key) or "unknown"
        per_cid.setdefault(cid, {
            "cid": cid,
            "tasks": [],
            "layer1_task_insights": [],
            "layer2_cid_syntheses": [],
            "layer2_cid_metrics": [],
            "layer2_cross_task_syntheses": [_rel(p, output_dir) for p in cross_task],
            "layer3_cid_handoff": None,
            "layer3_oracle_handoff": _rel(oracle_feedback_path, output_dir) if oracle_feedback_path else None,
        })["layer1_task_insights"].append(_rel(path, output_dir))
    for path in cid_syntheses:
        cid = _extract_cid_from_values(path.parent.name) or "unknown"
        per_cid.setdefault(cid, {
            "cid": cid,
            "tasks": [],
            "layer1_task_insights": [],
            "layer2_cid_syntheses": [],
            "layer2_cid_metrics": [],
            "layer2_cross_task_syntheses": [_rel(p, output_dir) for p in cross_task],
            "layer3_cid_handoff": None,
            "layer3_oracle_handoff": _rel(oracle_feedback_path, output_dir) if oracle_feedback_path else None,
        })["layer2_cid_syntheses"].append(_rel(path, output_dir))
    for path in cid_metrics:
        cid = _extract_cid_from_values(path.parent.name) or "unknown"
        per_cid.setdefault(cid, {
            "cid": cid,
            "tasks": [],
            "layer1_task_insights": [],
            "layer2_cid_syntheses": [],
            "layer2_cid_metrics": [],
            "layer2_cross_task_syntheses": [_rel(p, output_dir) for p in cross_task],
            "layer3_cid_handoff": None,
            "layer3_oracle_handoff": _rel(oracle_feedback_path, output_dir) if oracle_feedback_path else None,
        })["layer2_cid_metrics"].append(_rel(path, output_dir))
    for path in cid_handoffs:
        cid = _extract_cid_from_values(path.stem) or "unknown"
        per_cid.setdefault(cid, {
            "cid": cid,
            "tasks": [],
            "layer1_task_insights": [],
            "layer2_cid_syntheses": [],
            "layer2_cid_metrics": [],
            "layer2_cross_task_syntheses": [_rel(p, output_dir) for p in cross_task],
            "layer3_cid_handoff": None,
            "layer3_oracle_handoff": _rel(oracle_feedback_path, output_dir) if oracle_feedback_path else None,
        })["layer3_cid_handoff"] = _rel(path, output_dir)
    by_cid_path = gen_dir / "oracle_feedback_by_cid.json"
    _write_json(by_cid_path, {
        "generation": generation,
        "status": status,
        "per_cid": dict(sorted(per_cid.items())),
    })
    _write_json(gen_dir / "oracle_feedback_index.json", {
        "generation": generation,
        "status": status,
        "tasks": task_manifest,
        "layer1_task_insights": [_rel(p, output_dir) for p in task_insights],
        "layer2_cid_syntheses": [_rel(p, output_dir) for p in cid_syntheses],
        "layer2_cid_metrics": [_rel(p, output_dir) for p in cid_metrics],
        "layer2_cross_task_syntheses": [_rel(p, output_dir) for p in cross_task],
        "layer3_cid_handoffs": [_rel(p, output_dir) for p in cid_handoffs],
        "layer3_oracle_handoff": _rel(oracle_feedback_path, output_dir) if oracle_feedback_path else None,
        "per_cid_index": _rel(by_cid_path, output_dir),
        "expected_layer3_path": _rel(gen_dir / "oracle_feedback.md", output_dir),
    })


def sanitize_feedback_artifact_for_mutation(
    *,
    text: str | None,
    path: Path | None,
    gen_dir: Path,
    generation: int,
    execution_contract,
    source: str,
    report_name: str,
) -> tuple[str | None, dict | None]:
    """Sanitize final oracle/mutation feedback before mutator consumption.

    Layer 1/2 artifacts may mention hidden verifier failures or repository
    harnesses as *evidence*. The mutator input is different: it must contain
    only actions the rollout agent can actually take. This helper rewrites the
    final handoff text, overwrites the handoff artifact when needed, and writes
    a compact audit report.
    """
    if not text:
        return text, None

    result = sanitize_feedback_for_execution_contract(
        text,
        execution_contract,
        source=source,
    )
    report = {
        "generation": generation,
        "source": source,
        "path": _rel(path, gen_dir) if path else None,
        **result.to_record(),
    }
    _write_json(gen_dir / report_name, report)
    if result.changed:
        if path is not None:
            path.write_text(result.text, encoding="utf-8")
        print(
            f"    [feedback-sanitizer] {source}: rewrote {len(result.rewrites)} "
            f"unavailable instruction(s) → {report_name}"
        )
    return result.text, report


def sanitize_cid_oracle_handoffs(
    *,
    gen_dir: Path,
    generation: int,
    execution_contract,
) -> list[dict]:
    """Sanitize per-CID final handoffs for traceability parity.

    The combined `oracle_feedback.md` is what mutation reads, but readers also
    inspect `cid_oracle_feedback/<cid>.md`. Keep those final handoffs under the
    same execution-contract filter so artifacts do not teach unavailable
    actions even when the combined handoff is clean.
    """
    records: list[dict] = []
    for cid_path in sorted((gen_dir / "cid_oracle_feedback").glob("*.md")):
        text = cid_path.read_text(encoding="utf-8")
        result = sanitize_feedback_for_execution_contract(
            text,
            execution_contract,
            source=f"cid_oracle_feedback:{cid_path.stem}",
        )
        record = {
            "generation": generation,
            "cid": cid_path.stem,
            "path": _rel(cid_path, gen_dir),
            **result.to_record(),
        }
        records.append(record)
        if result.changed:
            cid_path.write_text(result.text, encoding="utf-8")
    if records:
        _write_json(gen_dir / "cid_oracle_feedback_sanitization.json", records)
    return records


def _should_challenge_child(ind: Individual, challenger_cfg: dict) -> tuple[bool, str]:
    if not challenger_cfg.get("enabled", True):
        return False, "disabled"
    if not ind.parent_prompt:
        return False, "no_parent_snapshot"
    if _sha256_text(ind.prompt) == _sha256_text(ind.parent_prompt):
        return False, "unchanged_from_parent"

    trigger = str(challenger_cfg.get("trigger", "on_regression"))
    child_score = _score_from_result(ind.fitness_result, ind.fitness)
    child_pass = _pass_from_result(ind.fitness_result, 0.0)
    parent_score = ind.parent_fitness if ind.parent_fitness is not None else _score_from_result(ind.parent_fitness_result, 0.0)
    parent_pass = _pass_from_result(ind.parent_fitness_result, 0.0)

    if trigger == "always":
        return True, "always"

    selection_drop = float(challenger_cfg.get("selection_drop", 0.02))
    pass_drop = float(challenger_cfg.get("pass_drop", 0.001))
    if parent_score is not None and child_score < float(parent_score) - selection_drop:
        return True, f"selection_regression:{child_score:.4f}<{float(parent_score):.4f}"
    if child_pass < parent_pass - pass_drop:
        return True, f"pass_regression:{child_pass:.4f}<{parent_pass:.4f}"
    return False, "no_regression_trigger"


def run_parent_child_challengers(
    *,
    population: list[Individual],
    generation: int,
    gen_dir: Path,
    challenger_cfg: dict,
    tasks_data: list[dict],
    ng_collect_bin: str,
    agent_name: str,
    num_repeats: int,
    num_parallel: int,
    fitness_timeout: int,
    eval_llm_cfg: dict,
    run_analyzer_flag: bool,
    repo_root: Path,
    nemogym_root: str | None,
    ng_config_paths: list[str] | None,
    rollout_model_cfg: dict,
    skill_monitor_cfg: dict,
    runtime_verifier_feedback_cfg: dict,
    dry_run: bool,
) -> list[dict]:
    """Evaluate a regressed child against its parent before accepting it.

    The standard generation evaluation tells us how the child performed. When
    that looks worse than its parent baseline, this challenger re-runs the
    parent under the same rollout configuration and restores the parent only if
    it wins the direct comparison. This is deliberately conservative and
    limited by max_per_generation because it can add real rollout cost.
    """
    records: list[dict] = []
    if dry_run or not challenger_cfg.get("enabled", True):
        return records

    max_challenges = int(challenger_cfg.get("max_per_generation", 1) or 0)
    if max_challenges <= 0:
        return records

    challenges_run = 0
    for idx, ind in enumerate(list(population)):
        should_challenge, reason = _should_challenge_child(ind, challenger_cfg)
        child_score = _score_from_result(ind.fitness_result, ind.fitness)
        child_pass = _pass_from_result(ind.fitness_result, 0.0)
        parent_cached_score = ind.parent_fitness if ind.parent_fitness is not None else _score_from_result(ind.parent_fitness_result, 0.0)
        parent_cached_pass = _pass_from_result(ind.parent_fitness_result, 0.0)
        base_record = {
            "generation": generation,
            "individual_index": idx,
            "child_parent_info": ind.parent_info,
            "child_origin": ind.child_origin,
            "child_sha256": _sha256_text(ind.prompt),
            "parent_sha256": ind.parent_sha256,
            "trigger_reason": reason,
            "child_selection_fitness": child_score,
            "child_pass_at_1": child_pass,
            "cached_parent_selection_fitness": parent_cached_score,
            "cached_parent_pass_at_1": parent_cached_pass,
        }
        if not should_challenge:
            continue
        if challenges_run >= max_challenges:
            records.append({**base_record, "status": "skipped", "decision": "keep_child", "skip_reason": "max_per_generation_reached"})
            continue

        challenges_run += 1
        trial_id = f"gen{generation}_ind{idx}_parent_challenger"
        work_dir = gen_dir / "challengers" / f"ind{idx}_parent"
        print(f"    Challenger: evaluating parent for child ind{idx} ({reason})")
        parent_result = evaluate_prompt(
            skill_text=ind.parent_prompt or "",
            tasks=tasks_data,
            ng_collect_bin=ng_collect_bin,
            work_dir=work_dir,
            agent_name=agent_name,
            num_repeats=num_repeats,
            num_parallel=num_parallel,
            timeout=fitness_timeout,
            trial_id=trial_id,
            eval_llm_cfg=eval_llm_cfg,
            run_analyzer_flag=run_analyzer_flag,
            repo_root=repo_root,
            nemogym_root=nemogym_root,
            ng_config_paths=ng_config_paths,
            rollout_model_cfg=rollout_model_cfg,
            skill_monitor_cfg=skill_monitor_cfg,
            runtime_verifier_feedback_cfg=runtime_verifier_feedback_cfg,
        )
        parent_score = _score_from_result(parent_result, 0.0)
        parent_pass = _pass_from_result(parent_result, 0.0)
        restore_selection_margin = float(challenger_cfg.get("restore_selection_margin", 0.0))
        restore_pass_margin = float(challenger_cfg.get("restore_pass_margin", 0.0))
        parent_wins = (
            parent_pass > child_pass + restore_pass_margin
            or parent_score > child_score + restore_selection_margin
        )
        decision = "restore_parent" if parent_wins else "keep_child"
        record = {
            **base_record,
            "status": "challenged",
            "decision": decision,
            "parent_trial_id": trial_id,
            "parent_rollout_path": parent_result.get("rollout_path"),
            "parent_selection_fitness": parent_score,
            "parent_pass_at_1": parent_pass,
            "parent_progress_fitness": parent_result.get("progress_fitness", 0.0),
            "child_progress_fitness": ind.fitness_result.get("progress_fitness", 0.0),
        }
        if parent_wins:
            survivor = Individual(
                ind.parent_prompt or "",
                generation=generation,
                parent_info=f"challenger_parent_survivor_for_ind{idx}",
            )
            survivor.fitness = parent_score
            survivor.fitness_result = parent_result
            survivor.challenger_decision = record
            population[idx] = survivor
            print(
                f"      → restored parent "
                f"(parent selection={parent_score:.3f}, pass={parent_pass:.3f}; "
                f"child selection={child_score:.3f}, pass={child_pass:.3f})"
            )
        else:
            ind.challenger_decision = record
            print(
                f"      → kept child "
                f"(parent selection={parent_score:.3f}, pass={parent_pass:.3f}; "
                f"child selection={child_score:.3f}, pass={child_pass:.3f})"
            )
        records.append(record)

    if records:
        _append_jsonl(gen_dir / "parent_child_challengers.jsonl", records)
        _write_json(gen_dir / "parent_child_challengers_summary.json", {
            "generation": generation,
            "config": challenger_cfg,
            "challenged": sum(1 for r in records if r.get("status") == "challenged"),
            "restored_parent": sum(1 for r in records if r.get("decision") == "restore_parent"),
            "kept_child": sum(1 for r in records if r.get("decision") == "keep_child"),
            "artifact": "parent_child_challengers.jsonl",
        })
    return records


def _build_parent_preserving_salvage_candidate(
    *,
    parent_prompt: str,
    candidate_report: dict,
    patch_plan: dict | None,
    max_lessons: int = 10,
) -> tuple[str | None, dict]:
    """Build a conservative fallback candidate from a flawed mutation.

    A raw mutator proposal can contain useful rollout-mined lessons and still
    fail the integration gate because it drops a parent rule, adds a
    contradiction, or over-compresses. Throwing the whole child away loses signal.
    This helper keeps the current parent as the floor and appends only the
    oracle directives that the flawed child demonstrably covered better than
    the parent. The normal sanitizer/integration/semantic-selector gates still
    run afterward, so this is a salvage attempt, not an unconditional accept.
    """
    plan = dict(patch_plan or {})
    if not plan.get("has_feedback"):
        return None, {"attempted": False, "reason": "no_oracle_feedback"}

    directive_rows = candidate_report.get("directive_results") or []
    parent_rows = {
        row.get("directive"): row
        for row in candidate_report.get("parent_directive_results") or []
        if row.get("directive")
    }
    salvaged: list[str] = []
    seen: set[str] = set()
    for row in directive_rows:
        directive = str(row.get("directive") or "").strip()
        if not directive or directive in seen:
            continue
        parent_covered = bool((parent_rows.get(directive) or {}).get("covered"))
        if row.get("covered") and not parent_covered:
            seen.add(directive)
            salvaged.append(directive)
        if len(salvaged) >= max_lessons:
            break

    if not salvaged:
        return None, {
            "attempted": False,
            "reason": "no_child_covered_new_directives",
            "child_issues": candidate_report.get("issues", []),
        }

    concrete_terms = [
        str(term).strip()
        for term in plan.get("concrete_terms") or []
        if str(term).strip()
    ][:8]
    lines = [
        parent_prompt.rstrip(),
        "",
        "## Recent Rollout-Grounded Lessons",
        "",
        "These lessons were salvaged from a flawed child proposal. Preserve the parent rules above, and use these additions only when they are executable with the available rollout tools.",
    ]
    lines.extend(f"- {item}" for item in salvaged)
    if concrete_terms:
        lines.extend(["", "### Concrete Terms To Preserve"])
        lines.extend(f"- {term}" for term in concrete_terms)

    return "\n".join(lines).strip() + "\n", {
        "attempted": True,
        "reason": "parent_floor_plus_child_covered_directives",
        "salvaged_directives": salvaged,
        "concrete_terms": concrete_terms,
        "child_issues": candidate_report.get("issues", []),
        "child_metrics": candidate_report.get("metrics", {}),
    }


def process_candidate_skill_for_injection(
    *,
    client: openai.OpenAI,
    mutation_model: str,
    objective: str,
    output_dir: Path,
    generation: int,
    child_slot: int,
    parent_info: str,
    stage: str,
    candidate: str,
    parent_prompt: str,
    max_skill_length: int,
    sanitizer_cfg: dict,
    execution_contract,
    execution_constraints_text: str,
    skill_patch_plan_text: str | None,
    skill_patch_plan: dict | None,
    integration_cfg: dict,
    repair_cfg: dict,
    audit_logger: LLMAuditLogger | None,
    context: dict | None = None,
) -> tuple[str, dict]:
    """Sanitize, semantically validate, and optionally repair a child skill.

    This is the single acceptance gate for a raw LLM-generated skill before it
    can be injected into the next generation. The order is deliberate:

      raw mutation -> sanitizer/condense -> oracle integration check
      -> optional targeted repair -> final integration check

    The sanitizer guards executability; the integration check guards whether
    the oracle's evidence survived the rewrite.
    """
    sanitized_prompt, sanitizer_record = _sanitize_candidate_skill(
        output_dir=output_dir,
        generation=generation,
        child_slot=child_slot,
        parent_info=parent_info,
        stage=stage,
        candidate=candidate,
        parent_prompt=parent_prompt,
        max_skill_length=max_skill_length,
        sanitizer_cfg=sanitizer_cfg,
        execution_contract=execution_contract,
    )
    integration_report = validate_skill_integration(
        candidate_skill=sanitized_prompt,
        parent_skill=parent_prompt,
        patch_plan=skill_patch_plan,
        execution_contract=execution_contract,
        config=integration_cfg,
    )
    write_skill_integration_report(
        output_dir,
        generation,
        child_slot,
        {
            "stage": stage,
            "status": "ok" if integration_report["ok"] else "needs_repair",
            "parent_info": parent_info,
            "repair_attempted": False,
            "report": integration_report,
        },
    )

    repaired = False
    repair_sanitizer_record = None
    semantic_sanitizer_record = None
    salvage_sanitizer_record = None
    semantic_repairs: list[dict] = []
    salvage_record: dict | None = None

    def _try_semantic_repair(current_prompt: str, current_report: dict, repair_stage: str) -> tuple[str, dict]:
        nonlocal semantic_sanitizer_record
        if current_report.get("ok") or "semantic_contradiction" not in (current_report.get("issues") or []):
            return current_prompt, current_report
        repaired_text, semantic_record = repair_semantic_contradictions(current_prompt, execution_contract)
        semantic_repairs.append({"stage": repair_stage, **semantic_record})
        if not semantic_record.get("changed"):
            write_skill_integration_report(
                output_dir,
                generation,
                child_slot,
                {
                    "stage": repair_stage,
                    "status": "failed",
                    "parent_info": parent_info,
                    "repair_attempted": True,
                    "repair_kind": "deterministic_semantic_scrub",
                    "semantic_repair": semantic_record,
                    "report": current_report,
                },
            )
            return current_prompt, current_report

        repaired_prompt, semantic_sanitizer_record = _sanitize_candidate_skill(
            output_dir=output_dir,
            generation=generation,
            child_slot=child_slot,
            parent_info=parent_info,
            stage=repair_stage,
            candidate=repaired_text,
            parent_prompt=parent_prompt,
            max_skill_length=max_skill_length,
            sanitizer_cfg=sanitizer_cfg,
            execution_contract=execution_contract,
        )
        repaired_report = validate_skill_integration(
            candidate_skill=repaired_prompt,
            parent_skill=parent_prompt,
            patch_plan=skill_patch_plan,
            execution_contract=execution_contract,
            config=integration_cfg,
        )
        write_skill_integration_report(
            output_dir,
            generation,
            child_slot,
            {
                "stage": repair_stage,
                "status": "ok" if repaired_report["ok"] else "needs_repair",
                "parent_info": parent_info,
                "repair_attempted": True,
                "repair_kind": "deterministic_semantic_scrub",
                "semantic_repair": semantic_record,
                "report": repaired_report,
            },
        )
        return repaired_prompt, repaired_report

    sanitized_prompt, integration_report = _try_semantic_repair(
        sanitized_prompt,
        integration_report,
        f"{stage}_semantic_repair",
    )

    if not integration_report["ok"] and repair_cfg.get("enabled", True):
        repaired = True
        repair_temperature = float(repair_cfg.get("temperature", 0.2))
        repair_budget = _candidate_skill_budget(parent_prompt, max_skill_length, sanitizer_cfg)
        repair_issues = format_integration_issues_for_repair(integration_report)
        print(f"      [skill-integration] repairing candidate: {', '.join(integration_report.get('issues', []))}")
        repaired_raw = repair_skill_candidate(
            client,
            mutation_model,
            candidate_skill=sanitized_prompt,
            parent_skill=parent_prompt,
            objective=objective,
            integration_issues=repair_issues,
            skill_patch_plan=skill_patch_plan_text,
            execution_constraints=execution_constraints_text,
            max_chars=repair_budget,
            audit_logger=audit_logger,
            temperature=repair_temperature,
            context={**(context or {}), "stage": stage, "repair_of": "skill_integration"},
        )
        sanitized_prompt, repair_sanitizer_record = _sanitize_candidate_skill(
            output_dir=output_dir,
            generation=generation,
            child_slot=child_slot,
            parent_info=parent_info,
            stage=f"{stage}_repair",
            candidate=repaired_raw,
            parent_prompt=parent_prompt,
            max_skill_length=max_skill_length,
            sanitizer_cfg=sanitizer_cfg,
            execution_contract=execution_contract,
        )
        integration_report = validate_skill_integration(
            candidate_skill=sanitized_prompt,
            parent_skill=parent_prompt,
            patch_plan=skill_patch_plan,
            execution_contract=execution_contract,
            config=integration_cfg,
        )
        write_skill_integration_report(
            output_dir,
            generation,
            child_slot,
            {
                "stage": f"{stage}_repair",
                "status": "ok" if integration_report["ok"] else "failed",
                "parent_info": parent_info,
                "repair_attempted": True,
                "report": integration_report,
            },
        )
        sanitized_prompt, integration_report = _try_semantic_repair(
            sanitized_prompt,
            integration_report,
            f"{stage}_repair_semantic_repair",
        )

    salvage_cfg = (repair_cfg.get("salvage") or {}) if isinstance(repair_cfg, dict) else {}
    if not integration_report["ok"] and salvage_cfg.get("enabled", True):
        salvaged_raw, salvage_record = _build_parent_preserving_salvage_candidate(
            parent_prompt=parent_prompt,
            candidate_report=integration_report,
            patch_plan=skill_patch_plan,
            max_lessons=int(salvage_cfg.get("max_lessons", 10)),
        )
        if salvaged_raw:
            salvaged_repaired, semantic_record = repair_semantic_contradictions(
                salvaged_raw,
                execution_contract,
            )
            semantic_repairs.append({
                "stage": f"{stage}_salvage_semantic_repair",
                **semantic_record,
            })
            salvage_prompt, salvage_sanitizer_record = _sanitize_candidate_skill(
                output_dir=output_dir,
                generation=generation,
                child_slot=child_slot,
                parent_info=parent_info,
                stage=f"{stage}_salvage",
                candidate=salvaged_repaired,
                parent_prompt=parent_prompt,
                max_skill_length=max_skill_length,
                sanitizer_cfg=sanitizer_cfg,
                execution_contract=execution_contract,
            )
            salvage_report = validate_skill_integration(
                candidate_skill=salvage_prompt,
                parent_skill=parent_prompt,
                patch_plan=skill_patch_plan,
                execution_contract=execution_contract,
                config=integration_cfg,
            )
            salvage_record = {
                **salvage_record,
                "semantic_repair": semantic_record,
                "status": "ok" if salvage_report["ok"] else "failed",
                "report": salvage_report,
            }
            write_skill_integration_report(
                output_dir,
                generation,
                child_slot,
                {
                    "stage": f"{stage}_salvage",
                    "status": "ok" if salvage_report["ok"] else "failed",
                    "parent_info": parent_info,
                    "repair_attempted": True,
                    "repair_kind": "parent_preserving_salvage",
                    "salvage": salvage_record,
                    "report": salvage_report,
                },
            )
            if salvage_report["ok"]:
                sanitized_prompt = salvage_prompt
                integration_report = salvage_report
                repaired = True

    if integration_report["ok"] and salvage_cfg.get("enabled", True) and salvage_cfg.get("soft_parent_floor", True):
        metrics = integration_report.get("metrics") or {}
        coverage_gain = float(metrics.get("coverage", 0.0) or 0.0) - float(
            metrics.get("parent_coverage", 0.0) or 0.0
        )
        candidate_ratio = float(metrics.get("candidate_parent_ratio", 1.0) or 1.0)
        min_parent_ratio = float(
            integration_cfg.get(
                "min_child_parent_ratio_for_soften",
                salvage_cfg.get("min_child_parent_ratio_for_soften", 0.75),
            )
            or 0.75
        )
        should_try_soft_salvage = (
            coverage_gain > float(salvage_cfg.get("min_soft_coverage_gain", 0.0) or 0.0)
            and candidate_ratio < min_parent_ratio
        )
        if should_try_soft_salvage:
            soft_raw, soft_record = _build_parent_preserving_salvage_candidate(
                parent_prompt=parent_prompt,
                candidate_report=integration_report,
                patch_plan=skill_patch_plan,
                max_lessons=int(salvage_cfg.get("max_lessons", 10)),
            )
            if soft_raw:
                soft_repaired, semantic_record = repair_semantic_contradictions(
                    soft_raw,
                    execution_contract,
                )
                semantic_repairs.append({
                    "stage": f"{stage}_soft_salvage_semantic_repair",
                    **semantic_record,
                })
                if len(soft_repaired) <= max_skill_length:
                    soft_prompt = soft_repaired
                    soft_sanitizer_record = {
                        "stage": f"{stage}_soft_salvage",
                        "ok": True,
                        "issues": [],
                        "warnings": [],
                        "metrics": {
                            "parent_chars": len(parent_prompt),
                            "raw_candidate_chars": len(soft_raw),
                            "sanitized_chars": len(soft_prompt),
                            "delta_chars": len(soft_prompt) - len(parent_prompt),
                            "budget_chars": max_skill_length,
                            "soft_parent_floor_no_condense": True,
                        },
                    }
                else:
                    soft_prompt, soft_sanitizer_record = _sanitize_candidate_skill(
                        output_dir=output_dir,
                        generation=generation,
                        child_slot=child_slot,
                        parent_info=parent_info,
                        stage=f"{stage}_soft_salvage",
                        candidate=soft_repaired,
                        parent_prompt=parent_prompt,
                        max_skill_length=max_skill_length,
                        sanitizer_cfg=sanitizer_cfg,
                        execution_contract=execution_contract,
                    )
                soft_report = validate_skill_integration(
                    candidate_skill=soft_prompt,
                    parent_skill=parent_prompt,
                    patch_plan=skill_patch_plan,
                    execution_contract=execution_contract,
                    config=integration_cfg,
                )
                candidate_metrics = integration_report.get("metrics") or {}
                soft_metrics = soft_report.get("metrics") or {}
                tolerance = float(salvage_cfg.get("soft_metric_tolerance", 1e-9) or 1e-9)
                soft_is_safe = (
                    soft_report.get("ok", False)
                    and int(soft_metrics.get("missing_critical_count", 0) or 0)
                    <= int(candidate_metrics.get("missing_critical_count", 0) or 0)
                    and int(soft_metrics.get("remove_violation_count", 0) or 0)
                    <= int(candidate_metrics.get("remove_violation_count", 0) or 0)
                    and int(soft_metrics.get("contradiction_count", 0) or 0)
                    <= int(candidate_metrics.get("contradiction_count", 0) or 0)
                    and float(soft_metrics.get("coverage", 0.0) or 0.0)
                    + tolerance
                    >= float(candidate_metrics.get("coverage", 0.0) or 0.0)
                )
                soft_record = {
                    **soft_record,
                    "kind": "soft_parent_floor",
                    "trigger": {
                        "coverage_gain": round(coverage_gain, 6),
                        "candidate_parent_ratio": round(candidate_ratio, 6),
                        "min_parent_ratio": round(min_parent_ratio, 6),
                    },
                    "semantic_repair": semantic_record,
                    "status": "ok" if soft_report.get("ok") else "failed",
                    "used": bool(soft_is_safe),
                    "sanitizer": soft_sanitizer_record,
                    "report": soft_report,
                }
                write_skill_integration_report(
                    output_dir,
                    generation,
                    child_slot,
                    {
                        "stage": f"{stage}_soft_salvage",
                        "status": "ok" if soft_report.get("ok") else "failed",
                        "parent_info": parent_info,
                        "repair_attempted": True,
                        "repair_kind": "soft_parent_floor_salvage",
                        "salvage": soft_record,
                        "report": soft_report,
                    },
                )
                if soft_is_safe:
                    sanitized_prompt = soft_prompt
                    integration_report = soft_report
                    salvage_record = soft_record
                    salvage_sanitizer_record = soft_sanitizer_record
                    repaired = True

    if not integration_report["ok"]:
        raise MutationValidationError(
            "skill integration gate rejected candidate: " + ", ".join(integration_report["issues"])
        )

    return sanitized_prompt, {
        "sanitizer": salvage_sanitizer_record or repair_sanitizer_record or semantic_sanitizer_record or sanitizer_record,
        "skill_integration": integration_report,
        "repair_attempted": repaired,
        "semantic_repairs": semantic_repairs,
        "salvage": salvage_record,
    }


def write_individual_eval_artifacts(
    individuals_dir: Path,
    generation: int,
    individual_index: int,
    ind: Individual,
) -> None:
    """Write the evaluated skill and metadata for one final individual slot."""
    skill_path = individuals_dir / f"ind{individual_index}.md"
    skill_path.write_text(ind.prompt, encoding="utf-8")
    result = getattr(ind, "fitness_result", None) or {}
    per_task_result = result.get("per_task", {}) if isinstance(result.get("per_task", {}), dict) else {}
    task_alias = None
    if len(per_task_result) == 1:
        only_task = next(iter(per_task_result))
        task_alias = re.sub(
            r"[^A-Za-z0-9_.-]+",
            "_",
            _short_task_id(str(only_task)),
        ).strip("_")
        if task_alias:
            task_skill_path = individuals_dir / f"gen{generation}_task_{task_alias}_ind{individual_index}_skill.md"
            task_skill_path.write_text(ind.prompt, encoding="utf-8")
    meta = {
        "generation": generation,
        "individual_index": individual_index,
        "skill_scope": "per_task" if task_alias else "unknown_or_multi_task",
        "task_alias": task_alias,
        "parent_info": ind.parent_info,
        "fitness": ind.fitness,
        "pass_at_1": result.get("pass_at_1", 0.0),
        "progress_fitness": result.get("progress_fitness", 0.0),
        "raw_progress_fitness": result.get("raw_progress_fitness"),
        "selection_fitness": result.get("selection_fitness", ind.fitness),
        "selection_fitness_original": result.get("selection_fitness_original"),
        "selection_fitness_breakdown": result.get("selection_fitness_breakdown", {}),
        "skill_quality": result.get("skill_quality"),
        "agent_behavior_quality": result.get("agent_behavior_quality"),
        "rollout_variance_quality": result.get("rollout_variance_quality"),
        "skill_adherence_quality": result.get("skill_adherence_quality"),
        "progress_components": result.get("progress_components", {}),
        "progress_rollout_scores": result.get("progress_rollout_scores", []),
        "rollout_variance": result.get("rollout_variance", {}),
        "path_grounding_fitness": result.get("path_grounding_fitness", {}),
        "skill_monitor": result.get("skill_monitor", {}),
        "prompt_length": len(ind.prompt),
        "sha256": _sha256_text(ind.prompt),
        "num_rollouts": result.get("num_rollouts", 0),
        "elapsed_secs": result.get("elapsed", 0),
        "parent_sha256": ind.parent_sha256,
        "child_origin": ind.child_origin,
        "challenger_decision": ind.challenger_decision,
        "semantic_retention": ind.semantic_retention,
        "semantic_selection": ind.semantic_selection,
        "per_task": {
            (tid or "unknown").replace("cvdp_agentic_heavy_", ""): v
            for tid, v in per_task_result.items()
        },
    }
    _write_json(individuals_dir / f"ind{individual_index}_meta.json", meta)


def write_lineage(
    path: Path,
    history: list[dict],
    best_ever: Individual,
    seed_skill_path: str,
    seed_skill_len: int,
) -> None:
    """Write a human-readable evolution narrative: seed → per-gen winners → best ever."""
    lines = ["# Optimization Lineage\n"]
    best_pass = best_ever.fitness_result.get("pass_at_1", best_ever.fitness) if best_ever.fitness_result else best_ever.fitness
    best_progress = best_ever.fitness_result.get("progress_fitness", 0.0) if best_ever.fitness_result else 0.0
    lines.append(f"**Seed skill**: `{seed_skill_path}` ({seed_skill_len} chars)")
    lines.append(f"**Final best selection fitness**: {best_ever.fitness:.3f}")
    lines.append(f"**Final best true pass@1**: {best_pass:.3f}")
    lines.append(f"**Best-producing generation**: {best_ever.generation}")
    lines.append(f"**Best individual's lineage**: `{best_ever.parent_info}`")
    lines.append("")
    lines.append("## Per-generation progression\n")
    lines.append("| Gen | Best selection | Mean selection | Worst selection | Best-ever selection | Top individual | Notes |")
    lines.append("|-----|------|------|-------|-----------|---------------|-------|")

    best_ever_so_far = 0.0
    for rec in history:
        gen = rec["generation"]
        best = rec["best_fitness"]
        mean = rec["mean_fitness"]
        worst = rec["worst_fitness"]
        best_ever_val = rec.get("best_ever", best)
        inds = rec.get("individuals", [])
        top = inds[0] if inds else {}
        top_info = top.get("parent_info", "?")
        top_len = top.get("prompt_length", 0)

        # Notes: did best-ever change? is best stagnant?
        notes = []
        if best_ever_val > best_ever_so_far + 1e-6:
            notes.append(f"↑ new best-ever ({best_ever_val:.3f})")
            best_ever_so_far = best_ever_val
        elif best_ever_val == best_ever_so_far and gen > 1:
            notes.append("= stagnant")
        if top.get("prompt_length", 0) == seed_skill_len:
            notes.append("original seed still winning")

        notes_str = "; ".join(notes) if notes else ""
        lines.append(
            f"| {gen} | {best:.3f} | {mean:.3f} | {worst:.3f} | {best_ever_val:.3f} | "
            f"{top_info} ({top_len}c) | {notes_str} |"
        )

    lines.append("")
    lines.append("## Best-ever lineage\n")
    lines.append(f"- **Generation**: {best_ever.generation}")
    lines.append(f"- **Parent info**: `{best_ever.parent_info}`")
    lines.append(f"- **Prompt length**: {len(best_ever.prompt)} chars")
    lines.append(f"- **Selection fitness**: {best_ever.fitness:.3f}")
    lines.append(f"- **True pass@1**: {best_pass:.3f}")
    lines.append(f"- **Progress fitness**: {best_progress:.3f}")
    lines.append("")
    lines.append("## Per-task trajectory across generations\n")

    # Per-task pass rates over generations
    all_tasks: dict[str, list[tuple[int, float]]] = {}
    for rec in history:
        gen = rec["generation"]
        for ind in rec.get("individuals", []):
            per_task = ind.get("per_task", {})
            for tid, val in per_task.items():
                rate = val.get("pass_at_1", 0.0) if isinstance(val, dict) else float(val)
                short = (tid or "unknown").replace("cvdp_agentic_heavy_", "")
                all_tasks.setdefault(short, []).append((gen, rate))

    if all_tasks:
        lines.append("Per-task avg pass rate (across all individuals in each generation):")
        lines.append("")
        lines.append("| Task | " + " | ".join(f"Gen {rec['generation']}" for rec in history) + " |")
        lines.append("|------|" + "|".join(["------"] * len(history)) + "|")
        for tid in sorted(all_tasks.keys()):
            by_gen: dict[int, list[float]] = {}
            for gen, rate in all_tasks[tid]:
                by_gen.setdefault(gen, []).append(rate)
            cells = []
            for rec in history:
                g = rec["generation"]
                if g in by_gen:
                    avg = sum(by_gen[g]) / len(by_gen[g])
                    cells.append(f"{avg:.0%}")
                else:
                    cells.append("-")
            lines.append(f"| {tid} | " + " | ".join(cells) + " |")

    lines.append("")
    lines.append("## How to inspect\n")
    lines.append("- Per-generation oracle feedback: `gen<N>/oracle_feedback.md`")
    lines.append("- Per-task insight accumulators: `gen<N>/task_insights/<cid>/<task>_{pass,fail}.md`")
    lines.append("- CID-local synthesis: `gen<N>/cid_synthesis/<cid>/{pass,fail}_synthesis.md`")
    lines.append("- CID oracle handoffs: `gen<N>/cid_oracle_feedback/<cid>.md`")
    lines.append("- Individual skills tested: `gen<N>/individuals/ind<I>.md` (+ `_meta.json`)")
    lines.append("- Raw best-performing skill: `best_performing_skill.md`")
    lines.append("- Distilled downstream-eval export: `optimized_skill.md` / `distilled_final_skill.md`")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _expand_env_vars(obj):
    """Recursively expand ${VAR} references in all string values."""
    import os, re
    if isinstance(obj, str):
        return re.sub(
            r'\$\{([^}]+)\}',
            lambda m: os.environ.get(m.group(1), m.group(0)),
            obj,
        )
    elif isinstance(obj, dict):
        return {k: _expand_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_expand_env_vars(item) for item in obj]
    return obj


def _resolve_cid_paths(config: dict) -> dict:
    """If config contains a `cid:` key (e.g. `cid: cid012`), auto-fill:
        - seed_skill: skills/rollout/<cid>_*.md       (first match wins)
        - tasks_path: nemogym/data/<cid>_*/train.jsonl
        - output_dir: orchestration/outputs/cvdp_<cid>

    Any of these keys that is already explicitly set in the config is NOT
    overridden — explicit wins.

    trace-skill repo layout: data lives under bundled `nemogym/`, outputs under
    `orchestration/outputs/`. (Source repo CVDP_Agentic_Long_Context used
    NeMo-Gym-CVDP/ and optimizer/outputs_*; this function is the trace-skill
    variant with paths re-rooted.)

    Returns the config (possibly mutated in-place).
    """
    cid = config.get("cid")
    if not cid:
        return config
    repo_root = Path(__file__).resolve().parent.parent

    # seed_skill
    if not config.get("seed_skill"):
        skill_matches = sorted((repo_root / "skills" / "rollout").glob(f"{cid}_*.md"))
        if skill_matches:
            config["seed_skill"] = str(skill_matches[0].relative_to(repo_root))
            print(f"[cid-dispatch] {cid}: seed_skill -> {config['seed_skill']}")
        else:
            fallback = repo_root / "skills" / "rollout" / "_base.md"
            if fallback.exists():
                config["seed_skill"] = str(fallback.relative_to(repo_root))
                print(f"[cid-dispatch] {cid}: no {cid}_*.md found, using {config['seed_skill']}")

    # tasks_path
    if not config.get("tasks_path"):
        data_matches = sorted((repo_root / "nemogym" / "data").glob(f"{cid}_*/train.jsonl"))
        if data_matches:
            config["tasks_path"] = str(data_matches[0].relative_to(repo_root))
            print(f"[cid-dispatch] {cid}: tasks_path -> {config['tasks_path']}")

    # output_dir
    if not config.get("output_dir"):
        config["output_dir"] = f"orchestration/outputs/cvdp_{cid}"
        print(f"[cid-dispatch] {cid}: output_dir -> {config['output_dir']}")

    return config


def load_config(config_path: Path) -> dict:
    with open(config_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return _resolve_cid_paths(_expand_env_vars(raw))


def tournament_select(population: list[Individual], tournament_size: int = 2) -> Individual:
    contestants = random.sample(population, min(tournament_size, len(population)))
    return max(contestants, key=lambda ind: ind.fitness)


def run_optimizer(config: dict, resume: bool = False) -> Individual:
    """Main GA optimization loop. If resume=True, picks up from the last checkpoint."""
    ga = config["ga"]
    pop_size = ga["population_size"]
    generations = ga["generations"]
    elitism = ga["elitism"]
    crossover_rate = ga["crossover_rate"]
    mutation_rate = ga["mutation_rate"]
    tournament_size = ga.get("tournament_size", 2)
    max_skill_length = config.get("max_skill_length", 0)

    repo_root = Path(__file__).resolve().parent.parent
    seed_skill_path = repo_root / config["seed_skill"]
    tasks_path = repo_root / config["tasks_path"]
    ng_collect_bin = config["ng_collect_bin"]
    output_dir = Path(config.get("output_dir", "optimizer/outputs"))
    output_dir.mkdir(parents=True, exist_ok=True)

    seed_skill = seed_skill_path.read_text(encoding="utf-8")
    tasks_data = load_tasks(tasks_path)
    task_manifest = build_task_manifest(tasks_data, tasks_path)
    skill_scope = _infer_skill_scope(seed_skill_path, task_manifest)
    write_initial_skill_artifacts(output_dir, seed_skill_path, seed_skill, tasks_path, task_manifest)
    write_artifact_manifest(output_dir)
    preflight_report = run_preflight_checks(
        output_dir=output_dir,
        seed_skill_path=seed_skill_path,
        seed_skill=seed_skill,
        tasks_path=tasks_path,
        tasks_data=tasks_data,
        task_manifest=task_manifest,
        config=config,
    )
    print(f"  Loaded {len(tasks_data)} tasks into memory (immune to directory renames)")
    objective = config.get("objective",
        "Maximize the pass rate of an LLM agent on Verilog/SystemVerilog chip design tasks. "
        "The agent uses tools (ls, cat, echo, iverilog, vvp) in a Docker sandbox.")

    llm_cfg = config["mutation_llm"]
    client = openai.OpenAI(
        base_url=llm_cfg["base_url"],
        api_key=llm_cfg.get("api_key", "ollama"),
        timeout=600.0,
        max_retries=0,
    )
    mutation_model = llm_cfg["model"]
    mutation_temperature = float(llm_cfg.get("temperature", 0.35))

    # Eval LLM config: prefer shared eval_models.yml, fall back to inline eval_llm block
    eval_config_path = config.get("eval_config")
    if eval_config_path:
        sys.path.insert(0, str(repo_root / "eval"))
        from eval_config import get_analyzer_config
        eval_llm_cfg = get_analyzer_config(str(repo_root / eval_config_path))
    else:
        eval_llm_cfg = config.get("eval_llm", llm_cfg)
    rollout_model_cfg = config.get("rollout_model", llm_cfg)
    runtime_verifier_feedback_cfg = {
        "enabled": False,
        "max_calls": 3,
        **(config.get("runtime_verifier_feedback") or {}),
    }
    nemogym_root = config.get("nemogym_root")
    ng_config_paths = config.get("ng_config_paths")

    fitness_cfg = config.get("fitness", {})
    num_repeats = fitness_cfg.get("num_repeats", 1)
    num_parallel = fitness_cfg.get("num_parallel", 1)
    fitness_timeout = fitness_cfg.get("timeout", 3600)
    agent_name = fitness_cfg.get("agent_name", "cvdp_agentic_heavy_simple_agent")
    dry_run = fitness_cfg.get("dry_run", False)
    run_analyzer_flag = fitness_cfg.get("run_analyzer", False)
    skill_monitor_user_cfg = config.get("skill_monitor") or {}
    skill_monitor_cfg = {
        "enabled": True,
        "mode": "passive",
        "inject_feedback": False,
        "compile_policy": True,
        "block_environment_invariants": True,
        "block_high_confidence_path": True,
        "block_skill_guidance": False,
        **skill_monitor_user_cfg,
    }
    if (
        skill_monitor_cfg.get("enabled")
        and skill_monitor_cfg.get("mode", "passive") != "passive"
        and "inject_feedback" not in skill_monitor_user_cfg
    ):
        skill_monitor_cfg["inject_feedback"] = True
    skill_sanitizer_user_cfg = config.get("skill_sanitizer", {}) or {}
    skill_sanitizer_user_condense_cfg = skill_sanitizer_user_cfg.get("condense", {}) or {}
    skill_sanitizer_base_cfg = {
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
            "soft_budget_slack_ratio": 0.10,
            "min_retention_ratio": 0.75,
        },
    }
    skill_sanitizer_cfg = {
        **skill_sanitizer_base_cfg,
        **{k: v for k, v in skill_sanitizer_user_cfg.items() if k != "condense"},
    }
    skill_sanitizer_cfg["condense"] = {
        **(skill_sanitizer_base_cfg.get("condense", {}) or {}),
        **skill_sanitizer_user_condense_cfg,
    }
    skill_integration_cfg = {
        "enabled": True,
        "min_directive_coverage": 0.60,
        "max_missing_critical": 0,
        "min_child_parent_ratio_for_soften": 0.75,
        "fail_on_remove_violation": True,
        "fail_on_contradiction": True,
        **(config.get("skill_integration", {}) or {}),
    }
    mutation_repair_cfg = {
        "enabled": True,
        "temperature": 0.2,
        **(config.get("mutation_repair", {}) or {}),
    }
    parent_child_survival = bool(ga.get("parent_child_survival", True))
    single_lineage_survival_margin = float(ga.get("single_lineage_survival_margin", 0.05))
    parent_child_challenger_cfg = {
        "enabled": True,
        "trigger": "on_regression",
        "selection_drop": 0.02,
        "pass_drop": 0.001,
        "restore_selection_margin": 0.0,
        "restore_pass_margin": 0.0,
        "max_per_generation": max(1, min(2, pop_size)),
        **(ga.get("parent_child_challenger") or {}),
    }
    semantic_survivor_cfg = {
        "enabled": True,
        # Preserve at most one semantically strong child per generation. The
        # behavior elite still occupies the first slot, so this adds exploration
        # without making semantic quality outrank measured rollout behavior.
        "max_per_generation": 1,
        # A child must be close enough that rollout stochasticity could explain
        # the score gap.
        "selection_margin": 0.010,
        "progress_margin": 0.10,
        "pass_margin": 0.0,
        # And it must have clearly integrated oracle-derived lessons.
        "min_coverage": 0.90,
        "min_coverage_gain": 0.10,
        "max_missing_critical": 0,
        "max_remove_violations": 0,
        "max_contradictions": 0,
        **(ga.get("semantic_survivor") or {}),
    }
    semantic_skill_selection_cfg = {
        "enabled": True,
        # Parent-as-floor selection: a child must beat the parent semantically,
        # not just ride a noisy high-fitness rollout.
        "min_improvement_margin": 0.02,
        "neutral_tolerance": 0.005,
        "min_coverage_gain_to_accept": 0.05,
        "reject_on_missing_critical_regression": True,
        "reject_on_remove_violation": True,
        "reject_on_contradiction": True,
        # Keep the semantic incumbent as an explicit next-gen slot so noisy
        # rollout elites cannot erase a stronger learned skill.
        "carry_incumbent": True,
        # Mutating from the incumbent makes task-wise optimization stable; other
        # population members still provide rollout evidence and diversity.
        "prefer_incumbent_parent": True,
        "incumbent_min_delta": 0.0,
        **(ga.get("semantic_skill_selection") or {}),
    }
    standard_ea_cfg = {
        "enabled": True,
        # Standard EA evaluates the current population once, selects an
        # evaluated survivor, then mutates that survivor into next-gen
        # candidates. Unevaluated children are never selected by semantic score.
        "mutation_parent": "survivor",
        "carry_evaluated_survivor": True,
        "defer_child_semantic_selection_to_rollout": True,
        "disable_parent_child_challenger": True,
        "disable_semantic_survivor": True,
        **(ga.get("standard_ea") or {}),
    }
    standard_ea_enabled = bool(standard_ea_cfg.get("enabled", True))
    if standard_ea_enabled:
        if standard_ea_cfg.get("disable_parent_child_challenger", True):
            parent_child_challenger_cfg["enabled"] = False
        if standard_ea_cfg.get("disable_semantic_survivor", True):
            semantic_survivor_cfg["enabled"] = False
        # These knobs belonged to the older semantic-incumbent path. Under the
        # standard EA flow, the evaluated survivor is the only parent floor.
        semantic_skill_selection_cfg["carry_incumbent"] = False
        semantic_skill_selection_cfg["prefer_incumbent_parent"] = False
    combined_selection_cfg = {
        "enabled": True,
        "default_skill_quality": 0.50,
        "fallback_selection_epsilon": 0.049,
        "enforce_validity": True,
        "enforce_semantic_floor": True,
        "semantic_floor_tolerance": 0.005,
        "weights": {
            "progress_lcb": 0.55,
            "progress_mean": 0.15,
            "skill_quality": 0.20,
            "adherence": 0.10,
        },
        **(ga.get("combined_selection_fitness") or {}),
    }
    regression_repair_cfg = {
        "enabled": True,
        "threshold": 0.05,
        **(config.get("regression_repair", {}) or {}),
    }
    change_attribution_cfg = {
        "enabled": True,
        "fail_closed": False,
        "include_in_mutation_handoff": True,
        "pass_rate_improvement_threshold": 0.001,
        "pass_rate_regression_threshold": 0.001,
        "dense_progress_threshold": 0.03,
        "selection_threshold": 0.03,
        **(config.get("change_attribution", {}) or {}),
    }
    lesson_bank_cfg = {
        "enabled": True,
        "include_in_mutation_handoff": True,
        "mutation_handoff_max_chars": 7000,
        "distilled_final_max_chars": 18000,
        **(config.get("lesson_bank", {}) or {}),
    }
    execution_contract = infer_execution_contract(tasks_data)
    execution_constraints_text = build_execution_constraints_text(execution_contract)
    _write_json(output_dir / "execution_contract.json", execution_contract.to_dict())
    (output_dir / "execution_constraints.md").write_text(execution_constraints_text + "\n", encoding="utf-8")

    # ── Rate limiter setup ──────────────────────────────────────────
    rate_limit_rpm = config.get("rate_limit", {}).get("max_requests_per_minute", 80)
    reset_rate_limiter()
    limiter = get_rate_limiter(max_rpm=rate_limit_rpm)
    print(f"  [safety] Rate limiter: {rate_limit_rpm} requests/min, "
          f"circuit breaker at {limiter._circuit_breaker_threshold} consecutive errors, "
          f"hard cap at {limiter._max_total_requests} total requests")

    # ── Telemetry setup ─────────────────────────────────────────────
    phoenix_endpoint = config.get("telemetry", {}).get(
        "phoenix_endpoint", os.environ.get("PHOENIX_ENDPOINT")
    )
    telemetry_enabled = config.get("telemetry", {}).get("enabled", True)
    if telemetry_enabled:
        init_telemetry(phoenix_endpoint=phoenix_endpoint)

    dashboard = LiveDashboard(output_dir / "live_dashboard.json")
    dashboard.set_config(config)

    print("=" * 70)
    print("  CVDP Skill Prompt Optimizer")
    print("=" * 70)
    print(f"  Seed skill: {seed_skill_path} ({len(seed_skill)} chars)")
    print(f"  Tasks: {tasks_path}")
    print(f"  Population: {pop_size}, Generations: {generations}")
    print(f"  Elitism: {elitism}, Crossover: {crossover_rate}, Mutation: {mutation_rate}")
    print(f"  Tournament size: {tournament_size}")
    print(f"  Oracle feedback: {ga.get('oracle_feedback', 'never')}")
    print(f"  Mutation LLM: {mutation_model} @ {llm_cfg['base_url']} "
          f"(temperature={mutation_temperature})")
    print(
        f"  Eval LLM: {eval_llm_cfg['model']} @ {eval_llm_cfg['base_url']} "
        f"(temperature={eval_llm_cfg.get('temperature', 0.0)})"
    )
    print(
        f"  Rollout LLM: {rollout_model_cfg['model']} @ {rollout_model_cfg['base_url']} "
        f"(temperature={rollout_model_cfg.get('temperature', 0.4)})"
    )
    print(f"  NeMo-Gym root: {nemogym_root}")
    print(f"  Fitness: {num_repeats} repeat(s), {num_parallel} parallel")
    print(f"  Execution tools: {', '.join(execution_contract.allowed_tools)}")
    print(
        f"  Skill sanitizer: {'enabled' if skill_sanitizer_cfg.get('enabled', True) else 'disabled'} "
        f"(max_growth_ratio={skill_sanitizer_cfg.get('max_growth_ratio')}, "
        f"max_growth_chars={skill_sanitizer_cfg.get('max_growth_chars')}, "
        f"min_budget_chars={skill_sanitizer_cfg.get('min_budget_chars')}, "
        f"absolute_max_chars={skill_sanitizer_cfg.get('absolute_max_chars')})"
    )
    condense_cfg = skill_sanitizer_cfg.get("condense", {}) or {}
    print(
        f"  Skill condenser: {'enabled' if condense_cfg.get('enabled', True) else 'disabled'} "
        f"(over_chars={condense_cfg.get('over_chars', 6000)}, "
        f"target_chars={condense_cfg.get('target_chars', 5200)}, "
        f"soft_budget_slack_chars={condense_cfg.get('soft_budget_slack_chars', 1024)}, "
        f"soft_budget_slack_ratio={condense_cfg.get('soft_budget_slack_ratio', 0.10)}, "
        f"min_retention_ratio={condense_cfg.get('min_retention_ratio', 0.75)})"
    )
    print(f"  Parent-child survival: {'enabled' if parent_child_survival else 'disabled'}")
    print(f"  Single-lineage survival margin: {single_lineage_survival_margin:.3f}")
    print(
        f"  EA flow: {'standard evaluated-survivor' if standard_ea_enabled else 'legacy semantic-incumbent'} "
        f"(mutation_parent={standard_ea_cfg.get('mutation_parent')}, "
        f"defer_child_selection={standard_ea_cfg.get('defer_child_semantic_selection_to_rollout')})"
    )
    print(
        f"  Parent-child challenger: {'enabled' if parent_child_challenger_cfg.get('enabled', True) else 'disabled'} "
        f"(trigger={parent_child_challenger_cfg.get('trigger')}, "
        f"max_per_generation={parent_child_challenger_cfg.get('max_per_generation')})"
    )
    print(
        f"  Semantic survivor: {'enabled' if semantic_survivor_cfg.get('enabled', True) else 'disabled'} "
        f"(max_per_generation={semantic_survivor_cfg.get('max_per_generation')}, "
        f"selection_margin={semantic_survivor_cfg.get('selection_margin')}, "
        f"progress_margin={semantic_survivor_cfg.get('progress_margin')}, "
        f"min_coverage={semantic_survivor_cfg.get('min_coverage')})"
    )
    print(
        f"  Semantic skill selector: {'enabled' if semantic_skill_selection_cfg.get('enabled', True) else 'disabled'} "
        f"(parent_floor={semantic_skill_selection_cfg.get('carry_incumbent')}, "
        f"prefer_incumbent_parent={semantic_skill_selection_cfg.get('prefer_incumbent_parent')}, "
        f"margin={semantic_skill_selection_cfg.get('min_improvement_margin')})"
    )
    print(
        f"  Combined selection fitness: {'enabled' if combined_selection_cfg.get('enabled', True) else 'disabled'} "
        f"(semantic_floor={combined_selection_cfg.get('enforce_semantic_floor')}, "
        f"validity_gate={combined_selection_cfg.get('enforce_validity')})"
    )
    print(
        f"  Regression repair: {'enabled' if regression_repair_cfg.get('enabled', True) else 'disabled'} "
        f"(threshold={regression_repair_cfg.get('threshold')})"
    )
    print(
        f"  Change attribution: {'enabled' if change_attribution_cfg.get('enabled', True) else 'disabled'} "
        f"(fail_closed={change_attribution_cfg.get('fail_closed')}, "
        f"include_in_handoff={change_attribution_cfg.get('include_in_mutation_handoff')})"
    )
    print(
        f"  Lesson bank: {'enabled' if lesson_bank_cfg.get('enabled', True) else 'disabled'} "
        f"(include_in_handoff={lesson_bank_cfg.get('include_in_mutation_handoff')}, "
        f"final_max_chars={lesson_bank_cfg.get('distilled_final_max_chars')})"
    )
    print(
        f"  Skill integration gate: {'enabled' if skill_integration_cfg.get('enabled', True) else 'disabled'} "
        f"(min_coverage={skill_integration_cfg.get('min_directive_coverage')}, "
        f"max_missing_critical={skill_integration_cfg.get('max_missing_critical')})"
    )
    print(
        f"  Mutation repair: {'enabled' if mutation_repair_cfg.get('enabled', True) else 'disabled'} "
        f"(temperature={mutation_repair_cfg.get('temperature')})"
    )
    if skill_monitor_cfg.get("enabled"):
        print(
            f"  Skill monitor: enabled "
            f"(mode={skill_monitor_cfg.get('mode', 'passive')}, "
            f"inject_feedback={skill_monitor_cfg.get('inject_feedback', True)}, "
            f"compile_policy={skill_monitor_cfg.get('compile_policy', True)}, "
            f"block_env={skill_monitor_cfg.get('block_environment_invariants', True)}, "
            f"block_path={skill_monitor_cfg.get('block_high_confidence_path', True)}, "
            f"block_skill={skill_monitor_cfg.get('block_skill_guidance', False)})"
        )
    else:
        print("  Skill monitor: disabled")
    print(
        f"  Runtime verifier feedback: {'enabled' if runtime_verifier_feedback_cfg.get('enabled') else 'disabled'} "
        f"(max_calls={runtime_verifier_feedback_cfg.get('max_calls', 3)})"
    )
    print(f"  Run analyzer: {run_analyzer_flag}")
    print(f"  Max skill length: {max_skill_length if max_skill_length > 0 else 'unlimited'}")
    print(f"  Dry run: {dry_run}")
    print(f"  Output: {output_dir}")
    print()

    run_config = {
        "seed_skill": str(seed_skill_path),
        "seed_skill_length": len(seed_skill),
        "tasks_path": str(tasks_path),
        "num_tasks": len(tasks_data),
        "task_manifest": task_manifest,
        "cids": sorted({row.get("cid") for row in task_manifest if row.get("cid")}),
        "skill_scope": skill_scope,
        "scope": _task_only_scope_record(task_manifest) if skill_scope == "per_task" else _skill_scope_record(seed_skill_path, task_manifest),
        "mutation_model": mutation_model,
        "mutation_temperature": mutation_temperature,
        "eval_model": eval_llm_cfg["model"],
        "eval_temperature": eval_llm_cfg.get("temperature", 0.0),
        "rollout_model": rollout_model_cfg["model"],
        "rollout_temperature": rollout_model_cfg.get("temperature", 0.4),
        "population_size": pop_size,
        "generations": generations,
        "elitism": elitism,
        "crossover_rate": crossover_rate,
        "mutation_rate": mutation_rate,
        "tournament_size": tournament_size,
        "num_repeats": num_repeats,
        "num_parallel": num_parallel,
        "fitness_timeout": fitness_timeout,
        "max_skill_length": max_skill_length,
        "run_analyzer": run_analyzer_flag,
        "skill_monitor": skill_monitor_cfg,
        "runtime_verifier_feedback": runtime_verifier_feedback_cfg,
        "skill_sanitizer": skill_sanitizer_cfg,
        "skill_integration": skill_integration_cfg,
        "mutation_repair": mutation_repair_cfg,
        "execution_contract": execution_contract.to_dict(),
        "parent_child_survival": parent_child_survival,
        "single_lineage_survival_margin": single_lineage_survival_margin,
        "standard_ea": standard_ea_cfg,
        "parent_child_challenger": parent_child_challenger_cfg,
        "semantic_survivor": semantic_survivor_cfg,
        "semantic_skill_selection": semantic_skill_selection_cfg,
        "combined_selection_fitness": combined_selection_cfg,
        "regression_repair": regression_repair_cfg,
        "change_attribution": change_attribution_cfg,
        "lesson_bank": lesson_bank_cfg,
        "preflight": {
            "status": preflight_report.get("status"),
            "report_path": "preflight_report.json",
            "errors": len(preflight_report.get("errors", [])),
            "warnings": len(preflight_report.get("warnings", [])),
        },
        "dry_run": dry_run,
    }
    with open(output_dir / "run_config.json", "w", encoding="utf-8") as f:
        json.dump(run_config, f, indent=2, ensure_ascii=False)

    # ── Reproducibility metadata: git commit, library versions, skill hashes ──
    skills_dir = repo_root / "skills"
    run_metadata = collect_run_metadata(repo_root, skills_dir)
    with open(output_dir / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(run_metadata, f, indent=2, ensure_ascii=False)
    print(f"  [repro] git={run_metadata.get('git_commit', '?')[:12]} "
          f"(dirty={run_metadata.get('git_dirty', '?')}), "
          f"{len(run_metadata.get('skill_hashes', {}))} skill files hashed")

    # ── Telemetry mode (debug = full logging; prod = index-only) ──
    telemetry_mode = resolve_telemetry_mode(config)
    print(f"  [telemetry] mode={telemetry_mode} — {describe_mode(telemetry_mode)}")

    # ── LLM audit logger: records every optimizer-side LLM call ──
    audit_logger = LLMAuditLogger(
        run_dir=output_dir,
        enabled=True,
        write_prompt_files=(telemetry_mode == "debug"),
    )
    print(f"  [audit] LLM call log → {audit_logger.log_path.relative_to(output_dir.parent)}")

    # ── Error logger: structured record of non-fatal exceptions ──
    error_logger = ErrorLogger(run_dir=output_dir, enabled=True)
    print(f"  [errors] Non-fatal exception log → {error_logger.log_path.relative_to(output_dir.parent)}")

    # ── Status heartbeat: "what is the optimizer doing right now?" ──
    # On crash, inspect <run>/status.json to see the last phase + generation
    # + individual + context. Updated at every major phase transition.
    import os as _os
    heartbeat = StatusHeartbeat(run_dir=output_dir, pid=_os.getpid())
    heartbeat.update(phase="init", message=f"output_dir={output_dir}")
    print(f"  [heartbeat] Status file → {heartbeat.path.relative_to(output_dir.parent)}")

    # ── Resume or initialize ─────────────────────────────────────────

    start_gen = 1
    best_ever: Individual | None = None
    semantic_incumbent: Individual | None = None
    history: list[dict] = []

    ckpt = load_checkpoint(output_dir) if resume else None

    if ckpt and resume:
        start_gen = ckpt["last_completed_gen"] + 1
        population = [Individual.from_checkpoint_dict(d) for d in ckpt["population"]]
        best_ever = Individual.from_checkpoint_dict(ckpt["best_ever"])
        if ckpt.get("semantic_incumbent"):
            semantic_incumbent = Individual.from_checkpoint_dict(ckpt["semantic_incumbent"])
        else:
            semantic_incumbent = copy.deepcopy(best_ever)
        history = ckpt["history"]
        print(f"── Resuming from checkpoint (gen {ckpt['last_completed_gen']} completed) ──")
        print(f"  Population: {len(population)} individuals")
        print(f"  Best ever: {best_ever.fitness:.3f} (gen {best_ever.generation})")
        print(f"  Semantic incumbent: {semantic_incumbent.parent_info} ({len(semantic_incumbent.prompt)} chars)")
        print(f"  History: {len(history)} generations recorded")

        needs_breeding = _checkpoint_needs_breeding(ckpt, population)

        if needs_breeding and start_gen <= generations:
            print(f"  Checkpoint has evaluated population — running oracle + breeding gen {start_gen} children...")
            population.sort(key=lambda x: x.fitness, reverse=True)
            if standard_ea_enabled and population:
                semantic_incumbent = _clone_individual_for_generation(
                    population[0],
                    ckpt["last_completed_gen"],
                    f"evaluated_survivor_from_gen{ckpt['last_completed_gen']}",
                )
                semantic_incumbent.semantic_selection = make_standard_ea_survivor_record(
                    generation=ckpt["last_completed_gen"],
                    survivor=population[0],
                )
                prev_gen_dir_for_survivor = output_dir / f"gen{ckpt['last_completed_gen']}"
                prev_gen_dir_for_survivor.mkdir(parents=True, exist_ok=True)
                _write_json(prev_gen_dir_for_survivor / "ea_survivor_decision.json", semantic_incumbent.semantic_selection)
                (prev_gen_dir_for_survivor / "ea_survivor_skill.md").write_text(semantic_incumbent.prompt, encoding="utf-8")
                (output_dir / "semantic_incumbent.md").write_text(semantic_incumbent.prompt, encoding="utf-8")

            # Bug fix (Apr 19, 2026): previously resume-breeding called Opus
            # mutation/crossover WITHOUT oracle_feedback, silently defeating
            # the whole 3-layer pipeline. Now we regenerate oracle feedback
            # from the checkpointed evaluated population and pass it through.
            prev_gen = ckpt["last_completed_gen"]
            prev_gen_dir = output_dir / f"gen{prev_gen}"
            resume_oracle_feedback: str | None = None
            if prev_gen_dir.exists() and ga.get("oracle_feedback", "never") in ("always", "adaptive"):
                try:
                    print(f"    [resume] Regenerating oracle feedback for gen{prev_gen}...")
                    oracle_client_resume = openai.OpenAI(
                        base_url=eval_llm_cfg["base_url"],
                        api_key=eval_llm_cfg.get("api_key", "ollama"),
                        timeout=300.0, max_retries=1,
                    )
                    # Load rollouts by eval-time index from disk (checkpoint
                    # doesn't preserve fitness_result.rollout_path; we use the
                    # predictable gen<N>/rollouts/ind<I>/rollouts_*.jsonl layout).
                    # Oracle doesn't require rollouts-align-to-sorted-population
                    # order -- Layer 1 processes each rollout independently.
                    rollouts_by_ind: list[list[dict]] = []
                    rollout_root = prev_gen_dir / "rollouts"
                    for ind_dir in sorted(rollout_root.glob("ind*")):
                        candidate = ind_dir / f"rollouts_gen{prev_gen}_{ind_dir.name}.jsonl"
                        ind_rs: list[dict] = []
                        if candidate.exists():
                            with open(candidate) as f:
                                for line in f:
                                    if line.strip():
                                        try: ind_rs.append(json.loads(line))
                                        except json.JSONDecodeError: continue
                        rollouts_by_ind.append(ind_rs)
                    print(f"    [resume] Loaded {sum(len(r) for r in rollouts_by_ind)} rollouts from {len(rollouts_by_ind)} individuals")
                    # Build scoreboard from population fitness
                    task_avgs: dict[str, list[float]] = {}
                    for ind in population:
                        fr = getattr(ind, 'fitness_result', None) or {}
                        for tid, val in fr.get("per_task", {}).items():
                            rate = val.get("pass_at_1", 0.0) if isinstance(val, dict) else float(val)
                            short = (tid or "unknown").replace("cvdp_agentic_heavy_", "")
                            task_avgs.setdefault(short, []).append(rate)
                    sb_lines = []
                    cid_lookup = _task_cid_lookup(task_manifest)
                    for tid in sorted(task_avgs):
                        rates = task_avgs[tid]
                        avg = sum(rates) / len(rates)
                        cid = cid_lookup.get(tid) or cid_lookup.get(_short_task_id(tid)) or "unknown"
                        sb_lines.append(f"  [{cid}] {tid}: avg={avg:.0%}")
                    scoreboard = "\n".join(sb_lines) or "(no per-task data)"
                    fits = [ind.fitness for ind in population]
                    oracle_path = run_generation_oracle(
                        gen_dir=prev_gen_dir, generation=prev_gen,
                        rollouts_by_individual=rollouts_by_ind,
                        scoreboard=scoreboard,
                        best=max(fits), mean=sum(fits)/len(fits), worst=min(fits),
                        llm_client=oracle_client_resume, llm_model=eval_llm_cfg["model"],
                        task_manifest=task_manifest,
                        audit_logger=audit_logger, error_logger=error_logger,
                    )
                    if oracle_path and oracle_path.exists():
                        resume_oracle_feedback = oracle_path.read_text(encoding="utf-8")
                        print(f"    [resume] Oracle feedback regenerated ({len(resume_oracle_feedback)} chars)")
                except Exception as e:
                    print(f"    [resume] ⚠ Oracle regeneration failed: {e}")
                    print(f"    [resume] Proceeding without oracle feedback (degraded).")

            resume_skill_patch_plan = None
            resume_skill_patch_plan_text = None
            if resume_oracle_feedback:
                resume_skill_patch_plan_obj = build_skill_patch_plan(
                    resume_oracle_feedback,
                    execution_contract,
                )
                resume_skill_patch_plan = resume_skill_patch_plan_obj.to_dict()
                if lesson_bank_cfg.get("enabled", True):
                    lesson_bank = update_lesson_bank(
                        output_dir=output_dir,
                        gen_dir=prev_gen_dir,
                        generation=prev_gen,
                        task_manifest=task_manifest,
                        generation_metrics_path=prev_gen_dir / "generation_metrics.json",
                        oracle_feedback_text=resume_oracle_feedback,
                        skill_patch_plan=resume_skill_patch_plan,
                        change_eval=None,
                    )
                    if lesson_bank_cfg.get("include_in_mutation_handoff", True):
                        lesson_bank_text = format_lesson_bank_for_mutation(
                            lesson_bank,
                            max_chars=int(lesson_bank_cfg.get("mutation_handoff_max_chars", 7000)),
                        )
                        if "### " in lesson_bank_text:
                            resume_oracle_feedback = resume_oracle_feedback + "\n\n" + lesson_bank_text
                            resume_skill_patch_plan_obj = build_skill_patch_plan(
                                resume_oracle_feedback,
                                execution_contract,
                            )
                            resume_skill_patch_plan = resume_skill_patch_plan_obj.to_dict()
                write_skill_patch_plan_artifacts(prev_gen_dir, resume_skill_patch_plan_obj)
                resume_skill_patch_plan = resume_skill_patch_plan_obj.to_dict()
                resume_skill_patch_plan_text = format_skill_patch_plan(resume_skill_patch_plan_obj)

            next_gen: list[Individual] = []
            if standard_ea_enabled and standard_ea_cfg.get("carry_evaluated_survivor", True):
                next_gen.append(_carry_prompt_for_reevaluation(
                    population[0],
                    start_gen,
                    f"ea_survivor_from_gen{prev_gen}",
                ))
                print("    Standard EA: carried evaluated survivor forward on resume")
            elif (
                semantic_skill_selection_cfg.get("enabled", True)
                and semantic_skill_selection_cfg.get("carry_incumbent", True)
                and semantic_incumbent is not None
                and pop_size > 1
            ):
                next_gen.append(_clone_individual_for_generation(
                    semantic_incumbent,
                    start_gen,
                    f"semantic_incumbent_from_gen{prev_gen}",
                ))
                print("    Semantic incumbent: carried forward on resume")
            elite_candidates = _breeding_pool_with_survivor(population, best_ever, parent_child_survival)
            elite_candidates.sort(key=lambda x: x.fitness, reverse=True)
            for i in range(min(elitism, len(elite_candidates))):
                if len(next_gen) >= pop_size:
                    break
                if _prompt_in_population(elite_candidates[i].prompt, next_gen):
                    continue
                elite = Individual(
                    elite_candidates[i].prompt,
                    generation=start_gen,
                    parent_info=f"elite_{i}_from_gen{prev_gen}",
                )
                next_gen.append(elite)
                print(f"    Elite {i}: carried forward (selection={elite_candidates[i].fitness:.3f})")
            breeding_pool = _breeding_pool_with_survivor(population, best_ever, parent_child_survival)
            while len(next_gen) < pop_size:
                if standard_ea_enabled and standard_ea_cfg.get("mutation_parent", "survivor") == "survivor":
                    parent_a = population[0]
                    parent_b = population[0]
                elif (
                    semantic_skill_selection_cfg.get("enabled", True)
                    and semantic_skill_selection_cfg.get("prefer_incumbent_parent", True)
                    and semantic_incumbent is not None
                ):
                    parent_a = semantic_incumbent
                    parent_b = semantic_incumbent
                elif parent_child_survival and best_ever is not None and pop_size == 1:
                    parent_a, survival_reason = _single_lineage_parent(
                        population[0],
                        best_ever,
                        single_lineage_survival_margin,
                    )
                    parent_b = parent_a
                    if survival_reason == "best_ever_after_regression":
                        print(
                            f"    Survival: mutating best-ever parent "
                            f"(selection={best_ever.fitness:.3f}) instead of regressed current best "
                            f"({population[0].fitness:.3f})"
                        )
                else:
                    parent_a = tournament_select(breeding_pool, tournament_size)
                    parent_b = tournament_select(breeding_pool, tournament_size)
                child_prompt = parent_a.prompt
                child_origin_steps = ["parent"]
                child_semantic_retention: dict = {}
                child_semantic_selection: dict = {}
                last_process_record: dict | None = None
                last_candidate_parent_prompt = parent_a.prompt
                last_selector_stage = "parent"
                if random.random() < crossover_rate:
                    try:
                        child_budget = _candidate_skill_budget(parent_a.prompt, max_skill_length, skill_sanitizer_cfg)
                        child_prompt = crossover_prompts(
                            client, mutation_model,
                            parent_a.prompt, parent_b.prompt, objective,
                            oracle_feedback=resume_oracle_feedback,
                            skill_patch_plan=resume_skill_patch_plan_text,
                            execution_constraints=execution_constraints_text,
                            max_chars=child_budget,
                            audit_logger=audit_logger,
                            temperature=mutation_temperature,
                        )
                        child_prompt, process_record = process_candidate_skill_for_injection(
                            client=client,
                            mutation_model=mutation_model,
                            objective=objective,
                            output_dir=output_dir,
                            generation=prev_gen,
                            child_slot=len(next_gen),
                            parent_info=parent_a.parent_info,
                            stage="resume_crossover",
                            candidate=child_prompt,
                            parent_prompt=parent_a.prompt,
                            max_skill_length=max_skill_length,
                            sanitizer_cfg=skill_sanitizer_cfg,
                            execution_contract=execution_contract,
                            execution_constraints_text=execution_constraints_text,
                            skill_patch_plan_text=resume_skill_patch_plan_text,
                            skill_patch_plan=resume_skill_patch_plan,
                            integration_cfg=skill_integration_cfg,
                            repair_cfg=mutation_repair_cfg,
                            audit_logger=audit_logger,
                        )
                        child_semantic_retention = build_semantic_retention_metadata(
                            generation=prev_gen,
                            next_generation=start_gen,
                            child_slot=len(next_gen),
                            stage="resume_crossover",
                            parent_info=parent_a.parent_info,
                            parent_prompt=parent_a.prompt,
                            candidate_prompt=child_prompt,
                            process_record=process_record,
                            skill_patch_plan=resume_skill_patch_plan,
                        )
                        last_process_record = process_record
                        last_candidate_parent_prompt = parent_a.prompt
                        last_selector_stage = "resume_crossover"
                        child_origin_steps.append("crossover")
                    except Exception as e:
                        print(f"      Crossover failed: {e}, using parent A")
                        child_prompt = parent_a.prompt
                if random.random() < mutation_rate:
                    child_slot = len(next_gen)
                    mutation_parent_prompt = child_prompt
                    try:
                        child_budget = _candidate_skill_budget(mutation_parent_prompt, max_skill_length, skill_sanitizer_cfg)
                        mutated_prompt = mutate_prompt(
                            client, mutation_model,
                            mutation_parent_prompt, objective,
                            oracle_feedback=resume_oracle_feedback,
                            skill_patch_plan=resume_skill_patch_plan_text,
                            execution_constraints=execution_constraints_text,
                            max_chars=child_budget,
                            audit_logger=audit_logger,
                            temperature=mutation_temperature,
                        )
                        sanitized_prompt, process_record = process_candidate_skill_for_injection(
                            client=client,
                            mutation_model=mutation_model,
                            objective=objective,
                            output_dir=output_dir,
                            generation=prev_gen,
                            child_slot=child_slot,
                            parent_info=parent_a.parent_info,
                            stage="resume_mutation",
                            candidate=mutated_prompt,
                            parent_prompt=mutation_parent_prompt,
                            max_skill_length=max_skill_length,
                            sanitizer_cfg=skill_sanitizer_cfg,
                            execution_contract=execution_contract,
                            execution_constraints_text=execution_constraints_text,
                            skill_patch_plan_text=resume_skill_patch_plan_text,
                            skill_patch_plan=resume_skill_patch_plan,
                            integration_cfg=skill_integration_cfg,
                            repair_cfg=mutation_repair_cfg,
                            audit_logger=audit_logger,
                        )
                        health = validate_mutated_skill(sanitized_prompt, mutation_parent_prompt, child_budget)
                        health["metrics"]["raw_candidate_chars"] = len(mutated_prompt or "")
                        health["metrics"]["sanitizer"] = process_record["sanitizer"]
                        health["metrics"]["skill_integration"] = process_record["skill_integration"]["metrics"]
                        health["metrics"]["repair_attempted"] = process_record["repair_attempted"]
                        health_record = write_mutation_health_record(
                            output_dir,
                            prev_gen,
                            {
                                "status": "ok" if health["ok"] else "invalid_output",
                                "ok": health["ok"],
                                "next_generation": start_gen,
                                "child_slot": child_slot,
                                "parent_info": parent_a.parent_info,
                                "mutation_model": mutation_model,
                                "mutation_temperature": mutation_temperature,
                                "has_oracle_feedback": bool(resume_oracle_feedback),
                                "resume_breeding": True,
                                "issues": health["issues"],
                                "metrics": health["metrics"],
                            },
                        )
                        if not health["ok"]:
                            raise MutationValidationError(
                                "mutator returned invalid skill: " + ", ".join(health["issues"])
                            )
                        child_prompt = sanitized_prompt
                        child_semantic_retention = build_semantic_retention_metadata(
                            generation=prev_gen,
                            next_generation=start_gen,
                            child_slot=child_slot,
                            stage="resume_mutation",
                            parent_info=parent_a.parent_info,
                            parent_prompt=mutation_parent_prompt,
                            candidate_prompt=child_prompt,
                            process_record=process_record,
                            skill_patch_plan=resume_skill_patch_plan,
                        )
                        last_process_record = process_record
                        last_candidate_parent_prompt = mutation_parent_prompt
                        last_selector_stage = "resume_mutation"
                        child_origin_steps.append("mutation")
                    except Exception as e:
                        if isinstance(e, MutationValidationError):
                            write_mutation_health_record(
                                output_dir,
                                prev_gen,
                                {
                                    "status": "invalid_output",
                                    "ok": False,
                                    "next_generation": start_gen,
                                    "child_slot": child_slot,
                                    "parent_info": parent_a.parent_info,
                                    "mutation_model": mutation_model,
                                    "mutation_temperature": mutation_temperature,
                                    "has_oracle_feedback": bool(resume_oracle_feedback),
                                    "resume_breeding": True,
                                    "issues": ["post_mutation_gate_rejected"],
                                    "exception_msg": str(e),
                                    "metrics": {
                                        "parent_chars": len(mutation_parent_prompt),
                                        "candidate_chars": 0,
                                        "delta_chars": -len(mutation_parent_prompt),
                                        "max_chars": max_skill_length,
                                        "parent_sha256": _sha256_text(mutation_parent_prompt),
                                    },
                                },
                            )
                        else:
                            write_mutation_health_record(
                                output_dir,
                                prev_gen,
                                {
                                    "status": "exception",
                                    "ok": False,
                                    "next_generation": start_gen,
                                    "child_slot": child_slot,
                                    "parent_info": parent_a.parent_info,
                                    "mutation_model": mutation_model,
                                    "mutation_temperature": mutation_temperature,
                                    "has_oracle_feedback": bool(resume_oracle_feedback),
                                    "resume_breeding": True,
                                    "issues": ["mutation_exception"],
                                    "exception_type": type(e).__name__,
                                    "exception_msg": str(e),
                                    "metrics": {
                                        "parent_chars": len(mutation_parent_prompt),
                                        "candidate_chars": 0,
                                        "delta_chars": -len(mutation_parent_prompt),
                                        "max_chars": max_skill_length,
                                        "parent_sha256": _sha256_text(mutation_parent_prompt),
                                    },
                                },
                            )
                        print(f"      Mutation unhealthy: {e}, keeping unmutated")
                if last_process_record is not None:
                    if (
                        standard_ea_enabled
                        and standard_ea_cfg.get("defer_child_semantic_selection_to_rollout", True)
                    ):
                        child_semantic_selection = defer_child_semantic_selection(
                            parent_prompt=last_candidate_parent_prompt,
                            candidate_prompt=child_prompt,
                            process_record=last_process_record,
                            output_dir=output_dir,
                            gen_dir=prev_gen_dir,
                            generation=prev_gen,
                            child_slot=len(next_gen),
                            stage=last_selector_stage,
                            parent_info=parent_a.parent_info,
                            skill_patch_plan=resume_skill_patch_plan,
                        )
                        child_origin_steps.append("semantic_selector_deferred")
                    else:
                        selected_prompt, child_semantic_selection = apply_semantic_skill_selection(
                            parent_prompt=last_candidate_parent_prompt,
                            candidate_prompt=child_prompt,
                            process_record=last_process_record,
                            output_dir=output_dir,
                            gen_dir=prev_gen_dir,
                            generation=prev_gen,
                            child_slot=len(next_gen),
                            stage=last_selector_stage,
                            parent_info=parent_a.parent_info,
                            skill_patch_plan=resume_skill_patch_plan,
                            execution_contract=execution_contract,
                            skill_integration_cfg=skill_integration_cfg,
                            semantic_skill_selection_cfg=semantic_skill_selection_cfg,
                        )
                        if selected_prompt != child_prompt:
                            child_origin_steps.append("semantic_selector_kept_parent")
                        else:
                            child_origin_steps.append("semantic_selector_accepted")
                        child_prompt = selected_prompt
                child = Individual(
                    child_prompt,
                    generation=start_gen,
                    parent_info=f"child_gen{start_gen}_{len(next_gen)}",
                )
                child.parent_prompt = parent_a.prompt
                child.parent_fitness = parent_a.fitness
                child.parent_fitness_result = copy.deepcopy(parent_a.fitness_result)
                child.parent_sha256 = _sha256_text(parent_a.prompt)
                child.child_origin = "+".join(child_origin_steps)
                child.semantic_retention = child_semantic_retention
                child.semantic_selection = child_semantic_selection
                next_gen.append(child)
            if (
                not standard_ea_enabled
                and semantic_skill_selection_cfg.get("enabled", True)
                and semantic_incumbent is not None
            ):
                new_incumbent, incumbent_decision = choose_semantic_incumbent(
                    current_incumbent=semantic_incumbent,
                    candidates=next_gen,
                    cfg=semantic_skill_selection_cfg,
                )
                semantic_incumbent = _clone_individual_for_generation(
                    new_incumbent,
                    start_gen,
                    "semantic_incumbent",
                )
                _write_json(prev_gen_dir / "semantic_incumbent_decision.json", {
                    "generation": prev_gen,
                    "next_generation": start_gen,
                    "config": semantic_skill_selection_cfg,
                    **incumbent_decision,
                })
                (output_dir / "semantic_incumbent.md").write_text(semantic_incumbent.prompt, encoding="utf-8")
            population = next_gen
            print(f"  Bred {len(population)} individuals for gen {start_gen}")

        print(f"  Starting from generation {start_gen}")
        print()
    else:
        print(f"── Initializing population ({pop_size} individuals) ──")
        population = []
        population.append(Individual(seed_skill, generation=0, parent_info="original"))
        semantic_incumbent = Individual(seed_skill, generation=0, parent_info="semantic_incumbent_seed")
        semantic_incumbent.semantic_selection = {
            "decision": "seed_incumbent",
            "rollout_fitness_used_for_selection": False,
            "candidate_score": {"score": 0.0},
        }
        print(f"  [0] Original seed skill ({len(seed_skill)} chars)")

        for i in range(1, pop_size):
            print(f"  [{i}] Mutating seed skill...")
            try:
                child_budget = _candidate_skill_budget(seed_skill, max_skill_length, skill_sanitizer_cfg)
                mutated = mutate_prompt(
                    client, mutation_model, seed_skill, objective,
                    execution_constraints=execution_constraints_text,
                    max_chars=child_budget,
                    audit_logger=audit_logger,
                    temperature=mutation_temperature,
                )
                sanitized, process_record = process_candidate_skill_for_injection(
                    client=client,
                    mutation_model=mutation_model,
                    objective=objective,
                    output_dir=output_dir,
                    generation=0,
                    child_slot=i,
                    parent_info="original",
                    stage="initial_mutation",
                    candidate=mutated,
                    parent_prompt=seed_skill,
                    max_skill_length=max_skill_length,
                    sanitizer_cfg=skill_sanitizer_cfg,
                    execution_contract=execution_contract,
                    execution_constraints_text=execution_constraints_text,
                    skill_patch_plan_text=None,
                    skill_patch_plan=None,
                    integration_cfg=skill_integration_cfg,
                    repair_cfg=mutation_repair_cfg,
                    audit_logger=audit_logger,
                )
                health = validate_mutated_skill(sanitized, seed_skill, child_budget)
                health["metrics"]["raw_candidate_chars"] = len(mutated or "")
                health["metrics"]["sanitizer"] = process_record["sanitizer"]
                health["metrics"]["skill_integration"] = process_record["skill_integration"]["metrics"]
                health["metrics"]["repair_attempted"] = process_record["repair_attempted"]
                write_mutation_health_record(
                    output_dir,
                    0,
                    {
                        "status": "ok" if health["ok"] else "invalid_output",
                        "ok": health["ok"],
                        "next_generation": 0,
                        "child_slot": i,
                        "parent_info": "original",
                        "mutation_model": mutation_model,
                        "mutation_temperature": mutation_temperature,
                        "has_oracle_feedback": False,
                        "initial_population": True,
                        "issues": health["issues"],
                        "metrics": health["metrics"],
                    },
                )
                if not health["ok"]:
                    raise MutationValidationError(
                        "mutator returned invalid skill: " + ", ".join(health["issues"])
                    )
                population.append(Individual(sanitized, generation=0, parent_info=f"init_mutant_{i}"))
                print(f"       → {len(sanitized)} chars")
            except Exception as e:
                if isinstance(e, MutationValidationError):
                    write_mutation_health_record(
                        output_dir,
                        0,
                        {
                            "status": "invalid_output",
                            "ok": False,
                            "next_generation": 0,
                            "child_slot": i,
                            "parent_info": "original",
                            "mutation_model": mutation_model,
                            "mutation_temperature": mutation_temperature,
                            "has_oracle_feedback": False,
                            "initial_population": True,
                            "issues": ["post_mutation_gate_rejected"],
                            "exception_msg": str(e),
                            "metrics": {
                                "parent_chars": len(seed_skill),
                                "candidate_chars": 0,
                                "delta_chars": -len(seed_skill),
                                "max_chars": max_skill_length,
                                "parent_sha256": _sha256_text(seed_skill),
                            },
                        },
                    )
                else:
                    write_mutation_health_record(
                        output_dir,
                        0,
                        {
                            "status": "exception",
                            "ok": False,
                            "next_generation": 0,
                            "child_slot": i,
                            "parent_info": "original",
                            "mutation_model": mutation_model,
                            "mutation_temperature": mutation_temperature,
                            "has_oracle_feedback": False,
                            "initial_population": True,
                            "issues": ["mutation_exception"],
                            "exception_type": type(e).__name__,
                            "exception_msg": str(e),
                            "metrics": {
                                "parent_chars": len(seed_skill),
                                "candidate_chars": 0,
                                "delta_chars": -len(seed_skill),
                                "max_chars": max_skill_length,
                                "parent_sha256": _sha256_text(seed_skill),
                            },
                        },
                    )
                print(f"       → Mutation unhealthy: {e}, using seed copy")
                population.append(Individual(seed_skill, generation=0, parent_info=f"seed_copy_{i}"))

    # ── Generational loop ───────────────────────────────────────────

    for gen in range(start_gen, generations + 1):
        gen_t0 = time.time()
        audit_logger.set_generation(gen)
        print(f"\n{'=' * 70}")
        print(f"  Generation {gen}/{generations}")
        print(f"{'=' * 70}")

        # ── GUARD: population integrity ──
        if len(population) != pop_size:
            print(f"  [GUARD] ✗ Population size mismatch: expected {pop_size}, got {len(population)}")
        for i, ind in enumerate(population):
            if not ind.prompt or len(ind.prompt) < 100:
                print(f"  [GUARD] ✗ Individual {i} ({ind.parent_info}) has suspiciously short prompt ({len(ind.prompt)} chars)")
            if max_skill_length > 0 and len(ind.prompt) > max_skill_length * 1.1:
                print(f"  [GUARD] ⚠ Individual {i} ({ind.parent_info}) prompt exceeds budget: {len(ind.prompt)} > {max_skill_length}")

        gen_span_ctx = trace_generation(gen, len(population)) if telemetry_enabled else None
        gen_span = gen_span_ctx.__enter__() if gen_span_ctx else None

        # Per-gen timing tracker (writes gen_dir/timing.json when gen finishes)
        gen_timer = GenTimer(output_dir / f"gen{gen}", enabled=(telemetry_mode == "debug"))

        # ── Per-generation output directory structure ──
        # Layout:
        #   output_dir/gen<N>/
        #     ├── individuals/ind<I>.md + ind<I>_meta.json
        #     ├── rollouts/ind<I>/...
        #     ├── task_insights/... (Layer 1, written by streaming oracle)
        #     ├── cross_task/...    (Layer 2, written by streaming oracle)
        #     └── oracle_feedback.md (Layer 3, written by streaming oracle)
        gen_dir = output_dir / f"gen{gen}"
        individuals_dir = gen_dir / "individuals"
        individuals_dir.mkdir(parents=True, exist_ok=True)
        task_skill_alias = _single_task_alias(task_manifest) if skill_scope == "per_task" else None

        print(f"\n  ── Evaluating {len(population)} individuals ──")
        _eval_phase_t0 = time.time()
        heartbeat.update(phase="fitness_eval_gen_start", generation=gen,
                         message=f"evaluating {len(population)} individuals")
        for idx, ind in enumerate(population):
            trial_id = f"gen{gen}_ind{idx}"
            heartbeat.update(phase="fitness_eval", generation=gen,
                             individual_idx=idx, individual_parent=ind.parent_info,
                             context={"prompt_chars": len(ind.prompt), "trial_id": trial_id})
            print(f"\n  [{idx}] {ind.parent_info}")

            # Save the individual's skill document before evaluation
            skill_path = individuals_dir / f"ind{idx}.md"
            skill_path.write_text(ind.prompt, encoding="utf-8")
            if task_skill_alias:
                task_skill_path = individuals_dir / f"gen{gen}_task_{task_skill_alias}_ind{idx}_skill.md"
                task_skill_path.write_text(ind.prompt, encoding="utf-8")

            eval_span_ctx = trace_fitness_eval(trial_id, gen, idx) if telemetry_enabled else None
            eval_span = eval_span_ctx.__enter__() if eval_span_ctx else None

            if dry_run:
                ind.fitness = random.random()
                ind.fitness_result = {
                    "pass_at_1": ind.fitness,
                    "progress_fitness": 0.0,
                    "selection_fitness": ind.fitness,
                    "per_task": {},
                    "dry_run": True,
                    "individual_index": idx,
                    "trial_id": trial_id,
                }
                print(f"       → DRY RUN fitness: {ind.fitness:.3f}")
            else:
                work_dir = gen_dir / "rollouts" / f"ind{idx}"
                try:
                    result = evaluate_prompt(
                        skill_text=ind.prompt,
                        tasks=tasks_data,
                        ng_collect_bin=ng_collect_bin,
                        work_dir=work_dir,
                        agent_name=agent_name,
                        num_repeats=num_repeats,
                        num_parallel=num_parallel,
                        timeout=fitness_timeout,
                        trial_id=trial_id,
                        eval_llm_cfg=eval_llm_cfg,
                        run_analyzer_flag=run_analyzer_flag,
                        repo_root=repo_root,
                        nemogym_root=nemogym_root,
                        ng_config_paths=ng_config_paths,
                        rollout_model_cfg=rollout_model_cfg,
                        skill_monitor_cfg=skill_monitor_cfg,
                        runtime_verifier_feedback_cfg=runtime_verifier_feedback_cfg,
                    )
                    result["individual_index"] = idx
                    result["trial_id"] = trial_id
                    ind.fitness = result.get("selection_fitness", result["pass_at_1"])
                    ind.fitness_result = result
                    analyzer_tag = " +report" if result.get("analyzer_report") else ""
                    print(
                        f"       → selection: {ind.fitness:.3f} "
                        f"(pass@1={result['pass_at_1']:.3f}, progress={result.get('progress_fitness', 0):.3f}; "
                        f"{result['num_rollouts']} rollouts, {result['elapsed']:.0f}s){analyzer_tag}"
                    )

                    # Write per-individual metadata for audit trail. This may
                    # be overwritten below if challenger evaluation restores a
                    # parent into this slot.
                    write_individual_eval_artifacts(individuals_dir, gen, idx, ind)
                except RolloutModelMismatchError as e:
                    print(f"       → ✗ ROLLOUT MODEL MISMATCH: {e}")
                    print("       → Aborting run because optimizer metrics would not reflect the configured rollout model.")
                    error_logger.record(
                        phase="fitness_evaluation",
                        generation=gen,
                        context={
                            "individual_idx": idx,
                            "parent_info": ind.parent_info,
                            "trial_id": trial_id,
                            "configured_rollout_model": rollout_model_cfg.get("model"),
                        },
                        exception=e,
                        severity="critical",
                    )
                    heartbeat.update(
                        phase="rollout_model_mismatch",
                        generation=gen,
                        individual_idx=idx,
                        individual_parent=ind.parent_info,
                        context={"configured_rollout_model": rollout_model_cfg.get("model")},
                        message=str(e),
                    )
                    raise
                except RolloutResponseError as e:
                    print(f"       → ✗ ROLLOUT RESPONSE ERROR: {e}")
                    print("       → Aborting run because rollout artifacts are infrastructure/API failures, not valid agent attempts.")
                    error_logger.record(
                        phase="fitness_evaluation",
                        generation=gen,
                        context={
                            "individual_idx": idx,
                            "parent_info": ind.parent_info,
                            "trial_id": trial_id,
                            "configured_rollout_model": rollout_model_cfg.get("model"),
                        },
                        exception=e,
                        severity="critical",
                    )
                    heartbeat.update(
                        phase="rollout_response_error",
                        generation=gen,
                        individual_idx=idx,
                        individual_parent=ind.parent_info,
                        context={"configured_rollout_model": rollout_model_cfg.get("model")},
                        message=str(e),
                    )
                    raise
                except Exception as e:
                    print(f"       → ⚠ EVALUATION FAILED: {e}")
                    print(f"       → Assigning fitness 0.0 and continuing")
                    error_logger.record(
                        phase="fitness_evaluation",
                        generation=gen,
                        context={"individual_idx": idx, "parent_info": ind.parent_info,
                                 "trial_id": trial_id},
                        exception=e,
                        severity="error",
                    )
                    ind.fitness = 0.0
                    ind.fitness_result = {
                        "pass_at_1": 0.0,
                        "progress_fitness": 0.0,
                        "selection_fitness": 0.0,
                        "per_task": {},
                        "num_rollouts": 0,
                        "elapsed": 0,
                        "error": str(e),
                        "individual_index": idx,
                        "trial_id": trial_id,
                    }

            write_individual_eval_artifacts(individuals_dir, gen, idx, ind)

            if eval_span and eval_span_ctx:
                eval_span.set_attribute("ga.fitness", ind.fitness)
                eval_span.set_attribute("ga.num_rollouts", ind.fitness_result.get("num_rollouts", 0))
                eval_span.set_attribute("ga.elapsed", ind.fitness_result.get("elapsed", 0))
                eval_span.set_attribute("ga.parent_info", ind.parent_info)
                eval_span.set_attribute("ga.prompt_length", len(ind.prompt))
                eval_span_ctx.__exit__(None, None, None)

        challenger_records = []
        if not (
            standard_ea_enabled
            and standard_ea_cfg.get("disable_parent_child_challenger", True)
        ):
            challenger_records = run_parent_child_challengers(
                population=population,
                generation=gen,
                gen_dir=gen_dir,
                challenger_cfg=parent_child_challenger_cfg,
                tasks_data=tasks_data,
                ng_collect_bin=ng_collect_bin,
                agent_name=agent_name,
                num_repeats=num_repeats,
                num_parallel=num_parallel,
                fitness_timeout=fitness_timeout,
                eval_llm_cfg=eval_llm_cfg,
                run_analyzer_flag=run_analyzer_flag,
                repo_root=repo_root,
                nemogym_root=nemogym_root,
                ng_config_paths=ng_config_paths,
                rollout_model_cfg=rollout_model_cfg,
                skill_monitor_cfg=skill_monitor_cfg,
                runtime_verifier_feedback_cfg=runtime_verifier_feedback_cfg,
                dry_run=dry_run,
            )
        if challenger_records:
            for idx, ind in enumerate(population):
                write_individual_eval_artifacts(individuals_dir, gen, idx, ind)
            print(
                f"  [challenger] {sum(1 for r in challenger_records if r.get('status') == 'challenged')} "
                f"parent challenger(s), {sum(1 for r in challenger_records if r.get('decision') == 'restore_parent')} restore(s)"
            )

        combined_selection_records = _apply_combined_selection_fitness(
            population=population,
            generation=gen,
            gen_dir=gen_dir,
            cfg=combined_selection_cfg,
        )
        if combined_selection_records:
            for idx, ind in enumerate(population):
                write_individual_eval_artifacts(individuals_dir, gen, idx, ind)
            best_preview = max(combined_selection_records, key=lambda r: r["combined_selection_fitness"])
            print(
                "  [selection] combined robust fitness applied: "
                f"best ind{best_preview['individual_index']}="
                f"{best_preview['combined_selection_fitness']:.3f}, "
                f"skillQ={best_preview['skill_quality']:.3f}, "
                f"lcb={best_preview['progress_lcb_95']:.3f}"
            )

        population.sort(key=lambda x: x.fitness, reverse=True)
        if standard_ea_enabled:
            semantic_survivors_for_next_gen = []
            semantic_survivor_records = []
            semantic_incumbent = _clone_individual_for_generation(
                population[0],
                gen,
                f"evaluated_survivor_from_gen{gen}",
            )
            semantic_incumbent.semantic_selection = make_standard_ea_survivor_record(
                generation=gen,
                survivor=population[0],
            )
            _write_json(gen_dir / "ea_survivor_decision.json", semantic_incumbent.semantic_selection)
            (gen_dir / "ea_survivor_skill.md").write_text(semantic_incumbent.prompt, encoding="utf-8")
            (output_dir / "semantic_incumbent.md").write_text(semantic_incumbent.prompt, encoding="utf-8")
            print(
                "  [standard-ea] evaluated survivor selected: "
                f"{semantic_incumbent.parent_info} (selection={population[0].fitness:.3f})"
            )
        else:
            semantic_survivors_for_next_gen, semantic_survivor_records = select_semantic_survivors(
                population=population,
                generation=gen,
                cfg=semantic_survivor_cfg,
            )
        if (not standard_ea_enabled) and semantic_survivor_cfg.get("enabled", True):
            _write_json(gen_dir / "semantic_survivor_selection.json", {
                "generation": gen,
                "config": semantic_survivor_cfg,
                "selected_count": len(semantic_survivors_for_next_gen),
                "records": semantic_survivor_records,
            })
            if semantic_survivors_for_next_gen:
                picked = ", ".join(s.parent_info for s in semantic_survivors_for_next_gen)
                print(f"  [semantic-survivor] preserving {len(semantic_survivors_for_next_gen)} near-fitness high-coverage child: {picked}")

        print(f"\n  ── Generation {gen} rankings ──")
        for idx, ind in enumerate(population):
            marker = " ★" if idx == 0 else ""
            pass_rate = (getattr(ind, "fitness_result", None) or {}).get("pass_at_1", ind.fitness)
            progress = (getattr(ind, "fitness_result", None) or {}).get("progress_fitness", 0.0)
            print(
                f"    {idx+1}. selection={ind.fitness:.3f} "
                f"(pass@1={pass_rate:.3f}, progress={progress:.3f}; {ind.parent_info}){marker}"
            )

        gen_timer.add("fitness_evaluation", time.time() - _eval_phase_t0)

        # ── Generation diagnostic summary ──
        fitnesses = [ind.fitness for ind in population]
        pass_fitnesses = [
            (getattr(ind, "fitness_result", None) or {}).get("pass_at_1", ind.fitness)
            for ind in population
        ]
        progress_fitnesses = [
            (getattr(ind, "fitness_result", None) or {}).get("progress_fitness", 0.0)
            for ind in population
        ]
        gen_best, gen_mean, gen_worst = max(fitnesses), sum(fitnesses)/len(fitnesses), min(fitnesses)
        reports_generated = sum(1 for ind in population
                                if (getattr(ind, 'fitness_result', None) or {}).get("analyzer_report"))
        zero_count = sum(1 for f in fitnesses if f == 0.0)

        all_tasks: dict[str, list[float]] = {}
        for ind in population:
            fr = getattr(ind, 'fitness_result', None) or {}
            for tid, val in fr.get("per_task", {}).items():
                rate = val.get("pass_at_1", 0.0) if isinstance(val, dict) else float(val)
                short = tid.replace("cvdp_agentic_heavy_", "")
                all_tasks.setdefault(short, []).append(rate)

        print(f"\n  ── Generation {gen} diagnostics ──")
        print(f"    Selection fitness: best={gen_best:.3f} mean={gen_mean:.3f} worst={gen_worst:.3f}")
        print(
            f"    True pass@1: best={max(pass_fitnesses):.3f} "
            f"mean={sum(pass_fitnesses)/len(pass_fitnesses):.3f} "
            f"worst={min(pass_fitnesses):.3f}"
        )
        total_passes = 0
        total_attempts = 0
        for ind in population:
            for val in ((getattr(ind, "fitness_result", None) or {}).get("per_task", {}) or {}).values():
                if isinstance(val, dict):
                    total_passes += int(val.get("passes", 0) or 0)
                    total_attempts += int(val.get("attempts", 0) or 0)
        if total_attempts:
            pass_ci = _wilson_ci_95(total_passes, total_attempts)
            print(
                f"    Rollout pass-rate 95% CI: "
                f"{pass_ci['low']:.1%}-{pass_ci['high']:.1%} "
                f"({total_passes}/{total_attempts}, Wilson)"
            )
        if any(progress_fitnesses):
            print(
                f"    Progress fitness: best={max(progress_fitnesses):.3f} "
                f"mean={sum(progress_fitnesses)/len(progress_fitnesses):.3f} "
                f"worst={min(progress_fitnesses):.3f}"
            )
        proof_skill_q = [
            _safe_float((getattr(ind, "fitness_result", None) or {}).get("skill_quality"), _skill_quality_from_individual(ind))
            for ind in population
        ]
        proof_behavior_q = [
            _safe_float((getattr(ind, "fitness_result", None) or {}).get("agent_behavior_quality"), 0.0)
            for ind in population
        ]
        proof_variance_q = [
            _safe_float((getattr(ind, "fitness_result", None) or {}).get("rollout_variance_quality"), 0.0)
            for ind in population
        ]
        proof_adherence_q = [
            _safe_float((getattr(ind, "fitness_result", None) or {}).get("skill_adherence_quality"), 0.0)
            for ind in population
        ]
        if proof_skill_q:
            print(
                "    Q metrics: "
                f"SkillQ mean={sum(proof_skill_q)/len(proof_skill_q):.3f}, "
                f"BehaviorQ mean={sum(proof_behavior_q)/len(proof_behavior_q):.3f}, "
                f"VarianceQ mean={sum(proof_variance_q)/len(proof_variance_q):.3f}, "
                f"AdherenceQ mean={sum(proof_adherence_q)/len(proof_adherence_q):.3f}"
            )
        print(f"    Analyzer reports: {reports_generated}/{len(population)}")
        if zero_count:
            print(f"    ⚠ {zero_count}/{len(population)} individuals scored 0.0")
        if all_tasks:
            print(f"    Per-task (population-aggregated):")
            for tid in sorted(all_tasks.keys()):
                rates = all_tasks[tid]
                avg = sum(rates) / len(rates)
                tag = "✓" if avg > 0.5 else "~" if avg > 0 else "✗"
                print(f"      {tag} {tid}: avg={avg:.0%} ({len([r for r in rates if r > 0])}/{len(rates)} individuals pass)")

        previous_generation_best = history[-1]["best_fitness"] if history else None
        regression_reflection_text: str | None = None
        change_attribution_handoff_text: str | None = None
        change_eval: dict | None = None

        if best_ever is None or population[0].fitness > best_ever.fitness:
            best_ever = copy.deepcopy(population[0])
            print(f"\n  New best ever: {best_ever.fitness:.3f}")

        gen_record = {
            "generation": gen,
            "best_fitness": population[0].fitness,
            "worst_fitness": population[-1].fitness,
            "mean_fitness": sum(ind.fitness for ind in population) / len(population),
            "best_ever": best_ever.fitness,
            "individuals": [ind.to_dict() for ind in population],
            "ea_flow": "standard_evaluated_survivor" if standard_ea_enabled else "legacy_semantic_incumbent",
            "semantic_survivor_selected": [ind.to_dict() for ind in semantic_survivors_for_next_gen],
            "semantic_incumbent": semantic_incumbent.to_dict() if semantic_incumbent is not None else None,
        }
        history.append(gen_record)

        best_path = gen_dir / "best_skill.md"
        best_path.write_text(population[0].prompt, encoding="utf-8")
        if semantic_incumbent is not None:
            semantic_best_path = gen_dir / "semantic_incumbent_skill.md"
            semantic_best_path.write_text(semantic_incumbent.prompt, encoding="utf-8")
        if task_skill_alias:
            task_best_path = gen_dir / f"gen{gen}_task_{task_skill_alias}_best_skill.md"
            task_best_path.write_text(population[0].prompt, encoding="utf-8")
            if semantic_incumbent is not None:
                task_semantic_path = gen_dir / f"gen{gen}_task_{task_skill_alias}_semantic_incumbent_skill.md"
                task_semantic_path.write_text(semantic_incumbent.prompt, encoding="utf-8")
        write_generation_traceability_artifacts(
            gen_dir=gen_dir,
            output_dir=output_dir,
            generation=gen,
            population=population,
            task_manifest=task_manifest,
            skill_scope=skill_scope,
        )

        if change_attribution_cfg.get("enabled", True):
            try:
                change_eval = write_change_attribution_artifacts(
                    output_dir=output_dir,
                    gen_dir=gen_dir,
                    generation=gen,
                    population=population,
                    task_manifest=task_manifest,
                    config=change_attribution_cfg,
                )
                summary = change_eval.get("summary") or {}
                verdicts = summary.get("verdict_counts") or {}
                verdict_text = ", ".join(f"{k}={v}" for k, v in sorted(verdicts.items())) or "none"
                print(
                    f"    Change attribution: {verdict_text} → "
                    f"{(gen_dir / 'change_evaluation.json').relative_to(output_dir)}"
                )
                if change_attribution_cfg.get("include_in_mutation_handoff", True):
                    change_attribution_handoff_text = format_change_evaluation_for_mutation(change_eval)
            except Exception as e:
                error_logger.record(
                    phase="change_attribution",
                    generation=gen,
                    context={"artifact": f"gen{gen}/change_evaluation.json"},
                    exception=e,
                    severity="error" if change_attribution_cfg.get("fail_closed") else "warning",
                )
                print(f"    ⚠ Change attribution failed: {e}")
                if change_attribution_cfg.get("fail_closed"):
                    raise

        if (
            regression_repair_cfg.get("enabled", True)
            and previous_generation_best is not None
            and population[0].fitness < float(previous_generation_best) - float(regression_repair_cfg.get("threshold", 0.05))
        ):
            previous_skill_path = output_dir / f"gen{gen - 1}" / "best_skill.md"
            if previous_skill_path.exists():
                regression_reflection_text = build_regression_reflection(
                    output_dir=output_dir,
                    gen_dir=gen_dir,
                    generation=gen,
                    previous_best_fitness=float(previous_generation_best),
                    current_best_fitness=population[0].fitness,
                    previous_skill=previous_skill_path.read_text(encoding="utf-8"),
                    current_skill=population[0].prompt,
                    execution_contract=execution_contract,
                )
                print(
                    f"    ⚠ Regression detected: gen{gen - 1} best={float(previous_generation_best):.3f} "
                    f"→ gen{gen} best={population[0].fitness:.3f}; wrote regression_reflection.md"
                )

        gen_elapsed = time.time() - gen_t0
        if gen_span and gen_span_ctx:
            record_generation_metrics(
                gen_span, gen,
                population[0].fitness, population[-1].fitness,
                gen_record["mean_fitness"], best_ever.fitness,
                gen_record["individuals"],
            )
            gen_span_ctx.__exit__(None, None, None)

        dashboard.record_generation(
            generation=gen,
            individuals=gen_record["individuals"],
            best_fitness=population[0].fitness,
            worst_fitness=population[-1].fitness,
            mean_fitness=gen_record["mean_fitness"],
            best_ever_fitness=best_ever.fitness,
            best_ever_generation=best_ever.generation,
            best_prompt_preview=best_ever.prompt[:300],
            elapsed_secs=gen_elapsed,
        )

        history_path = output_dir / "optimization_history.json"
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

        rl_stats = limiter.stats()
        print(f"  [safety] Requests: {rl_stats['total_requests']} total, "
              f"{rl_stats['requests_last_60s']}/{rl_stats['max_rpm']} in last 60s, "
              f"{rl_stats['total_errors']} errors")

        # ── CHECKPOINT 1 OF 2 (post-fitness, pre-oracle) ──
        # Bug fix (Apr 19, 2026): previously the only save_checkpoint call ran
        # AFTER breeding. If the process died any time during oracle synthesis
        # or breeding (sometimes 20+ minutes), the entire generation's fitness
        # eval — potentially 1.5 hours of rollouts — was lost with no resume
        # path. Saving here preserves the evaluated population so resume can
        # redo the cheap oracle+breeding work without re-rollout.
        ckpt_path = save_checkpoint(
            output_dir, gen, population, best_ever, history,
            checkpoint_stage="post_fitness",
            semantic_incumbent=semantic_incumbent,
        )
        print(f"  [checkpoint] Saved post-fitness → {ckpt_path.relative_to(output_dir.parent)}")

        if gen == generations:
            write_oracle_feedback_index(
                gen_dir=gen_dir,
                output_dir=output_dir,
                generation=gen,
                task_manifest=task_manifest,
                status="not_run_final_generation",
            )
            if lesson_bank_cfg.get("enabled", True):
                lesson_bank = update_lesson_bank(
                    output_dir=output_dir,
                    gen_dir=gen_dir,
                    generation=gen,
                    task_manifest=task_manifest,
                    generation_metrics_path=gen_dir / "generation_metrics.json",
                    oracle_feedback_text=None,
                    skill_patch_plan=None,
                    change_eval=change_eval,
                )
                print(f"    Lesson bank snapshot → {(gen_dir / 'lesson_bank.md').relative_to(output_dir)}")
            gen_timer.write()
            break

        # Selection + breeding
        print(f"\n  ── Breeding next generation ──")
        oracle_mode = ga.get("oracle_feedback", "never")

        # ── 3-layer streaming oracle pipeline ──
        # Layer 1: per-rollout streaming updates to task_insights/*.md
        # Layer 2: cross-task synthesis → cross_task/{pass,fail}_synthesis.md
        # Layer 3: final handoff → oracle_feedback.md (mutation-LLM input)
        oracle_feedback_text = None
        oracle_feedback_path = None
        oracle_status = "not_requested"
        _oracle_phase_t0 = time.time()
        heartbeat.update(phase="oracle_3layer", generation=gen,
                         message="running Layer 1 → Layer 2 → Layer 3 pipeline")
        def _oracle_heartbeat_callback(**kwargs) -> None:
            kwargs.setdefault("generation", gen)
            heartbeat.update(**kwargs)

        if oracle_mode in ("always", "adaptive"):
            oracle_status = "skipped_adaptive"
            stagnant = (oracle_mode == "always") or (
                len(history) >= 2 and
                history[-1]["best_fitness"] <= history[-2].get("best_ever", 0)
            )
            if stagnant:
                oracle_status = "running"
                oracle_client = openai.OpenAI(
                    base_url=eval_llm_cfg["base_url"],
                    api_key=eval_llm_cfg.get("api_key", "ollama"),
                    timeout=300.0,
                    max_retries=1,
                )

                # Collect rollouts per individual for Layer 1 streaming
                rollouts_by_individual: list[list[dict]] = []
                for ind in population:
                    fr = getattr(ind, 'fitness_result', None) or {}
                    rollout_path = fr.get("rollout_path")
                    ind_rollouts = []
                    if rollout_path and Path(rollout_path).exists():
                        with open(rollout_path, encoding="utf-8") as f:
                            for line in f:
                                if line.strip():
                                    try:
                                        ind_rollouts.append(json.loads(line))
                                    except json.JSONDecodeError:
                                        continue
                    rollouts_by_individual.append(ind_rollouts)

                # Build scoreboard text (reused by Layer 3)
                scoreboard_lines = []
                task_avgs: dict[str, list[float]] = {}
                cid_lookup = _task_cid_lookup(task_manifest)
                for ind in population:
                    fr = getattr(ind, 'fitness_result', None) or {}
                    for tid, val in fr.get("per_task", {}).items():
                        rate = val.get("pass_at_1", 0.0) if isinstance(val, dict) else float(val)
                        short = (tid or "unknown").replace("cvdp_agentic_heavy_", "")
                        task_avgs.setdefault(short, []).append(rate)
                for tid in sorted(task_avgs.keys()):
                    rates = task_avgs[tid]
                    avg = sum(rates) / len(rates)
                    rates_str = ", ".join(f"{r:.0%}" for r in rates)
                    if avg >= 1.0:
                        tag = " [ALWAYS SOLVED]"
                    elif avg > 0.6:
                        tag = " [USUALLY SOLVED]"
                    elif avg > 0:
                        tag = " [SOMETIMES SOLVED]"
                    else:
                        tag = " [NEVER SOLVED]"
                    cid = cid_lookup.get(tid) or cid_lookup.get(_short_task_id(tid)) or "unknown"
                    scoreboard_lines.append(f"  [{cid}] {tid}: avg={avg:.0%} ({rates_str}){tag}")
                scoreboard_text = "\n".join(scoreboard_lines)

                oracle_path = run_generation_oracle(
                    gen_dir=gen_dir,
                    generation=gen,
                    rollouts_by_individual=rollouts_by_individual,
                    scoreboard=scoreboard_text,
                    best=gen_best, mean=gen_mean, worst=gen_worst,
                    llm_client=oracle_client,
                    llm_model=eval_llm_cfg["model"],
                    task_manifest=task_manifest,
                    audit_logger=audit_logger,
                    error_logger=error_logger,
                    heartbeat_callback=_oracle_heartbeat_callback,
                )

                if oracle_path and oracle_path.exists():
                    oracle_feedback_path = oracle_path
                    oracle_status = "completed"
                    oracle_feedback_text = oracle_path.read_text(encoding="utf-8")
                    sanitize_cid_oracle_handoffs(
                        gen_dir=gen_dir,
                        generation=gen,
                        execution_contract=execution_contract,
                    )
                    oracle_feedback_text, _oracle_sanitize_report = sanitize_feedback_artifact_for_mutation(
                        text=oracle_feedback_text,
                        path=oracle_feedback_path,
                        gen_dir=gen_dir,
                        generation=gen,
                        execution_contract=execution_contract,
                        source="oracle_feedback",
                        report_name="oracle_feedback_sanitization.json",
                    )
                    print(f"    Oracle: 3-layer feedback ({len(oracle_feedback_text)} chars) → {oracle_path.relative_to(output_dir)}")
                    for line in oracle_feedback_text.split("\n")[:15]:
                        print(f"    │ {line}")
                    if oracle_feedback_text.count("\n") > 15:
                        print(f"    │ ... ({oracle_feedback_text.count(chr(10)) - 15} more lines)")
                else:
                    print(f"    Oracle: 3-layer pipeline failed; falling back to Python-only summary")
                    oracle_feedback_text = build_contrastive_oracle(
                        population, generation=gen, max_chars=12000,
                        llm_client=oracle_client,
                        llm_model=eval_llm_cfg["model"],
                        audit_logger=audit_logger,
                    )
                    if oracle_feedback_text:
                        fallback_path = gen_dir / "oracle_feedback.md"
                        fallback_path.write_text(oracle_feedback_text, encoding="utf-8")
                        oracle_feedback_path = fallback_path
                        oracle_feedback_text, _oracle_sanitize_report = sanitize_feedback_artifact_for_mutation(
                            text=oracle_feedback_text,
                            path=oracle_feedback_path,
                            gen_dir=gen_dir,
                            generation=gen,
                            execution_contract=execution_contract,
                            source="oracle_feedback_fallback",
                            report_name="oracle_feedback_sanitization.json",
                        )
                        oracle_status = "fallback_completed"
                    else:
                        oracle_status = "failed"
            else:
                print(f"    Oracle: skipped (adaptive mode, best is still improving)")

        write_oracle_feedback_index(
            gen_dir=gen_dir,
            output_dir=output_dir,
            generation=gen,
            task_manifest=task_manifest,
            status=oracle_status,
            oracle_feedback_path=oracle_feedback_path,
        )

        gen_timer.add("oracle_3layer", time.time() - _oracle_phase_t0)

        mutation_feedback_parts = []
        if oracle_feedback_text:
            mutation_feedback_parts.append(oracle_feedback_text)
        if change_attribution_handoff_text:
            mutation_feedback_parts.extend([
                "",
                change_attribution_handoff_text,
            ])
        if regression_reflection_text:
            mutation_feedback_parts.extend([
                "",
                "## Regression-aware repair addendum",
                regression_reflection_text,
            ])
        base_mutation_feedback_text = "\n".join(part for part in mutation_feedback_parts if part is not None).strip() or None

        lesson_bank_handoff_text = None
        if lesson_bank_cfg.get("enabled", True):
            preliminary_patch_plan = None
            if base_mutation_feedback_text:
                preliminary_patch_plan_obj = build_skill_patch_plan(
                    base_mutation_feedback_text,
                    execution_contract,
                )
                preliminary_patch_plan = preliminary_patch_plan_obj.to_dict()
            lesson_bank = update_lesson_bank(
                output_dir=output_dir,
                gen_dir=gen_dir,
                generation=gen,
                task_manifest=task_manifest,
                generation_metrics_path=gen_dir / "generation_metrics.json",
                oracle_feedback_text=oracle_feedback_text,
                skill_patch_plan=preliminary_patch_plan,
                change_eval=change_eval,
            )
            print(f"    Lesson bank: updated → {(gen_dir / 'lesson_bank.md').relative_to(output_dir)}")
            if lesson_bank_cfg.get("include_in_mutation_handoff", True):
                rendered_bank = format_lesson_bank_for_mutation(
                    lesson_bank,
                    max_chars=int(lesson_bank_cfg.get("mutation_handoff_max_chars", 7000)),
                )
                # Avoid sending an empty shell when only metric history exists.
                if "### " in rendered_bank:
                    lesson_bank_handoff_text = rendered_bank

        final_mutation_feedback_parts = []
        if base_mutation_feedback_text:
            final_mutation_feedback_parts.append(base_mutation_feedback_text)
        if lesson_bank_handoff_text:
            final_mutation_feedback_parts.extend(["", lesson_bank_handoff_text])
        mutation_feedback_text = "\n".join(part for part in final_mutation_feedback_parts if part is not None).strip() or None
        if mutation_feedback_text:
            mutation_feedback_text, _mutation_sanitize_report = sanitize_feedback_artifact_for_mutation(
                text=mutation_feedback_text,
                path=None,
                gen_dir=gen_dir,
                generation=gen,
                execution_contract=execution_contract,
                source="mutation_handoff_prewrite",
                report_name="mutation_handoff_sanitization.json",
            )
        skill_patch_plan = None
        skill_patch_plan_text = None
        if mutation_feedback_text:
            mutation_handoff_path = gen_dir / "mutation_handoff.md"
            mutation_handoff_path.write_text(mutation_feedback_text + "\n", encoding="utf-8")
            skill_patch_plan_obj = build_skill_patch_plan(
                mutation_feedback_text,
                execution_contract,
            )
            write_skill_patch_plan_artifacts(gen_dir, skill_patch_plan_obj)
            skill_patch_plan = skill_patch_plan_obj.to_dict()
            skill_patch_plan_text = format_skill_patch_plan(skill_patch_plan_obj)
            print(
                f"    Skill patch plan: add={len(skill_patch_plan_obj.must_add)}, "
                f"preserve={len(skill_patch_plan_obj.must_preserve)}, "
                f"remove={len(skill_patch_plan_obj.must_remove)} → "
                f"{(gen_dir / 'skill_patch_plan.json').relative_to(output_dir)}"
            )
            if regression_reflection_text:
                print(f"    Mutation handoff includes regression repair → {mutation_handoff_path.relative_to(output_dir)}")

        next_gen: list[Individual] = []
        _breed_phase_t0 = time.time()
        heartbeat.update(phase="breeding", generation=gen,
                         message=f"breeding gen {gen + 1} population")

        if standard_ea_enabled and standard_ea_cfg.get("carry_evaluated_survivor", True):
            survivor = _carry_prompt_for_reevaluation(
                population[0],
                gen + 1,
                f"ea_survivor_from_gen{gen}",
            )
            next_gen.append(survivor)
            print(
                f"    Standard EA survivor: carried evaluated survivor forward "
                f"(selection={population[0].fitness:.3f})"
            )
        elif (
            semantic_skill_selection_cfg.get("enabled", True)
            and semantic_skill_selection_cfg.get("carry_incumbent", True)
            and semantic_incumbent is not None
            and pop_size > 1
        ):
            incumbent = _clone_individual_for_generation(
                semantic_incumbent,
                gen + 1,
                f"semantic_incumbent_from_gen{gen}",
            )
            next_gen.append(incumbent)
            print(
                f"    Semantic incumbent: carried forward "
                f"({len(incumbent.prompt)} chars; rollout fitness not used)"
            )

        elite_candidates = _breeding_pool_with_survivor(population, best_ever, parent_child_survival)
        elite_candidates.sort(key=lambda x: x.fitness, reverse=True)
        for i in range(min(elitism, len(elite_candidates))):
            if len(next_gen) >= pop_size:
                break
            if _prompt_in_population(elite_candidates[i].prompt, next_gen):
                continue
            elite = Individual(
                elite_candidates[i].prompt,
                generation=gen + 1,
                parent_info=f"elite_{i}_from_gen{gen}",
            )
            next_gen.append(elite)
            print(f"    Elite {i}: carried forward (selection={elite_candidates[i].fitness:.3f})")

        if not standard_ea_enabled:
            for semantic_survivor in semantic_survivors_for_next_gen:
                if len(next_gen) >= pop_size:
                    break
                if _prompt_in_population(semantic_survivor.prompt, next_gen):
                    continue
                next_gen.append(semantic_survivor)
                meta = semantic_survivor.semantic_retention or {}
                print(
                    "    Semantic survivor: carried forward "
                    f"(source ind{meta.get('source_individual_index')}, "
                    f"source selection={meta.get('source_selection_fitness', 0.0):.3f}, "
                    f"coverage={((_semantic_metrics(semantic_survivor)).get('coverage', 0.0) or 0.0):.3f})"
                )

        breeding_pool = _breeding_pool_with_survivor(population, best_ever, parent_child_survival)
        while len(next_gen) < pop_size:
            if standard_ea_enabled and standard_ea_cfg.get("mutation_parent", "survivor") == "survivor":
                parent_a = population[0]
                parent_b = population[0]
            elif (
                semantic_skill_selection_cfg.get("enabled", True)
                and semantic_skill_selection_cfg.get("prefer_incumbent_parent", True)
                and semantic_incumbent is not None
            ):
                parent_a = semantic_incumbent
                parent_b = semantic_incumbent
            elif parent_child_survival and best_ever is not None and pop_size == 1:
                parent_a, survival_reason = _single_lineage_parent(
                    population[0],
                    best_ever,
                    single_lineage_survival_margin,
                )
                parent_b = parent_a
                if survival_reason == "best_ever_after_regression":
                    print(
                        f"    Survival: mutating best-ever parent "
                        f"(selection={best_ever.fitness:.3f}) instead of regressed current best "
                        f"({population[0].fitness:.3f})"
                    )
            else:
                parent_a = tournament_select(breeding_pool, tournament_size)
                parent_b = tournament_select(breeding_pool, tournament_size)
            child_prompt = parent_a.prompt
            child_origin_steps = ["parent"]
            child_semantic_retention: dict = {}
            child_semantic_selection: dict = {}
            last_process_record: dict | None = None
            last_candidate_parent_prompt = parent_a.prompt
            last_selector_stage = "parent"

            pre_len = len(child_prompt)
            child_slot = len(next_gen)  # which slot in next gen's population this child will fill
            if random.random() < crossover_rate:
                feedback_tag = " +feedback" if mutation_feedback_text else ""
                print(f"    Crossover (parents: {len(parent_a.prompt)}, {len(parent_b.prompt)} chars){feedback_tag}...")
                try:
                    child_budget = _candidate_skill_budget(parent_a.prompt, max_skill_length, skill_sanitizer_cfg)
                    child_prompt = crossover_prompts(
                        client, mutation_model,
                        parent_a.prompt, parent_b.prompt, objective,
                        oracle_feedback=mutation_feedback_text,
                        skill_patch_plan=skill_patch_plan_text,
                        execution_constraints=execution_constraints_text,
                        max_chars=child_budget,
                        audit_logger=audit_logger,
                        temperature=mutation_temperature,
                        context={
                            "next_gen": gen + 1,
                            "child_slot": child_slot,
                            "parent_a_info": parent_a.parent_info,
                            "parent_b_info": parent_b.parent_info,
                        },
                    )
                    child_prompt, process_record = process_candidate_skill_for_injection(
                        client=client,
                        mutation_model=mutation_model,
                        objective=objective,
                        output_dir=output_dir,
                        generation=gen,
                        child_slot=child_slot,
                        parent_info=parent_a.parent_info,
                        stage="crossover",
                        candidate=child_prompt,
                        parent_prompt=parent_a.prompt,
                        max_skill_length=max_skill_length,
                        sanitizer_cfg=skill_sanitizer_cfg,
                        execution_contract=execution_contract,
                        execution_constraints_text=execution_constraints_text,
                        skill_patch_plan_text=skill_patch_plan_text,
                        skill_patch_plan=skill_patch_plan,
                        integration_cfg=skill_integration_cfg,
                        repair_cfg=mutation_repair_cfg,
                        audit_logger=audit_logger,
                        context={
                            "next_gen": gen + 1,
                            "child_slot": child_slot,
                            "parent_a_info": parent_a.parent_info,
                            "parent_b_info": parent_b.parent_info,
                        },
                    )
                    child_semantic_retention = build_semantic_retention_metadata(
                        generation=gen,
                        next_generation=gen + 1,
                        child_slot=child_slot,
                        stage="crossover",
                        parent_info=parent_a.parent_info,
                        parent_prompt=parent_a.prompt,
                        candidate_prompt=child_prompt,
                        process_record=process_record,
                        skill_patch_plan=skill_patch_plan,
                    )
                    last_process_record = process_record
                    last_candidate_parent_prompt = parent_a.prompt
                    last_selector_stage = "crossover"
                    child_origin_steps.append("crossover")
                    print(f"      → {len(child_prompt)} chars")
                except Exception as e:
                    print(f"      Crossover failed: {e}, using parent A")
                    error_logger.record(
                        phase="breeding_crossover",
                        generation=gen,
                        context={
                            "next_gen": gen + 1,
                            "child_slot": child_slot,
                            "parent_a_info": parent_a.parent_info,
                            "parent_b_info": parent_b.parent_info,
                        },
                        exception=e,
                    )
                    child_prompt = parent_a.prompt

            if random.random() < mutation_rate:
                pre_mut = len(child_prompt)
                mutation_parent_prompt = child_prompt
                feedback_tag = " +feedback" if mutation_feedback_text else ""
                print(f"    Mutation ({pre_mut} chars){feedback_tag}...")
                heartbeat.update(
                    phase="breeding_mutation",
                    generation=gen,
                    individual_idx=child_slot,
                    individual_parent=parent_a.parent_info,
                    context={
                        "next_gen": gen + 1,
                        "child_slot": child_slot,
                        "parent_chars": pre_mut,
                        "mutation_model": mutation_model,
                        "mutation_temperature": mutation_temperature,
                        "has_oracle_feedback": bool(oracle_feedback_text),
                        "has_regression_repair": bool(regression_reflection_text),
                    },
                )
                health_record = {}
                try:
                    child_budget = _candidate_skill_budget(mutation_parent_prompt, max_skill_length, skill_sanitizer_cfg)
                    mutated_prompt = mutate_prompt(
                        client, mutation_model,
                        mutation_parent_prompt, objective,
                        oracle_feedback=mutation_feedback_text,
                        skill_patch_plan=skill_patch_plan_text,
                        execution_constraints=execution_constraints_text,
                        max_chars=child_budget,
                        audit_logger=audit_logger,
                        temperature=mutation_temperature,
                        context={
                            "next_gen": gen + 1,
                            "child_slot": child_slot,
                            "parent_info": parent_a.parent_info,
                        },
                    )
                    sanitized_prompt, process_record = process_candidate_skill_for_injection(
                        client=client,
                        mutation_model=mutation_model,
                        objective=objective,
                        output_dir=output_dir,
                        generation=gen,
                        child_slot=child_slot,
                        parent_info=parent_a.parent_info,
                        stage="mutation",
                        candidate=mutated_prompt,
                        parent_prompt=mutation_parent_prompt,
                        max_skill_length=max_skill_length,
                        sanitizer_cfg=skill_sanitizer_cfg,
                        execution_contract=execution_contract,
                        execution_constraints_text=execution_constraints_text,
                        skill_patch_plan_text=skill_patch_plan_text,
                        skill_patch_plan=skill_patch_plan,
                        integration_cfg=skill_integration_cfg,
                        repair_cfg=mutation_repair_cfg,
                        audit_logger=audit_logger,
                    )
                    health = validate_mutated_skill(sanitized_prompt, mutation_parent_prompt, child_budget)
                    health["metrics"]["raw_candidate_chars"] = len(mutated_prompt or "")
                    health["metrics"]["sanitizer"] = process_record["sanitizer"]
                    health["metrics"]["skill_integration"] = process_record["skill_integration"]["metrics"]
                    health["metrics"]["repair_attempted"] = process_record["repair_attempted"]
                    health_record = write_mutation_health_record(
                        output_dir,
                        gen,
                        {
                            "status": "ok" if health["ok"] else "invalid_output",
                            "ok": health["ok"],
                            "next_generation": gen + 1,
                            "child_slot": child_slot,
                            "parent_info": parent_a.parent_info,
                            "mutation_model": mutation_model,
                            "mutation_temperature": mutation_temperature,
                            "has_oracle_feedback": bool(oracle_feedback_text),
                            "has_regression_repair": bool(regression_reflection_text),
                            "issues": health["issues"],
                            "metrics": health["metrics"],
                        },
                    )
                    if not health["ok"]:
                        raise MutationValidationError(
                            "mutator returned invalid skill: " + ", ".join(health["issues"])
                        )
                    child_prompt = sanitized_prompt
                    child_semantic_retention = build_semantic_retention_metadata(
                        generation=gen,
                        next_generation=gen + 1,
                        child_slot=child_slot,
                        stage="mutation",
                        parent_info=parent_a.parent_info,
                        parent_prompt=mutation_parent_prompt,
                        candidate_prompt=child_prompt,
                        process_record=process_record,
                        skill_patch_plan=skill_patch_plan,
                    )
                    last_process_record = process_record
                    last_candidate_parent_prompt = mutation_parent_prompt
                    last_selector_stage = "mutation"
                    child_origin_steps.append("mutation")
                    print(f"      → {len(child_prompt)} chars ({len(child_prompt) - pre_mut:+d})")
                    print(f"      [mutation-health] ok → gen{gen}/mutation_health.jsonl")
                except Exception as e:
                    if isinstance(e, MutationValidationError):
                        health_record = write_mutation_health_record(
                            output_dir,
                            gen,
                            {
                                "status": "invalid_output",
                                "ok": False,
                                "next_generation": gen + 1,
                                "child_slot": child_slot,
                                "parent_info": parent_a.parent_info,
                                "mutation_model": mutation_model,
                                "mutation_temperature": mutation_temperature,
                                "has_oracle_feedback": bool(oracle_feedback_text),
                                "has_regression_repair": bool(regression_reflection_text),
                                "issues": ["post_mutation_gate_rejected"],
                                "exception_msg": str(e),
                                "metrics": {
                                    "parent_chars": pre_mut,
                                    "candidate_chars": 0,
                                    "delta_chars": -pre_mut,
                                    "max_chars": max_skill_length,
                                    "parent_sha256": _sha256_text(mutation_parent_prompt),
                                },
                            },
                        )
                    else:
                        health_record = write_mutation_health_record(
                            output_dir,
                            gen,
                            {
                                "status": "exception",
                                "ok": False,
                                "next_generation": gen + 1,
                                "child_slot": child_slot,
                                "parent_info": parent_a.parent_info,
                                "mutation_model": mutation_model,
                                "mutation_temperature": mutation_temperature,
                                "has_oracle_feedback": bool(oracle_feedback_text),
                                "issues": ["mutation_exception"],
                                "exception_type": type(e).__name__,
                                "exception_msg": str(e),
                                "metrics": {
                                    "parent_chars": pre_mut,
                                    "candidate_chars": 0,
                                    "delta_chars": -pre_mut,
                                    "max_chars": max_skill_length,
                                    "parent_sha256": _sha256_text(mutation_parent_prompt),
                                },
                            },
                        )
                    print(f"      Mutation unhealthy: {e}, keeping unmutated")
                    heartbeat.update(
                        phase="mutation_failed",
                        generation=gen,
                        individual_idx=child_slot,
                        individual_parent=parent_a.parent_info,
                        context={
                            "next_gen": gen + 1,
                            "child_slot": child_slot,
                            "parent_chars": pre_mut,
                            "mutation_model": mutation_model,
                            "mutation_temperature": mutation_temperature,
                            "issues": health_record.get("issues", []),
                            "mutation_health": f"gen{gen}/mutation_health.jsonl",
                        },
                        message="mutator failed or returned an invalid skill; child kept unmutated",
                    )
                    error_logger.record(
                        phase="breeding_mutation",
                        generation=gen,
                        context={
                            "next_gen": gen + 1,
                            "child_slot": child_slot,
                            "parent_info": parent_a.parent_info,
                            "pre_mut_chars": pre_mut,
                            "mutation_model": mutation_model,
                            "mutation_temperature": mutation_temperature,
                            "mutation_health": f"gen{gen}/mutation_health.jsonl",
                            "mutation_status": health_record.get("status"),
                            "mutation_issues": health_record.get("issues", []),
                        },
                        exception=e,
                        severity="error",
                    )

            if last_process_record is not None:
                if (
                    standard_ea_enabled
                    and standard_ea_cfg.get("defer_child_semantic_selection_to_rollout", True)
                ):
                    child_semantic_selection = defer_child_semantic_selection(
                        parent_prompt=last_candidate_parent_prompt,
                        candidate_prompt=child_prompt,
                        process_record=last_process_record,
                        output_dir=output_dir,
                        gen_dir=gen_dir,
                        generation=gen,
                        child_slot=child_slot,
                        stage=last_selector_stage,
                        parent_info=parent_a.parent_info,
                        skill_patch_plan=skill_patch_plan,
                    )
                    child_origin_steps.append("semantic_selector_deferred")
                    print("      [semantic-selector] deferred until child rollout evaluation")
                else:
                    selected_prompt, child_semantic_selection = apply_semantic_skill_selection(
                        parent_prompt=last_candidate_parent_prompt,
                        candidate_prompt=child_prompt,
                        process_record=last_process_record,
                        output_dir=output_dir,
                        gen_dir=gen_dir,
                        generation=gen,
                        child_slot=child_slot,
                        stage=last_selector_stage,
                        parent_info=parent_a.parent_info,
                        skill_patch_plan=skill_patch_plan,
                        execution_contract=execution_contract,
                        skill_integration_cfg=skill_integration_cfg,
                        semantic_skill_selection_cfg=semantic_skill_selection_cfg,
                    )
                    if selected_prompt != child_prompt:
                        child_origin_steps.append("semantic_selector_kept_parent")
                        print(
                            f"      [semantic-selector] kept parent: "
                            f"{', '.join(child_semantic_selection.get('reasons', []))}"
                        )
                    else:
                        child_origin_steps.append("semantic_selector_accepted")
                        print(
                            f"      [semantic-selector] accepted child: "
                            f"{', '.join(child_semantic_selection.get('reasons', []))}"
                        )
                    child_prompt = selected_prompt

            child = Individual(
                child_prompt,
                generation=gen + 1,
                parent_info=f"child_gen{gen+1}_{len(next_gen)}",
            )
            child.parent_prompt = parent_a.prompt
            child.parent_fitness = parent_a.fitness
            child.parent_fitness_result = copy.deepcopy(parent_a.fitness_result)
            child.parent_sha256 = _sha256_text(parent_a.prompt)
            child.child_origin = "+".join(child_origin_steps)
            child.semantic_retention = child_semantic_retention
            child.semantic_selection = child_semantic_selection
            next_gen.append(child)

        if (
            not standard_ea_enabled
            and semantic_skill_selection_cfg.get("enabled", True)
            and semantic_incumbent is not None
        ):
            new_incumbent, incumbent_decision = choose_semantic_incumbent(
                current_incumbent=semantic_incumbent,
                candidates=next_gen,
                cfg=semantic_skill_selection_cfg,
            )
            semantic_incumbent = _clone_individual_for_generation(
                new_incumbent,
                gen + 1,
                "semantic_incumbent",
            )
            _write_json(gen_dir / "semantic_incumbent_decision.json", {
                "generation": gen,
                "next_generation": gen + 1,
                "config": semantic_skill_selection_cfg,
                **incumbent_decision,
            })
            (gen_dir / "next_semantic_incumbent.md").write_text(semantic_incumbent.prompt, encoding="utf-8")
            (output_dir / "semantic_incumbent.md").write_text(semantic_incumbent.prompt, encoding="utf-8")
            print(
                f"    Semantic incumbent decision: {incumbent_decision.get('decision')} "
                f"({incumbent_decision.get('reason')})"
            )

        population = next_gen

        gen_timer.add("breeding", time.time() - _breed_phase_t0)
        timing_path = gen_timer.write()
        if timing_path is not None:
            print(f"  [timing] → {timing_path.relative_to(output_dir)}")

        # ── GUARD: post-breeding validation ──
        if len(population) != pop_size:
            print(f"  [GUARD] ✗ Bred population size wrong: expected {pop_size}, got {len(population)}")
        empty_prompts = [i for i, ind in enumerate(population) if not ind.prompt or len(ind.prompt) < 100]
        if empty_prompts:
            print(f"  [GUARD] ✗ Individuals with empty/short prompts after breeding: {empty_prompts}")
        breed_lengths = [len(ind.prompt) for ind in population]
        print(f"  [pipeline] ✓ Bred {len(population)} individuals: "
              f"prompt lengths {min(breed_lengths)}-{max(breed_lengths)} chars")

        # ── CHECKPOINT 2 OF 2 (post-breeding, ready for next gen) ──
        # Population here is the newly-bred gen (N+1) children, fitness=0,
        # awaiting evaluation. On resume, the "needs_breeding=False" branch
        # skips re-breeding and goes straight to fitness eval for gen (N+1).
        ckpt_path = save_checkpoint(
            output_dir, gen, population, best_ever, history,
            checkpoint_stage="post_breeding",
            semantic_incumbent=semantic_incumbent,
        )
        print(f"  [checkpoint] Saved post-breeding (gen {gen + 1} ready) → {ckpt_path.relative_to(output_dir.parent)}")
        heartbeat.update(phase="gen_complete", generation=gen,
                         message=f"gen {gen + 1} bred, awaiting evaluation")

    # ── Final output ────────────────────────────────────────────────

    best_pass = best_ever.fitness_result.get("pass_at_1", best_ever.fitness) if best_ever.fitness_result else best_ever.fitness
    best_progress = best_ever.fitness_result.get("progress_fitness", 0.0) if best_ever.fitness_result else 0.0
    heartbeat.update(phase="complete", generation=best_ever.generation,
                     message=f"optimization finished, best_selection={best_ever.fitness:.3f}, pass@1={best_pass:.3f}")
    print(f"\n{'=' * 70}")
    print(f"  Optimization complete")
    print(f"{'=' * 70}")
    print(f"  Best selection fitness: {best_ever.fitness:.3f}")
    print(f"  Best true pass@1: {best_pass:.3f}")
    print(f"  Best progress fitness: {best_progress:.3f}")
    print(f"  Best generation: {best_ever.generation}")

    best_performing_path = output_dir / "best_performing_skill.md"
    best_performing_path.write_text(best_ever.prompt, encoding="utf-8")

    if standard_ea_enabled:
        optimized_source = best_ever
        optimized_source_kind = "best_performing_standard_ea_survivor"
    else:
        optimized_source = semantic_incumbent if (
            semantic_skill_selection_cfg.get("enabled", True) and semantic_incumbent is not None
        ) else best_ever
        optimized_source_kind = "semantic_incumbent" if optimized_source is semantic_incumbent else "best_performing_skill"
    semantic_incumbent_path = output_dir / "semantic_incumbent.md"
    semantic_incumbent_path.write_text(optimized_source.prompt, encoding="utf-8")

    if lesson_bank_cfg.get("enabled", True):
        lesson_bank = load_lesson_bank(output_dir)
        write_lesson_bank_artifacts(output_dir=output_dir, gen_dir=None, bank=lesson_bank)
        final_skill_text = distill_final_skill(
            best_skill=optimized_source.prompt,
            lesson_bank=lesson_bank,
            max_chars=int(lesson_bank_cfg.get("distilled_final_max_chars", 18000)),
        )
        final_kind = f"distilled_final_skill_from_{optimized_source_kind}"
    else:
        lesson_bank = {}
        final_skill_text = optimized_source.prompt
        final_kind = optimized_source_kind

    distilled_path = output_dir / "distilled_final_skill.md"
    distilled_path.write_text(final_skill_text, encoding="utf-8")

    final_path = output_dir / "optimized_skill.md"
    final_path.write_text(final_skill_text, encoding="utf-8")
    task_skill_alias = _single_task_alias(task_manifest) if skill_scope == "per_task" else None
    task_exports = {}
    if task_skill_alias:
        task_best_path = output_dir / f"best_performing_skill_task_{task_skill_alias}.md"
        task_best_path.write_text(best_ever.prompt, encoding="utf-8")
        task_distilled_path = output_dir / f"distilled_final_skill_task_{task_skill_alias}.md"
        task_distilled_path.write_text(final_skill_text, encoding="utf-8")
        task_final_path = output_dir / f"optimized_skill_task_{task_skill_alias}.md"
        task_final_path.write_text(final_skill_text, encoding="utf-8")
        task_exports = {
            "best_performing_task_skill_path": task_best_path.name,
            "distilled_task_skill_path": task_distilled_path.name,
            "optimized_task_skill_path": task_final_path.name,
        }
    _write_json(output_dir / "optimized_skill_meta.json", {
        "optimized_skill_kind": final_kind,
        "optimized_skill_path": "optimized_skill.md",
        "best_performing_skill_path": "best_performing_skill.md",
        "semantic_incumbent_skill_path": "semantic_incumbent.md",
        "distilled_final_skill_path": "distilled_final_skill.md",
        "skill_scope": skill_scope,
        "scope": _task_only_scope_record(task_manifest) if skill_scope == "per_task" else None,
        "task_exports": task_exports,
        "best_performing_generation": best_ever.generation,
        "best_performing_selection_fitness": best_ever.fitness,
        "best_performing_pass_at_1": best_pass,
        "best_performing_progress_fitness": best_progress,
        "best_performing_sha256": _sha256_text(best_ever.prompt),
        "optimized_source_kind": optimized_source_kind,
        "semantic_incumbent_generation": optimized_source.generation,
        "semantic_incumbent_sha256": _sha256_text(optimized_source.prompt),
        "semantic_incumbent_selection": optimized_source.semantic_selection,
        "optimized_sha256": _sha256_text(final_skill_text),
        "optimized_chars": len(final_skill_text),
        "lesson_bank_enabled": bool(lesson_bank_cfg.get("enabled", True)),
        "lesson_bank_updated_generation": lesson_bank.get("updated_generation") if isinstance(lesson_bank, dict) else None,
        "note": (
            "optimized_skill.md is the downstream-eval export. In standard EA mode "
            "it comes from the best evaluated survivor; in legacy semantic-incumbent "
            "mode it comes from the semantic incumbent. best_performing_skill.md "
            "always preserves the raw best rollout performer."
        ),
    })
    print(f"  Saved best-performing skill to {best_performing_path}")
    print(f"  Saved semantic incumbent skill to {semantic_incumbent_path}")
    print(f"  Saved distilled optimized skill to {final_path}")

    history_path = output_dir / "optimization_history.json"
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    print(f"  Saved history to {history_path}")

    # Generate human-readable lineage narrative
    lineage_path = output_dir / "lineage.md"
    write_lineage(lineage_path, history, best_ever, seed_skill_path, len(seed_skill))
    print(f"  Saved lineage to {lineage_path}")

    dashboard.finalize(best_ever.fitness, best_ever.generation)
    print(f"  Live dashboard: {output_dir / 'live_dashboard.json'}")

    rl_stats = limiter.stats()
    print(f"  Total API requests: {rl_stats['total_requests']} ({rl_stats['total_errors']} errors)")

    if telemetry_enabled:
        shutdown_telemetry()

    return best_ever


def main():
    parser = argparse.ArgumentParser(description="CVDP Skill Prompt Optimizer")
    parser.add_argument("--config", required=True, help="Path to optimizer config YAML")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from the last checkpoint instead of starting fresh")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    best = run_optimizer(config, resume=args.resume)
    best_pass = best.fitness_result.get("pass_at_1", best.fitness) if best.fitness_result else best.fitness
    print(f"\nDone. Best selection fitness: {best.fitness:.3f}; best true pass@1: {best_pass:.3f}")


if __name__ == "__main__":
    main()

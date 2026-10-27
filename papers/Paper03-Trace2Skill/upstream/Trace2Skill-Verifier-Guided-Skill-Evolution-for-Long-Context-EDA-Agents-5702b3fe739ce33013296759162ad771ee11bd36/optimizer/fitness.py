#!/usr/bin/env python3
"""Fitness function for CVDP prompt optimization.

Integrates the NAT eval flow with NeMo-Gym rollouts:
  1. Inject the mutated skill into tasks.jsonl
  2. Run NeMo-Gym rollout collection
  3. Convert rollouts via NAT eval pipeline (structured metrics + trajectories)
  4. Optionally run the NAT analyzer for behavioral report
  5. Return true pass@1 plus dense progress/selection fitness

The NeMo-Gym servers (ng_run) must be running before calling this.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import openai

from rate_limiter import get_rate_limiter
from path_grounding import analyze_path_grounding

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "nemogym"))
try:
    from responses_api_agents.cvdp_agentic_heavy_agent.skill_monitor import compile_skill_policy
except Exception:  # pragma: no cover - optimizer can still run without monitor policy compilation
    compile_skill_policy = None

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent
        / "nemogym"
        / "resources_servers"
        / "cvdp_agentic_heavy"
        / "scripts"
    ),
)
try:
    from convert_to_gym import enable_runtime_verifier_feedback_in_gym_row
except Exception:  # pragma: no cover - sparse configs do not need the helper
    enable_runtime_verifier_feedback_in_gym_row = None

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "eval"))
from convert_rollouts import convert_single_file, compute_metrics, load_rollouts_from_file
from run_analyzer import run_analyzer, build_user_prompt, load_skill


class RolloutModelMismatchError(RuntimeError):
    """Raised when NeMo-Gym rollouts were produced by the wrong policy model."""


class RolloutResponseError(RuntimeError):
    """Raised when NeMo-Gym produced placeholder error responses instead of rollouts."""


def _archive_rollout_attempt(work_dir: Path, trial_id: str, attempt: int, reason: str) -> list[str]:
    """Move invalid rollout-attempt artifacts aside before retrying.

    NeMo-Gym may occasionally return placeholder responses such as
    `model="error"` when the upstream policy server/API fails before producing
    a usable response. Those artifacts are valuable postmortem evidence, but
    they must not be mixed into the retried rollout file. We keep the injected
    `tasks_<trial_id>.jsonl` in place and archive generated outputs with an
    `.invalid_attempt<N>.*` suffix.
    """
    archived: list[str] = []
    for path in sorted(work_dir.glob(f"*{trial_id}*")):
        if not path.is_file():
            continue
        if path.name == f"tasks_{trial_id}.jsonl":
            continue
        if path.name == f"rollout_retries_{trial_id}.jsonl":
            continue
        if ".invalid_attempt" in path.name:
            continue
        target = path.with_name(f"{path.stem}.invalid_attempt{attempt}{path.suffix}")
        if target.exists():
            target = path.with_name(
                f"{path.stem}.invalid_attempt{attempt}.{int(time.time())}{path.suffix}"
            )
        path.rename(target)
        archived.append(str(target))

    retry_log = work_dir / f"rollout_retries_{trial_id}.jsonl"
    with retry_log.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "attempt": attempt,
            "reason": reason,
            "archived_files": archived,
        }, ensure_ascii=False) + "\n")
    return archived


def _summarize_rollout_file(rollout_output: Path) -> dict:
    """Return lightweight rollout counts used before NAT conversion."""
    rollout_lines = 0
    passes = 0
    fails = 0
    total_steps = 0
    with open(rollout_output, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                rollout_lines += 1
                reward = rec.get("reward", 0)
                if reward > 0:
                    passes += 1
                else:
                    fails += 1
                steps = len([
                    o for o in rec.get("response", {}).get("output", [])
                    if isinstance(o, dict) and o.get("type") == "function_call"
                ])
                total_steps += steps
            except json.JSONDecodeError:
                pass
    avg_steps = total_steps / rollout_lines if rollout_lines else 0
    return {
        "rollout_lines": rollout_lines,
        "passes": passes,
        "fails": fails,
        "total_steps": total_steps,
        "avg_steps": avg_steps,
    }


def _path_grounding_rollout_score(analysis: dict) -> float:
    """Return a dense progress multiplier for target-path grounding.

    A rollout with no inferred target is neutral. Once a target is inferred,
    wrong same-basename edits/validation are strong evidence that the apparent
    progress is misleading, so they reduce dense progress used for selection.
    """
    if not analysis.get("expected_targets"):
        return 1.0
    issues = analysis.get("issues") or []
    if not issues:
        return 1.0
    if analysis.get("has_critical_issue"):
        return 0.15
    return 0.60


def _summarize_rollout_score_variance(scores: list[float]) -> dict:
    clean = [max(0.0, min(1.0, float(v))) for v in scores if isinstance(v, (int, float))]
    if not clean:
        return {
            "n": 0,
            "mean": 0.0,
            "stdev": 0.0,
            "sem": 0.0,
            "lower_confidence_bound_95": 0.0,
            "variance_penalty": 1.0,
            "variance_quality": 0.0,
        }
    mean = sum(clean) / len(clean)
    if len(clean) == 1:
        stdev = 0.0
        sem = 0.0
    else:
        stdev = (sum((v - mean) ** 2 for v in clean) / (len(clean) - 1)) ** 0.5
        sem = stdev / (len(clean) ** 0.5)
    lcb = max(0.0, mean - 1.96 * sem)
    variance_penalty = min(1.0, stdev / 0.30)
    return {
        "n": len(clean),
        "mean": round(mean, 4),
        "stdev": round(stdev, 4),
        "sem": round(sem, 4),
        "lower_confidence_bound_95": round(lcb, 4),
        "variance_penalty": round(variance_penalty, 4),
        "variance_quality": round(1.0 - variance_penalty, 4),
    }


def apply_path_grounding_fitness_adjustment(metrics: dict, rollouts: list[dict]) -> dict:
    """Fold deterministic path-grounding diagnostics into dense fitness.

    The verifier pass rate remains untouched. Only `progress_fitness` and the
    small selection tie-breaker are adjusted, so a real pass still dominates a
    prettier failure while wrong-target failures stop looking deceptively good.
    """
    if not rollouts:
        return metrics

    analyses = [analyze_path_grounding(rec) for rec in rollouts]
    scored = [a for a in analyses if a.get("expected_targets")]
    if not scored:
        return metrics

    scores = [_path_grounding_rollout_score(a) for a in scored]
    path_score = sum(scores) / len(scores) if scores else 1.0
    issue_counts: dict[str, int] = {}
    critical_count = 0
    for analysis in analyses:
        if analysis.get("has_critical_issue"):
            critical_count += 1
        for code in analysis.get("issue_codes") or []:
            issue_counts[str(code)] = issue_counts.get(str(code), 0) + 1

    raw_progress = float(metrics.get("progress_fitness", 0.0) or 0.0)
    progress_multiplier = 0.55 + 0.45 * path_score
    adjusted_progress = raw_progress * progress_multiplier
    pass_at_1 = float(metrics.get("overall_pass_at_1", 0.0) or 0.0)
    epsilon = float(metrics.get("selection_epsilon", 0.0) or 0.0)
    adjusted_selection = pass_at_1 + epsilon * adjusted_progress

    components = dict(metrics.get("progress_components") or {})
    components["path_grounding"] = round(path_score, 4)
    raw_rollout_scores = metrics.get("progress_rollout_scores") or []
    if isinstance(raw_rollout_scores, list) and raw_rollout_scores:
        adjusted_rollout_scores = []
        for idx, raw_score in enumerate(raw_rollout_scores):
            try:
                raw_value = float(raw_score)
            except (TypeError, ValueError):
                raw_value = 0.0
            if idx < len(analyses) and analyses[idx].get("expected_targets"):
                rollout_multiplier = 0.55 + 0.45 * _path_grounding_rollout_score(analyses[idx])
            else:
                rollout_multiplier = 1.0
            adjusted_rollout_scores.append(round(raw_value * rollout_multiplier, 4))
        metrics["raw_progress_rollout_scores"] = [round(float(v or 0.0), 4) for v in raw_rollout_scores]
        metrics["progress_rollout_scores"] = adjusted_rollout_scores
        metrics["rollout_variance"] = _summarize_rollout_score_variance(adjusted_rollout_scores)
    metrics["raw_progress_fitness"] = round(raw_progress, 4)
    metrics["progress_fitness"] = round(adjusted_progress, 4)
    metrics["selection_fitness"] = round(adjusted_selection, 6)
    metrics["progress_components"] = components
    metrics["path_grounding_fitness"] = {
        "mean_score": round(path_score, 4),
        "progress_multiplier": round(progress_multiplier, 4),
        "scored_rollouts": len(scored),
        "critical_rollouts": critical_count,
        "issue_counts": dict(sorted(issue_counts.items())),
    }
    return metrics


def load_tasks(tasks_path: Path) -> list[dict]:
    """Load tasks from JSONL file. Call once at startup and cache the result."""
    with open(tasks_path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _response_model_from_rollout(rec: dict) -> str:
    response = rec.get("response") if isinstance(rec, dict) else None
    if isinstance(response, dict):
        model = response.get("model")
        if model:
            return str(model)
    return "<missing>"


def validate_rollout_model_consistency(
    rollout_path: Path,
    expected_model: str | None,
    report_path: Path | None = None,
) -> dict:
    """Validate that collected rollouts came from the configured policy model.

    The NeMo-Gym policy model is fixed when `ng_run` starts. Passing a different
    model to `ng_collect_rollouts` is not enough if an old server is still live,
    so this post-collection guard checks the actual `response.model` recorded in
    the rollout artifacts and fails fast on any mismatch.
    """
    expected = (expected_model or "").strip()
    observed: dict[str, int] = {}
    total = 0
    if rollout_path.exists():
        with open(rollout_path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                total += 1
                model = _response_model_from_rollout(rec)
                observed[model] = observed.get(model, 0) + 1

    status = "skipped"
    ok = True
    error_count = int(observed.get("error", 0) or 0)
    missing_count = int(observed.get("<missing>", 0) or 0)
    non_error_observed = {
        model: count
        for model, count in observed.items()
        if model not in {"error", "<missing>"}
    }
    wrong_models = {
        model: count
        for model, count in non_error_observed.items()
        if expected and model != expected
    }

    if expected:
        if wrong_models:
            ok = False
            status = "mismatch"
        elif error_count or missing_count:
            ok = False
            status = "response_error"
        else:
            ok = bool(non_error_observed) and set(non_error_observed) == {expected}
            status = "ok" if ok else "mismatch"

    report = {
        "status": status,
        "ok": ok,
        "expected_model": expected or None,
        "observed_models": dict(sorted(observed.items())),
        "error_rollouts": error_count,
        "missing_model_rollouts": missing_count,
        "wrong_models": dict(sorted(wrong_models.items())),
        "total_rollouts": total,
        "rollout_path": str(rollout_path),
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    if expected and status == "response_error":
        detail = []
        if error_count:
            detail.append(f"error response x{error_count}")
        if missing_count:
            detail.append(f"missing model x{missing_count}")
        detail_text = ", ".join(detail) or "invalid response"
        raise RolloutResponseError(
            "Rollout collection produced invalid response artifacts "
            f"({detail_text}) while configured for {expected!r}. "
            "This is an infrastructure/API collection failure, not evidence that a different rollout model ran."
        )

    if expected and not ok:
        observed_text = ", ".join(f"{model} x{count}" for model, count in sorted(observed.items())) or "none"
        raise RolloutModelMismatchError(
            "Rollout model mismatch: configured "
            f"{expected!r}, but rollout artifacts contain {observed_text}. "
            "Restart NeMo-Gym with policy_model_name set to the configured rollout model."
        )
    return report


def inject_skill_into_tasks(
    tasks: list[dict],
    skill_text: str,
    output_path: Path,
    skill_monitor_cfg: Optional[dict] = None,
    runtime_verifier_feedback_cfg: Optional[dict] = None,
) -> None:
    """Write tasks with the skill text injected into context_files."""
    with open(output_path, "w", encoding="utf-8") as f:
        for task in tasks:
            task = copy.deepcopy(task)
            vm = task.setdefault("verifier_metadata", {})
            cf = vm.setdefault("context_files", {})
            cf["SKILL.md"] = skill_text
            if runtime_verifier_feedback_cfg and runtime_verifier_feedback_cfg.get("enabled"):
                if enable_runtime_verifier_feedback_in_gym_row is None:
                    raise RuntimeError("runtime verifier feedback requested, but converter helper is unavailable")
                enable_runtime_verifier_feedback_in_gym_row(task)
            if skill_monitor_cfg and skill_monitor_cfg.get("enabled"):
                responses_params = task.setdefault("responses_create_params", {})
                metadata = responses_params.setdefault("metadata", {})
                monitor_payload = dict(skill_monitor_cfg)
                monitor_payload.setdefault("mode", "passive")
                # Default monitor mode is observation-only. Experiments that
                # want runtime guardrails can explicitly set warn/block plus
                # inject_feedback=true; baseline optimization should only log
                # adherence so it remains an ablation axis.
                monitor_payload.setdefault("inject_feedback", False)
                monitor_payload["task_id"] = vm.get("task_id", "")
                monitor_payload["categories"] = vm.get("categories", [])
                monitor_payload["difficulty"] = vm.get("difficulty", "")
                if monitor_payload.get("compile_policy", True) and compile_skill_policy is not None:
                    try:
                        monitor_payload["policy"] = compile_skill_policy(
                            skill_text,
                            task.get("responses_create_params", {}).get("input"),
                            task_id=monitor_payload["task_id"],
                            categories=monitor_payload["categories"],
                            difficulty=monitor_payload["difficulty"],
                        )
                    except Exception as e:
                        monitor_payload["policy_compile_error"] = type(e).__name__
                # OpenAI Responses metadata is safest as string values. The
                # agent consumes this private key and strips it before calling
                # the policy model.
                metadata["skill_monitor"] = json.dumps(monitor_payload, ensure_ascii=False)
            f.write(json.dumps(task, ensure_ascii=False) + "\n")


def run_rollouts(
    ng_collect_bin: str,
    tasks_path: Path,
    output_path: Path,
    agent_name: str = "cvdp_agentic_heavy_simple_agent",
    num_repeats: int = 1,
    num_parallel: int = 1,
    timeout: int = 3600,
    nemogym_root: Optional[str] = None,
    ng_config_paths: Optional[list[str]] = None,
    rollout_model_cfg: Optional[dict] = None,
    runtime_verifier_feedback_cfg: Optional[dict] = None,
    resume_from_cache: bool = False,
) -> Path:
    """Run NeMo-Gym rollout collection. Returns path to output JSONL."""
    cmd = [ng_collect_bin]
    responses_max_output_tokens = 16384
    responses_temperature = 0.4
    if rollout_model_cfg:
        responses_max_output_tokens = rollout_model_cfg.get(
            "max_output_tokens", responses_max_output_tokens
        )
        responses_temperature = rollout_model_cfg.get("temperature", responses_temperature)
    responses_max_output_tokens = int(responses_max_output_tokens)
    responses_temperature = float(responses_temperature)

    if ng_config_paths:
        paths_str = ",".join(ng_config_paths)
        cmd.append(f"+config_paths=[{paths_str}]")

    cmd.extend([
        f"+agent_name={agent_name}",
        f"+input_jsonl_fpath={tasks_path}",
        f"+output_jsonl_fpath={output_path}",
        f"+num_repeats={num_repeats}",
        f"+num_samples_in_parallel={num_parallel}",
        (
            "+responses_create_params="
            f"{{max_output_tokens: {responses_max_output_tokens}, "
            f"temperature: {responses_temperature}}}"
        ),
    ])
    if resume_from_cache:
        cmd.append("+resume_from_cache=true")

    env = dict(os.environ)
    if runtime_verifier_feedback_cfg and runtime_verifier_feedback_cfg.get("enabled"):
        env["CVDP_RUNTIME_VERIFIER_FEEDBACK_ENABLED"] = "1"
        env["CVDP_RUNTIME_VERIFIER_FEEDBACK_MAX_CALLS"] = str(
            runtime_verifier_feedback_cfg.get("max_calls", 3)
        )
        artifact_root = runtime_verifier_feedback_cfg.get("artifact_root")
        if artifact_root:
            env["CVDP_RUNTIME_VERIFIER_FEEDBACK_ARTIFACT_ROOT"] = str(artifact_root)
    else:
        env["CVDP_RUNTIME_VERIFIER_FEEDBACK_ENABLED"] = "0"
    if rollout_model_cfg:
        env["policy_base_url"] = rollout_model_cfg.get("base_url", os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1"))
        env["policy_api_key"] = rollout_model_cfg.get("api_key", os.environ.get("LLM_API_KEY", "ollama"))
        env["policy_model_name"] = rollout_model_cfg.get("model", os.environ.get("ROLLOUT_MODEL", ""))
        # NeMo-Gym's env config still resolves the public LLM_* keys. Keep the
        # policy_* aliases and LLM_* names in sync so standalone eval runners do
        # not fail config interpolation when launched outside launch_optimizer.sh.
        env["LLM_BASE_URL"] = env["policy_base_url"]
        env["LLM_API_KEY"] = env["policy_api_key"]
        env["ROLLOUT_MODEL"] = env["policy_model_name"]
        timeout_env_map = {
            "internal_request_max_retries": "NEMOGYM_INTERNAL_REQUEST_MAX_RETRIES",
            "external_request_max_retries": "NEMOGYM_EXTERNAL_REQUEST_MAX_RETRIES",
            "aiohttp_timeout_total": "NEMOGYM_AIOHTTP_TIMEOUT_TOTAL",
            "aiohttp_timeout_sock_read": "NEMOGYM_AIOHTTP_TIMEOUT_SOCK_READ",
        }
        for cfg_key, env_key in timeout_env_map.items():
            if cfg_key in rollout_model_cfg and rollout_model_cfg[cfg_key] is not None:
                env[env_key] = str(rollout_model_cfg[cfg_key])

    cwd = nemogym_root or None

    print(f"  [fitness] Running rollouts: {agent_name}, {num_repeats} repeat(s), {num_parallel} parallel")
    print(f"  [fitness] Model: {env.get('policy_model_name', 'default')}")
    print(f"  [fitness] Responses temperature: {responses_temperature}")
    if resume_from_cache:
        print("  [fitness] Resume from cache: enabled")
    print(f"  [fitness] Tasks: {tasks_path}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
        )
    except subprocess.TimeoutExpired:
        print(f"  [fitness] ⚠ Rollout collection timed out after {timeout}s — using partial results from {output_path}")
        return output_path

    if result.returncode != 0:
        print(f"  [fitness] Rollout collection failed (exit {result.returncode})")
        if result.stderr:
            stderr_lines = result.stderr.strip().split("\n")
            for line in stderr_lines[-5:]:
                print(f"  [fitness]   {line}")
    else:
        print(f"  [fitness] Rollouts complete")
        if output_path.exists():
            import json as _json
            with open(output_path) as _f:
                for _i, _line in enumerate(_f):
                    if not _line.strip():
                        continue
                    try:
                        _r = _json.loads(_line)
                        _tid = _r.get("task_id", "?")
                        _reward = _r.get("reward", 0)
                        _steps = len([o for o in _r.get("response", {}).get("output", []) if o.get("type") == "function_call"])
                        _tools = set(o.get("name", "?") for o in _r.get("response", {}).get("output", []) if o.get("type") == "function_call")
                        _status = "PASS" if _reward > 0 else "FAIL"
                        print(f"  [fitness]   {_status} {_tid} | {_steps} steps | tools: {', '.join(_tools)}")
                    except Exception:
                        pass

    return output_path


def run_eval_analyzer(
    rollout_summary: dict,
    eval_llm_cfg: dict,
    repo_root: Path,
) -> Optional[str]:
    """Run the NAT analyzer on a rollout summary to produce a behavioral report."""
    try:
        skill_text = load_skill(repo_root)
        user_prompt = build_user_prompt(rollout_summary)
        client = openai.OpenAI(
            base_url=eval_llm_cfg["base_url"],
            api_key=eval_llm_cfg.get("api_key", "ollama"),
            timeout=600.0,
            max_retries=0,
        )
        limiter = get_rate_limiter()
        limiter.wait()
        try:
            report = run_analyzer(
                client,
                eval_llm_cfg["model"],
                skill_text,
                user_prompt,
            )
            limiter.record_success()
        except Exception:
            limiter.record_error()
            raise
        return report
    except Exception as e:
        print(f"  [fitness] Analyzer failed: {e}")
        return None


def evaluate_prompt(
    skill_text: str,
    tasks: list[dict],
    ng_collect_bin: str,
    work_dir: Path,
    agent_name: str = "cvdp_agentic_heavy_simple_agent",
    num_repeats: int = 1,
    num_parallel: int = 1,
    timeout: int = 3600,
    trial_id: str = "trial",
    eval_llm_cfg: Optional[dict] = None,
    run_analyzer_flag: bool = False,
    repo_root: Optional[Path] = None,
    nemogym_root: Optional[str] = None,
    ng_config_paths: Optional[list[str]] = None,
    rollout_model_cfg: Optional[dict] = None,
    skill_monitor_cfg: Optional[dict] = None,
    runtime_verifier_feedback_cfg: Optional[dict] = None,
) -> dict:
    """Full fitness evaluation using NAT eval flow.

    Pipeline: inject skill → run rollouts → convert (structured metrics) →
              optionally analyze (behavioral report) → return fitness.

    Returns dict with:
      - pass_at_1: float (true verifier pass-rate objective)
      - progress_fitness: float (dense auxiliary progress signal)
      - selection_fitness: float (pass_at_1 plus bounded progress tiebreaker)
      - per_task: dict[str, dict] (structured per-task metrics from NAT eval)
      - num_rollouts: int
      - elapsed: float (seconds)
      - rollout_path: str
      - eval_summary: dict (full NAT eval model summary)
      - analyzer_report: str | None (behavioral analysis from NAT analyzer)
    """
    work_dir.mkdir(parents=True, exist_ok=True)

    # ── CHECKPOINT 1: Pre-rollout (skill injection) ──
    modified_tasks = (work_dir / f"tasks_{trial_id}.jsonl").resolve()
    inject_skill_into_tasks(
        tasks,
        skill_text,
        modified_tasks,
        skill_monitor_cfg=skill_monitor_cfg,
        runtime_verifier_feedback_cfg=runtime_verifier_feedback_cfg,
    )
    print(f"  [pipeline] ✓ Skill injected ({len(skill_text)} chars) → {len(tasks)} tasks written to {modified_tasks.name}")
    if skill_monitor_cfg and skill_monitor_cfg.get("enabled"):
        print(
            "  [pipeline] ✓ Skill monitor enabled "
            f"(mode={skill_monitor_cfg.get('mode', 'passive')}, "
            f"inject_feedback={skill_monitor_cfg.get('inject_feedback', True)})"
        )
    if runtime_verifier_feedback_cfg and runtime_verifier_feedback_cfg.get("enabled"):
        print(
            "  [pipeline] ✓ Runtime verifier feedback enabled "
            f"(max_calls={runtime_verifier_feedback_cfg.get('max_calls', 3)})"
        )

    rollout_output = (work_dir / f"rollouts_{trial_id}.jsonl").resolve()

    # ── CHECKPOINT 2: Rollout execution ──
    t0 = time.time()
    expected_rollouts = len(tasks) * num_repeats
    expected_rollout_model = (rollout_model_cfg or {}).get("model")
    rollout_cfg = rollout_model_cfg or {}
    response_error_retries = int(
        rollout_cfg.get(
            "response_error_retries",
            os.environ.get("CVDP_ROLLOUT_RESPONSE_ERROR_RETRIES", 2),
        )
    )
    response_error_retry_sleep = float(
        rollout_cfg.get(
            "response_error_retry_sleep",
            os.environ.get("CVDP_ROLLOUT_RESPONSE_ERROR_RETRY_SLEEP", 120),
        )
    )
    max_collection_attempts = max(1, response_error_retries + 1)
    stale_generated_outputs = [
        p for p in work_dir.glob(f"*{trial_id}*")
        if p.is_file()
        and p.name != f"tasks_{trial_id}.jsonl"
        and not p.name.startswith(f"rollout_retries_{trial_id}")
        and ".invalid_attempt" not in p.name
    ]
    if stale_generated_outputs:
        archived = _archive_rollout_attempt(
            work_dir,
            trial_id,
            0,
            "stale_generated_outputs_before_rollout_collection",
        )
        print(
            "  [pipeline] ⚠ Archived stale rollout artifacts before retry/resume: "
            f"{len(archived)} files"
        )

    rollout_elapsed = 0.0
    model_report = {}
    for collection_attempt in range(1, max_collection_attempts + 1):
        attempt_t0 = time.time()
        if collection_attempt > 1:
            print(
                "  [pipeline] ↻ Retrying rollout collection "
                f"({collection_attempt}/{max_collection_attempts})"
            )
        run_rollouts(
            ng_collect_bin=ng_collect_bin,
            tasks_path=modified_tasks,
            output_path=rollout_output,
            agent_name=agent_name,
            num_repeats=num_repeats,
            num_parallel=num_parallel,
            timeout=timeout,
            nemogym_root=nemogym_root,
            ng_config_paths=ng_config_paths,
            rollout_model_cfg=rollout_model_cfg,
            runtime_verifier_feedback_cfg=runtime_verifier_feedback_cfg,
            resume_from_cache=collection_attempt > 1 and rollout_output.exists(),
        )
        rollout_elapsed = time.time() - attempt_t0

        if not rollout_output.exists() or rollout_output.stat().st_size == 0:
            reason = f"missing_or_empty_rollout_output_after_{rollout_elapsed:.0f}s"
            if collection_attempt < max_collection_attempts:
                archived = _archive_rollout_attempt(work_dir, trial_id, collection_attempt, reason)
                print(
                    "  [pipeline] ⚠ No rollout output; "
                    f"archived {len(archived)} files and will retry after "
                    f"{response_error_retry_sleep:.0f}s"
                )
                time.sleep(response_error_retry_sleep)
                continue
            print(f"  [pipeline] ✗ No rollout output — file missing or empty after {rollout_elapsed:.0f}s")
            elapsed = time.time() - t0
            return {
                "pass_at_1": 0.0,
                "per_task": {},
                "num_rollouts": 0,
                "expected_rollouts": expected_rollouts,
                "missing_rollouts": expected_rollouts,
                "complete": False,
                "elapsed": round(elapsed, 1),
                "rollout_path": str(rollout_output),
                "eval_summary": {},
                "analyzer_report": None,
            }

        # ── CHECKPOINT 3: Post-rollout (parse and verify) ──
        rollout_summary = _summarize_rollout_file(rollout_output)
        rollout_lines = rollout_summary["rollout_lines"]
        passes = rollout_summary["passes"]
        fails = rollout_summary["fails"]
        avg_steps = rollout_summary["avg_steps"]
        print(
            f"  [pipeline] ✓ Rollouts: {rollout_lines}/{expected_rollouts} collected, "
            f"{passes} pass / {fails} fail, avg {avg_steps:.1f} steps/rollout ({rollout_elapsed:.0f}s)"
        )

        if rollout_lines == 0:
            reason = "zero_rollouts_parsed"
            if collection_attempt < max_collection_attempts:
                archived = _archive_rollout_attempt(work_dir, trial_id, collection_attempt, reason)
                print(
                    "  [pipeline] ⚠ Parsed 0 rollouts; "
                    f"archived {len(archived)} files and will retry after "
                    f"{response_error_retry_sleep:.0f}s"
                )
                time.sleep(response_error_retry_sleep)
                continue
            print(f"  [pipeline] ✗ GUARD: 0 rollouts parsed — aborting evaluation")
            elapsed = time.time() - t0
            return {
                "pass_at_1": 0.0,
                "per_task": {},
                "num_rollouts": 0,
                "expected_rollouts": expected_rollouts,
                "missing_rollouts": expected_rollouts,
                "complete": False,
                "elapsed": round(elapsed, 1),
                "rollout_path": str(rollout_output),
                "eval_summary": {},
                "analyzer_report": None,
            }

        if avg_steps < 3:
            print(f"  [pipeline] ⚠ WARNING: avg steps={avg_steps:.1f} — agent may be stopping too early (Sonnet tool-call issue?)")

        if rollout_lines < expected_rollouts:
            print(f"  [pipeline] ⚠ WARNING: only {rollout_lines}/{expected_rollouts} rollouts collected — some may have timed out")

        try:
            model_report = validate_rollout_model_consistency(
                rollout_output,
                expected_rollout_model,
                report_path=work_dir / f"rollout_model_check_{trial_id}.json",
            )
        except RolloutResponseError as exc:
            if collection_attempt < max_collection_attempts:
                archived = _archive_rollout_attempt(work_dir, trial_id, collection_attempt, str(exc))
                print(
                    "  [pipeline] ⚠ Rollout response error; "
                    f"archived {len(archived)} files and will retry after "
                    f"{response_error_retry_sleep:.0f}s: {exc}"
                )
                time.sleep(response_error_retry_sleep)
                continue
            raise

        if model_report.get("status") == "ok":
            print(
                "  [pipeline] ✓ Rollout model verified: "
                f"{model_report.get('expected_model')} "
                f"({model_report.get('total_rollouts')} rollouts)"
            )
        if rollout_lines < expected_rollouts and collection_attempt < max_collection_attempts:
            print(
                "  [pipeline] ⚠ Partial rollout output is valid but incomplete; "
                f"will resume missing rollouts after {response_error_retry_sleep:.0f}s"
            )
            time.sleep(response_error_retry_sleep)
            continue
        if rollout_lines < expected_rollouts:
            print(
                "  [pipeline] ⚠ Final rollout output remains incomplete after "
                f"{collection_attempt}/{max_collection_attempts} collection attempt(s)"
            )
        break

    # ── CHECKPOINT 4: NAT eval conversion ──
    eval_summary = convert_single_file(rollout_output, model_name=trial_id)
    metrics = eval_summary.get("metrics", {})
    metrics = apply_path_grounding_fitness_adjustment(
        metrics,
        load_rollouts_from_file(rollout_output),
    )
    if eval_summary:
        eval_summary["metrics"] = metrics
    pass_at_1 = metrics.get("overall_pass_at_1", 0.0)
    progress_fitness = metrics.get("progress_fitness", 0.0)
    selection_fitness = metrics.get("selection_fitness", pass_at_1)
    per_task = metrics.get("per_task", {})
    num_rollouts = metrics.get("total_rollouts", 0)
    skill_monitor_metrics = metrics.get("skill_monitor", {})
    runtime_verifier_feedback_metrics = metrics.get("runtime_verifier_feedback", {})
    missing_rollouts = max(0, expected_rollouts - int(num_rollouts or 0))

    summary_path = work_dir / f"eval_summary_{trial_id}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(eval_summary, f, indent=2, ensure_ascii=False)

    task_summary = ", ".join(
        f"{(tid or 'unknown').replace('cvdp_agentic_heavy_', '')}={v.get('pass_at_1', 0):.0%}"
        if isinstance(v, dict) else f"{tid or 'unknown'}={v:.0%}"
        for tid, v in per_task.items()
    )
    print(
        f"  [pipeline] ✓ Eval: pass@1={pass_at_1:.3f}, "
        f"progress={progress_fitness:.3f}, selection={selection_fitness:.3f} [{task_summary}]"
    )
    if skill_monitor_metrics:
        print(
            "  [pipeline] ✓ Skill monitor: "
            f"adherence={skill_monitor_metrics.get('mean_adherence_score', 0):.3f}, "
            f"violations={skill_monitor_metrics.get('total_violations', 0)}, "
            f"blocked={skill_monitor_metrics.get('total_blocked_actions', 0)}"
        )
    if runtime_verifier_feedback_metrics:
        print(
            "  [pipeline] ✓ Runtime verifier feedback: "
            f"calls={runtime_verifier_feedback_metrics.get('VerifierFeedbackCalls', 0)}, "
            f"mean_partial={runtime_verifier_feedback_metrics.get('VerifierFeedbackPartialScore', 0):.3f}, "
            f"policy_violations={runtime_verifier_feedback_metrics.get('VerifierFeedbackPolicyViolations', 0)}"
        )
    path_grounding_fitness = metrics.get("path_grounding_fitness") or {}
    if path_grounding_fitness:
        print(
            "  [pipeline] ✓ Path grounding fitness: "
            f"score={path_grounding_fitness.get('mean_score', 1.0):.3f}, "
            f"multiplier={path_grounding_fitness.get('progress_multiplier', 1.0):.3f}, "
            f"critical={path_grounding_fitness.get('critical_rollouts', 0)}"
        )

    # ── CHECKPOINT 5: NAT analyzer ──
    # NOTE: Per-individual analyzer is skipped — GPT-5 analysis now happens at the
    # generation level inside build_contrastive_oracle() which receives compressed
    # rollout data (~5K chars) instead of raw trajectories (~147K chars that caused
    # empty responses due to prompt size overflow).
    analyzer_report = None

    elapsed = time.time() - t0
    print(f"  [pipeline] ✓ Evaluation complete: {elapsed:.0f}s total")

    return {
        "pass_at_1": pass_at_1,
        "progress_fitness": progress_fitness,
        "selection_fitness": selection_fitness,
        "selection_epsilon": metrics.get("selection_epsilon", 0.0),
        "progress_components": metrics.get("progress_components", {}),
        "progress_rollout_scores": metrics.get("progress_rollout_scores", []),
        "rollout_variance": metrics.get("rollout_variance", {}),
        "raw_progress_fitness": metrics.get("raw_progress_fitness"),
        "raw_progress_rollout_scores": metrics.get("raw_progress_rollout_scores", []),
        "path_grounding_fitness": metrics.get("path_grounding_fitness", {}),
        "skill_monitor": skill_monitor_metrics,
        "runtime_verifier_feedback": runtime_verifier_feedback_metrics,
        "per_task": per_task,
        "num_rollouts": num_rollouts,
        "expected_rollouts": expected_rollouts,
        "missing_rollouts": missing_rollouts,
        "complete": missing_rollouts == 0,
        "elapsed": round(elapsed, 1),
        "rollout_path": str(rollout_output),
        "eval_summary": {
            "model_name": eval_summary.get("model_name"),
            "metrics": metrics,
        },
        "analyzer_report": analyzer_report,
    }

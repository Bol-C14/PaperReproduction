#!/usr/bin/env python3
"""Streaming Oracle — 3-layer feedback pipeline for GA-style prompt optimization.

Architecture:

    Rollout N completes
         │
         ▼
    LAYER 1: update_task_insight(rollout)
        → GPT-5 refines task_insights/<cid>/{task}_{pass|fail}.md in place
        → Called once per rollout (tasks × repeats × population per generation)
         │
         │ ... end of generation ...
         │
         ▼
    LAYER 2: synthesize_cid_task()
        → 2 GPT-5 calls per CID (pass + fail)
        → Reads task_insights/<cid>/{task}_pass.md → cid_synthesis/<cid>/pass_synthesis.md
        → Reads task_insights/<cid>/{task}_fail.md → cid_synthesis/<cid>/fail_synthesis.md
         │
         ▼
    LAYER 3: build_cid_oracle_feedback()
        → 1 GPT-5 call per CID
        → Combines CID pass/fail synthesis + CID scoreboard → cid_oracle_feedback/<cid>.md
        → oracle_feedback.md is the combined handoff the mutation LLM reads
          for next-gen mutations
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Optional

import openai

from debug_logging import ErrorLogger
from llm_audit import LLMAuditLogger, chat_completion
from path_grounding import format_path_grounding_for_oracle
from rate_limiter import get_rate_limiter


# ── Prompt loading ────────────────────────────────────────────────
_SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


def _load_prompt(relpath: str) -> str:
    path = _SKILLS_DIR / relpath
    if not path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {path}. See skills/README.md for layout."
        )
    return path.read_text(encoding="utf-8")


TASK_INSIGHT_REFINE_PROMPT = _load_prompt("optimizer/task_insight_refine.md")
PASS_CROSS_SYNTHESIS_PROMPT = _load_prompt("optimizer/pass_cross_synthesis.md")
FAIL_CROSS_SYNTHESIS_PROMPT = _load_prompt("optimizer/fail_cross_synthesis.md")
ORACLE_HANDOFF_PROMPT = _load_prompt("optimizer/oracle_handoff.md")

CID_RE = re.compile(r"cid\d{3}", re.IGNORECASE)
HeartbeatCallback = Callable[..., None]


def _oracle_heartbeat(
    callback: Optional[HeartbeatCallback],
    *,
    phase: str,
    generation: int,
    context: Optional[dict[str, Any]] = None,
    message: Optional[str] = None,
) -> None:
    """Best-effort heartbeat for long oracle stages.

    Layer 1/2/3 calls can take many minutes even though prompt/response files
    are actively moving. Updating the run-level heartbeat inside those layers
    prevents monitors from mistaking an active oracle call for a dead optimizer.
    """
    if callback is None:
        return
    try:
        callback(
            phase=phase,
            generation=generation,
            context=context or {},
            message=message,
        )
    except Exception:
        pass


def _short_task_id(task_id: str | None) -> str:
    return (task_id or "unknown").replace("cvdp_agentic_heavy_", "")


def _find_cid(*values) -> str | None:
    for value in values:
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            found = _find_cid(*value)
            if found:
                return found
            continue
        match = CID_RE.search(str(value))
        if match:
            return match.group(0).lower()
    return None


def _normalize_task_cid_lookup(
    task_manifest: Optional[list[dict]] = None,
    task_cid_lookup: Optional[dict[str, str]] = None,
) -> dict[str, str]:
    lookup: dict[str, str] = {}
    if task_cid_lookup:
        for task_id, cid in task_cid_lookup.items():
            cid_norm = _find_cid(cid) or str(cid or "unknown")
            lookup[str(task_id)] = cid_norm
            lookup[_short_task_id(str(task_id))] = cid_norm
    for row in task_manifest or []:
        task_id = str(row.get("task_id") or "unknown")
        short = str(row.get("short_task_id") or _short_task_id(task_id))
        cid = _find_cid(row.get("cid"), row.get("categories"), task_id, short) or "unknown"
        lookup[task_id] = cid
        lookup[short] = cid
    return lookup


def _rollout_cid(rollout: dict, task_cid_lookup: Optional[dict[str, str]] = None) -> str:
    task_id = rollout.get("task_id") or "unknown"
    metadata = rollout.get("verifier_metadata") or {}
    cid = _find_cid(
        rollout.get("category"),
        rollout.get("categories"),
        metadata.get("cid") if isinstance(metadata, dict) else None,
        metadata.get("categories") if isinstance(metadata, dict) else None,
        task_cid_lookup.get(task_id) if task_cid_lookup else None,
        task_cid_lookup.get(_short_task_id(task_id)) if task_cid_lookup else None,
        task_id,
    )
    return cid or "unknown"


# ── Rollout compression ───────────────────────────────────────────


def _compress_rollout_for_refine(rollout: dict, rollout_id: str) -> str:
    """Compress a single rollout into a Layer-1-friendly text summary.

    Captures more detail than `_analyze_rollout` in prompt_mutator.py:
    - Tool names WITH arguments (echo targets, iverilog files/flags)
    - Full error messages (not truncated to 200 chars)
    - Docker stderr tail if rollout failed
    - Reasoning blocks if present
    """
    task_id = (rollout.get("task_id") or "unknown").replace("cvdp_agentic_heavy_", "")
    reward = rollout.get("reward", 0)
    outcome = "PASS" if reward > 0 else "FAIL"

    response = rollout.get("response") or {}
    output_items = response.get("output") or []
    fn_calls = [o for o in output_items if isinstance(o, dict) and o.get("type") == "function_call"]
    fn_outputs = [o for o in output_items if isinstance(o, dict) and o.get("type") == "function_call_output"]
    messages = [o for o in output_items if isinstance(o, dict) and o.get("type") == "message"]

    # Build tool-call-with-args sequence
    tool_trace = []
    for call in fn_calls:
        name = call.get("name") or "?"
        args_raw = call.get("arguments") or "{}"
        try:
            args = json.loads(args_raw) if isinstance(args_raw, str) else (args_raw or {})
        except Exception:
            args = {}
        if not isinstance(args, dict):
            args = {}
        # Summarize args compactly
        if name == "echo":
            target = args.get("filename") or args.get("path") or "?"
            content_len = len(args.get("content") or "")
            tool_trace.append(f"echo → {target} ({content_len} bytes)")
        elif name == "iverilog":
            arg_str = args.get("args") or args.get("command") or ""
            if isinstance(arg_str, list):
                arg_str = " ".join(str(x) for x in arg_str)
            elif not isinstance(arg_str, str):
                arg_str = str(arg_str)
            tool_trace.append(f"iverilog {arg_str[:150]}")
        elif name in ("ls", "cat", "vvp", "pwd"):
            target = args.get("path") or args.get("filename") or ""
            tool_trace.append(f"{name}({target})" if target else name)
        else:
            tool_trace.append(f"{name}({str(args)[:80]})")

    # Extract errors from tool outputs (full, not truncated)
    errors = []
    for o in fn_outputs:
        out = o.get("output", "")
        if isinstance(out, str):
            try:
                parsed = json.loads(out)
                text = parsed.get("output", out) if isinstance(parsed, dict) else out
            except Exception:
                text = out
            if isinstance(text, str):
                low = text.lower()
                if ("error:" in low or "syntax error" in low or "not found" in low or
                    "unknown module" in low or "timed out" in low):
                    # Keep up to 400 chars per error for context
                    errors.append(text[:400].strip())

    # Docker stderr tail (grading output)
    docker_stderr = rollout.get("docker_stderr", "") or ""
    docker_exit = rollout.get("docker_exit_code", -1)
    stderr_excerpt = ""
    if outcome == "FAIL" and docker_stderr:
        # Tail the last 1500 chars (usually where the grading verdict is)
        stderr_excerpt = docker_stderr[-1500:] if len(docker_stderr) > 1500 else docker_stderr

    # Reasoning excerpts (agent's stated thinking)
    reasoning = []
    for m in messages[:3]:  # limit to first 3 messages
        content = m.get("content") or ""
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") in ("text", "output_text"):
                    text = item.get("text") or ""
                    if text:
                        reasoning.append(text[:300])
        elif isinstance(content, str):
            if content:
                reasoning.append(content[:300])

    # Phase classification
    tool_names = {call.get("name", "?") for call in fn_calls}
    if "vvp" in tool_names:
        phase = "P4-tested"
    elif "iverilog" in tool_names:
        phase = "P3-compiled"
    elif "echo" in tool_names:
        phase = "P2-wrote-files"
    elif "cat" in tool_names or "ls" in tool_names:
        phase = "P1-explored"
    else:
        phase = "P0-no-tools"

    lines = [
        f"ROLLOUT_ID: {rollout_id}",
        f"TASK: {task_id}",
        f"OUTCOME: {outcome} (reward={reward}, docker_exit={docker_exit})",
        f"PHASE_REACHED: {phase}",
        f"STEPS: {len(fn_calls)}",
        "",
        "TOOL_TRACE:",
    ]
    for i, step in enumerate(tool_trace):
        lines.append(f"  [{i+1}] {step}")

    path_grounding = format_path_grounding_for_oracle(rollout)
    if path_grounding:
        lines.append("")
        lines.append(path_grounding)

    if errors:
        lines.append("")
        lines.append(f"ERRORS OBSERVED ({len(errors)}):")
        for err in errors[:5]:  # up to 5 errors per rollout
            lines.append(f"  - {err}")

    if stderr_excerpt:
        lines.append("")
        lines.append("DOCKER_STDERR (tail, grading output):")
        lines.append(stderr_excerpt)

    if reasoning:
        lines.append("")
        lines.append("AGENT_REASONING (excerpts):")
        for r in reasoning[:2]:
            if r.strip():
                lines.append(f"  - {r.strip()}")

    return "\n".join(lines)


# ── Layer 1: streaming per-task insight refinement ───────────────


def update_task_insight(
    rollout: dict,
    rollout_id: str,
    task_insights_dir: Path,
    llm_client: openai.OpenAI,
    llm_model: str,
    max_tokens: int = 16384,
    audit_logger: Optional[LLMAuditLogger] = None,
    error_logger: Optional[ErrorLogger] = None,
    generation: Optional[int] = None,
    task_cid_lookup: Optional[dict[str, str]] = None,
    cid_aware: bool = False,
) -> Optional[Path]:
    """Layer 1: update the task-specific pass/fail insight doc with a new rollout.

    Reads the existing `{task}_{pass|fail}.md` (or empty if first rollout),
    asks GPT-5 to refine it using the CONFIRMS/EXTENDS/CONTRADICTS/NEW protocol,
    and writes back the updated document.

    Returns the path to the updated file, or None on error.
    """
    task_id = _short_task_id(rollout.get("task_id") or "unknown")
    cid = _rollout_cid(rollout, task_cid_lookup)
    reward = rollout.get("reward", 0)
    outcome = "pass" if reward > 0 else "fail"

    doc_dir = task_insights_dir / cid if cid_aware else task_insights_dir
    doc_dir.mkdir(parents=True, exist_ok=True)
    doc_path = doc_dir / f"{task_id}_{outcome}.md"

    existing_doc = doc_path.read_text(encoding="utf-8") if doc_path.exists() else ""
    new_rollout_summary = _compress_rollout_for_refine(rollout, rollout_id)

    prompt = TASK_INSIGHT_REFINE_PROMPT.replace("{task_id}", task_id) \
                                        .replace("{outcome}", outcome) \
                                        .replace("{existing_doc}", existing_doc or "(empty — this is the first rollout for this task+outcome)") \
                                        .replace("{new_rollout}", new_rollout_summary)

    limiter = get_rate_limiter()
    limiter.wait()
    try:
        response = chat_completion(
            llm_client, llm_model,
            messages=[
                {"role": "system", "content": "You are an expert RTL agent behavioral analyst. Follow the refinement protocol exactly."},
                {"role": "user", "content": prompt},
            ],
            audit_logger=audit_logger,
            purpose="layer1_refine",
            context={
                "task": task_id,
                "cid": cid if cid_aware else None,
                "outcome": outcome,
                "rollout_id": rollout_id,
                "existing_doc_chars": len(existing_doc),
            },
            temperature=0.0,
            max_tokens=max_tokens,
        )
        limiter.record_success()
        updated = response.choices[0].message.content or ""
    except Exception as e:
        limiter.record_error()
        print(f"    [Layer1] GPT-5 refine failed for {task_id}/{outcome}: {e}")
        if error_logger is not None:
            error_logger.record(
                phase="oracle_layer1",
                generation=generation,
                context={"task": task_id, "cid": cid if cid_aware else None,
                         "outcome": outcome, "rollout_id": rollout_id},
                exception=e,
            )
        return None

    if not updated.strip():
        msg = f"[Layer1] Empty response for {task_id}/{outcome} (reasoning tokens likely exhausted budget)"
        print(f"    {msg}")
        if error_logger is not None:
            error_logger.record_info(
                phase="oracle_layer1",
                message=msg,
                generation=generation,
                context={"task": task_id, "cid": cid if cid_aware else None,
                         "outcome": outcome, "rollout_id": rollout_id},
            )
        return None

    doc_path.write_text(updated, encoding="utf-8")
    return doc_path


# ── Layer 2: cross-task synthesis ────────────────────────────────


def synthesize_cross_task(
    task_insights_dir: Path,
    cross_task_dir: Path,
    outcome: str,  # "pass" or "fail"
    generation: int,
    llm_client: openai.OpenAI,
    llm_model: str,
    max_tokens: int = 16384,
    audit_logger: Optional[LLMAuditLogger] = None,
    error_logger: Optional[ErrorLogger] = None,
) -> Optional[Path]:
    """Layer 2: synthesize cross-task generalizable patterns for one outcome.

    Reads all task_insights/{task}_{outcome}.md files, concatenates them,
    and asks GPT-5 to extract generalizable principles with task-specific
    evidence.

    Returns the path to cross_task/{outcome}_synthesis.md, or None on error.
    """
    if outcome not in ("pass", "fail"):
        raise ValueError(f"outcome must be 'pass' or 'fail', got {outcome!r}")

    input_docs = sorted(task_insights_dir.rglob(f"*_{outcome}.md"))
    if not input_docs:
        print(f"    [Layer2] No {outcome} docs to synthesize in {task_insights_dir}")
        return None

    # Concatenate all per-task docs with clear headers
    sections = []
    for doc in input_docs:
        content = doc.read_text(encoding="utf-8").strip()
        if content:
            sections.append(f"### FROM {doc.name}\n\n{content}")
    concatenated = "\n\n---\n\n".join(sections)

    prompt_tmpl = PASS_CROSS_SYNTHESIS_PROMPT if outcome == "pass" else FAIL_CROSS_SYNTHESIS_PROMPT
    prompt = prompt_tmpl.replace("{generation}", str(generation)) \
                        .replace("{task_insight_docs}", concatenated)

    limiter = get_rate_limiter()
    limiter.wait()
    try:
        response = chat_completion(
            llm_client, llm_model,
            messages=[
                {"role": "system", "content": "You are an expert RTL agent behavioral analyst. Synthesize cross-task patterns."},
                {"role": "user", "content": prompt},
            ],
            audit_logger=audit_logger,
            purpose=f"layer2_{outcome}_synthesis",
            context={
                "generation": generation,
                "outcome": outcome,
                "n_input_docs": len(input_docs),
            },
            temperature=0.0,
            max_tokens=max_tokens,
        )
        limiter.record_success()
        synthesis = response.choices[0].message.content or ""
    except Exception as e:
        limiter.record_error()
        print(f"    [Layer2] GPT-5 {outcome} synthesis failed: {e}")
        if error_logger is not None:
            error_logger.record(
                phase="oracle_layer2",
                generation=generation,
                context={"outcome": outcome, "n_input_docs": len(input_docs)},
                exception=e,
            )
        return None

    if not synthesis.strip():
        msg = f"[Layer2] Empty response for {outcome} synthesis"
        print(f"    {msg}")
        if error_logger is not None:
            error_logger.record_info(
                phase="oracle_layer2",
                message=msg,
                generation=generation,
                context={"outcome": outcome, "n_input_docs": len(input_docs)},
            )
        return None

    cross_task_dir.mkdir(parents=True, exist_ok=True)
    out_path = cross_task_dir / f"{outcome}_synthesis.md"
    out_path.write_text(synthesis, encoding="utf-8")
    return out_path


def _task_from_insight_path(path: Path, outcome: str) -> str:
    return path.stem.removesuffix(f"_{outcome}")


def _group_task_insight_docs_by_cid(
    task_insights_dir: Path,
    outcome: str,
    task_cid_lookup: Optional[dict[str, str]] = None,
) -> dict[str, list[Path]]:
    grouped: dict[str, list[Path]] = {}
    for doc in sorted(task_insights_dir.rglob(f"*_{outcome}.md")):
        rel_parts = doc.relative_to(task_insights_dir).parts
        task_id = _task_from_insight_path(doc, outcome)
        if len(rel_parts) > 1:
            cid = _find_cid(rel_parts[0]) or "unknown"
        else:
            cid = (
                (task_cid_lookup or {}).get(task_id)
                or (task_cid_lookup or {}).get(_short_task_id(task_id))
                or _find_cid(task_id)
                or "unknown"
            )
        grouped.setdefault(cid, []).append(doc)
    return grouped


def synthesize_cid_task(
    input_docs: list[Path],
    cid_synthesis_dir: Path,
    cid: str,
    outcome: str,
    generation: int,
    llm_client: openai.OpenAI,
    llm_model: str,
    max_tokens: int = 16384,
    audit_logger: Optional[LLMAuditLogger] = None,
    error_logger: Optional[ErrorLogger] = None,
) -> Optional[Path]:
    """Layer 2: synthesize task evidence into a CID-local pass/fail summary."""
    if outcome not in ("pass", "fail"):
        raise ValueError(f"outcome must be 'pass' or 'fail', got {outcome!r}")
    if not input_docs:
        print(f"    [Layer2:{cid}] No {outcome} docs to synthesize")
        return None

    sections = []
    for doc in input_docs:
        content = doc.read_text(encoding="utf-8").strip()
        if content:
            sections.append(f"### CID {cid} FROM {doc.name}\n\n{content}")
    concatenated = "\n\n---\n\n".join(sections)
    if not concatenated.strip():
        return None

    prompt_tmpl = PASS_CROSS_SYNTHESIS_PROMPT if outcome == "pass" else FAIL_CROSS_SYNTHESIS_PROMPT
    prompt = prompt_tmpl.replace("{generation}", str(generation)) \
                        .replace("{task_insight_docs}", f"CID: {cid}\n\n{concatenated}")

    limiter = get_rate_limiter()
    limiter.wait()
    try:
        response = chat_completion(
            llm_client, llm_model,
            messages=[
                {"role": "system", "content": f"You are an expert RTL agent behavioral analyst. Synthesize patterns only for CID {cid}; do not mix in other CID behavior."},
                {"role": "user", "content": prompt},
            ],
            audit_logger=audit_logger,
            purpose=f"layer2_{outcome}_synthesis_by_cid",
            context={
                "generation": generation,
                "cid": cid,
                "outcome": outcome,
                "n_input_docs": len(input_docs),
            },
            temperature=0.0,
            max_tokens=max_tokens,
        )
        limiter.record_success()
        synthesis = response.choices[0].message.content or ""
    except Exception as e:
        limiter.record_error()
        print(f"    [Layer2:{cid}] GPT-5 {outcome} synthesis failed: {e}")
        if error_logger is not None:
            error_logger.record(
                phase="oracle_layer2_cid",
                generation=generation,
                context={"cid": cid, "outcome": outcome, "n_input_docs": len(input_docs)},
                exception=e,
            )
        return None

    if not synthesis.strip():
        msg = f"[Layer2:{cid}] Empty response for {outcome} synthesis"
        print(f"    {msg}")
        if error_logger is not None:
            error_logger.record_info(
                phase="oracle_layer2_cid",
                message=msg,
                generation=generation,
                context={"cid": cid, "outcome": outcome, "n_input_docs": len(input_docs)},
            )
        return None

    out_dir = cid_synthesis_dir / cid
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{outcome}_synthesis.md"
    out_path.write_text(synthesis, encoding="utf-8")
    return out_path


def _rollout_counts_by_cid(
    rollouts_by_individual: list[list[dict]],
    task_cid_lookup: dict[str, str],
) -> dict[str, dict]:
    counts: dict[str, dict] = {}
    for ind_rollouts in rollouts_by_individual:
        for rollout in ind_rollouts:
            cid = _rollout_cid(rollout, task_cid_lookup)
            task_id = _short_task_id(rollout.get("task_id") or "unknown")
            row = counts.setdefault(cid, {
                "cid": cid,
                "rollouts": 0,
                "passes": 0,
                "fails": 0,
                "tasks": {},
            })
            row["rollouts"] += 1
            if rollout.get("reward", 0) > 0:
                row["passes"] += 1
            else:
                row["fails"] += 1
            task_row = row["tasks"].setdefault(task_id, {"rollouts": 0, "passes": 0, "fails": 0})
            task_row["rollouts"] += 1
            if rollout.get("reward", 0) > 0:
                task_row["passes"] += 1
            else:
                task_row["fails"] += 1
    for row in counts.values():
        row["pass_rate"] = row["passes"] / row["rollouts"] if row["rollouts"] else 0.0
        task_rates = []
        for task_row in row["tasks"].values():
            task_row["pass_rate"] = (
                task_row["passes"] / task_row["rollouts"]
                if task_row["rollouts"] else 0.0
            )
            task_rates.append(task_row["pass_rate"])
        row["macro_task_pass_rate"] = sum(task_rates) / len(task_rates) if task_rates else 0.0
    return counts


def synthesize_cid_level(
    task_insights_dir: Path,
    cid_synthesis_dir: Path,
    generation: int,
    rollouts_by_individual: list[list[dict]],
    task_cid_lookup: dict[str, str],
    llm_client: openai.OpenAI,
    llm_model: str,
    max_tokens: int = 16384,
    audit_logger: Optional[LLMAuditLogger] = None,
    error_logger: Optional[ErrorLogger] = None,
    heartbeat_callback: Optional[HeartbeatCallback] = None,
) -> dict[str, dict[str, Optional[Path]]]:
    """Layer 2 for multi-task-per-CID runs."""
    grouped = {
        "pass": _group_task_insight_docs_by_cid(task_insights_dir, "pass", task_cid_lookup),
        "fail": _group_task_insight_docs_by_cid(task_insights_dir, "fail", task_cid_lookup),
    }
    all_cids = sorted(set(grouped["pass"]) | set(grouped["fail"]) | set(_rollout_counts_by_cid(rollouts_by_individual, task_cid_lookup)))
    counts = _rollout_counts_by_cid(rollouts_by_individual, task_cid_lookup)
    results: dict[str, dict[str, Optional[Path]]] = {}

    for cid in all_cids:
        _oracle_heartbeat(
            heartbeat_callback,
            phase="oracle_layer2_cid",
            generation=generation,
            context={"cid": cid, "stage": "metrics", "num_cids": len(all_cids)},
            message=f"Layer 2 CID synthesis metrics for {cid}",
        )
        cid_dir = cid_synthesis_dir / cid
        cid_dir.mkdir(parents=True, exist_ok=True)
        metrics = counts.get(cid, {"cid": cid, "rollouts": 0, "passes": 0, "fails": 0, "tasks": {}, "pass_rate": 0.0})
        metrics["layer1_docs"] = {
            "pass": [str(p.relative_to(task_insights_dir.parent)) for p in grouped["pass"].get(cid, [])],
            "fail": [str(p.relative_to(task_insights_dir.parent)) for p in grouped["fail"].get(cid, [])],
        }
        (cid_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

        _oracle_heartbeat(
            heartbeat_callback,
            phase="oracle_layer2_cid",
            generation=generation,
            context={
                "cid": cid,
                "outcome": "pass",
                "n_input_docs": len(grouped["pass"].get(cid, [])),
                "num_cids": len(all_cids),
            },
            message=f"Layer 2 pass synthesis for {cid}",
        )
        pass_path = synthesize_cid_task(
            grouped["pass"].get(cid, []), cid_synthesis_dir, cid, "pass",
            generation, llm_client, llm_model, max_tokens=max_tokens,
            audit_logger=audit_logger, error_logger=error_logger,
        )
        _oracle_heartbeat(
            heartbeat_callback,
            phase="oracle_layer2_cid",
            generation=generation,
            context={
                "cid": cid,
                "outcome": "fail",
                "n_input_docs": len(grouped["fail"].get(cid, [])),
                "num_cids": len(all_cids),
            },
            message=f"Layer 2 fail synthesis for {cid}",
        )
        fail_path = synthesize_cid_task(
            grouped["fail"].get(cid, []), cid_synthesis_dir, cid, "fail",
            generation, llm_client, llm_model, max_tokens=max_tokens,
            audit_logger=audit_logger, error_logger=error_logger,
        )
        results[cid] = {"pass": pass_path, "fail": fail_path}
    return results


def _combine_cid_syntheses_for_legacy_index(
    cid_synthesis_dir: Path,
    cross_task_dir: Path,
    outcome: str,
) -> Optional[Path]:
    docs = sorted(cid_synthesis_dir.glob(f"*/{outcome}_synthesis.md"))
    if not docs:
        return None
    sections = []
    for doc in docs:
        cid = doc.parent.name
        content = doc.read_text(encoding="utf-8").strip()
        if content:
            sections.append(f"## CID {cid}\n\n{content}")
    if not sections:
        return None
    cross_task_dir.mkdir(parents=True, exist_ok=True)
    out_path = cross_task_dir / f"{outcome}_synthesis.md"
    out_path.write_text("\n\n---\n\n".join(sections) + "\n", encoding="utf-8")
    return out_path


# ── Layer 3: oracle feedback handoff ─────────────────────────────


def build_oracle_feedback(
    gen_dir: Path,
    generation: int,
    scoreboard: str,
    best: float,
    mean: float,
    worst: float,
    n_pass: int,
    n_fail: int,
    llm_client: openai.OpenAI,
    llm_model: str,
    max_tokens: int = 16384,
    audit_logger: Optional[LLMAuditLogger] = None,
    error_logger: Optional[ErrorLogger] = None,
) -> Optional[Path]:
    """Layer 3: produce the final oracle feedback document Opus will consume.

    Reads cross_task/pass_synthesis.md and cross_task/fail_synthesis.md,
    combines with the scoreboard and generation stats, and asks GPT-5 to
    produce a KEEP/ADD/REMOVE/CHANGE directive document.

    Returns the path to oracle_feedback.md, or None on error.
    """
    pass_path = gen_dir / "cross_task" / "pass_synthesis.md"
    fail_path = gen_dir / "cross_task" / "fail_synthesis.md"

    pass_synthesis = pass_path.read_text(encoding="utf-8") if pass_path.exists() else "(none)"
    fail_synthesis = fail_path.read_text(encoding="utf-8") if fail_path.exists() else "(none)"

    total = n_pass + n_fail
    prompt = ORACLE_HANDOFF_PROMPT \
        .replace("{generation}", str(generation)) \
        .replace("{best:.3f}", f"{best:.3f}") \
        .replace("{mean:.3f}", f"{mean:.3f}") \
        .replace("{worst:.3f}", f"{worst:.3f}") \
        .replace("{total}", str(total)) \
        .replace("{n_pass}", str(n_pass)) \
        .replace("{n_fail}", str(n_fail)) \
        .replace("{scoreboard}", scoreboard) \
        .replace("{pass_synthesis}", pass_synthesis) \
        .replace("{fail_synthesis}", fail_synthesis) \
        .replace("{gen}", str(generation))

    limiter = get_rate_limiter()
    limiter.wait()
    try:
        response = chat_completion(
            llm_client, llm_model,
            messages=[
                {"role": "system", "content": "You are producing actionable oracle feedback for a prompt-optimization LLM. Every directive must be concrete and grounded."},
                {"role": "user", "content": prompt},
            ],
            audit_logger=audit_logger,
            purpose="layer3_handoff",
            context={
                "generation": generation,
                "best": best, "mean": mean, "worst": worst,
                "n_pass": n_pass, "n_fail": n_fail,
            },
            temperature=0.0,
            max_tokens=max_tokens,
        )
        limiter.record_success()
        handoff = response.choices[0].message.content or ""
    except Exception as e:
        limiter.record_error()
        print(f"    [Layer3] GPT-5 oracle handoff failed: {e}")
        if error_logger is not None:
            error_logger.record(
                phase="oracle_layer3",
                generation=generation,
                context={"best": best, "mean": mean, "worst": worst,
                         "n_pass": n_pass, "n_fail": n_fail},
                exception=e,
            )
        return None

    if not handoff.strip():
        msg = "[Layer3] Empty response for oracle handoff"
        print(f"    {msg}")
        if error_logger is not None:
            error_logger.record_info(
                phase="oracle_layer3",
                message=msg,
                generation=generation,
            )
        return None

    out_path = gen_dir / "oracle_feedback.md"
    out_path.write_text(handoff, encoding="utf-8")
    return out_path


def _scoreboard_for_cid(scoreboard: str, cid: str, task_cid_lookup: dict[str, str]) -> str:
    task_keys = [task for task, task_cid in task_cid_lookup.items() if task_cid == cid]
    lines = []
    for line in scoreboard.splitlines():
        if any(task and task in line for task in task_keys):
            lines.append(line)
    if not lines:
        lines = [line for line in scoreboard.splitlines() if cid in line]
    return "\n".join(lines).strip() or scoreboard


def build_cid_oracle_feedback(
    gen_dir: Path,
    generation: int,
    scoreboard: str,
    best: float,
    mean: float,
    worst: float,
    cid_results: dict[str, dict[str, Optional[Path]]],
    cid_counts: dict[str, dict],
    task_cid_lookup: dict[str, str],
    llm_client: openai.OpenAI,
    llm_model: str,
    max_tokens: int = 16384,
    audit_logger: Optional[LLMAuditLogger] = None,
    error_logger: Optional[ErrorLogger] = None,
    heartbeat_callback: Optional[HeartbeatCallback] = None,
) -> Optional[Path]:
    """Layer 3: produce one oracle handoff per CID, then combine them.

    This is the key multi-task-per-CID behavior: a CID skill is mutated from
    patterns mined across tasks in the same CID, not from one task in isolation
    and not from a flattened global summary.
    """
    out_dir = gen_dir / "cid_oracle_feedback"
    out_dir.mkdir(parents=True, exist_ok=True)
    cid_handoffs: dict[str, str] = {}

    for cid in sorted(cid_results):
        paths = cid_results[cid]
        pass_path = paths.get("pass")
        fail_path = paths.get("fail")
        if not pass_path and not fail_path:
            continue
        _oracle_heartbeat(
            heartbeat_callback,
            phase="oracle_layer3_cid",
            generation=generation,
            context={
                "cid": cid,
                "has_pass_synthesis": bool(pass_path),
                "has_fail_synthesis": bool(fail_path),
            },
            message=f"Layer 3 CID oracle handoff for {cid}",
        )
        pass_synthesis = pass_path.read_text(encoding="utf-8") if pass_path and pass_path.exists() else "(none)"
        fail_synthesis = fail_path.read_text(encoding="utf-8") if fail_path and fail_path.exists() else "(none)"
        counts = cid_counts.get(cid, {"rollouts": 0, "passes": 0, "fails": 0})
        total = int(counts.get("rollouts", 0) or 0)
        n_pass = int(counts.get("passes", 0) or 0)
        n_fail = int(counts.get("fails", 0) or 0)
        cid_scoreboard = _scoreboard_for_cid(scoreboard, cid, task_cid_lookup)

        prompt = ORACLE_HANDOFF_PROMPT \
            .replace("{generation}", str(generation)) \
            .replace("{best:.3f}", f"{best:.3f}") \
            .replace("{mean:.3f}", f"{mean:.3f}") \
            .replace("{worst:.3f}", f"{worst:.3f}") \
            .replace("{total}", str(total)) \
            .replace("{n_pass}", str(n_pass)) \
            .replace("{n_fail}", str(n_fail)) \
            .replace("{scoreboard}", f"CID: {cid}\n{cid_scoreboard}") \
            .replace("{pass_synthesis}", f"CID: {cid}\n\n{pass_synthesis}") \
            .replace("{fail_synthesis}", f"CID: {cid}\n\n{fail_synthesis}") \
            .replace("{gen}", str(generation))

        limiter = get_rate_limiter()
        limiter.wait()
        try:
            response = chat_completion(
                llm_client, llm_model,
                messages=[
                    {"role": "system", "content": f"You are producing actionable oracle feedback for the CID {cid} skill only. Do not prescribe task-specific one-offs unless they generalize within this CID."},
                    {"role": "user", "content": prompt},
                ],
                audit_logger=audit_logger,
                purpose="layer3_handoff_by_cid",
                context={
                    "generation": generation,
                    "cid": cid,
                    "best": best, "mean": mean, "worst": worst,
                    "n_pass": n_pass, "n_fail": n_fail,
                },
                temperature=0.0,
                max_tokens=max_tokens,
            )
            limiter.record_success()
            handoff = response.choices[0].message.content or ""
        except Exception as e:
            limiter.record_error()
            print(f"    [Layer3:{cid}] GPT-5 oracle handoff failed: {e}")
            if error_logger is not None:
                error_logger.record(
                    phase="oracle_layer3_cid",
                    generation=generation,
                    context={"cid": cid, "best": best, "mean": mean, "worst": worst,
                             "n_pass": n_pass, "n_fail": n_fail},
                    exception=e,
                )
            continue

        if not handoff.strip():
            msg = f"[Layer3:{cid}] Empty response for oracle handoff"
            print(f"    {msg}")
            if error_logger is not None:
                error_logger.record_info(
                    phase="oracle_layer3_cid",
                    message=msg,
                    generation=generation,
                    context={"cid": cid},
                )
            continue

        cid_path = out_dir / f"{cid}.md"
        cid_path.write_text(handoff, encoding="utf-8")
        cid_handoffs[cid] = handoff
        _oracle_heartbeat(
            heartbeat_callback,
            phase="oracle_layer3_cid_done",
            generation=generation,
            context={"cid": cid, "handoff_chars": len(handoff), "path": str(cid_path.name)},
            message=f"Layer 3 CID oracle handoff written for {cid}",
        )

    if not cid_handoffs:
        return None

    lines = [
        f"# Oracle feedback — Generation {generation} (CID-aware)",
        "",
        "This handoff is grouped by CID. Each section should mutate only that CID's skill.",
        "",
    ]
    for cid, handoff in sorted(cid_handoffs.items()):
        lines.append(f"## CID {cid}")
        lines.append("")
        lines.append(handoff.strip())
        lines.append("")
        lines.append("---")
        lines.append("")
    out_path = gen_dir / "oracle_feedback.md"
    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    _oracle_heartbeat(
        heartbeat_callback,
        phase="oracle_layer3_done",
        generation=generation,
        context={"num_cids": len(cid_handoffs), "oracle_feedback": str(out_path.name)},
        message="Layer 3 combined oracle handoff written",
    )
    return out_path


# ── Full generation pipeline ─────────────────────────────────────


def run_generation_oracle(
    gen_dir: Path,
    generation: int,
    rollouts_by_individual: list[list[dict]],
    scoreboard: str,
    best: float,
    mean: float,
    worst: float,
    llm_client: openai.OpenAI,
    llm_model: str,
    skip_layer1: bool = False,
    task_manifest: Optional[list[dict]] = None,
    task_cid_lookup: Optional[dict[str, str]] = None,
    cid_aware: bool = True,
    audit_logger: Optional[LLMAuditLogger] = None,
    error_logger: Optional[ErrorLogger] = None,
    heartbeat_callback: Optional[HeartbeatCallback] = None,
) -> Optional[Path]:
    """End-to-end 3-layer oracle pipeline for a single generation.

    Args:
        gen_dir: the gen<N>/ output directory
        generation: the generation number
        rollouts_by_individual: list of lists; outer index = individual, inner
            list = that individual's rollouts (parsed from rollouts.jsonl)
        scoreboard: pre-formatted per-task scoreboard text
        best, mean, worst: fitness stats across the generation's population
        llm_client, llm_model: GPT-5 client + model name
        skip_layer1: if True, skip streaming Layer 1 updates (assumes docs
            already exist from an earlier pass). Use for retroactive analysis.
        task_manifest/task_cid_lookup: maps each task to its owning CID.
        cid_aware: if True, Layer 1 writes task docs under task_insights/<cid>/,
            Layer 2 synthesizes cid_synthesis/<cid>/, and Layer 3 writes
            cid_oracle_feedback/<cid>.md before composing oracle_feedback.md.

    Returns path to oracle_feedback.md, or None on pipeline failure.
    """
    # NOTE (design): task_insights_dir lives under gen_dir, so each generation
    # starts with an empty corpus. This is intentional — oracle feedback should
    # diagnose the CURRENT mutated skill, not anchor on failure modes of prior
    # skills that no longer exist. Cross-generation carry-forward is a deferred
    # ablation (see AGENT_CONTEXT.md → "Future Work / Deferred Ablations").
    task_insights_dir = gen_dir / "task_insights"
    cross_task_dir = gen_dir / "cross_task"
    cid_synthesis_dir = gen_dir / "cid_synthesis"
    task_cid_lookup_norm = _normalize_task_cid_lookup(task_manifest, task_cid_lookup)

    n_pass = sum(1 for ind_rollouts in rollouts_by_individual
                 for r in ind_rollouts if r.get("reward", 0) > 0)
    n_fail = sum(1 for ind_rollouts in rollouts_by_individual
                 for r in ind_rollouts if r.get("reward", 0) <= 0)
    total_rollouts = n_pass + n_fail
    _oracle_heartbeat(
        heartbeat_callback,
        phase="oracle_start",
        generation=generation,
        context={
            "rollouts": total_rollouts,
            "passes": n_pass,
            "fails": n_fail,
            "cid_aware": cid_aware,
        },
        message="Starting 3-layer oracle pipeline",
    )

    # ── Layer 1: streaming updates ───────────────────────────
    if not skip_layer1:
        print(f"    [oracle] Layer 1: streaming {total_rollouts} per-rollout updates...")
        _oracle_heartbeat(
            heartbeat_callback,
            phase="oracle_layer1_start",
            generation=generation,
            context={"rollouts": total_rollouts},
            message=f"Layer 1 streaming {total_rollouts} per-rollout updates",
        )
        processed_rollouts = 0
        for ind_idx, ind_rollouts in enumerate(rollouts_by_individual):
            repeats_seen: dict[str, int] = {}
            for rollout_idx, rollout in enumerate(ind_rollouts):
                short_task = _short_task_id(rollout.get("task_id") or "unknown")
                repeat_idx = repeats_seen.get(short_task, 0)
                repeats_seen[short_task] = repeat_idx + 1
                rollout_id = f"ind{ind_idx}_task{short_task}_rep{repeat_idx}_r{rollout_idx}"
                processed_rollouts += 1
                _oracle_heartbeat(
                    heartbeat_callback,
                    phase="oracle_layer1",
                    generation=generation,
                    context={
                        "processed": processed_rollouts,
                        "total": total_rollouts,
                        "individual_index": ind_idx,
                        "rollout_index": rollout_idx,
                        "rollout_id": rollout_id,
                        "task": short_task,
                        "cid": _rollout_cid(rollout, task_cid_lookup_norm),
                        "outcome": "pass" if rollout.get("reward", 0) > 0 else "fail",
                    },
                    message=f"Layer 1 refining rollout {processed_rollouts}/{total_rollouts}",
                )
                update_task_insight(
                    rollout=rollout,
                    rollout_id=rollout_id,
                    task_insights_dir=task_insights_dir,
                    llm_client=llm_client,
                    llm_model=llm_model,
                    audit_logger=audit_logger,
                    error_logger=error_logger,
                    generation=generation,
                    task_cid_lookup=task_cid_lookup_norm,
                    cid_aware=cid_aware,
                )
        _oracle_heartbeat(
            heartbeat_callback,
            phase="oracle_layer1_done",
            generation=generation,
            context={"processed": processed_rollouts, "total": total_rollouts},
            message="Layer 1 rollout insight refinement complete",
        )

    if cid_aware:
        # ── Layer 2: task → CID synthesis (pass + fail per CID) ───
        print(f"    [oracle] Layer 2: CID-local synthesis...")
        _oracle_heartbeat(
            heartbeat_callback,
            phase="oracle_layer2_start",
            generation=generation,
            context={"cid_aware": True},
            message="Layer 2 CID-local synthesis starting",
        )
        cid_results = synthesize_cid_level(
            task_insights_dir=task_insights_dir,
            cid_synthesis_dir=cid_synthesis_dir,
            generation=generation,
            rollouts_by_individual=rollouts_by_individual,
            task_cid_lookup=task_cid_lookup_norm,
            llm_client=llm_client,
            llm_model=llm_model,
            audit_logger=audit_logger,
            error_logger=error_logger,
            heartbeat_callback=heartbeat_callback,
        )
        pass_path = _combine_cid_syntheses_for_legacy_index(cid_synthesis_dir, cross_task_dir, "pass")
        fail_path = _combine_cid_syntheses_for_legacy_index(cid_synthesis_dir, cross_task_dir, "fail")
        if not cid_results or not any(v.get("pass") or v.get("fail") for v in cid_results.values()):
            print(f"    [oracle] Layer 2 produced no CID output — aborting pipeline")
            if error_logger is not None:
                error_logger.record_info(
                    phase="oracle_pipeline",
                    message="CID-aware Layer 2 produced no pass/fail synthesis — aborting pipeline",
                    generation=generation,
                )
            return None

        # ── Layer 3: CID-specific oracle handoffs ────────────────
        print(f"    [oracle] Layer 3: building CID-specific oracle handoffs...")
        _oracle_heartbeat(
            heartbeat_callback,
            phase="oracle_layer3_start",
            generation=generation,
            context={"num_cids": len(cid_results)},
            message="Layer 3 CID-specific oracle handoff starting",
        )
        cid_counts = _rollout_counts_by_cid(rollouts_by_individual, task_cid_lookup_norm)
        return build_cid_oracle_feedback(
            gen_dir=gen_dir, generation=generation,
            scoreboard=scoreboard,
            best=best, mean=mean, worst=worst,
            cid_results=cid_results,
            cid_counts=cid_counts,
            task_cid_lookup=task_cid_lookup_norm,
            llm_client=llm_client, llm_model=llm_model,
            audit_logger=audit_logger, error_logger=error_logger,
            heartbeat_callback=heartbeat_callback,
        )

    # ── Legacy Layer 2: flat cross-task synthesis (pass + fail) ──
    print(f"    [oracle] Layer 2: cross-task synthesis...")
    pass_path = synthesize_cross_task(
        task_insights_dir, cross_task_dir, "pass", generation, llm_client, llm_model,
        audit_logger=audit_logger, error_logger=error_logger,
    )
    fail_path = synthesize_cross_task(
        task_insights_dir, cross_task_dir, "fail", generation, llm_client, llm_model,
        audit_logger=audit_logger, error_logger=error_logger,
    )
    if not pass_path and not fail_path:
        print(f"    [oracle] Layer 2 produced no output — aborting pipeline")
        if error_logger is not None:
            error_logger.record_info(
                phase="oracle_pipeline",
                message="Layer 2 produced no output for either pass or fail — aborting pipeline",
                generation=generation,
            )
        return None

    # ── Legacy Layer 3: oracle handoff ───────────────────────
    print(f"    [oracle] Layer 3: building oracle handoff...")
    return build_oracle_feedback(
        gen_dir=gen_dir, generation=generation,
        scoreboard=scoreboard,
        best=best, mean=mean, worst=worst,
        n_pass=n_pass, n_fail=n_fail,
        llm_client=llm_client, llm_model=llm_model,
        audit_logger=audit_logger, error_logger=error_logger,
    )

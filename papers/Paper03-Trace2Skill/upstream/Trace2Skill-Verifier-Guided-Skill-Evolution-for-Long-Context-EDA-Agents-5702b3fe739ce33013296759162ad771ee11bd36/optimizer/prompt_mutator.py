#!/usr/bin/env python3
"""LLM-powered prompt mutation and crossover for CVDP skill optimization.

Follows the same approach as NAT's GA prompt optimizer:
  - Mutation: LLM rewrites the prompt given an objective and optional oracle feedback
  - Crossover: LLM combines two parent prompts into a child
  - Oracle feedback: extracts failure patterns from rollouts to guide mutations
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import openai

from llm_audit import LLMAuditLogger, chat_completion
from rate_limiter import get_rate_limiter


# ── Prompt loading ────────────────────────────────────────────────
# All LLM prompts are stored as markdown files under skills/ at the repo root.
# This lets us edit/diff/version prompts without touching code.

_SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


def _load_prompt(relpath: str) -> str:
    """Load a prompt markdown file from skills/. Raises FileNotFoundError if missing."""
    path = _SKILLS_DIR / relpath
    if not path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {path}. "
            f"Expected under {_SKILLS_DIR}/. See skills/README.md for layout."
        )
    return path.read_text(encoding="utf-8").rstrip("\n")


MUTATION_SYSTEM_PROMPT = _load_prompt("optimizer/mutation_system.md")
CROSSOVER_SYSTEM_PROMPT = _load_prompt("optimizer/crossover_system.md")
COMPRESS_SYSTEM_PROMPT = _load_prompt("optimizer/compress_system.md")


def _safe_trim_to_budget(text: str, max_chars: int) -> str:
    """Trim at a section/line boundary instead of slicing a skill mid-rule."""
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    cut = text[:max_chars].rfind("\n## ")
    if cut < max_chars // 2:
        cut = text[:max_chars].rfind("\n- ")
    if cut < max_chars // 2:
        cut = text[:max_chars].rfind("\n")
    if cut < max_chars // 2:
        cut = max_chars
    trimmed = text[:cut].rstrip()
    if not trimmed.endswith("\n"):
        trimmed += "\n"
    return trimmed


def _compress_if_needed(
    client: openai.OpenAI,
    model: str,
    text: str,
    max_chars: int,
    audit_logger: Optional[LLMAuditLogger] = None,
    context: Optional[dict] = None,
) -> str:
    """If text exceeds max_chars, ask the LLM to compress it."""
    if len(text) <= max_chars or max_chars <= 0:
        return text

    print(f"       [mutator] Output {len(text)} chars exceeds budget {max_chars}, compressing...")
    limiter = get_rate_limiter()
    limiter.wait()
    try:
        response = chat_completion(
            client, model,
            messages=[
                {"role": "system", "content": COMPRESS_SYSTEM_PROMPT},
                {"role": "user", "content": f"CHARACTER BUDGET: {max_chars} characters\n\nDOCUMENT:\n{text}"},
            ],
            audit_logger=audit_logger,
            purpose="compress",
            context={**(context or {}), "input_chars": len(text), "budget": max_chars},
            temperature=0.3,
            max_tokens=8192,
        )
        limiter.record_success()
    except Exception:
        limiter.record_error()
        raise
    compressed = (response.choices[0].message.content or "").strip()
    print(f"       [mutator] Compressed to {len(compressed)} chars")
    if len(compressed) > max_chars:
        compressed = _safe_trim_to_budget(compressed, max_chars)
    return compressed


def mutate_prompt(
    client: openai.OpenAI,
    model: str,
    original_prompt: str,
    objective: str,
    oracle_feedback: Optional[str] = None,
    skill_patch_plan: Optional[str] = None,
    execution_constraints: Optional[str] = None,
    max_tokens: int = 8192,
    max_chars: int = 0,
    temperature: float = 0.7,
    audit_logger: Optional[LLMAuditLogger] = None,
    context: Optional[dict] = None,
) -> str:
    """Use an LLM to rewrite/improve a prompt based on an objective.

    Args:
        client: OpenAI-compatible client
        model: Model name
        original_prompt: The current skill document
        objective: What the prompt should achieve
        oracle_feedback: Optional failure analysis from worst-performing rollouts
        execution_constraints: Concrete tools/actions the rollout agent can use
        max_tokens: Max output tokens
        max_chars: Max output characters (0 = no limit)
    Returns:
        The mutated prompt text
    """
    budget_instruction = f"\n\nCHARACTER BUDGET: {max_chars} characters maximum. The current document is {len(original_prompt)} characters." if max_chars > 0 else ""

    user_msg = f"""Improve the following skill document to better achieve this objective:

OBJECTIVE: {objective}{budget_instruction}
"""

    if execution_constraints:
        user_msg += f"""
The improved skill MUST be executable under this exact rollout contract. If oracle feedback suggests actions outside this contract, rewrite them into contract-valid guidance or omit them:

{execution_constraints}
"""

    if oracle_feedback:
        user_msg += f"""
The current version of this skill document was tested on RTL coding tasks. Here are the failure patterns observed — use these to guide your improvements:

FAILURE FEEDBACK:
{oracle_feedback}
"""

    if skill_patch_plan:
        user_msg += f"""
STRUCTURED PATCH PLAN:
{skill_patch_plan}

Patch-plan requirements:
- Integrate every Must Add/Preserve directive unless it conflicts with the rollout contract.
- Remove or rewrite every Must Remove directive.
- Preserve concrete paths, signal names, module names, and tool constraints when they are relevant.
- Prefer minimal edits to the parent skill over a broad rewrite.
"""

    user_msg += f"""
CURRENT SKILL DOCUMENT:
{original_prompt}

Output the improved skill document below:"""

    limiter = get_rate_limiter()
    limiter.wait()
    try:
        response = chat_completion(
            client, model,
            messages=[
                {"role": "system", "content": MUTATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            audit_logger=audit_logger,
            purpose="mutate",
            context={**(context or {}),
                     "parent_chars": len(original_prompt),
                     "has_oracle_feedback": bool(oracle_feedback),
                     "has_skill_patch_plan": bool(skill_patch_plan),
                     "has_execution_constraints": bool(execution_constraints),
                     "budget": max_chars,
                     "temperature": temperature},
            temperature=temperature,
            max_tokens=max_tokens,
        )
        limiter.record_success()
    except Exception:
        limiter.record_error()
        raise
    result = (response.choices[0].message.content or "").strip()
    return _compress_if_needed(
        client, model, result, max_chars,
        audit_logger=audit_logger,
        context={**(context or {}), "parent_purpose": "mutate"},
    )


def crossover_prompts(
    client: openai.OpenAI,
    model: str,
    parent_a: str,
    parent_b: str,
    objective: str,
    oracle_feedback: Optional[str] = None,
    skill_patch_plan: Optional[str] = None,
    execution_constraints: Optional[str] = None,
    max_tokens: int = 8192,
    max_chars: int = 0,
    temperature: float = 0.7,
    audit_logger: Optional[LLMAuditLogger] = None,
    context: Optional[dict] = None,
) -> str:
    """Use an LLM to combine two parent prompts into a child.

    Args:
        client: OpenAI-compatible client
        model: Model name
        parent_a: First parent skill document
        parent_b: Second parent skill document
        objective: What the prompt should achieve
        oracle_feedback: Optional contrastive feedback to guide crossover priorities
        execution_constraints: Concrete tools/actions the rollout agent can use
        max_tokens: Max output tokens
        max_chars: Max output characters (0 = no limit)
    Returns:
        The combined child prompt text
    """
    budget_instruction = f"\n\nCHARACTER BUDGET: {max_chars} characters maximum. Parent A is {len(parent_a)} chars, Parent B is {len(parent_b)} chars." if max_chars > 0 else ""

    user_msg = f"""Combine the best ideas from these two skill documents into one improved version.

OBJECTIVE: {objective}{budget_instruction}
"""

    if execution_constraints:
        user_msg += f"""
The combined skill MUST be executable under this exact rollout contract. If parent skills or oracle feedback contain actions outside this contract, rewrite them into contract-valid guidance or omit them:

{execution_constraints}
"""

    if oracle_feedback:
        user_msg += f"""
When combining these parents, prioritize keeping guidance that addresses the failure patterns below, and reinforce the patterns that lead to success:

{oracle_feedback}
"""

    if skill_patch_plan:
        user_msg += f"""
STRUCTURED PATCH PLAN:
{skill_patch_plan}

Patch-plan requirements:
- Integrate every Must Add/Preserve directive unless it conflicts with the rollout contract.
- Remove or rewrite every Must Remove directive.
- Preserve concrete paths, signal names, module names, and tool constraints when they are relevant.
- Prefer the more specific/actionable parent rule when parents disagree.
"""

    user_msg += f"""
PARENT A:
{parent_a}

PARENT B:
{parent_b}

Output the combined skill document below:"""

    limiter = get_rate_limiter()
    limiter.wait()
    try:
        response = chat_completion(
            client, model,
            messages=[
                {"role": "system", "content": CROSSOVER_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            audit_logger=audit_logger,
            purpose="crossover",
            context={**(context or {}),
                     "parent_a_chars": len(parent_a),
                     "parent_b_chars": len(parent_b),
                     "has_oracle_feedback": bool(oracle_feedback),
                     "has_skill_patch_plan": bool(skill_patch_plan),
                     "has_execution_constraints": bool(execution_constraints),
                     "budget": max_chars,
                     "temperature": temperature},
            temperature=temperature,
            max_tokens=max_tokens,
        )
        limiter.record_success()
    except Exception:
        limiter.record_error()
        raise
    result = (response.choices[0].message.content or "").strip()
    return _compress_if_needed(
        client, model, result, max_chars,
        audit_logger=audit_logger,
        context={**(context or {}), "parent_purpose": "crossover"},
    )


def repair_skill_candidate(
    client: openai.OpenAI,
    model: str,
    candidate_skill: str,
    parent_skill: str,
    objective: str,
    integration_issues: str,
    skill_patch_plan: Optional[str] = None,
    execution_constraints: Optional[str] = None,
    max_tokens: int = 8192,
    max_chars: int = 0,
    temperature: float = 0.2,
    audit_logger: Optional[LLMAuditLogger] = None,
    context: Optional[dict] = None,
) -> str:
    """Minimally repair a mutated skill that failed semantic integration.

    This is intentionally narrower than mutation. The repair model receives the
    candidate, the parent, the patch plan, and concrete validation failures, then
    edits only what is needed for coverage/safety. It prevents silent fallback
    to the parent when a child is close but dropped one critical oracle lesson.
    """
    budget_instruction = (
        f"\n\nCHARACTER BUDGET: {max_chars} characters maximum. "
        f"The candidate is {len(candidate_skill)} characters."
        if max_chars > 0 else ""
    )
    user_msg = f"""Repair the candidate skill so it satisfies the oracle integration check.

OBJECTIVE: {objective}{budget_instruction}

REPAIR ISSUES:
{integration_issues}
"""
    if execution_constraints:
        user_msg += f"""
ROLLOUT CONTRACT:
{execution_constraints}
"""
    if skill_patch_plan:
        user_msg += f"""
STRUCTURED PATCH PLAN:
{skill_patch_plan}
"""
    user_msg += f"""
PARENT SKILL:
{parent_skill}

CANDIDATE SKILL TO REPAIR:
{candidate_skill}

Output ONLY the repaired skill document. Do not include a report."""

    limiter = get_rate_limiter()
    limiter.wait()
    try:
        response = chat_completion(
            client, model,
            messages=[
                {"role": "system", "content": MUTATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            audit_logger=audit_logger,
            purpose="repair_mutation",
            context={**(context or {}),
                     "candidate_chars": len(candidate_skill),
                     "parent_chars": len(parent_skill),
                     "has_skill_patch_plan": bool(skill_patch_plan),
                     "has_execution_constraints": bool(execution_constraints),
                     "budget": max_chars,
                     "temperature": temperature},
            temperature=temperature,
            max_tokens=max_tokens,
        )
        limiter.record_success()
    except Exception:
        limiter.record_error()
        raise
    result = (response.choices[0].message.content or "").strip()
    return _compress_if_needed(
        client, model, result, max_chars,
        audit_logger=audit_logger,
        context={**(context or {}), "parent_purpose": "repair_mutation"},
    )


def extract_oracle_feedback(
    fitness_result: dict,
    max_chars: int = 2000,
) -> Optional[str]:
    """Extract failure patterns from rollout results for oracle-guided mutation.

    Looks at per-task pass rates and identifies failure patterns to feed back
    to the mutation LLM.
    """
    per_task = fitness_result.get("per_task", {})
    if not per_task:
        return None

    failed_tasks = {tid: rate for tid, rate in per_task.items() if rate < 1.0}
    if not failed_tasks:
        return None

    lines = [f"Failed or partially failed tasks (pass@1 < 1.0):"]
    for tid, rate in sorted(failed_tasks.items(), key=lambda x: x[1]):
        lines.append(f"  - {tid}: pass@1 = {rate:.1%}")

    total_pass = fitness_result.get("pass_at_1", 0.0)
    lines.append(f"\nOverall pass@1: {total_pass:.1%}")
    lines.append(f"Total rollouts: {fitness_result.get('num_rollouts', 0)}")

    feedback = "\n".join(lines)
    if len(feedback) > max_chars:
        feedback = feedback[:max_chars] + "\n... (truncated)"

    return feedback


def extract_detailed_oracle_feedback(
    rollout_path: str,
    max_chars: int = 3000,
) -> Optional[str]:
    """Extract detailed failure patterns by reading actual rollout trajectories.

    Identifies common tool errors, behavioral patterns, and failure phases
    from the rollout data to provide richer feedback to the mutation LLM.
    """
    from pathlib import Path
    import json

    path = Path(rollout_path)
    if not path.exists():
        return None

    failures = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("reward", 0) > 0:
                continue
            failures.append(rec)

    if not failures:
        return None

    lines = [f"Detailed failure analysis from {len(failures)} failed rollouts:"]

    for rec in failures[:5]:
        tid = rec.get("task_id", "unknown")
        output_items = rec.get("response", {}).get("output", [])
        fn_calls = [o for o in output_items if o.get("type") == "function_call"]
        fn_outputs = [o for o in output_items if o.get("type") == "function_call_output"]

        tools_used = [o.get("name", "?") for o in fn_calls]
        has_echo = "echo" in tools_used
        has_iverilog = "iverilog" in tools_used
        has_vvp = "vvp" in tools_used

        errors = []
        for o in fn_outputs:
            out = o.get("output", "")
            if isinstance(out, str) and ("error" in out.lower() or "Error" in out):
                errors.append(out[:150])

        lines.append(f"\n  Task: {tid}")
        lines.append(f"  Steps: {len(fn_calls)} tool calls")
        lines.append(f"  Tools: {', '.join(set(tools_used))}")
        lines.append(f"  Wrote files: {has_echo}, Compiled: {has_iverilog}, Ran sim: {has_vvp}")
        if errors:
            lines.append(f"  Errors ({len(errors)}):")
            for e in errors[:3]:
                lines.append(f"    - {e}")

    feedback = "\n".join(lines)
    if len(feedback) > max_chars:
        feedback = feedback[:max_chars] + "\n... (truncated)"

    return feedback


def _truncate(text: str, max_len: int) -> str:
    if not text or len(text) <= max_len:
        return text or ""
    cut = text[:max_len].rfind("\n")
    if cut < max_len // 2:
        cut = max_len
    return text[:cut] + "\n... (truncated)"


def _analyze_rollout(rec: dict) -> dict:
    """Extract behavioral profile from a single rollout record."""
    output_items = rec.get("response", {}).get("output", [])
    fn_calls = [o for o in output_items if isinstance(o, dict) and o.get("type") == "function_call"]
    fn_outputs = [o for o in output_items if isinstance(o, dict) and o.get("type") == "function_call_output"]

    tools_seq = [o.get("name", "?") for o in fn_calls]
    tool_set = set(tools_seq)
    errors = []
    for o in fn_outputs:
        out = o.get("output", "")
        if not isinstance(out, str):
            continue
        if out.startswith("{"):
            try:
                parsed = json.loads(out)
                out = parsed.get("output", out)
            except (json.JSONDecodeError, TypeError):
                pass
        if not isinstance(out, str):
            continue
        is_error = ("error" in out.lower() or "warning" in out.lower()) and not out.startswith(("#", "//", "/*", "import ", "module ", "`"))
        is_tool_output = len(out) < 500
        if is_error and is_tool_output:
            errors.append(out[:200])

    has_read = "cat" in tool_set
    has_write = "echo" in tool_set
    has_compile = "iverilog" in tool_set
    has_sim = "vvp" in tool_set

    if has_sim:
        phase = "P4-tested"
    elif has_compile:
        phase = "P3-compiled"
    elif has_write:
        phase = "P2-wrote-files"
    elif has_read:
        phase = "P1-explored"
    else:
        phase = "P0-no-tools"

    return {
        "task_id": (rec.get("task_id") or "unknown").replace("cvdp_agentic_heavy_", ""),
        "reward": rec.get("reward", 0),
        "steps": len(fn_calls),
        "tools": tools_seq,
        "tool_set": tool_set,
        "phase": phase,
        "has_read": has_read,
        "has_write": has_write,
        "has_compile": has_compile,
        "has_sim": has_sim,
        "errors": errors,
    }


def _summarize_rollout_group(profiles: list[dict], label: str, max_examples: int = 3) -> list[str]:
    """Summarize a group of rollout profiles (all passes or all failures)."""
    if not profiles:
        return [f"  No {label} rollouts."]

    lines = []

    # Phase distribution
    from collections import Counter
    phase_counts = Counter(p["phase"] for p in profiles)
    lines.append(f"  Total: {len(profiles)} rollouts")
    lines.append(f"  Phase distribution: {', '.join(f'{phase}={n}' for phase, n in phase_counts.most_common())}")

    # Tool usage rates and step analysis
    n = len(profiles)
    steps = [p["steps"] for p in profiles]
    avg_steps = sum(steps) / n
    min_steps = min(steps)
    max_steps = max(steps)
    lines.append(f"  Steps: avg={avg_steps:.1f}, min={min_steps}, max={max_steps}")

    early_exits = sum(1 for p in profiles if p["steps"] < 16)
    step_exhausted = sum(1 for p in profiles if p["steps"] >= 20)
    if early_exits:
        lines.append(f"  ⚠ Early exits (<16 steps): {early_exits}/{n} — agent gave up before using full step budget")
    if step_exhausted:
        lines.append(f"  Step exhaustion (≥20 steps): {step_exhausted}/{n}")

    lines.append(f"  Read files (cat): {sum(1 for p in profiles if p['has_read'])}/{n}")
    lines.append(f"  Wrote files (echo): {sum(1 for p in profiles if p['has_write'])}/{n}")
    compile_counts = [p["tools"].count("iverilog") for p in profiles]
    sim_counts = [p["tools"].count("vvp") for p in profiles]
    lines.append(f"  Compiled (iverilog): {sum(1 for p in profiles if p['has_compile'])}/{n}, avg {sum(compile_counts)/n:.1f} attempts/rollout")
    lines.append(f"  Ran simulation (vvp): {sum(1 for p in profiles if p['has_sim'])}/{n}, avg {sum(sim_counts)/n:.1f} attempts/rollout")

    # Per-task breakdown
    task_groups: dict[str, list] = {}
    for p in profiles:
        task_groups.setdefault(p["task_id"], []).append(p)
    lines.append(f"  Per-task: {', '.join(f'{tid}={len(ps)}' for tid, ps in sorted(task_groups.items()))}")

    # Common errors (for failures)
    all_errors = [e for p in profiles for e in p["errors"]]
    if all_errors:
        error_counts = Counter(all_errors)
        lines.append(f"  Common errors ({len(all_errors)} total):")
        for err, count in error_counts.most_common(5):
            lines.append(f"    [{count}x] {err}")

    # Example trajectories — pick diverse examples across tasks
    seen_tasks = set()
    examples = []
    for p in profiles:
        if p["task_id"] not in seen_tasks and len(examples) < max_examples:
            seen_tasks.add(p["task_id"])
            examples.append(p)
    if len(examples) < max_examples:
        for p in profiles:
            if len(examples) >= max_examples:
                break
            if p not in examples:
                examples.append(p)

    lines.append(f"  Representative tool sequences ({len(examples)} examples):")
    for p in examples:
        seq = " → ".join(p["tools"][:15])
        if len(p["tools"]) > 15:
            seq += f" ... ({len(p['tools'])} total)"
        lines.append(f"    [{p['task_id']}] {p['phase']}, {p['steps']} steps: {seq}")

    return lines


def _build_scoreboard(population: list) -> tuple[str, dict]:
    """Build per-task scoreboard and classify tasks into solved/mixed/unsolved."""
    from collections import defaultdict
    task_stats: dict[str, dict] = {}
    for ind in population:
        fr = getattr(ind, 'fitness_result', None) or {}
        per_task = fr.get("per_task", {})
        for tid, val in per_task.items():
            rate = val.get("pass_at_1", 0.0) if isinstance(val, dict) else float(val)
            short_tid = (tid or "unknown").replace("cvdp_agentic_heavy_", "")
            if short_tid not in task_stats:
                task_stats[short_tid] = {"rates": [], "full_tid": tid}
            task_stats[short_tid]["rates"].append(rate)

    for tid, info in task_stats.items():
        info["avg"] = sum(info["rates"]) / len(info["rates"]) if info["rates"] else 0

    lines = []
    for tid in sorted(task_stats.keys()):
        info = task_stats[tid]
        rates_str = ", ".join(f"{r:.0%}" for r in info["rates"])
        if info["avg"] >= 1.0:
            tag = " [ALWAYS SOLVED]"
        elif info["avg"] > 0.6:
            tag = " [USUALLY SOLVED]"
        elif info["avg"] > 0:
            tag = " [SOMETIMES SOLVED]"
        else:
            tag = " [NEVER SOLVED]"
        lines.append(f"  {tid}: avg={info['avg']:.0%} ({rates_str}){tag}")

    return "\n".join(lines), task_stats


def _build_structured_rollout_data(population: list) -> str:
    """Build compressed, per-task rollout summaries from raw rollout data.

    Groups rollouts by task, separates pass/fail, includes per-task error
    details and tool sequences — structured for LLM consumption.
    """
    from pathlib import Path
    from collections import defaultdict

    task_rollouts: dict[str, list[dict]] = defaultdict(list)

    for ind_idx, ind in enumerate(population):
        fr = getattr(ind, 'fitness_result', None) or {}
        rollout_path = fr.get("rollout_path")
        if not rollout_path or not Path(rollout_path).exists():
            continue
        with open(rollout_path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    profile = _analyze_rollout(rec)
                    profile["ind"] = ind_idx
                    profile["prompt_len"] = len(getattr(ind, 'prompt', ''))
                    task_rollouts[profile["task_id"]].append(profile)
                except (json.JSONDecodeError, Exception):
                    continue

    if not task_rollouts:
        return ""

    sections = []
    for tid in sorted(task_rollouts.keys()):
        rollouts = task_rollouts[tid]
        passes = [r for r in rollouts if r["reward"] > 0]
        failures = [r for r in rollouts if r["reward"] <= 0]

        sec = [f"\n### {tid} — {len(passes)}/{len(rollouts)} pass"]

        if passes:
            sec.append(f"  PASSING ({len(passes)}):")
            for r in passes:
                seq = " → ".join(r["tools"][:20])
                sec.append(f"    ind{r['ind']} | {r['phase']} | {r['steps']} steps | {seq}")

        if failures:
            sec.append(f"  FAILING ({len(failures)}):")
            for r in failures:
                seq = " → ".join(r["tools"][:20])
                sec.append(f"    ind{r['ind']} | {r['phase']} | {r['steps']} steps | {seq}")
                if r["errors"]:
                    for err in r["errors"][:3]:
                        sec.append(f"      ERROR: {err[:150]}")

        if passes and failures:
            pass_tools = set()
            fail_tools = set()
            for r in passes:
                pass_tools.update(r["tool_set"])
            for r in failures:
                fail_tools.update(r["tool_set"])
            diff = pass_tools - fail_tools
            if diff:
                sec.append(f"  KEY DIFF: passing rollouts use {diff} but failures don't")

        sections.append("\n".join(sec))

    return "\n".join(sections)


ORACLE_SYNTHESIS_PROMPT = _load_prompt("optimizer/oracle_synthesis.md")


def build_contrastive_oracle(
    population: list,
    generation: int,
    max_chars: int = 12000,
    llm_client: Optional[openai.OpenAI] = None,
    llm_model: Optional[str] = None,
    audit_logger: Optional[LLMAuditLogger] = None,
) -> Optional[str]:
    """Build oracle feedback by having GPT-5 analyze compressed rollout data.

    Pipeline:
      1. Extract structured behavioral profiles from all rollouts (Python)
      2. Group by task with pass/fail separation and per-task errors (Python)
      3. Send compressed data to GPT-5 for causal analysis (LLM)
      4. Return GPT-5's synthesis as the oracle feedback for mutation

    Falls back to Python-only summarization if no LLM client is provided.
    """
    if not population or not any(getattr(ind, 'fitness_result', None) for ind in population):
        return None

    scoreboard_text, task_stats = _build_scoreboard(population)
    rollout_data = _build_structured_rollout_data(population)

    if not scoreboard_text and not rollout_data:
        return None

    fitnesses = [ind.fitness for ind in population]
    n_pass = sum(1 for _ in _collect_profiles(population) if _["reward"] > 0)
    n_fail = sum(1 for _ in _collect_profiles(population) if _["reward"] <= 0)
    total = n_pass + n_fail

    # If LLM client available, use GPT-5 synthesis
    if llm_client and llm_model:
        prompt = ORACLE_SYNTHESIS_PROMPT.format(
            rollout_data=rollout_data,
            scoreboard=scoreboard_text,
            best=max(fitnesses),
            mean=sum(fitnesses) / len(fitnesses),
            worst=min(fitnesses),
            total=total,
            n_pass=n_pass,
            n_fail=n_fail,
        )

        prompt_chars = len(prompt)
        print(f"    [oracle] Sending {prompt_chars} chars to {llm_model} for synthesis...")

        limiter = get_rate_limiter()
        limiter.wait()
        try:
            response = chat_completion(
                llm_client, llm_model,
                messages=[
                    {"role": "system", "content": "You are an expert RTL agent behavioral analyst. Produce concise, actionable feedback."},
                    {"role": "user", "content": prompt},
                ],
                audit_logger=audit_logger,
                purpose="legacy_oracle_single_shot",
                context={"generation": generation, "n_pass": n_pass, "n_fail": n_fail},
                temperature=0.0,
                max_tokens=16384,
            )
            limiter.record_success()
            synthesis = response.choices[0].message.content or ""
        except Exception as e:
            limiter.record_error()
            print(f"    [oracle] LLM synthesis failed: {e}, falling back to Python summary")
            synthesis = ""

        if synthesis:
            header = (
                f"OPTIMIZATION FEEDBACK FROM GENERATION {generation}:\n\n"
                f"GENERATION STATS: best={max(fitnesses):.3f}, "
                f"mean={sum(fitnesses)/len(fitnesses):.3f}, "
                f"worst={min(fitnesses):.3f}, "
                f"rollouts={total} ({n_pass} pass, {n_fail} fail)\n\n"
                f"PER-TASK SCOREBOARD:\n{scoreboard_text}\n\n"
                f"--- GPT-5 BEHAVIORAL ANALYSIS ---\n\n"
                f"{synthesis}"
            )
            if len(header) > max_chars:
                header = header[:max_chars - 20] + "\n... (truncated)"
            return header

    # ── Fallback: Python-only summary (original logic) ──
    return _build_python_oracle(population, generation, task_stats,
                                scoreboard_text, fitnesses, max_chars)


def _collect_profiles(population: list) -> list[dict]:
    """Collect all rollout profiles from population."""
    from pathlib import Path
    profiles = []
    for ind in population:
        fr = getattr(ind, 'fitness_result', None) or {}
        rollout_path = fr.get("rollout_path")
        if not rollout_path or not Path(rollout_path).exists():
            continue
        with open(rollout_path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    profiles.append(_analyze_rollout(rec))
                except (json.JSONDecodeError, Exception):
                    continue
    return profiles


def _build_python_oracle(
    population: list,
    generation: int,
    task_stats: dict,
    scoreboard_text: str,
    fitnesses: list[float],
    max_chars: int,
) -> str:
    """Fallback Python-only oracle (original logic, used when LLM unavailable)."""
    profiles = _collect_profiles(population)
    passes = [p for p in profiles if p["reward"] > 0]
    failures = [p for p in profiles if p["reward"] <= 0]

    consistent_pass = [t for t, i in task_stats.items() if i["avg"] > 0.6]
    sometimes_pass = [t for t, i in task_stats.items() if 0 < i["avg"] <= 0.6]
    consistent_fail = [t for t, i in task_stats.items() if i["avg"] == 0]

    lines = [f"OPTIMIZATION FEEDBACK FROM GENERATION {generation}:"]

    lines.append(f"\nGENERATION STATS: best={max(fitnesses):.3f}, "
                 f"mean={sum(fitnesses)/len(fitnesses):.3f}, "
                 f"worst={min(fitnesses):.3f}, "
                 f"rollouts={len(profiles)} ({len(passes)} pass, {len(failures)} fail)")

    lines.append(f"\nPER-TASK SCOREBOARD:\n{scoreboard_text}")

    lines.append(f"\n{'='*60}")
    lines.append(f"FAILURE PATTERNS (aggregated from {len(failures)} failed rollouts)")
    lines.append(f"{'='*60}")
    lines.extend(_summarize_rollout_group(failures, "failed", max_examples=4))

    lines.append(f"\n{'='*60}")
    lines.append(f"SUCCESS PATTERNS (aggregated from {len(passes)} passing rollouts)")
    lines.append(f"{'='*60}")
    lines.extend(_summarize_rollout_group(passes, "passing", max_examples=4))

    lines.append(f"\n{'='*60}")
    lines.append("DIRECTIVES FOR NEXT GENERATION:")
    lines.append(f"{'='*60}")
    if consistent_pass:
        lines.append(f"KEEP: Guidance that solves {', '.join(consistent_pass)}.")
    if consistent_fail:
        lines.append(f"ADD: The agent never solves {', '.join(consistent_fail)}. Add specific guidance.")
    if sometimes_pass:
        lines.append(f"STRENGTHEN: {', '.join(sometimes_pass)} are solved sometimes — make the workflow more explicit.")

    feedback = "\n".join(lines)
    if len(feedback) > max_chars:
        feedback = feedback[:max_chars - 20] + "\n... (truncated)"
    return feedback

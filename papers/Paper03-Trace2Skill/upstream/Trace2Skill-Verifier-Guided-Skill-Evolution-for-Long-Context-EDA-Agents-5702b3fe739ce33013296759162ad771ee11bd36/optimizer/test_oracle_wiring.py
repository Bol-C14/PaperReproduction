#!/usr/bin/env python3
"""Smoke test: verify oracle feedback wiring and unified config loading.

Tests the full chain WITHOUT requiring NeMo-Gym servers or real LLM calls:
1. Loads eval_models.yml and verifies GPT-5 is configured
2. Simulates a fitness result with an analyzer report
3. Extracts oracle feedback from the simulated result
4. Verifies mutate_prompt() would receive the feedback
5. Verifies the optimizer config references the shared eval config

Run from repo root:
    python optimizer/test_oracle_wiring.py
"""

import json
import os
import sys
from pathlib import Path

# Setup paths
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "eval"))
sys.path.insert(0, str(REPO_ROOT / "optimizer"))

PASS = "\033[92m✓ PASS\033[0m"
FAIL = "\033[91m✗ FAIL\033[0m"
results = []


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    msg = f"  {status}  {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    results.append(condition)
    return condition


print("=" * 60)
print("  Oracle Feedback Wiring — Smoke Test")
print("=" * 60)
print()

# ── Test 1: Unified config loads and has GPT-5 ──────────────────

print("── 1. Unified eval config ──")
try:
    from eval_config import load_eval_config, get_analyzer_config, get_judge_config
    config_path = str(REPO_ROOT / "eval" / "configs" / "eval_models.yml")
    full_config = load_eval_config(config_path)

    check("eval_models.yml loads", True)
    check("Has 'analyzer' key", "analyzer" in full_config)
    check("Has 'judge' key", "judge" in full_config)

    analyzer_cfg = get_analyzer_config(config_path)
    judge_cfg = get_judge_config(config_path)

    check("Analyzer model is gpt-5", analyzer_cfg.get("model") == "gpt-5",
          f"got: {analyzer_cfg.get('model')}")
    check("Judge model is gpt-5", judge_cfg.get("model") == "gpt-5",
          f"got: {judge_cfg.get('model')}")
    check("Analyzer max_tokens is 8192", analyzer_cfg.get("max_tokens") == 8192)
    check("Judge max_tokens is 4096", judge_cfg.get("max_tokens") == 4096)

except Exception as e:
    check("eval_models.yml loads", False, str(e))

print()

# ── Test 2: Optimizer config references shared eval config ───────

print("── 2. Optimizer config ──")
try:
    import yaml
    opt_config_path = REPO_ROOT / "optimizer" / "configs" / "optimize_skill.yml"
    with open(opt_config_path) as f:
        opt_config = yaml.safe_load(f)

    has_eval_config = "eval_config" in opt_config
    check("optimize_skill.yml has eval_config key", has_eval_config,
          f"value: {opt_config.get('eval_config', 'MISSING')}")

    has_inline = "eval_llm" in opt_config
    check("No inline eval_llm (superseded)", not has_inline,
          "inline block removed" if not has_inline else "WARNING: inline block still present (fallback)")

except Exception as e:
    check("optimize_skill.yml loads", False, str(e))

print()

# ── Test 3: Oracle feedback extraction from analyzer report ──────

print("── 3. Oracle feedback extraction ──")
try:
    from prompt_mutator import extract_oracle_feedback

    simulated_fitness_result = {
        "pass_at_1": 0.2667,
        "num_rollouts": 30,
        "per_task": {
            "axi4_lite_0002": 0.4,
            "enso_0007": 0.4,
            "enso_0017": 0.0,
            "enso_0037": 0.0,
            "reckon_0001": 0.2,
            "biriscv_0001": 0.6,
        },
        "analyzer_report": """# Failure Analysis Report

## Executive Summary
The agent achieves 26.7% overall pass rate (8/30 rollouts). Two tasks (enso_0017, enso_0037) 
are never solved, indicating systematic capability gaps.

## Dominant Failure Mode
**B3: Premature Implementation** — The agent writes code before fully reading the testbench 
constraints in 18/22 failed rollouts. It guesses the interface instead of reading *_tb.v files.

## Root Cause Classification
- enso_0017: Knowledge Gap (KG) — Agent lacks understanding of clock domain crossing patterns
- enso_0037: Behavioral Issue (BI) — Agent reads the spec but ignores constraint annotations
- reckon_0001: Unreliable Knowledge (UK) — Sometimes reads the full spec, sometimes skips it

## Recommendation
The skill document should explicitly instruct: "ALWAYS read all *_tb.v and *_spec.md files 
BEFORE writing any RTL code. Extract interface signals, clock domains, and assertion patterns 
from the testbench before modifying any source files."
""",
    }

    # Test basic feedback (pass/fail numbers)
    basic_feedback = extract_oracle_feedback(simulated_fitness_result)
    check("extract_oracle_feedback() returns text", basic_feedback is not None and len(basic_feedback) > 0,
          f"{len(basic_feedback)} chars" if basic_feedback else "None")
    check("Feedback mentions enso_0017 (0%)", "enso_0017" in (basic_feedback or ""))

    # Test that analyzer report is accessible
    report = simulated_fitness_result.get("analyzer_report", "")
    check("Analyzer report is present", len(report) > 0, f"{len(report)} chars")
    check("Report contains root cause analysis", "Root Cause" in report)
    check("Report contains recommendation", "Recommendation" in report)

    # Simulate what the optimizer breeding loop does
    truncated = report[:3000]
    if len(report) > 3000:
        truncated += "\n... (truncated)"
    check("Truncated report fits mutation budget", len(truncated) <= 3500,
          f"{len(truncated)} chars")

except Exception as e:
    check("Oracle feedback extraction", False, str(e))

print()

# ── Test 4: mutate_prompt accepts oracle_feedback parameter ──────

print("── 4. Mutation function signature ──")
try:
    import inspect
    from prompt_mutator import mutate_prompt

    sig = inspect.signature(mutate_prompt)
    params = list(sig.parameters.keys())

    check("mutate_prompt has 'oracle_feedback' param", "oracle_feedback" in params,
          f"params: {params}")

    # Verify the oracle_feedback default is None (optional)
    oracle_param = sig.parameters.get("oracle_feedback")
    check("oracle_feedback defaults to None", oracle_param.default is None)

except Exception as e:
    check("mutate_prompt signature", False, str(e))

print()

# ── Test 5: Optimizer breeding loop has oracle wiring ────────────

print("── 5. Optimizer oracle wiring ──")
try:
    optimizer_src = (REPO_ROOT / "optimizer" / "run_optimizer.py").read_text()

    check("Imports extract_oracle_feedback",
          "extract_oracle_feedback" in optimizer_src)
    check("Reads oracle_feedback config",
          'oracle_feedback' in optimizer_src and 'oracle_mode' in optimizer_src)
    check("Passes oracle_feedback to mutate_prompt",
          'oracle_feedback=oracle_feedback_text' in optimizer_src)
    check("Prefers analyzer report over pass/fail",
          'analyzer_report' in optimizer_src and 'report[:3000]' in optimizer_src)
    check("Supports adaptive mode (stagnation check)",
          'stagnant' in optimizer_src and 'adaptive' in optimizer_src)

except Exception as e:
    check("Optimizer wiring check", False, str(e))

print()

# ── Summary ──────────────────────────────────────────────────────

passed = sum(results)
total = len(results)
all_pass = all(results)

print("=" * 60)
if all_pass:
    print(f"  {PASS}  ALL {total} CHECKS PASSED")
else:
    print(f"  {FAIL}  {passed}/{total} checks passed")
print("=" * 60)

sys.exit(0 if all_pass else 1)

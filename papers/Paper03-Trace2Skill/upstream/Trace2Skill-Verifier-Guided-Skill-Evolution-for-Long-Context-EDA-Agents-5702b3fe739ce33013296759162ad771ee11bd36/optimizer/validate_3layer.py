#!/usr/bin/env python3
"""Local validation for the 3-layer streaming oracle before kicking off a full run.

Checks (no NeMo-Gym servers required, no rollout model invoked):
  1. Environment + .env variables present
  2. Configs load; all referenced paths exist
  3. GPT-5 endpoint reachable
  4. Real GPT-5 call for Layer 1 on a PASS rollout from legacy data
  5. Real GPT-5 call for Layer 1 on a FAIL rollout from legacy data
  6. Real GPT-5 call for Layer 2 pass synthesis
  7. Real GPT-5 call for Layer 2 fail synthesis
  8. Real GPT-5 call for Layer 3 oracle handoff
  9. Outputs saved under optimizer/_validation/ for inspection

Usage:
    source .env && source envs/unified/bin/activate
    python optimizer/validate_3layer.py

Total real GPT-5 calls: 5 (~$1-2 depending on token usage).
"""

from __future__ import annotations
import json
import os
import shutil
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "optimizer"))

PASS_TAG = "\033[92m✓\033[0m"
FAIL_TAG = "\033[91m✗\033[0m"
WARN_TAG = "\033[93m⚠\033[0m"
results: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> bool:
    tag = PASS_TAG if cond else FAIL_TAG
    msg = f"  {tag} {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    results.append((name, cond, detail))
    return cond


def section(title: str):
    print(f"\n{'=' * 62}")
    print(f"  {title}")
    print("=" * 62)


# ──────────────────────────────────────────────────────────────────
section("1. Environment variables")

required = ["LLM_BASE_URL", "LLM_API_KEY", "ANALYZER_MODEL",
            "ROLLOUT_MODEL", "MUTATION_MODEL", "NEMOGYM_ROOT", "NG_COLLECT_BIN"]
missing = [k for k in required if not os.environ.get(k)]
check("All required env vars set", not missing,
      f"missing: {missing}" if missing else ", ".join(required))
if missing:
    print("\nRun: source .env  — then re-run this script")
    sys.exit(1)

check("NG_COLLECT_BIN exists on disk", Path(os.environ["NG_COLLECT_BIN"]).exists(),
      os.environ["NG_COLLECT_BIN"])
check("NEMOGYM_ROOT exists on disk", Path(os.environ["NEMOGYM_ROOT"]).exists(),
      os.environ["NEMOGYM_ROOT"])

# ──────────────────────────────────────────────────────────────────
section("2. Configs load + referenced paths exist")

import yaml

for cfg_name in ("optimize_skill_smoketest.yml", "haiku_all_tasks.yml"):
    # trace-skill layout: configs moved from optimizer/configs/ to orchestration/configs/legacy/
    cfg_path = REPO_ROOT / "orchestration" / "configs" / "legacy" / cfg_name
    if not cfg_path.exists():
        # Fallback to the legacy optimizer/configs/ location (for source-repo compatibility)
        cfg_path = REPO_ROOT / "optimizer" / "configs" / cfg_name
    try:
        with open(cfg_path) as f:
            raw = f.read()
        # Expand ${VAR} placeholders so we can validate referenced paths
        expanded = os.path.expandvars(raw)
        cfg = yaml.safe_load(expanded)
        check(f"{cfg_name} parses", True)

        seed = REPO_ROOT / cfg["seed_skill"]
        check(f"  seed_skill exists", seed.exists(), cfg["seed_skill"])

        tasks = REPO_ROOT / cfg["tasks_path"]
        check(f"  tasks_path exists", tasks.exists(), cfg["tasks_path"])

        eval_cfg = REPO_ROOT / cfg["eval_config"]
        check(f"  eval_config exists", eval_cfg.exists(), cfg["eval_config"])

        nemogym = Path(cfg["nemogym_root"])
        check(f"  nemogym_root exists", nemogym.exists(), str(nemogym))
        for ng_cfg in cfg.get("ng_config_paths", []):
            p = nemogym / ng_cfg
            check(f"    ng_config: {ng_cfg}", p.exists(), str(p))
    except Exception as e:
        check(f"{cfg_name} parses", False, f"{type(e).__name__}: {e}")

# ──────────────────────────────────────────────────────────────────
section("3. GPT-5 connectivity")

import openai  # noqa: E402

base_url = os.environ["LLM_BASE_URL"]
api_key = os.environ["LLM_API_KEY"]
analyzer_model = os.environ["ANALYZER_MODEL"]
client = openai.OpenAI(base_url=base_url, api_key=api_key, timeout=120.0, max_retries=1)

try:
    t0 = time.time()
    # GPT-5 is a reasoning model — needs generous max_tokens or reasoning burns
    # all of them before any output text is produced (see nemo-gym-bugs.md #4).
    resp = client.chat.completions.create(
        model=analyzer_model,
        messages=[
            {"role": "system", "content": "You are a test probe."},
            {"role": "user", "content": "Reply with exactly: OK"},
        ],
        max_tokens=4096,
        temperature=0.0,
    )
    latency = time.time() - t0
    content = (resp.choices[0].message.content or "").strip()
    # Treat any non-empty content as success (reasoning model may add preamble)
    check("GPT-5 reachable",
          bool(content),
          f"{latency:.1f}s, reply={content[:60]!r}")
except Exception as e:
    check("GPT-5 reachable", False, f"{type(e).__name__}: {e}")
    print(f"\nCannot reach GPT-5 at {base_url}. Aborting further checks.")
    sys.exit(1)

# ──────────────────────────────────────────────────────────────────
section("4. Pick real rollouts from legacy run")

legacy_work = REPO_ROOT / "optimizer" / "outputs_haiku_run_legacy_gen1-3" / "work"
gen1_files = sorted(legacy_work.glob("gen1_ind*/rollouts_gen1_ind*.jsonl"))
gen1_files = [f for f in gen1_files if "materialized" not in f.name and "reward" not in f.name]

all_rollouts: list[dict] = []
for rf in gen1_files:
    with open(rf) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                all_rollouts.append(json.loads(line))
            except json.JSONDecodeError:
                pass

pass_rollouts = [r for r in all_rollouts if r.get("reward", 0) > 0]
fail_rollouts = [r for r in all_rollouts if r.get("reward", 0) <= 0]
check(f"Legacy pass rollouts available ({len(pass_rollouts)})", len(pass_rollouts) > 0)
check(f"Legacy fail rollouts available ({len(fail_rollouts)})", len(fail_rollouts) > 0)

# Pick one pass + one fail, preferably different tasks for a good smoketest
sample_pass = pass_rollouts[0] if pass_rollouts else None
sample_fail = fail_rollouts[0] if fail_rollouts else None

# ──────────────────────────────────────────────────────────────────
section("5. Layer 1: real GPT-5 refinement calls")

import streaming_oracle as so  # noqa: E402

out_dir = REPO_ROOT / "optimizer" / "_validation"
if out_dir.exists():
    shutil.rmtree(out_dir)
out_dir.mkdir(parents=True)
task_insights_dir = out_dir / "task_insights"
cross_task_dir = out_dir / "cross_task"

for label, sample in [("pass", sample_pass), ("fail", sample_fail)]:
    if sample is None:
        check(f"Layer1 ({label})", False, "no sample rollout")
        continue
    task_id = (sample.get("task_id") or "?").replace("cvdp_agentic_heavy_", "")
    print(f"\n  → Refining {label} rollout (task={task_id})...")
    t0 = time.time()
    path = so.update_task_insight(
        rollout=sample,
        rollout_id=f"validation_{label}",
        task_insights_dir=task_insights_dir,
        llm_client=client,
        llm_model=analyzer_model,
    )
    latency = time.time() - t0
    ok = path is not None and path.exists() and path.stat().st_size > 100
    detail = f"{latency:.1f}s, "
    if path and path.exists():
        detail += f"{path.stat().st_size} bytes → {path.name}"
    else:
        detail += "no output"
    check(f"Layer1 {label} rollout refinement", ok, detail)
    if path and path.exists():
        # Show a preview
        preview = path.read_text()[:400]
        print(f"    [preview]")
        for line in preview.split("\n")[:8]:
            print(f"      │ {line}")
        if len(preview) > 400:
            print(f"      │ ...")

# Seed the other task_insights files so Layer 2 has input
# If pass sample is task A and fail sample is task B, generate a cross doc for each
# by running Layer 1 again against a few more rollouts
print("\n  → Feeding 2 more rollouts to grow corpus for Layer 2...")
for extra_label, extra in [("pass_extra", pass_rollouts[1] if len(pass_rollouts) > 1 else None),
                            ("fail_extra", fail_rollouts[1] if len(fail_rollouts) > 1 else None)]:
    if extra is None:
        continue
    task_id = (extra.get("task_id") or "?").replace("cvdp_agentic_heavy_", "")
    path = so.update_task_insight(
        rollout=extra,
        rollout_id=f"validation_{extra_label}",
        task_insights_dir=task_insights_dir,
        llm_client=client,
        llm_model=analyzer_model,
    )
    if path:
        print(f"    {PASS_TAG} extra {extra_label}: {task_id} ({path.stat().st_size}b)")

# ──────────────────────────────────────────────────────────────────
section("6. Layer 2: cross-task synthesis (real GPT-5)")

for outcome in ("pass", "fail"):
    print(f"\n  → Synthesizing cross-task {outcome}...")
    t0 = time.time()
    path = so.synthesize_cross_task(
        task_insights_dir=task_insights_dir,
        cross_task_dir=cross_task_dir,
        outcome=outcome,
        generation=1,
        llm_client=client,
        llm_model=analyzer_model,
    )
    latency = time.time() - t0
    ok = path is not None and path.exists() and path.stat().st_size > 100
    detail = f"{latency:.1f}s, "
    if path and path.exists():
        detail += f"{path.stat().st_size} bytes → {path.name}"
    else:
        detail += "no output"
    check(f"Layer2 {outcome} synthesis", ok, detail)

# ──────────────────────────────────────────────────────────────────
section("7. Layer 3: oracle handoff (real GPT-5)")

scoreboard = """  axi4_lite_0002: avg=78% (67%, 100%, 67%) [USUALLY SOLVED]
  enso_0017: avg=22% (0%, 33%, 33%) [SOMETIMES SOLVED]
  reckon_0001: avg=0% (0%, 0%, 0%) [NEVER SOLVED]"""

print("\n  → Building Layer-3 handoff...")
t0 = time.time()
path = so.build_oracle_feedback(
    gen_dir=out_dir,
    generation=1,
    scoreboard=scoreboard,
    best=0.556, mean=0.537, worst=0.500,
    n_pass=10, n_fail=8,
    llm_client=client,
    llm_model=analyzer_model,
)
latency = time.time() - t0
ok = path is not None and path.exists() and path.stat().st_size > 100
detail = f"{latency:.1f}s, "
if path and path.exists():
    detail += f"{path.stat().st_size} bytes → {path.name}"
check("Layer3 oracle handoff", ok, detail)

if path and path.exists():
    text = path.read_text()
    check("  Output contains 'KEEP'", "KEEP" in text)
    check("  Output contains 'ADD'", "ADD" in text)
    check("  Output contains 'REMOVE'", "REMOVE" in text)
    check("  Output contains 'CHANGE'", "CHANGE" in text)
    check("  No literal '{gen}' leaks", "{gen}" not in text and "{generation}" not in text)
    check("  No literal '{best:.3f}' leaks", "{best:.3f}" not in text)

# ──────────────────────────────────────────────────────────────────
section("8. Output integrity")

for rel in ["task_insights", "cross_task", "oracle_feedback.md"]:
    p = out_dir / rel
    check(f"{rel} produced", p.exists(), str(p.relative_to(REPO_ROOT)))

# ──────────────────────────────────────────────────────────────────
section("9. Pre-flight for real run")

# Check haiku_all_tasks.yml output_dir collision
try:
    # trace-skill layout: configs moved to orchestration/configs/legacy/
    cfg_path = REPO_ROOT / "orchestration/configs/legacy/haiku_all_tasks.yml"
    if not cfg_path.exists():
        cfg_path = REPO_ROOT / "optimizer/configs/haiku_all_tasks.yml"
    with open(cfg_path) as f:
        cfg = yaml.safe_load(os.path.expandvars(f.read()))
    legacy_dir = REPO_ROOT / cfg["output_dir"]
    warning_needed = legacy_dir.exists() and any(legacy_dir.iterdir())
    if warning_needed:
        print(f"  {WARN_TAG} output_dir {cfg['output_dir']} is NOT empty — real run will overwrite")
        print(f"    existing: {len(list(legacy_dir.iterdir()))} entries; rename it before launching:")
        print(f"      mv {cfg['output_dir']} {cfg['output_dir']}_legacy")
    else:
        check("output_dir clean for new run", True, cfg["output_dir"])
except Exception as e:
    print(f"  {FAIL_TAG} collision check failed: {e}")

# ──────────────────────────────────────────────────────────────────
section("Summary")

passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"\n  {passed}/{total} checks passed")
print(f"  Validation artifacts: {out_dir.relative_to(REPO_ROOT)}/")
print()

if passed == total:
    print(f"  {PASS_TAG} READY — safe to launch the real run")
    sys.exit(0)
else:
    print(f"  {FAIL_TAG} NOT READY — inspect failing checks above")
    for name, ok, detail in results:
        if not ok:
            print(f"    - {name}: {detail}")
    sys.exit(1)

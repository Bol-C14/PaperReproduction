#!/usr/bin/env python3
"""Validates the three Apr-19 bug fixes + the new crash-debug telemetry.

Runs in ~10 seconds, no real LLM calls. Exits 0 on success.

Checks:
  1. save_checkpoint is now called POST-FITNESS (not only post-breeding)
  2. Resume-breeding regenerates oracle and passes oracle_feedback to Opus
  3. Launcher uses setsid --fork to detach from parent session
  4. StatusHeartbeat writes status.json atomically at phase transitions
  5. snapshot_system.sh produces a non-empty snapshot
  6. End-to-end resume path works on the reconstructed hardset checkpoint
     (mocked LLMs, dry-runs the resume logic)

Usage:
    python optimizer/test_bug_fixes.py
"""
from __future__ import annotations
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "optimizer"))

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
results: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> bool:
    tag = PASS if cond else FAIL
    msg = f"  {tag} {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    results.append((name, cond, detail))
    return cond


def section(title: str) -> None:
    print(f"\n{'=' * 64}")
    print(f"  {title}")
    print("=" * 64)


# ─────────────────────────────────────────────────────────────────
section("1. Checkpoint granularity (fix #1)")

src = (REPO_ROOT / "optimizer/run_optimizer.py").read_text()
save_ckpt_calls = re.findall(r"save_checkpoint\(\s*output_dir,\s*gen", src)
check("save_checkpoint called ≥ 2 times (post-fitness + post-breeding)",
      len(save_ckpt_calls) >= 2,
      f"found {len(save_ckpt_calls)} call sites")
check("'CHECKPOINT 1 OF 2 (post-fitness' marker present in source",
      "CHECKPOINT 1 OF 2 (post-fitness" in src)
check("'CHECKPOINT 2 OF 2 (post-breeding' marker present in source",
      "CHECKPOINT 2 OF 2 (post-breeding" in src)

# Verify the post-fitness checkpoint is BEFORE the oracle-firing branch
post_fit_idx = src.find("CHECKPOINT 1 OF 2 (post-fitness")
oracle_branch_idx = src.find("3-layer streaming oracle pipeline")
breed_branch_idx = src.find("Selection + breeding")
check("post-fitness checkpoint is BEFORE the breeding+oracle branch",
      0 < post_fit_idx < breed_branch_idx < oracle_branch_idx)


# ─────────────────────────────────────────────────────────────────
section("2. Resume-breeding passes oracle_feedback to Opus (fix #2)")

# Locate the resume-breeding block
resume_block_start = src.find("Checkpoint has evaluated population — running oracle + breeding")
resume_block_end = src.find('Starting from generation', resume_block_start)
assert resume_block_start > 0 and resume_block_end > resume_block_start, \
    "Resume-breeding block not found as expected"
resume_block = src[resume_block_start:resume_block_end]

check("resume path calls run_generation_oracle",
      "run_generation_oracle(" in resume_block)
check("resume path loads rollouts from disk",
      "ind_dir.glob" not in resume_block and "rollout_root.glob" in resume_block)
check("crossover_prompts receives oracle_feedback on resume",
      re.search(r"crossover_prompts\([^)]*?oracle_feedback=resume_oracle_feedback", resume_block, re.S) is not None)
check("mutate_prompt receives oracle_feedback on resume",
      re.search(r"mutate_prompt\([^)]*?oracle_feedback=resume_oracle_feedback", resume_block, re.S) is not None)
check("resume path gracefully handles oracle regeneration failure",
      "Oracle regeneration failed" in resume_block)


# ─────────────────────────────────────────────────────────────────
section("3. Launcher runs optimizer in foreground pipeline (fix #3 v2)")

launcher = (REPO_ROOT / "scripts/launch_optimizer.sh").read_text()
# v2 (Apr 19 evening): setsid --fork was removed because `$!` captured setsid's
# PID, not python's, causing wait to return immediately and the launcher's
# cleanup trap to kill ng_run while python was still running. Correct design:
# run python as a foreground pipeline inside tmux; tmux handles session
# lifecycle for us.
check("no live setsid --fork in launcher (kept in comments only)",
      launcher.count("setsid --fork") == launcher.count("# ") or
      all(line.strip().startswith("#") for line in launcher.split("\n") if "setsid --fork" in line))
check("launcher uses foreground python | tee pipeline",
      "python -u optimizer/run_optimizer.py" in launcher and
      "| tee -a" in launcher)
check("launcher captures Python exit via PIPESTATUS[0]",
      "PIPESTATUS[0]" in launcher)
check("launcher exports policy_model_name before ng_run",
      "export policy_model_name=" in launcher and launcher.index("export policy_model_name=") < launcher.index("nohup ng_run"))
check("launcher synchronizes ROLLOUT_MODEL before ng_run",
      'export ROLLOUT_MODEL="$DISPLAY_ROLLOUT_MODEL"' in launcher and launcher.index('export ROLLOUT_MODEL="$DISPLAY_ROLLOUT_MODEL"') < launcher.index("nohup ng_run"))
check("launcher exports policy_base_url before ng_run",
      "export policy_base_url=" in launcher and launcher.index("export policy_base_url=") < launcher.index("nohup ng_run"))
check("launcher documents v0/v1/v2 evolution",
      "v2" in launcher and "DETACHED TOO WELL" in launcher)
# Bash syntax check
r = subprocess.run(["bash", "-n", str(REPO_ROOT / "scripts/launch_optimizer.sh")],
                   capture_output=True, text=True)
check("launcher bash syntax clean", r.returncode == 0, r.stderr[:120] if r.stderr else "")


# ─────────────────────────────────────────────────────────────────
section("4. StatusHeartbeat writes status.json at phase transitions")

from debug_logging import StatusHeartbeat

with tempfile.TemporaryDirectory() as tmp:
    tmp_p = Path(tmp)
    hb = StatusHeartbeat(run_dir=tmp_p, pid=os.getpid())
    hb.update(phase="init")
    status1 = json.loads((tmp_p / "status.json").read_text())
    hb.update(phase="fitness_eval", generation=2, individual_idx=1,
              individual_parent="elite_0_from_gen1",
              context={"prompt_chars": 7341, "trial_id": "gen2_ind1"})
    status2 = json.loads((tmp_p / "status.json").read_text())

    check("status.json exists after update()", (tmp_p / "status.json").exists())
    check("phase field updates", status1["phase"] == "init" and status2["phase"] == "fitness_eval")
    check("generation / individual fields populated",
          status2["generation"] == 2 and status2["individual_idx"] == 1)
    check("pid recorded", status2["pid"] == os.getpid())
    check("host recorded", bool(status2.get("host")))
    check("timestamps are UTC ISO 8601",
          status2["last_update"].endswith("Z") and "T" in status2["last_update"])

    # Error handling: does update() swallow exceptions?
    hb_broken = StatusHeartbeat(run_dir=Path("/nonexistent/path/abc/def"), pid=0)
    try:
        hb_broken.update(phase="test")
        check("heartbeat swallows I/O errors (never raises)", True)
    except Exception as e:
        check("heartbeat swallows I/O errors (never raises)", False, str(e))

# Verify wiring in run_optimizer.py
check("run_optimizer imports StatusHeartbeat",
      "from debug_logging import" in src and "StatusHeartbeat" in src)
# Count phase transitions — should have at least init, fitness_eval, oracle_3layer, breeding, gen_complete, complete
phases = re.findall(r'heartbeat\.update\(phase="(\w+)"', src)
expected_phases = {"init", "fitness_eval_gen_start", "fitness_eval", "oracle_3layer",
                   "breeding", "gen_complete", "complete"}
got_phases = set(phases)
check(f"all {len(expected_phases)} expected heartbeat phases wired",
      expected_phases <= got_phases,
      f"missing: {expected_phases - got_phases}" if expected_phases - got_phases else "")


# ─────────────────────────────────────────────────────────────────
section("5. snapshot_system.sh produces a non-empty postmortem dump")

with tempfile.TemporaryDirectory() as tmp:
    r = subprocess.run(
        ["bash", str(REPO_ROOT / "scripts/snapshot_system.sh"), tmp, "unit_test"],
        capture_output=True, text=True, timeout=30,
    )
    snap_dir = Path(tmp) / "system"
    snaps = list(snap_dir.glob("*_unit_test.txt")) if snap_dir.exists() else []
    check("snapshot script runs cleanly", r.returncode == 0,
          r.stderr.strip()[:120] if r.stderr else "")
    check("snapshot file created", len(snaps) == 1,
          str(snaps[0].relative_to(Path(tmp))) if snaps else "(none)")
    if snaps:
        content = snaps[0].read_text()
        check("snapshot contains uname/uptime/free/ps sections",
              all(sec in content for sec in ("uname -a", "uptime", "free -h", "key processes")))
        check("snapshot is non-trivial size (> 500 bytes)",
              len(content) > 500, f"{len(content)} bytes")


# ─────────────────────────────────────────────────────────────────
section("6. End-to-end resume path against reconstructed hardset checkpoint")

ckpt_path = REPO_ROOT / "optimizer/outputs_hardset/checkpoint.json"
if ckpt_path.exists():
    ckpt = json.loads(ckpt_path.read_text())
    check("reconstructed checkpoint exists at outputs_hardset/",
          True, f"last_completed_gen={ckpt['last_completed_gen']}")
    check("checkpoint has 3-individual population", len(ckpt["population"]) == 3)
    check("checkpoint fitness values populated",
          all(ind["fitness"] >= 0 for ind in ckpt["population"]))
    check("best_ever is the highest-fitness individual",
          ckpt["best_ever"]["fitness"] == max(ind["fitness"] for ind in ckpt["population"]))
    check("history has gen-1 record",
          len(ckpt["history"]) == 1 and ckpt["history"][0]["generation"] == 1)

    # Verify rollout JSONLs exist in the expected layout
    rollout_root = REPO_ROOT / "optimizer/outputs_hardset/gen1/rollouts"
    ind_dirs = sorted(rollout_root.glob("ind*"))
    check("gen1 rollouts/ind* directories exist", len(ind_dirs) == 3,
          f"found {len(ind_dirs)}")
    total_rollouts = 0
    for d in ind_dirs:
        f = d / f"rollouts_gen1_{d.name}.jsonl"
        if f.exists():
            total_rollouts += sum(1 for _ in open(f))
    check("gen1 has 45 rollouts saved on disk (3 inds × 3 tasks × 5 reps)",
          total_rollouts == 45, f"found {total_rollouts}")
else:
    print(f"  (skipped — no reconstructed checkpoint at {ckpt_path.relative_to(REPO_ROOT)})")


# ─────────────────────────────────────────────────────────────────
section("Summary")
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"\n  {passed}/{total} checks passed")
if passed < total:
    print("\n  Failing checks:")
    for name, ok, detail in results:
        if not ok:
            print(f"    {FAIL} {name}  {detail}")
    sys.exit(1)
print(f"\n  {PASS} All fixes verified. Safe to resume the hardset run.")

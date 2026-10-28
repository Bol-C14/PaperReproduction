"""One complete attempt; refuses to overwrite results. Run from any directory."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import traceback

import z3
import reconstruct
import verify

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def accept(f, p, v):
    expected = f["expect"]
    if expected == "valid_range":
        return v["range_escape"]["verdict"] == "unsat" and v["range_matches_paper"]
    if expected == "reject_empty":
        return not p["applied"] and v["guard"]["verdict"] == "unsat"
    if v["guard"]["verdict"] != "sat":
        return False
    required = "unsat" if expected == "valid" else "sat"
    if any(v[name]["verdict"] != required for name in ["local_mismatch", "full_mismatch"]):
        return False
    if expected == "valid":
        if not p["applied"]:
            return False
        if "range_escape" in v and v["range_escape"]["verdict"] != "unsat":
            return False
    else:
        if p["applied"] or not v["local_mismatch"].get("model_replays_formula") or not v["full_mismatch"].get("model_replays_formula"):
            return False
    if f["id"] == "F09" and v["valid_local_guard_mismatch"]["verdict"] != "unsat":
        return False
    if "assume_controls" in v:
        ctrl = v["assume_controls"]
        if any(ctrl[n]["verdict"] != "unsat" for n in ["create", "propagate", "combine"]):
            return False
        if ctrl["bottom_is_not_zero"]["verdict"] != "sat":
            return False
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT.parent / "RESULTS.jsonl")
    args = parser.parse_args()
    fixtures = json.loads((ROOT / "fixtures.json").read_text())
    if len(fixtures) != 10:
        raise ValueError("frozen protocol requires exactly ten fixtures")
    hashes = {n: digest(ROOT / n) for n in ["PROTOCOL.md", "fixtures.json", "reconstruct.py", "verify.py", "run.py", "requirements.lock"]}
    manifest = json.loads((ROOT / "FROZEN.json").read_text())
    for name in ["PROTOCOL.md", "fixtures.json"]:
        if hashes[name] != manifest[name]:
            raise ValueError(f"frozen protocol changed: {name}")
    start, cpu = time.perf_counter(), time.process_time()
    failed = 0
    with args.output.open("x") as out:
        for f in fixtures:
            t, c = time.perf_counter(), time.process_time()
            row = {"fixture": f, "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   "z3_version": z3.get_version_string(), "source_sha256": hashes}
            try:
                p = reconstruct.propose(f)
                v = verify.check(f, p)
                if f["id"] == "F01":
                    nested = reconstruct.Assume(reconstruct.Assume("x", "g"), "h")
                    v["assume_controls"] = verify.assume_controls(
                        reconstruct.create_true_branch("g", "x", "zero"),
                        reconstruct.propagate(reconstruct.Assume(("add", "x", "y"), "g")),
                        reconstruct.combine(nested), nested)
                row.update(proposal=p, verification=v, passed=accept(f, p, v))
            except Exception as exc:
                row.update(passed=False, error=repr(exc), traceback=traceback.format_exc())
            row.update(wall_seconds=time.perf_counter()-t, cpu_seconds=time.process_time()-c,
                       peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            failed += not row["passed"]
            out.write(json.dumps(row, sort_keys=True) + "\n")
            out.flush()
            print(f'{f["id"]}: {"PASS" if row["passed"] else "FAIL"}')
    summary = {"fixtures": len(fixtures), "passed": len(fixtures)-failed, "failed": failed,
               "wall_seconds": time.perf_counter()-start, "cpu_seconds": time.process_time()-cpu,
               "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               "output": str(args.output), "source_sha256": hashes}
    args.output.with_suffix(".summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    print(json.dumps(summary, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

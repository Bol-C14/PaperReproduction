#!/usr/bin/env python3
"""Bounded structural retrieval/configuration-transfer smoke test, not CROP."""
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parent


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2) + "\n")


def features(path):
    text = re.sub(r"//[^\n]*", "", path.read_text())
    # Source-expression structure only; excludes design ID, family and bit width.
    raw = [text.count("+"), text.count("<"), text.count("?")]
    norm = math.sqrt(sum(x*x for x in raw))
    return [x/norm for x in raw] if norm else raw


def measure_netlist(path):
    mod = json.loads(path.read_text())["modules"]["dut"]
    cells = mod.get("cells", {})
    inputs = {b for p in mod["ports"].values() if p["direction"] == "input"
              for b in p["bits"]}
    depth = {b: 0 for b in inputs}
    pending = dict(cells)
    for cell in cells.values():
        if not cell["type"].startswith("$_"):
            raise ValueError("Unmapped cell: " + cell["type"])
    while pending:
        progress = False
        for name, cell in list(pending.items()):
            ins = [b for port, bits in cell["connections"].items()
                   if cell["port_directions"][port] == "input" for b in bits]
            if all(isinstance(b, str) or b in depth for b in ins):
                d = 1 + max([depth.get(b, 0) for b in ins] or [0])
                for port, bits in cell["connections"].items():
                    if cell["port_directions"][port] == "output":
                        for b in bits:
                            depth[b] = d
                del pending[name]
                progress = True
        if not progress:
            raise ValueError("Unresolved/cyclic netlist")
    outputs = [b for p in mod["ports"].values() if p["direction"] == "output"
               for b in p["bits"]]
    return {"area_proxy_generic_gate_count": len(cells),
            "delay_proxy_unit_gate_depth": max([depth.get(b, 0) for b in outputs] or [0]),
            "physical_area": None, "physical_delay_ns": None}


def main():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    ledger = ROOT / "measurements.jsonl"
    # A completed or partial run must never silently spend another budget.
    if ledger.exists():
        raise SystemExit("Existing measurement ledger: preserve it; refuse automatic rerun.")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "toolchain")
    env["XDG_CACHE_HOME"] = str(ROOT / "cache")
    exe = ROOT / "toolchain/bin/yowasp-yosys"
    dump(ROOT / "source_hashes.json", {
        d["id"]: hashlib.sha256((ROOT/d["path"]).read_bytes()).hexdigest()
        for d in manifest["designs"]})
    rows = []

    def trial(design, config, phase, arm=None, retrieved=None):
        assert len(rows) < manifest["max_measurement_invocations"]
        label = f"{len(rows)+1:02d}_{phase}_{arm or 'history'}_{design['id']}_{config}"
        folder = ROOT / "runs" / label
        folder.mkdir(parents=True)
        rel = folder.relative_to(ROOT)
        opts = manifest["configs"][config]["synth_options"]
        script = f"""read_verilog {design['path']}
hierarchy -check -top dut
proc
flatten
opt
design -save reference
synth -top dut {opts}
check -assert
write_json {rel}/mapped.json
stat
ltp -noff
design -save mapped
design -reset
design -copy-from reference -as gold dut
design -copy-from mapped -as gate dut
miter -equiv -flatten gold gate miter
hierarchy -check -top miter
sat -verify -prove trigger 0 -show-inputs -show-outputs
"""
        (folder / "flow.ys").write_text(script)
        row = {"invocation":len(rows)+1,"phase":phase,"arm":arm,
               "design":design["id"],"config":config,"retrieved":retrieved,
               "log":str(rel/"tool.log"),"status":"started"}
        rows.append(row)
        # Persist the consumed budget before invoking the tool (also on timeout).
        with ledger.open("a") as f:
            f.write(json.dumps(row)+"\n")
        started = time.monotonic()
        with (folder/"tool.log").open("w") as out:
            try:
                cp = subprocess.run([str(exe), "-Q", "-T", "-s", str(rel/"flow.ys")],
                                    cwd=ROOT, env=env, stdout=out, stderr=subprocess.STDOUT,
                                    timeout=120)
                row["returncode"] = cp.returncode
                log = (folder/"tool.log").read_text()
                if cp.returncode != 0 or "SUCCESS!" not in log:
                    raise RuntimeError("Synthesis or combinational SAT proof failed; see log")
                row.update(measure_netlist(folder/"mapped.json"))
                row["functional_check"] = "PASS: SAT equivalence for all binary inputs"
                row["status"] = "ok"
            except Exception as exc:
                row["status"] = "failed"
                row["error"] = str(exc)
        row["elapsed_seconds"] = time.monotonic()-started
        dump(folder/"result.json",row)
        with ledger.open("a") as f:
            f.write(json.dumps(dict(row,event="finished"))+"\n")
        dump(ROOT/"results.json",rows)
        print(label, row["status"], flush=True)
        return row

    priors = [d for d in manifest["designs"] if d["role"] == "prior"]
    targets = [d for d in manifest["designs"] if d["role"] == "target"]
    for design in priors:
        for config in manifest["configs"]:
            trial(design, config, "prior")
    history = {}
    for design in priors:
        available = [r for r in rows if r["design"] == design["id"] and r["status"] == "ok"]
        if available:
            history[design["id"]] = min(available,key=lambda r:(
                r["area_proxy_generic_gate_count"],r["delay_proxy_unit_gate_depth"],r["config"]))
    dump(ROOT/"history.json",history)
    if len(history) != len(priors):
        raise SystemExit("Incomplete measured prior pool; stop without fabricating history.")
    rng = random.Random(7)
    frozen_choices = []
    for target in targets:
        query = features(ROOT/target["path"])
        scored = [(sum(a*b for a,b in zip(query,features(ROOT/d["path"]))),d["id"])
                  for d in priors]
        nearest = sorted(scored,key=lambda x:(-x[0],x[1]))[0][1]
        random_prior = rng.choice(priors)["id"]
        for arm, neighbor in [("structural",nearest),("random",random_prior)]:
            frozen_choices.append({"target":target["id"],"arm":arm,"retrieved":neighbor,
                                   "config":history[neighbor]["config"],
                                   "query_features":query,"candidate_scores":scored})
    # Both arms' proposals are fixed before any target measurement is visible.
    dump(ROOT/"transfer_choices.json",frozen_choices)
    for choice in frozen_choices:
        design = next(d for d in targets if d["id"] == choice["target"])
        trial(design,choice["config"],"target",choice["arm"],choice["retrieved"])
    summary = {
        "measurement_invocations":len(rows),"successful":sum(r["status"]=="ok" for r in rows),
        "prior_history_construction_calls":6,"target_calls":6,
        "prior_history_construction_seconds":sum(r["elapsed_seconds"] for r in rows if r["phase"]=="prior"),
        "target_seconds":sum(r["elapsed_seconds"] for r in rows if r["phase"]=="target"),
        "semantic_component":"NOT RUN", "full_crop":"NOT RUN",
        "claim":"Only a bounded structural configuration-transfer smoke test; no industrial or semantic CROP result."
    }
    dump(ROOT/"summary.json",summary)


if __name__ == "__main__":
    main()

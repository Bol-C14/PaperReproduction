"""Copy completed RQ1 artifacts with stability checks; compare EDIF bytes only.

No normalization, semantics inference, vendor processes, or source writes.
"""
import hashlib
import itertools
import json
from pathlib import Path
import sys
from zipfile import ZipFile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def edif_payload(path):
    with ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.endswith(".edf")]
        if len(names) != 1:
            raise ValueError("Require exactly one EDIF payload")
        return archive.read(names[0])


def exact_screen(left, right):
    return left == right


def snapshot(source, destination):
    relatives = ["ROUND2_SUMMARY.json", "ROUND2_METRICS.json",
                 "DEFAULT_SLICE_PROOF.json", "logs/panel_ledger.json",
                 "logs/confirmation_ledger.json", "logs/contract/exit_code.txt",
                 "logs/contract/serialized.dcp"]
    # Only artifacts whose immutable completion ledgers explicitly report success.
    summary = json.loads((source / "ROUND2_SUMMARY.json").read_text())
    if summary["running_jobs"]:
        raise RuntimeError("Summary reports a running job; defer snapshot")
    arms = [a for a in summary["arms"]
            if a["status"] == "tool_complete" and a["exit_code"] == 0]
    for arm in arms:
        for name in ("output.dcp", "command.json", "timing.rpt", "route.rpt",
                     "drc.rpt", "constraints.xdc", "funcsim.v"):
            relatives.append("logs/" + arm["arm"] + "/" + name)
    initial = {}
    manifest = []
    for rel in relatives:
        path = source / rel
        before = path.stat()
        data = path.read_bytes()
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise RuntimeError("Source changed during read: " + rel)
        initial[rel] = (digest(data), before.st_size, before.st_mtime_ns)
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    # Check all originals again after every copy, not just each file individually.
    for rel in relatives:
        path = source / rel
        stat = path.stat()
        observed = (digest(path.read_bytes()), stat.st_size, stat.st_mtime_ns)
        if observed != initial[rel]:
            raise RuntimeError("Source changed during snapshot; reject all: " + rel)
        if digest((destination / rel).read_bytes()) != initial[rel][0]:
            raise RuntimeError("Copy hash mismatch: " + rel)
        manifest.append({"relative_path": rel, "sha256": initial[rel][0],
                         "size": initial[rel][1], "mtime_ns": initial[rel][2]})
    paths = {"serialized": destination / "logs/contract/serialized.dcp"}
    paths.update({a["arm"]: destination / "logs" / a["arm"] / "output.dcp" for a in arms})
    payloads = {name: edif_payload(path) for name, path in paths.items()}
    comparisons = [{"left": a, "right": b,
                    "exact_edif_bytes_equal": exact_screen(payloads[a], payloads[b])}
                   for a, b in itertools.combinations(paths, 2)]
    return {"source_files_stable_before_after": True, "source_files": manifest,
            "edif": {name: {"bytes": len(data), "sha256": digest(data)}
                     for name, data in payloads.items()}, "comparisons": comparisons,
            "scope": "Exact EDIF representation screen, not semantic/equivalence proof"}


if __name__ == "__main__":
    result = snapshot(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps(result, indent=2))

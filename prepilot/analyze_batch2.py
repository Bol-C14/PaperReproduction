"""Read completed Batch 2 reports; no vendor calls or semantic equivalence claims."""
import hashlib
import json
from pathlib import Path
import re
import sys
from rq4_timestamp_v1 import canonicalize_timestamp_v1


def timing(path):
    text = path.read_text()
    for line in text.splitlines():
        values = line.split()
        if len(values) == 12:
            try:
                nums = list(map(float, values))
            except ValueError:
                continue
            return dict(zip(["wns", "tns", "setup_failing", "setup_total", "whs", "ths",
                             "hold_failing", "hold_total", "wpws", "tpws", "pulse_failing",
                             "pulse_total"], nums))
    raise ValueError("No exact 12-column timing-summary row: " + str(path))


def analyze(root):
    records = []
    for name in ("RouteNoPSIR", "RouteNoPSIRTNS"):
        directory = root / name
        if not (directory / "exit_code.txt").exists():
            records.append({"path": name, "status": "not_completed_or_not_run"})
            continue
        code = int((directory / "exit_code.txt").read_text())
        record = {"path": name, "exit_code": code,
                  "wall_seconds": float((directory / "wall_seconds.txt").read_text())}
        if code == 0:
            before = (directory / "before.edf").read_bytes()
            after = (directory / "after.edf").read_bytes()
            record.update({"before_edif_sha256": hashlib.sha256(before).hexdigest(),
                           "after_edif_sha256": hashlib.sha256(after).hexdigest(),
                           "exact_edif_bytes_equal": before == after})
            try:
                record["timestamp_v1_equal"] = canonicalize_timestamp_v1(before) == canonicalize_timestamp_v1(after)
            except ValueError as error:
                record["timestamp_v1_equal"] = False
                record["instrument_error"] = str(error)
            record["before_timing"] = timing(directory / "before_timing.rpt")
            record["after_timing"] = timing(directory / "timing.rpt")
        records.append(record)
    return {"scope": "completed-report screen only; no equivalence or future-effect proof", "paths": records}


if __name__ == "__main__":
    print(json.dumps(analyze(Path(sys.argv[1])), indent=2))

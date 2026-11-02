"""One capped two-thread Vivado session; evaluator evidence, no agent."""
import hashlib
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--original', required=True, type=Path)
parser.add_argument('--updated', required=True, type=Path)
args = parser.parse_args()
inputs = {
    "original": args.original.resolve(),
    "updated": args.updated.resolve(),
}
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

manifest = {key: {"path": str(path), "sha256_before": sha(path)} for key, path in inputs.items()}
command = [os.environ['VIVADO_EXEC'], '-mode', 'batch', '-notrace', '-source',
           str(root / 'report_probe.tcl'), '-log', str(root / 'vivado.log'),
           '-journal', str(root / 'vivado.jou'), '-tclargs', str(root),
           *[str(p) for p in inputs.values()]]
start = time.monotonic()
with (root / 'stdout.log').open('w') as output:
    # GNU timeout terminates the process group, with bounded kill grace.
    result = subprocess.run(['timeout', '--signal=TERM', '--kill-after=5s', '540s', *command],
                            cwd=root, stdout=output, stderr=subprocess.STDOUT, check=False)
wall = time.monotonic() - start
reports = []
for path in sorted(root.glob('*.rpt')):
    begin = time.monotonic_ns()
    content = path.read_bytes()  # existing-byte retrieval, not a new observation
    elapsed = time.monotonic_ns() - begin
    reports.append(dict(file=path.name, bytes=len(content), sha256=hashlib.sha256(content).hexdigest(),
                        existing_file_read_ns=elapsed, cache_state='uncontrolled OS cache'))
for key, path in inputs.items():
    manifest[key]['sha256_after'] = sha(path)
receipt = dict(exit_code=result.returncode, process_wall_s=wall, input_states=manifest,
               reports=reports, max_tool_threads=2, timeout_s=540,
               command=command, interpretation='report generation only; no agent or intervention')
(root / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(dict(exit_code=result.returncode, process_wall_s=wall, report_count=len(reports))))

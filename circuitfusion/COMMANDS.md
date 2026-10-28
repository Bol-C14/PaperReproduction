# Commands and execution ledger

All paths below are relative to `/workspace/PaperReproduction`. Executed in the selected cloud environment on 2026-10-28 UTC. No external publication or push.

1. Read environment metadata, searched workspace instructions, inspected unborn Git repository. Created branch with `git switch -c reproduction/circuitfusion-iclr2025`.
2. Used Python stdlib `urllib.request.urlopen` for seven official raw GitHub files. URLs, byte counts and SHA256 are in `provenance.json`. The GitHub API commit request was denied by proxy 403; no SHA invented and no bypass attempted.
3. `python -m venv circuitfusion/.venv`
4. `circuitfusion/.venv/bin/python -m pip install --index-url https://download.pytorch.org/whl/cpu torch numpy > circuitfusion/logs/dependency_setup.log 2>&1`
5. `python circuitfusion/repair_sources.py > circuitfusion/logs/repair.patch.log`
6. `circuitfusion/.venv/bin/python circuitfusion/tests/test_repairs.py > circuitfusion/logs/repair_controls.log 2>&1`
7. `circuitfusion/.venv/bin/python -m pip freeze > circuitfusion/requirements-cpu.lock`
8. Wrote protocol before constructing data/training, then `sha256sum circuitfusion/pilot/PROTOCOL.json > circuitfusion/pilot/PROTOCOL.sha256`.
9. `circuitfusion/.venv/bin/python circuitfusion/pilot/data.py > circuitfusion/logs/data_integrity.log 2>&1`
10. `circuitfusion/.venv/bin/python circuitfusion/tests/test_integrity.py > circuitfusion/logs/integrity_controls.log 2>&1`. Initial tamper fixture changed a gate outside the observable output cone / without changing function, so semantic corruption was not detected. Initial log retained as `integrity_controls_initial.log`. Changed fixture to corrupt an observable output XOR to AND; all seven controls pass. This was a test-fixture correction, not outcome-dependent model tuning.
11. Initial launch with `/usr/bin/time -v` failed before training because `/usr/bin/time` is absent (exit 127). Retained `pilot_launch_initial.log`. Used Bash `time` and Python resource accounting instead.
12. `time circuitfusion/.venv/bin/python circuitfusion/pilot/run.py > circuitfusion/logs/pilot.log 2> circuitfusion/logs/pilot_resources.log`

The nine model runs use the frozen protocol; no post-result tuning. `run.py` logs per-run seeds, losses, metrics, parameter count and wall time. `results/pilot_metrics.json` contains the full results and bootstrap calculations. It does not save or load pretrained weights. Source snapshots and small controls are used instead of importing the full upstream DGL/BERT pipeline.

Setup and pilot started within the 10:41–10:50 UTC window; exact individual setup duration was not separately instrumented. Download ledger is reconstructed from pip's advertised wheel sizes, not an operating-system network-byte counter. Public raw-source payloads total 45,485 bytes. No model/API/data/paid/GPU downloads or calls occurred.

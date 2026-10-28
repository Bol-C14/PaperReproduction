# Reproduce the finite CPU continuation

Use the existing paper branch, a dedicated Linux venv and the same Yosys source pin. Run on APRIL, not Mac. Download the exact HF revision URL described in PROTOCOL.md without credentials. Also download its revision API metadata and dataset card into `sources/`; keep this ignored. Run `inventory.py` and require the recorded SHA256, Git blob and 291-row schema before HDL work.

Build Yosys with `make -j2 CONFIG=gcc ENABLE_ABC=0 ENABLE_TCL=0 ENABLE_READLINE=0 ENABLE_PLUGINS=0 ENABLE_ZLIB=0 PREFIX=<isolated-install>`, then `make install` with the same flags. Source URL and SHA256 are in the preexisting `pilot/source_download.json`. Dedicated Python dependency: `numpy==1.26.4`. No training/inference packages are required.

From the repository root, define `PYTHON` as the dedicated venv executable, `YOSYS` as the **absolute** installed executable, and `RESULT_ROOT` as a new isolated result directory. Keep result directories unique: the runner intentionally refuses to overwrite one.

```sh
"$PYTHON" P07_VeriThoughts/continuation/inventory.py
taskset -c 32 "$PYTHON" P07_VeriThoughts/continuation/run_checks.py \
  --phase frontend --yosys "$YOSYS" --out "$RESULT_ROOT/frontend-attempt1"
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
taskset -c 32 "$PYTHON" P07_VeriThoughts/continuation/run_checks.py \
  --phase controls --yosys "$YOSYS" --out "$RESULT_ROOT/controls-attempt1"
```

Select an actually available affinity core in place of 32 when necessary; the recorded run used 32, serial. Use the project's file lock to prevent concurrent writers. Frontend and controls are distinct phases and distinct stopping contracts. The runner and upstream SHA256 must match freeze.json before reproduction. The original failed first frontend launch was infrastructure-only and remains in the raw archive; successful recorded frontend run is named `frontend-attempt2`.

Read written `responses_evaluation.jsonl` and nested subprocess return codes for control acceptance; an evaluator exit of 0 is only successful orchestration. Original pass@5/10 console values are excluded. Count five nested Yosys calls, three SAT solves and one zero-check acceptance, not six successful proofs.

The raw selected-hash output's inherited payload status is stale; use hashes and indices, and consult the explicitly corrected selection_verified.json. No experiment is rerun to repair a metadata string.

Raw source inputs, generated temporary HDL, tool environment files and all first-failure/complete logs remain in separate private evidence, hashed in raw_evidence_manifest.json. The reviewable repository candidate contains summary/command ledgers and hashes, not a redistributed dataset or environment archive. Exact unmodified source and log material can be inspected locally or regenerated after independently checking source download permission. No API or GPU is needed for this completed phase.

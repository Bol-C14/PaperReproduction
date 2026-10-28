# Replay the independent reconstruction

Preservation update: all15 locally generated final/preflight checkpoints are now included in a normal follow-on commit, unchanged. Earlier local-only/Git-excluded statements describe the initial export. The two unchanged downloadable upstream binaries remain omitted. See CHECKPOINT_PRESERVATION.json and CHECKPOINT_SECRET_SCAN.json.


Use the existing CPU venv from `/workspace/PaperReproduction`; no network or new resources are needed. Original audit/pilot files are preserved. This phase is under `P13_DeepCell/closure/`.

```bash
# Regenerate exhaustive-checked synthetic corpus and parent/function/family manifest.
P13_DeepCell/pilot/.venv/bin/python P13_DeepCell/closure/data.py

# Fixed protocol CPU preflight, then the five-arm/two-seed comparison.
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 P13_DeepCell/pilot/.venv/bin/python P13_DeepCell/closure/train.py --preflight --arms paired_pretrained
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 P13_DeepCell/pilot/.venv/bin/python P13_DeepCell/closure/train.py

# Independent exhaustive replay of every emitted main-run patch.
P13_DeepCell/pilot/.venv/bin/python P13_DeepCell/closure/replay_verify.py
```

Do not overwrite the retained run directory when doing a new experiment; copy outputs or change the output directory explicitly. Local model checkpoints live in `closure/checkpoints/` (excluded from Git) and include final state, configuration, seed and epochs. Results JSONs contain all training curves, per-case rankings and explicit synthesized AND/NOT patch netlists. `results/main_readiness.json` freezes data/protocol/source hashes before the main run and gives the measured CPU expansion decision. `PROTOCOL.md` defines interpretation and known departures from paper methodology. Package/runtime versions remain in the prior pilot and new summary.

The independent verifier imports neither the training script nor ECO solver. It does not trust recorded success flags without checking each emitted gate-level patch. It evaluates PM cells by direct Boolean operations (not stored truth tables) and compares the final patched output to independently generated parent truth signatures on all 64 assignments. A deliberately inverted patch must fail. No physical timing ECO, ABC mapping or original benchmark claim is implied.

If resuming only after the documented correctness repair, use `train.py --resume`; it retains complete arm/seed results. The v1 error and sources are preserved. The downstream model input separation check is:

```bash
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 P13_DeepCell/pilot/.venv/bin/python P13_DeepCell/closure/check_public_inputs.py
P13_DeepCell/pilot/.venv/bin/python P13_DeepCell/closure/summarize.py
```

The separately bounded public-tool extension uses an already built pinned ABC binary; it neither retrains nor selects a winning model:

```bash
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 P13_DeepCell/pilot/.venv/bin/python P13_DeepCell/closure/external/flow.py --prepare-only
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 P13_DeepCell/pilot/.venv/bin/python P13_DeepCell/closure/external/flow.py
```

It evaluates paired pretrained, PM-only, paired random and no-MCM models for both seeds. The shuffled-AIG training arm is not applied in this single-public-design extension because there is no separate public parent AIG for that corruption. Every successful actual repair BLIF has an individual ABC CEC log. The source commit/archive SHA256, benchmark commit/SHA256, compiler flags and local build duration are preserved under external/logs; upstream/archive/builds are Git-excluded. To rebuild that same local source: `make -j2 ABC_USE_NO_READLINE=1 ABC_USE_NO_PTHREADS=1` from its pinned extracted directory. No `make install` was used. `-s` skips ABC startup scripts; its local batch history was moved into logs. Do not substitute another tool/source after a denial.

The separately declared full-token fidelity sensitivity and its public-site check are replayed without overwriting the primary five-arm experiment:

```bash
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 P13_DeepCell/pilot/.venv/bin/python P13_DeepCell/closure/faithful_tokens.py
P13_DeepCell/pilot/.venv/bin/python P13_DeepCell/closure/replay_verify.py --directory full_token
P13_DeepCell/pilot/.venv/bin/python P13_DeepCell/closure/summarize_full_token.py
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 P13_DeepCell/pilot/.venv/bin/python P13_DeepCell/closure/external/flow.py --training-directory full_token
P13_DeepCell/pilot/.venv/bin/python P13_DeepCell/closure/write_report.py
```

`checkpoints_manifest.json` indexes all14 final local checkpoints by objective/arm/seed, exact size and SHA256. Large learned weights, upstream ABC archive/build and Python environment remain local/Git-excluded; source, explicit patch outputs, experiment data, numerical results and replay/proof logs are committed. Preflight checkpoint is separately retained but is not a selected final model.

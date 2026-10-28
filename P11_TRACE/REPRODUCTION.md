# TRACE bounded CPU methodology reproduction

FSL means **function-shift learning**. Few-shot support adaptation is a separate added evaluation, not the expansion of FSL.

Completed 2026-10-28 in selected cloud `/workspace/PaperReproduction`, local branch `reproduction/trace-dac2026`, origin `Bol-C14/PaperReproduction`. No external push or PR. The earlier asset audit is preserved separately as the pre-experiment assessment.

## Outcome

A real, small learning pilot completed using seven unchanged lightweight source files from official TRACE commit `b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70`. This closes the low-cost synthetic-data/training-harness gap for method learning. It does not reproduce DAC benchmark results or establish learned MUX/SUB correctness. Full-paper route remains provisional L3; no full corpus was downloaded.

| Held-out metric | Local-only approximation | Direct-target learning | Function-shift learning |
|---|---:|---:|---:|
| Non-PI node MAE | 0.114846 | 0.080647 | **0.068253** |
| Terminal-output MAE | 0.228299 | **0.079770** | 0.128100 |

These are one-seed results on four held-out parent DAGs / 32 distribution assignments. FSL improves the average non-PI metric here; direct prediction does better at terminal outputs. Neither arm wins every metric. No significance/generalization/industrial advantage claim is supported.

Both models trained for exactly 120 Adam steps, with 60,337 parameters each. Direct training L1 decreased from 0.285855 to 0.060622; residual training L1 from 0.103736 to 0.055526. The losses supervise different quantities and cannot be compared directly. Final train non-PI MAE: direct 0.046504, FSL 0.057838. FSL reconstruction produced five training-node probabilities below zero (minimum -0.048004); held-out predictions had no values outside [0,1]. Raw FSL reconstruction was retained, without final probability clamping.

## Frozen design and fidelity

`pilot/PROTOCOL.md` was saved before model/data experiments. Twelve deterministic parent DAGs contain three PIs, four intermediate AND/NOT gates and a terminal reconvergent AND. Parents 100–107 supply 64 training assignments; parents 108–111 supply 32 test assignments. Each assignment uses PI probabilities from {0.2,0.5,0.8}. The exact eight-row joint truth table yields all global marginal labels. All assignments/views inherit the parent split. No exact serialized topology hash overlaps the split. Parent-disjoint does not guarantee Boolean-function-disjoint or graph-isomorphism-disjoint: no such claim or test-set tuning was made.

`frozen_circuits.json` SHA256: `cf2e49f12640e2adb17ac8186fefc5bdcf75ff2c2615f575cab232f037275826`. It embeds the frozen protocol hash. It was saved before learning.

- Official AIG encoder: unchanged implementation, reduced hidden dimension 32 and one forward round; the encoder retains its fixed five-layer/eight-head AND Transformer and NOT MLP. Official MLP supplies the 3-layer scalar head. A plain torch harness replaces Lightning orchestration; no torch-scatter/DGL/Lightning needed for this source path.
- Hierarchy and ordered fanin grouping are preserved. The AIG source does not use explicit positional embeddings; its AND inputs are commutative. This pilot cannot establish the paper's noncommutative input-role learning claim.
- Official `cov2prob.py` reconstructs probabilities recursively. Training shifts use exact global target minus product of true fanin marginals, matching the inspected AIG loader. This is actual residual learning, not the untrained tutorial forward.
- Departures from full training: exact synthetic labels rather than simulation-derived industrial data, hidden/round reductions, one seed, full-batch 120-step optimization, plain MLP without decoder BatchNorm/dropout, direct supervision only on non-PI nodes. The same architecture/initialization/optimizer budget is used for both learned arms; direct and residual target masks differ by definition.
- Encoder PI initialization uses marginal probability repeated across hidden channels, with no explicit PI identity. Equal-probability primary inputs can be indistinguishable, limiting the ability to represent dependencies. No result here resolves this expressivity question.
- Three graph modalities in the repository remain separate tasks; no cross-layer correspondence experiment was performed.

## Controls and known labels

- Exact SUB labels: `(3-5) mod 97 = 95`, `(5-3) mod 97 = 2`; default polynomial label is 49. ADD operand swap preserves its exact label.
- Tutorial arbitrary node renaming with transported metadata: max prediction difference 0. Tutorial edge storage reversal with retained `edge_pos`: difference 0. Its level helper was not reused on arbitrary IDs.
- Swapping SUB input ports in the untrained tutorial changed its output by 0.000600547. This is structural sensitivity only; no learned subtraction accuracy claim.
- MUX select/data swap semantic oracle: targets 1 and 0 on the frozen nondegenerate assignment. No MUX model exists in the selected official paths, so no learned MUX claim.
- For `x AND NOT x`, exact output=0, local approximation=0.25 and residual=-0.25 at p=0.5. Independent AND has exact probability 0.25 and residual 0.
- Official reconstruction with oracle residuals matches all frozen node probabilities within `1.19209e-7`.
- Both trained AIG arms preserve predictions under bijective node renaming (max error 0). Edge groups/port order and PI distributions are transported. This is a bounded implementation control, not a universal invariance proof.

## Re-run

Current environment:

```bash
cd /workspace/PaperReproduction/P11_TRACE/pilot
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python run_pilot.py
.venv/bin/python verify_results.py
```

`RESULTS.jsonl` is append-only; re-running appends another run and regenerates deterministic pilot weights/predictions. Archive a prior run first if separate histories are desired. The original run log is `pilot/logs/pilot.log`. Verification is read-only and independently recomputes the saved test MAEs.

For a fresh Python 3.12 environment (commands documented, not a second installation performed):

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --only-binary=:all: --no-cache-dir torch==2.8.0+cpu --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install --only-binary=:all: --no-cache-dir -r requirements-cpu-lock.txt --index-url https://pypi.org/simple
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python run_pilot.py
```

The actual environment used `--system-site-packages` to reuse installed scientific dependencies; `SOURCE_VERSIONS.json` records versions, and `requirements-cpu-lock.txt` pins the 29-distribution runtime dependency closure except torch (installed separately from official CPU index). A fresh isolated replay has not been tested. Installation followed [official PyTorch CPU instructions](https://pytorch.org/get-started/previous-versions/) and [PyG minimal installation guidance](https://pytorch-geometric.readthedocs.io/en/2.7.0/install/installation.html).

## Resources and remaining boundaries

Actual pilot wall time 12.64 s, process CPU time 12.67 s, peak RSS 376,000 KiB (~367 MiB), one thread, no initialized CUDA. Setup, diagnosis, implementation and reporting were minutes rather than hours; detailed time and transfer accounting are in RESOURCE_LEDGER.md. No training failures, hyperparameter search, retry, or test-driven redesign occurred.

No extra user resources are needed to reproduce this bounded pilot. Full-paper work would need accessible verified graph datasets/splits, missing task checkpoints or retraining, complete sequential/similarity/transition task reconciliation and a measured compute budget. Dataset metadata was previously blocked by HTTP 403 and was not retried; reported 9.28GB remains unverified. GPU/full training is outside this authorization and cost remains unknown. Stop after this pilot.

## Later closure tranche — supersedes the stop milestone, preserves the pilot

The subsequent predictive loop is complete: three seeds, actual official PM architecture/weights, held-out hardware families, matched train/adapt/no-adapt controls, independent label/prediction verification and retrospective diagnosis of the pilot's mixed metrics. See [closure/CLOSURE_REPORT.md](closure/CLOSURE_REPORT.md) and [closure/RESULTS_SUMMARY.md](closure/RESULTS_SUMMARY.md). The v1 files and results above remain unchanged as historical evidence.

Targeted scientific evidence: [closure/evidence_packet/EVIDENCE_PACKET.md](closure/evidence_packet/EVIDENCE_PACKET.md), including per-seed/no-adaptation tables and exact label budgets. No new training in this audit.

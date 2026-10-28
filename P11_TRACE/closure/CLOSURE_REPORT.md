# TRACE: predictive methodology loop closed on available CPU resources

FSL means **function-shift learning**. Few-shot support adaptation is a separate added evaluation, not the expansion of FSL.

The selected predictive loop now runs **train → branch on support data → adapt → recursively predict → independently evaluate**, using the actual official PM backbone and a separately evaluated official checkpoint. The experiment is reduced-data methodology reproduction, not full-dataset DAC reproduction. The frozen design and all comparisons are in [PROTOCOL.md](PROTOCOL.md), [MECHANISM_COVERAGE.md](MECHANISM_COVERAGE.md) and [RESULTS_SUMMARY.md](RESULTS_SUMMARY.md).

## What was executed

Three seeds (2026–2028); 48 training parents from random DAG, chain and balanced-tree families; four composition families excluded from training: ripple carry, comparator, priority selector and reconvergent MUX. Each held-out family supplies two support parents and six different query parents. Eight PI-distribution assignments per parent produce384 training,64 support and192 query examples. Each graph has6 independent Bernoulli PIs; all support examples are fully node-labeled, not just output-labeled. Parents/views never cross splits. Structural identity hashes are disjoint; Boolean-function/isomorphism disjointness is not asserted. Held-out parents are input-negation variants of four hardware templates, rather than24 independent industrial design templates.

The source PM model has417,761 parameters: hidden128,8 heads,2 Transformer layers,1 forward round, truth-table operator features and learned port positions. Six paired pretraining runs use240 updates each. Each family/seed/arm then branches from the same pretrained state for20 support updates, against its untouched0-update copy. Official-weight and random-weight FSL models receive the same20-update support budget in a separate transfer comparison; the original checkpoint's inherited training cost is unknown and not counted as free training.

No additional package, checkpoint or dataset downloads were needed. The already-present official PM asset was exported from the local Git object store, SHA256 `19fe1e95857072e5eb838802ee21260ffe48345df85785f9f6ddd0e784cad7c0`, epoch metadata50. Loading used `weights_only=True` and strict matching of all64 state entries. This verifies architecture/asset compatibility, not industrial-domain preprocessing equivalence.

## Main evidence

Seed mean ± sample SD of macro family terminal-output MAE:

| Method | No adaptation |20 support updates/family |
|---|---:|---:|
| Direct-target, source backbone |0.115395 ±0.009236 |0.083105 ±0.008398 |
| FSL, source backbone |0.048243 ±0.001094 |0.047170 ±0.001908 |
| Official PM checkpoint, FSL |0.044879 |0.041842 ±0.000215 |
| Random initialization, FSL without pretraining |0.300723 ±0.214000 |0.218462 ±0.177123 |
| Exact local independence approximation |0.049009 |No adaptation |

The local approximation is a strong baseline. FSL's learned improvement over it is small here; the official checkpoint's improvement is larger but still synthetic-domain evidence. Adaptation helps aggregate output error, but not every family: official-checkpoint comparator error worsens0.041438→0.043004, while reconvergent-MUX improves0.079718→0.065954. Main FSL's non-PI MAE0.031978 is worse than local-only0.028684; adapted official weights achieve0.027760. No across-the-board advantage is claimed. Official no-adaptation repetitions use the same checkpoint; a zero SD there is not an uncertainty estimate.

## Why the first pilot's metrics disagreed

`diagnose_v1.py` reloads both preserved v1 checkpoints and reproduces every saved prediction exactly. Its result is `V1_DIAGNOSIS.json`.

- V1 FSL's low average node MAE came substantially from NOT nodes:0.010161 error versus direct0.070344 across48 NOT nodes. The AIG FSL recurrence implements NOT analytically; direct prediction learned it. On112 AND nodes, FSL was worse:0.093149 versus0.085063.
- Terminal nodes were ANDs. V1 FSL terminal MAE0.128100 fell to0.110069 when true predecessor marginals replaced recursive estimates. Propagation contributed to the problem, but even that inaccessible oracle diagnostic remained worse than direct0.079770. The reversal cannot be explained solely by error accumulation.
- In v2, main FSL terminal MAE0.047170 becomes0.024094 under the same oracle-predecessor diagnostic. The actual-prediction versus oracle-prediction gap is0.027051. Intermediate-node averaging and terminal recursion measure different behavior. These are diagnostic comparisons, not deployable scores or a causal proof.

V2 changes the source modality/backbone, feature encoding, task families, capacity and sampling from v1. Its improved ranking does not establish which change caused it. Within v2, direct/FSL comparisons share architecture, data, initialization seeds and optimizer budgets.

## Independent checks and negative controls

- Labels: bit-parallel truth vectors versus independent recursive Boolean evaluation with Fraction arithmetic agree within1.45e-15 over all640 examples. No random simulation or learned labeler.
- Local-function encoding agrees with the original `_cop` within1.2e-7. Oracle residual reconstruction matches labels. The original PM `_cop_with_cov` skips its deepest level (`range(1,max_level)`); it returned zero on the tested terminal outputs, with max error0.83673. The new recurrence follows the paper's inclusive level traversal. Original source remains unchanged and its failure is recorded.
- Independent saved-output verification checked96 prediction files, recomputing local truth-table expectations and metrics without training's polynomial implementation. Max recurrence difference3.30e-7; metric difference6.31e-8. All2400 valid updates are journaled.
- Hidden intermediate-label poisoning, raw-output node renaming and normalized edge-order controls pass for all48 adapted states. Complete prediction renaming/reload checks pass on all24 saved main adapted states, max difference0. Source edge grouping is enforced by explicit port metadata, not numeric node IDs.
- MUX role-change target delta0.54: mean pipeline delta0.539962 for main FSL and0.402776 for direct. FSL's analytic local function itself supplies the role dependence; this does **not** isolate learned Transformer role reasoning. Direct's AND port-swap discrepancy0.028166 shows imperfect learned commutative consistency.
- Equal-marginal aliasing: shared-PI and independent-PI reconvergent graphs with exact outputs0.125 and0.0625 produced identical final embeddings (difference0) in the unchanged backbone. PI identity is not explicitly encoded. This observed limitation remains unresolved; no performance claim contradicts it.
- Adapted official FSL produced7 out-of-range query-node values across6432 evaluated nodes, retained without final clipping. The random transfer control produced676. Raw values and ranges remain saved.

## Implementation identity and scope

Original implementation: unchanged AST-extracted official `MLP`, `PlainMLP`, `TRACE` classes and official PM checkpoint. Faithful task port: plain torch training orchestration, explicit port adapter, exact truth-table synthetic labels and inclusive paper recurrence. New baselines/extensions: sigmoid direct-target interpretation, matched support adaptation/no-adaptation protocol, random-initialization transfer control, independent oracle diagnostics. Few-shot adaptation is an evaluation extension requested here, not claimed as an original TRACE paper protocol.

Source version is `b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70`; paper reference is [arXiv2509.21886v3](https://arxiv.org/html/2509.21886v3). All source/data/protocol/checkpoint hashes and environment versions are saved in SOURCE_VERSIONS.json; prior environment pins remain in ../pilot/requirements-cpu-lock.txt.

Remaining gap: industrial-scale predictive results, sequential/similarity/transition tasks, contrastive retrieval and cross-modal correspondence are not established. The previously403-blocked dataset metadata was not retried; reported9.28GB is still unverified. Full benchmark closure needs accessible verified assets/splits and measured compute. No extra resource is needed for the completed methodology loop. No paid services, external LLM calls, GPU, credentials/security changes, push, PR or publication.

## Re-run and evidence preservation

From `P11_TRACE/closure`, using the existing pinned CPU venv:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 ../pilot/.venv/bin/python run_closure.py
../pilot/.venv/bin/python verify_closure.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 ../pilot/.venv/bin/python check_pipeline_controls.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 ../pilot/.venv/bin/python diagnose_v1.py
../pilot/.venv/bin/python summarize.py
```

For an independent fresh run, copy closure's sources, protocol, frozen data and official asset into a new local output directory first; the runner appends journals and writes deterministic artifact filenames. Never mix two runs' journals for verification. A fresh isolated dependency install is documented in the prior reproduction report but was not repeated.

Two interrupted harness attempts and their weights/predictions are preserved in `attempt1_invalid_direct_clamp/` and `attempt2_unpaired_dropout/`. They are excluded from aggregate scores for explicit correctness reasons, not poor performance. ATTEMPTS.jsonl records why. No HPO/test-selected seed, shortened valid budget or hidden failure.

## Targeted evidence audit

See [evidence_packet/EVIDENCE_PACKET.md](evidence_packet/EVIDENCE_PACKET.md) for unmodified-source minimal examples, identity-preserving repeated-edge checks, exact label budgets, final run provenance and all per-seed paired results. FSL is function-shift learning; support adaptation is a separate evaluation. No new training was performed.

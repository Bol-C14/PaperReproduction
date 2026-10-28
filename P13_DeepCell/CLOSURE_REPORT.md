# DeepCell: closest feasible CPU methodology closure

Implemented and executed a learned representation-to-functional-ECO loop, with independent patch checking and a real public ABC/netlist extension. **The controlled runs do not establish a useful paired-view pruning advantage.** They establish executable learning, patch synthesis and correctness checks; the paper's original accuracy, runtime and technology-mapping results remain unreproduced.

The minimum multiview mechanism has been independently reconstructed and run. The historical asset audit remains valid for the original release; the full-paper route still has L3 asset/integration gaps. No GPU/Runpod, paid resource, external model API, credentials, gated agreement, upload, push or PR was used.

Reference: [paper v2](https://arxiv.org/html/2502.06816v2), [official fusion model](https://github.com/zshi0616/DeepCell/blob/b82aef22559c6d8c52eb4feb437ebdd32709360e/deepcell/top_model.py), [official reconstruction trainer](https://github.com/zshi0616/DeepCell/blob/b82aef22559c6d8c52eb4feb437ebdd32709360e/deepcell/top_trainer.py). Title history and original asset evidence remain in [ASSET_AUDIT.md](ASSET_AUDIT.md).

## Executed loop

1. Use unchanged official 128+128-dimensional PM/AIG DG2 encoders. PM checkpoint loads its full 56 state tensors; AIG loads all 64 encoder/readout tensors after explicitly removing the unprovided auxiliary connectivity head (the full class still lacks 16 tensors). Frozen AIG, trainable PM.
2. Generate 216 semantically verified paired graphs from 108 distinct six-input parent functions. Training 144 variants/72 parents from parity/muxbank/arithmetic; validation 24/12 from conditional; testing 48/24 from majority/comparator. Families, parent descendants and full truth functions are disjoint across splits. Every case agrees with separate Boolean expressions and AIG evaluation on 64 input assignments. Synthetic cells and SOP lowering substitute for original Liberty/commercial mapping assets.
3. Probability adaptation 2 epochs; four-hop cone MCM 6 epochs; ECO finetuning 6 epochs, batch 4, Adam 1e-4. Fusion retains the full 4-layer, 8-head, 256-channel Transformer shape. All 5 primary arms use both seeds 208/209 with no early stopping, tuning or winner selection.
4. Erase one known cell's pins/function from the observed PM. Refine with the golden AIG, learn candidate ancestry ranking with BCE plus teacher reconstruction, and send ranked candidates to a separate exact repair engine. The engine derives patch requirements by comparing whole-circuit outputs under patch 0/1 to golden outputs. It receives no hidden golden-PM function/pin/ancestry labels or internal cross-view map at inference.
5. Synthesize explicit AND/NOT patches when top-three prefix constraints are feasible. Independently evaluate all resulting full circuits and retain failures. Oracle direct-fanin and PI fallback are separately labelled, privileged/correctness baselines.

Source, configuration, data/checkpoint hashes, complete curves and failed-attempt logs are retained. [Protocol](closure/PROTOCOL.md), [correctness amendment](closure/AMENDMENTS.md), [coverage map](closure/MECHANISM_COVERAGE.md), [replay commands](closure/REPLAY.md), and [command ledger](closure/COMMANDS.md) are the inspectable record.

## Primary controlled comparison

The first declared experiment reconstructs functional channels. The stage2 probability MAE uses common exact-probability units; reconstruction L1 is in each model's learned latent space and does not alone demonstrate semantic quality.

| Arm | Held-out ECO success at3 | Stage2 probability MAE | Functional reconstruction L1 |
|---|---:|---:|---:|
| `paired_pretrained` | 6/96 (6.25%) | 0.0991 | 0.0411 |
| `pm_only` | 9/96 (9.38%) | 0.1011 | 0.0405 |
| `shuffled_aig` | 7/96 (7.29%) | 0.0931 | 0.0403 |
| `paired_random` | 5/96 (5.21%) | 0.1659 | 0.0487 |
| `no_mcm` | 12/96 (12.50%) | 0.0883 | 0.9107 |

Each arm has 96 trials = 48 cases x 2 seeds; these are **24 parent-function units**, not 96 independent designs. Paired minus PM-only success is -3.12 percentage points; the descriptive parent-cluster bootstrap 95% interval is [-7.29, 1.04] points. Only two held-out families are covered.

On 48 test cases, fixed random ranking solves 2/48, reverse-topological 13/48, privileged direct-fanin oracle 48/48, and the separate six-PI fallback 48/48. The oracle confirms that feasible compact repairs exist; it does not represent learned performance. The learned paired model averages about 20.8 ms ranking plus 2.0 ms exact solving here. These tiny workloads and overlapping ABC build do not support a speedup claim.

Wrong-parent AIG counterfactuals change 72/96 rankings but solve 7/96 versus 6/96 with correct views. That establishes input sensitivity without a useful paired-context benefit. Shuffling also changes context length and the shared PI initialization relation, so this is a broad corruption control. Random-start encoders receive the same PM optimization schedule and a frozen random AIG; their higher probability error measures a warm-start contribution in this setup, not a clean equal-pretraining comparison or demonstrated downstream benefit.

## Full-token source-fidelity sensitivity

The public trainer applies reconstruction L1 to full returned structural+functional tokens. A separately declared sensitivity therefore repeats paired and PM-only for both seeds with the full 256-channel MCM and ECO teacher target, leaving the primary experiment intact. It is post-primary, predeclared before these four runs, and never used to select a better result.

| Full-token arm | Held-out ECO success at3 | Stage2 probability MAE | Functional RE metric |
|---|---:|---:|---:|
| `paired_pretrained` | 10/96 (10.42%) | 0.0976 | 0.2370 |
| `pm_only` | 12/96 (12.50%) | 0.0976 | 0.2303 |

Full-token paired minus PM-only success is -2.08 points, with descriptive 24-parent bootstrap interval [-6.25, 0.00]. See [separate protocol](closure/FULL_TOKEN_PROTOCOL.md), [source diff](closure/full_token_changes.patch), and [full-token results](closure/results/full_token/controlled_comparison.json). No primary-control row is silently relabelled as full-token training.

## Independent correctness and real tool execution

The separate checker imports neither trainer nor solver. It executes patch gates recursively, evaluates PM cell Boolean operations directly without trusting stored cell truth tables, and compares whole-circuit outputs with separately generated parent truth signatures. **All 207 primary/control/baseline patches (13,248 assignments) and all 168 full-token patches (10,752 assignments) pass.** Deliberately inverted patches produce counterexamples. All 48 principal held-out rankings and repairs are reproduced after removing hidden golden PM, cell function/pins, internal correspondence, ancestry/probability labels and family-oracle specification from inputs. [Primary replay evidence](closure/results/main/independent_verification.json), [full-token replay](closure/results/full_token/independent_verification.json), [inference separation](closure/results/main/public_input_noninterference.json).

A separately bounded public-flow extension builds upstream ABC commit `ba65576141a5a0f605d2876ad5041e3ec7dfbf59` locally. It reads EPFL `ctrl.blif` from benchmark commit `82d8cc6910419298e713a46644ed59fd3df53038`, maps with an explicit unit-cost teaching genlib, and converts PM back through actual `strash`. Parsed views contain 167 PM and 266 explicit AIG nodes, 7 inputs and 26 outputs. All 128 assignments agree with the original public BLIF; **ABC CEC proves mapping equivalence**.

Four nontrivial patch sites are fixed at index quantiles before model scoring. No model is trained on this public circuit. Primary frozen models solve 0/32 top-three trials across 8 model/seed combinations; random and reverse-topological controls solve 0/4 each. Direct-fanin oracle and seven-PI fallback each emit 4/4 repairs; **all 8 actual patch BLIFs pass 128-assignment checks and ABC CEC against the original public circuit**. Full-token frozen paired/PM-only models solve 0/16 additional trials at the same sites; their complete results and baseline proofs are retained separately. A deliberately inverted public output is confirmed **NOT EQUIVALENT** by ABC with a counterexample; the harness checks proof text because ABC can return process exit 0 for failed equivalence.

This is an actual baseline mapping/functional repair flow, not the authors' DeepCell-enhanced `&nf` or `runeco` implementation. Teaching library costs/delays have no foundry significance, so no PPA/physical timing ECO result is claimed. Original pretraining exposure to EPFL remains unknown even though this CPU training used only synthetic families. [Public flow](closure/external/results/flow_results.json), [full-token public flow](closure/external/results/full_token/flow_results.json), [negative formal control](closure/external/results/negative_formal_control.json), and emitted repair BLIFs are saved locally.

## Costs, errors and remaining gaps

Across 14 successful model/seed runs there are 7,056 optimizer updates, plus 504 duplicate failed-attempt updates and 3 preflight updates. Main resumed process: 878.2s and 607.9MiB peak RSS; full-token process: 411.4s and 602.7MiB. ABC build: 371.5s with two jobs. Observed environment-wide memory peak including build is 2.72GiB under the existing 16 GiB limit. This phase downloads only 9,825,361 bytes of public ABC source/README/benchmark payload, plus small unmetered git metadata. No new model weights or system installation. Costs overlap; adding wall times would overstate elapsed time. [Costs](closure/costs.json).

Two errors were repaired and preserved: verifier scheduling of legal later-serialized wires, and ABC's default LUT BENCH output requiring documented `write_bench -l` for the AND/NOT reader. These were correctness/format repairs, not response to model quality. Earlier IEEE/arXiv/wheel access restrictions were not bypassed; this phase encountered no new access denial.

The remaining boundary is original-result fidelity and effective transfer, not an inability to fit the model. Exact original paired corpus/split/parent lineage, Liberty/pin/tool recipes, original ECO corruption/label definitions, author-finetuned heads and modified ABC integration are still unverified. For mapping, the actual load/cell-type head, modified `&nf`, library corners and constraints remain essential. A GPU would not supply those assets; none is requested.

Our explicit substitutions include a single-cell cut, interpreted fan-in ancestry labels, tiny exact enumeration instead of SAT-scale ECO, reduced training, deterministic per-case/shared paired PI basis and synthetic teaching libraries. Low reconstruction error can reflect moving teacher embeddings and generic reconstruction; it did not establish a paired-view advantage here. The execution loop is closed and verified on these domains. Original paper performance/generalization claims remain open. Exact provision targets are listed in the [coverage/gap map](closure/MECHANISM_COVERAGE.md). Stop after this declared comparison and fidelity sensitivity.

# CircuitFusion methodology closure — CPU, real synthesis

**Outcome: the feasible end-to-end loop is closed, with a negative controlled result.** Correct pairing and the graph path do not show a consistent held-out advantage over trained graph removal, text-only or corrupted-edge controls at the frozen budget. This is evidence about this small port, not a finding that the paper is invalid. No extra resource is required for the completed loop.

## What actually ran

144 accepted designs: 95 training cones from 16 generated parent families, 48 test cones from 8 different generated families, and one unchanged open Yosys counter held out separately. One duplicate candidate was excluded before training. Family variants never cross splits; commutative canonical expression skeletons and complete truth tables do not overlap across splits. All code streams are complete (at most 75 tokens), not artificially truncated. The training set covers test graph types; three unknown HDL tokens occur only in the external 3-bit counter.

Each sequential Verilog design goes through actual Yosys `proc`, explicit DFF D/Q boundary extraction, equivalent RTL optimization, `techmap`, ABC Boolean mapping, independent gate evaluation, formal equivalence, multimodal training, held-out retrieval, and train-pool-only retrieval-augmented structural-proxy regression. All 144 formal proofs have per-design evidence. Native GCC evaluation agrees byte-for-byte on 2,342,944 input cases; the Python reference/operator/gate checks cover 7,028,832 input/view comparisons. Corrected graph tensors distinguish all 144 functions. Arbitrary node-order changes preserve model outputs; graph-removed outputs are independent of graph inputs.

The learned port includes full HDL GRU states, directed graph message passing with operand/output bit positions, summary-query cross-attention, equivalent-view contrastive learning, graph/summary multi-positive contrastive learning, masked node/token reconstruction, summary matching, a learned gate encoder and RTL–gate alignment. All weights start randomly. It is a scaled mechanism port, not execution of the original foundation models. Gate count/depth targets are generated structural measurements, never relabeled as physical PPA.

## Removing summary-template leakage

The old AST-verbalization summaries are not used. New descriptions use only coarse input/output properties, state dependence and bit activity: four classes across 144 samples (largest class 109). They include no AST, operation names, constants, circuit IDs, paths, gate counts or depths. Identical summaries are treated as multi-positive and are not deliberately mislabeled as mismatches. These descriptions are explicitly **heuristics, not LLM-generated natural-language summaries**. Their loss of semantic detail is a real fidelity limit.

The counter has no data operands. A later correctness audit found its generic operand-exchange sentence inapplicable. That sentence was removed in a separately logged checkpoint-only evaluation; training and the primary 48-cone results are unchanged. Raw original evaluation remains preserved, and corrected external results are reported separately.

## Matched-budget results

Each corrected arm used the same three seeds (11,23,37), 400 minibatches, batch size 16, width 32, optimizer, learning rate and shared sample schedule: 6,000 updates in 15 runs. Controls were fixed before corrected training. Shared allocated modules match parameter counts; graph removal and text-only have fewer active gradient parameters and lower FLOPs, which are reported. Shuffled edges retains the full graph modules/losses. No best-seed selection or outcome-driven hyperparameter tuning.

Primary queries: 48 cones in eight held-out generated parents, ranked against 49 held-out gate candidates. Chance Recall@1 = 2.04%, Recall@5 = 10.20%.

| Arm | Recall@1 | Recall@5 | Recall@1 seeds 11 / 23 / 37 | Active gradient parameters |
|---|---:|---:|---|---|
| paired | 3.47% | 15.97% | 2.08% / 6.25% / 2.08% | [63554] |
| shuffled_pairing | 2.08% | 16.67% | 2.08% / 4.17% / 0.00% | [63554] |
| no_graph | 1.39% | 24.31% | 0.00% / 2.08% / 2.08% | [44741] |
| text_only | 2.78% | 19.44% | 6.25% / 2.08% / 0.00% | [41541] |
| shuffled_edges | 2.78% | 15.28% | 2.08% / 2.08% / 4.17% | [63554] |

| Paired minus control, Recall@1 | Mean difference | Exploratory 95% parent bootstrap |
|---|---:|---|
| shuffled_pairing | +1.39 pp | [-1.39, +4.86] pp |
| no_graph | +2.08 pp | [-1.39, +5.56] pp |
| text_only | +0.69 pp | [-3.47, +5.56] pp |
| shuffled_edges | +0.69 pp | [-3.47, +4.86] pp |

Intervals resample eight parent families, averaging predeclared seeds, rather than treating cones as independent. This small synthetic-family universe is not population-level evidence. The counter has one cone and cannot substantiate broad real-RTL generalization.

| Corrected external counter | Recall@1 by seed | Recall@5 by seed |
|---|---|---|
| paired | [1, 0, 0] | [1, 0, 0] |
| shuffled_pairing | [1, 0, 0] | [1, 0, 0] |
| no_graph | [0, 0, 0] | [0, 0, 0] |
| text_only | [0, 0, 0] | [0, 0, 0] |
| shuffled_edges | [0, 0, 0] | [0, 0, 0] |

## Downstream closure: structural proxies, not PPA

Known-circuit retrieval uses only training-family RTL embeddings and measured gate count/depth. Training queries exclude the entire own parent family; held-out queries use training parents only. All predictors share available RTL operator counts. Targets are log1p transformed; a fixed alpha=1 ridge model is fitted using training data only. Counts-only is a new cheap baseline; text-only embeddings plus counts also receive counts, which are reported transparently.

| Arm | Embedding + counts MAE (log1p gate count / depth) | Retrieval-augmented MAE |
|---|---|---|
| paired | 0.2397 / 0.2036 | 0.2563 / 0.2022 |
| shuffled_pairing | 0.2567 / 0.1949 | 0.3039 / 0.2164 |
| no_graph | 0.1744 / 0.1485 | 0.1668 / 0.1491 |
| text_only | 0.1849 / 0.1313 | 0.1897 / 0.1302 |
| shuffled_edges | 0.2255 / 0.1427 | 0.2233 / 0.1595 |

Shared counts-only MAE: 0.2456 / 0.1738. No target or count from a test netlist enters any downstream prediction. The supplied test gate netlists are used only as retrieval candidates in the separate cross-stage retrieval evaluation and as ground truth for scoring.

## Failures, repairs and limits

- Protocol 1.0 was stopped after three completed seed11 runs when independent checks proved 144 semantic functions collapsed to 81 graph tensors because aggregated word edges erased bit positions. The entire attempt, data, code, checkpoint and logs are preserved in `attempt1/`. Protocol 1.1 added explicit operand pins/output bits and actual alternate HDL augmentation before corrected training. Hyperparameters/seeds/steps were unchanged. Early incomplete results are not pooled with the corrected comparison.
- Initial YoWASP startup failed because its default cache location was read-only. A documented per-process writable task cache fixed it; no permissions or security settings changed. No GitHub API denial was bypassed. Two absent guessed ALU files were recorded as path-specific 404s; a third-party-borrowed source was excluded.
- The native and metric verifiers are independently written checks, not independent neural-network implementations. Checkpoint verification uses NumPy rank calculations and reconstructs train-only/family-excluded retrieval and ridge errors. All corrected runs must pass before this report is generated.
- Graph rewiring is deterministic for seed and batch position, preserves node and edge counts, and may produce cycles. It is a corrupted-input control, not a semantics-preserving circuit. Active losses/compute differ in removed-modality arms. The graph path is a three-layer directed message-passing substitute for the paper Graphormer, and the small GRUs replace pretrained 7B/BERT encoders.
- The earlier 66.7% synthetic retrieval result does not survive the stronger setup. Dataset, summaries, synthesis, representation and objectives changed together; this is not a causal estimate of summary leakage alone. The observed null should not be advertised as evidence against the paper.

## Resources, evidence and remaining gate

Corrected training/evaluation wall time: 743.15 seconds; peak training-process RSS: 631.8 MiB; PyTorch 2.14.1+cpu, two Torch CPU threads. The interrupted run and setup are additional costs and remain logged. Corrected preparation took 12.06 seconds; native checking 0.84 seconds. Tool compilation peak was not separately captured. New wheel payload about 26.8 MB; no weights/API/data-service downloads or costs. Compiled WASM cache is about 210 MiB and is excluded from Git.

The original code/audit, previous method port and this corrected real-synthesis port remain separate. Read `MECHANISM_COVERAGE.md`, `EXECUTION.md`, both protocols and `results_v1_1/metrics.json` for provenance and deviations. The official Yosys counter and ISC COPYING are stored with URL hashes. This tranche used no paid services, credentials, security changes, gated agreements, LLM calls, publication, push or PR.

**Remaining gap:** graph contribution and family-general semantic alignment remain unproven at this budget. A future predeclared comparison with a closer Graphormer/code encoder and broader licensed real RTL would test representation capacity and transfer. Original GPT summaries, 7B encoder/checkpoints, commercial constraints and PPA labels remain unavailable or outside this tranche. Full paper reproduction remains L3. The currently feasible controlled methodology loop is complete; no further scaling is launched.

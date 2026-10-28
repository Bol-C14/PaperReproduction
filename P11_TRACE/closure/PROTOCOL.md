# TRACE closure protocol v2 — frozen before experiments

2026-10-28. Earlier v1 evidence immutable. No repository AGENTS.md or .agents skills found; current branch reproduction/trace-dac2026. Scope is predictive probability/FSL method, not all DAC tasks.

## Mechanism and design

Use the official PM TRACE class definitions (MLP, PlainMLP, TRACE) extracted unchanged with Python AST from pinned source b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70. No Lightning shim. Hidden128, 8 heads, 2 Transformer layers, 1 forward round: shape-compatible official PM weights. Preserve 64-entry cell truth tables, ordered ports/positional embeddings, level-by-level updates. Paper-faithful reconstruction includes every level; test original reconstruction separately against oracle labels. No final probability clipping. Direct uses a sigmoid head interpretation; FSL uses source clamp [-1,1] and reconstructs using predicted predecessor marginals.

Independent label paths: training labels via bit-parallel truth vectors and Bernoulli-weighted enumeration (6 PIs, 64 assignments); verification via recursive scalar Boolean evaluation and Fraction-weighted enumeration. Oracle residual = true marginal minus operator truth-table independence function of true predecessor marginals. Only primary input probabilities enter the encoder; non-PI probability fields zeroed. Check poisoned hidden labels do not affect raw inference.

## Frozen data split

All graphs are combinational Boolean cell graphs, no EDA. 6 primary inputs; bounded families constructed from INV, AND, OR, XOR, XNOR, MUX, MAJ. 8 deterministic PI-distribution vectors per parent from {0.1,0.3,0.5,0.7,0.9}^6. Each parent has a unique input-negation mask within its family; entire parent and all views remain in one split. Training: 3 families (random DAG, chain, balanced tree), 16 parents each =384 assignments. Held-out composition families: 2-bit ripple carry, 3-bit comparator, priority selector, reconvergent MUX; each 8 parents, first2 support (16 labeled assignments/family), remaining6 query (48/family). Training families never appear as support/query families. Serialize full graphs, port order, labels, parent metadata and split before optimization. Verify no exact graph identity overlap; no Boolean-function-disjoint claim.

## Fixed budget and comparisons

Seeds 2026,2027,2028. Main arms scratch-direct and scratch-FSL: same full source model architecture, seed/init, training data order, Adam lr0.001, batch16, 240 pretrain updates, no test selection/early stopping. For each held-out family branch from the same pretrained state, adapt on that family's support only for20 updates, Adam lr0.0001, batch16 (all support), same paired seed. Evaluate identical query examples before/after; no-adaptation baseline is exact copied model with0 support updates. Adapt all parameters; record inherited pretraining cost separately. All support labels share the same oracle budget across arms.

Official-checkpoint transfer track: source PM FSL checkpoint SHA256 19fe1e95857072e5eb838802ee21260ffe48345df85785f9f6ddd0e784cad7c0 loaded weights_only=True with strict keys. Evaluate zero-shot and20 support updates per family/seed. Compare to random-initialized same-shape FSL with20 support updates (no source pretraining); inherited checkpoint training cost unknown, so only incremental adaptation budgets matched. Do not initialize direct arm with residual-trained weights. Official industrial preprocessing exactness remains unverified; use known cell truth-table semantics/source compatibility checks, report synthetic domain shift.

Pilot execution is the first20 pretraining updates of seed2026/direct, retained as part of240 (no duplicate run); inspect cost and finite loss only, no held-out outcomes. If projected total >30 CPU-minutes or RSS>4GiB, stop and report cap, do not silently shrink. One CPU thread. Global wall limit30min, no GPU/downloads/API/services. No hyperparameter search or test-driven changes.

## Evaluation and diagnosis

Primary metric: macro family terminal-output MAE on held-out query parents. Also non-PI MAE, family/parent MAE, per-depth MAE, worst-family MAE and fraction outside[0,1]. Report seed means and sample SD (3 seeds descriptive only); support/query costs, optimizer steps, parameter counts, batched inference time and end-to-end wall/RSS. Save all query-node predictions and per-step loss.

For FSL at every evaluation compute (a) actual recursive prediction and (b) diagnostic teacher-predecessor reconstruction using true input marginals. Difference localizes propagated error; (b) uses inaccessible oracle information and is never a deployable score. Report residual target MAE, terminal residual error, recursive-vs-teacher discrepancy by depth/family; relate metric reversal to intermediate-node weighting versus terminal accumulation without claiming causation from correlation alone.

Controls: oracle residual reconstruction within1e-6; original deepest-level omission diagnostic; independent labels agreement within1e-10 before float conversion; randomized bijective node renaming with transported semantic metadata and canonical edge grouping, error<=1e-5; edge storage reorder normalized by explicit port; hidden target poisoning invariance; MUX select/data role swap with exact changed targets and learned response reported, not accuracy assumed; commutative AND swap reported as learned semantic consistency. Save one executable symmetry/aliasing diagnostic for equal-marginal PI shared-vs-independent reconvergence. Negative/failed controls remain recorded, not tuned away.

Close the loop when train, adapt, predict, independent evaluate, matched controls and honest scope map are saved; no paper benchmark/full-data claim.

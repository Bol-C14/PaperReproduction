# Counted checkpoint ablation on APRIL

This phase tests the released checkpoint with real AIGs, BERT recipe encoding,
native ABC mapping and equivalence checking. It does not reproduce training or
the paper's numerical benchmark. The frozen executable contract is
[ABLATION_PROTOCOL.json](ABLATION_PROTOCOL.json); source upstream remains
`db6186cb4018963b5bc15926772c3edc0c2873f1`.

## Training provenance and complete retrieval bank

The complete bank in this phase means all **22 circuits listed by released
`main.py` split5001**, not all 23 paper training circuits and not a proven list of
the checkpoint's actual training examples. The released checkpoint directory
names split5001 but supplies no verified run manifest connecting the weights to
that list, source revision, architecture, seed or preprocessing history. The
source/paper discrepancy includes `c6288`; inserting that circuit would silently
assert a training provenance we do not have. The bank uses only the source
training list; neither evaluated circuit, `sin` or `cavlc`, enters it. This is not
proof that the unknown checkpoint training history excluded them.

Checkpoint SHA256 is
`d4747eeff16c7247acf8f1480a33f2239a1a51adaac78a0a6e915c5ba12164f5`.
All 26 tensors load strictly and match the supplied values. The checkpoint
contains the released two-layer graph encoder and heads, not the paper's
described three-layer architecture or BERT weights. The source unconditionally
rounds graph embeddings, blocking graph-encoder learning gradients in that
source version. None of these facts establishes how the saved weights were
trained. The canonical cased BERT snapshot is pinned to
`cd5ef92a9fb2f889e972770a36d4ed042daf221e`; it is not established as the historical
training snapshot. Inference retains source evaluation rounding and the original
recipe-token convention. No model is retrained or replaced with random features.

## Controls and actual execution budget

Two circuits, three seeds (566, 567, 568), five arms and twelve objective recipes
per arm produce 360 search evaluations. Two shared deterministic resyn2 baselines
bring the mapped ADP total to 362. Every generated AIG, including all losers and
baselines, receives CEC against the original, giving 724 planned ABC invocations.
Initialization is recipe zero, not a free uncounted evaluation. The 740-call cap
leaves 16 diagnostic calls; no failed candidate is replaced or retried.

| Arm | PUCT prior | Rollout starting action | Retrieval bank |
|---|---|---|---|
| unguided | uniform | independent uniform draw | none |
| policy_start | uniform | policy argmax | none |
| fixed | unnormalized policy | policy argmax | none |
| adaptive_full | unnormalized policy raised to beta | policy argmax | source22 |
| adaptive_subset | same adaptive rule | policy argmax | alu2, int2float |

`policy_start - unguided` isolates policy choice of rollout starting action;
`fixed - policy_start` tests policy PUCT priors with that start rule held fixed;
`adaptive_full - fixed` tests the gate against full guidance;
`adaptive_full - adaptive_subset` tests the bank expansion under the same gate.
These are paired executed comparisons, not inferred counterfactual rewards.
Source PUCT constant 1.38 and unnormalized prior exponentiation are preserved;
changing beta therefore changes both relative action weights and total
exploration weight. This is part of the released method, not a separately
identified novelty-only effect.

Each seed/arm draws the same full-horizon random suffix vector at each iteration.
A separate start-action RNG avoids consuming suffix randomness only in the
unguided arm. Different tree prefixes can use different suffix positions;
identical full recipes are not guaranteed. Arm order rotates by seed. Lazy tree
prefixes use original-graph features plus recipe tokens; full candidate recipes
are actually materialized and measured in native ABC. There are no hidden
per-prefix synthesis calls. Upstream `MCTSNode` selection and Monte Carlo backup
are used, with actual rollout reward in both backup channels as in released
synergy search. Learned value predictions do not drive this search. This bounded
single-root search does not reproduce the full original per-depth schedule.

## Graph-lifecycle defect and interpretation of the earlier pilot

The first full-bank attempt failed before objective evaluation on apex5 because
the sparse adjacency inferred unequal dimensions. Explicit node-count dimensions
then exposed out-of-range edge endpoints. A native audit identified the root
cause in pinned abc_py: `updateGraph()` resizes and reuses its node vector, while
`configureNodeFromAbc()` does not clear old fanins when a node becomes a PI or
constant in a subsequent circuit. For apex5 after apex3, the shared interface
reported 44 out-of-range fanin entries; a fresh interface reported zero.

The corrected runner creates and closes a fresh native interface per circuit,
never overlaps native contexts, checks every edge bound, and explicitly declares
the square adjacency size. A 48-read comparison covers all 24 circuits. An
earlier diagnostic that overlapped contexts exited255 without complete output;
its precise number of graph reads is uncertain. It made no subprocess synthesis
or objective invocation. Both failed search attempts made zero objective/CEC
calls and remain preserved with their original protocols and logs. Graph reads
are counted separately from ABC synthesis subprocesses.

The old four-circuit pilot reused an interface. Its retrieval embeddings and
gates therefore require reassessment, even where stale edges remained in range.
Preservation of its values after the square-shape fix only proved that fix alone
was compatible; it did not validate the old graph lifecycle. Its independently
executed candidate ADP and CEC logs remain evidence for those specific recipes.
They cannot establish an uncontaminated retrieval effect. New comparisons use
fresh graphs in every arm and both banks, so bank size is not confounded by old
versus corrected graph extraction.

## Reporting and correctness

Report every seed and arm, all candidates and the best-so-far curve at each
counted recipe. Summarize median best ADP reduction and range across the three
seeds, plus paired per-seed differences. Three seeds on two circuits do not
support broad statistical superiority, a dataset-wide ranking, or a reliable
distance/usefulness correlation. Gate threshold .007 and scaling100 remain
fixed, with no tuning against these results.

Invalid mappings or failed CEC get reward -1 and cannot be selected as valid
best results. Failure logs and spent calls remain in the ledger. CEC certifies
each un-mapped recipe AIG; mapped library netlists are not separately certified.
ADP is from the author's 7nm `map; topo; stime` flow, not measured silicon PPA.
Setup, graph extraction, inference and evaluation time are recorded separately
where available. Native versions and asset hashes accompany the evidence.

All work is CPU only, one process on CPUs0-7 with eight-thread caps and substantial
shared-machine headroom. No API request, GPU resource, local generative LLM,
global dependency change or credential change is part of this phase. Public
training AIG downloads use fixed upstream raw URLs, no credentials and no retry;
original circuit/model/library binaries remain outside Git. Source code and
repairs retain upstream GPL-3.0, and no separate redistribution permission is
asserted for external binary assets.

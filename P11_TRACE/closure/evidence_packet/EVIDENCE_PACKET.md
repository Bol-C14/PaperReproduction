# TRACE targeted scientific evidence packet

FSL means **function-shift learning**. Few-shot support adaptation is an added evaluation, not the expansion of FSL. This packet audits existing evidence; it adds no optimizer updates, data sweep or hyperparameter search.

## 1. Deepest-level omission: upstream body, minimal executed example

Pinned upstream: `b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70`, [tasks/predictive/pm/models/trace_trainer.py, lines139–151](https://github.com/zyzheng17/TRACE_DAC26/blob/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/tasks/predictive/pm/models/trace_trainer.py#L139-L151). File SHA256 `0e541bd719ebd5b19cc851af259a15a766cda0254101566b2dc288d64c411d68` matches the local upstream snapshot byte-for-byte.

The original code at lines142–143 is:

```python
max_level = torch.max(graph.forward_level)
for level in range(1, max_level):
```

The minimal graph has three nodes: `0=x`, `1=y`, `2=AND(x,y)`; edges `(0,2,port0),(1,2,port1)`, levels `[0,0,1]`, PI probabilities `[0.5,0.5]`. The original loop is empty, leaving output probability zero. A separate copied function changes only the bound assignment to `torch.max(graph.forward_level) + 1`.

| Identical input / residual condition | Unmodified upstream output vector | Corrected bound output vector |
|---|---|---|
| Zero shift (independent-AND oracle) | `[0.5,0.5,0]` | `[0.5,0.5,0.25]` |
| Same official checkpoint / same predicted shifts | `[0.5,0.5,0]` | `[0.5,0.5,0.2500006854534149]` |

The official AND shift was `6.839688921900233e-7`. State SHA256 stayed `29455ba5ceef368ac976e93fd439c6f6df73774cdc14218403a0864a3c1c78dc` before/after both evaluations. Same tensor graph and shift array were passed to both functions; model classes/weights were not changed.

`focused_checks.py` imports the **entire unchanged source file**, then invokes its original method. A declared inert `pytorch_lightning.LightningModule=nn.Module` symbol supplies the trainer class's base for import only; no trainer constructor, Lightning orchestration or overridden method executes. This is a source-method execution check, not validation of a full Lightning installation. The corrected function is saved separately. Raw evidence: DEEPEST_LEVEL.json and focused_checks.log.

Attribution: this loop bound occurs in the pinned upstream method. The direct-sigmoid/residual-clamp and dropout-pairing errors below were **local harness defects**; they are not attributed to upstream.

## 2. Equal-marginal ambiguity: graph identity is retained

The minimal pair uses the same three node IDs and PI identities `x0,x1`, each PI probability0.5:

- Shared repeated input: `AND(x0,x0)` with tensor `edge_index=[[0,0],[2,2]]` and ports0,1. Exact probability0.5.
- Distinct inputs: `AND(x0,x1)` with tensor `edge_index=[[0,1],[2,2]]` and ports0,1. Exact probability0.25.

The edge tensors differ. Repeated edges survive an asserted JSON→tensor round trip unchanged; conversion uses raw ordered edge lists, with no coalescing/deduplication or graph-library serialization. The source's two operand tokens are nevertheless identical: line57 initializes both PIs from the same marginal value, with no semantic PI identity channel. Both input sequences (including positional encoding) and final output embeddings had max difference **0**.

A second pair preserves shared fanout rather than duplicate edge columns:

```text
shared:      a=AND(x0,x1); b=AND(x0,x2); z=AND(a,b) -> P(z)=0.125
independent: a=AND(x0,x1); b=AND(x2,x3); z=AND(a,b) -> P(z)=0.0625
```

All six PIs exist with distinct semantic IDs and marginal0.5; nodes6,7,8 are a,b,z. Edge lists differ and retain all six columns. Again, operator sequences and output embeddings have difference0.

Both pairs were checked with **seven actual states**: the official PM checkpoint and all six saved direct/function-shift pretrained states (three seeds). All14 state/pair checks preserved distinct graphs but produced identical embeddings. IDENTITY_GRAPHS.json contains every node, semantic ID, edge, port and level; EQUAL_MARGINAL.json contains the observed tensors and hook comparisons. This rules out serialization information loss in these examples. The limitation is specific to this PM encoder's equal-marginal PI initialization and local computation; it is not a claim about every TRACE modality or PI encoding.

## 3. Splits, labels and paired comparisons

| Split | Families / parents | Graph-distribution assignments | Non-PI label entries (node×assignment) |
|---|---|---:|---:|
| Train | random DAG, chain, balanced;16 parents each |384 |3920 |
| Support | four held-out families;2 parents each |64 |640 |
| Query | same four held-out families;6 different parents each |192 |2144 |

Each parent has eight PI-distribution assignments. Held-out families are ripple carry, comparator, priority selector and reconvergent MUX; their parents are input-negation variants of four templates, not24 independent industrial designs. Each support family contributes16 **fully node-labeled** assignments:160,224,96,160 non-PI labels respectively. This is not16 scalar labels. Direct and function-shift arms share the same label information; shift labels derive from those marginals. All exact parent/sample IDs, node counts and reconstructed sampled-label presentation counts are in SPLIT_LABEL_BUDGET.json.

Each seed/arm:240 pretrain steps×16 graphs, then independently20 support steps×16 graphs/family versus its unchanged0-step model. Unique train coverage is all384 assignments for every seed. Non-PI scalar supervision presentations during pretraining were39209,39081,39344 for seeds2026,2027,2028, identically paired across arms. Per-family adaptation repeats the unique non-PI labels20 times:3200,4480,1920,3200 presentations.

PAIRED_RESULTS.md provides every main direct/function-shift paired output and non-PI result by seed/family, including0→20 steps, plus the complete official/random transfer table. PAIRED_RESULTS.csv stores the exact floats. No best seed/family/checkpoint is selected.

Macro family output MAE (seed mean±sample SD): direct adaptation `0.083105±0.008398`; function-shift adaptation `0.047170±0.001908`; local-only `0.049009`. Function-shift seed means were **0.0489813695,0.0473509943,0.0451777945**. The mean improvement over local-only is only0.001839, similar in scale to seed SD0.001908; no robustness or significance claim. Five of12 function-shift family/seed output comparisons worsen after adaptation. Non-PI MAE after function-shift adaptation is0.031978, worse than local-only0.028684.

Official checkpoint adaptation gives0.041842±0.000215, but this is **transfer with unknown inherited pretraining cost**. Only its incremental20-step support budget matches the random-initialization transfer arm. Official zero-step scores repeat identical weights; zero SD there does not establish certainty.

## 4. Final run and failure provenance

The valid run is committed in `76e5cb1761ba775c0927b77c97456333a9931331`; harness SHA256 `a50f6eda846553bb172bc8b669accb7e933da420832e989f77f6f342bda8d335` is unchanged by this audit. Protocol SHA256 `99a7e865ae0fbda4e2e0aad558b1c69201d008e3f1de400f883270cf6f09d946`; data SHA256 `ca22b243b7e8c34aa7ba847599452970057c8fed879f64019c7da32f59341e53`.

Final config: official PM model128 hidden/8 heads/2 Transformer layers/1 round,417761 parameters; Adam(default betas0.9/0.999, eps1e-8, weight decay0); L1 on all non-PI nodes; LR0.001 pretrain /0.0001 adaptation; one CPU thread. Direct is `sigmoid(unbounded readout)`; function shift clamps only the shift to[-1,1], then adds it to the recursively computed local function, without final probability clipping. PyTorch training RNG is reset at every training call: pretrain2026/2027/2028; paired adaptation2126/2127/2128. Original source dropout/BatchNorm behavior is retained. Exact2400 updates are journaled.

Hyperparameters, data, metric and step budgets were frozen before experiments. Invalid-attempt query scores existed before the two correctness repairs; no LR, step count, architecture, split or evaluation metric was selected from those scores. There was no HPO or test-based stopping. The fixes implement the declared baseline and RNG pairing; they are not evidence of an independently blinded rerun.

| Cost component | Wall / CPU / updates | Status |
|---|---|---|
| Historical dependency setup |~188.5MB rounded reported package transfers; process CPU/wall not separately instrumented |Earlier logs retained; not included in valid-run time |
| Invalid direct-clamp attempt |~26.66s wall (±1s),320 completed updates; CPU unknown |Archived, excluded |
| Invalid dropout-pairing attempt |~42.55s wall (±1s),580 persisted+0–19 unpersisted updates; CPU unknown |Archived, excluded |
| Valid run |158.652s wall,159.687s process CPU,2400 updates,357684KiB peak RSS |Included scientific comparison |
| This source/identity audit |1.238s measured inner wall,2.331s process CPU including imports,351724KiB RSS,0 updates |Seven states/two graph pairs; no new training |

The focused-check wall clock begins after imports, while process CPU includes imports; do not compare those two as identical timing boundaries. Valid pretraining time90.48s; adaptation47.34s; median batched-query inference0.0472s per48 graphs. Total interrupted-run CPU is unknown, not invented. Current setup reused the pinned venv; no new installation/download, GPU, external API/LLM, paid service, credentials/access change, push or PR. FINAL_RUN_PROVENANCE.json embeds config, per-tag steps, failures, prior resource accounting and hashes.

## Reproduce only these targeted checks

From this evidence_packet directory:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 ../../pilot/.venv/bin/python focused_checks.py
../../pilot/.venv/bin/python build_packet.py
```

These commands do not optimize a model. Prior industrial/full-task claims remain unverified; the packet supports only the stated reduced-data method execution and source/identity findings.

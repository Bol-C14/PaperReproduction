# Mechanism coverage map

FSL means **function-shift learning**. Few-shot support adaptation is a separate added evaluation, not the expansion of FSL.

| Paper mechanism / requirement | Existing v1 | Closure v2 execution | Implementation identity |
|---|---|---|---|
| Typed operator and intermediate state, causal levels | Tiny AIG trained | Native truth-table cell graphs, varied hardware families | Original official PM TRACE classes, unchanged extraction |
| Ordered operands, positional encoding, joint Transformer | Tutorial untrained, AIG AND-only no PE | Train/evaluate MUX-containing families; role and rename controls | Original official PM class with learned pos_enc |
| FSL global-minus-local training | Exact small AIG labels, 1seed | 3seeds,384 pretrain examples, held-out family support/query | Plain torch harness around original class; faithful task port |
| Recursive inference with predicted predecessors | Official AIG recurrence | Generic truth-table recurrence, include deepest level | Paper-faithful port; original PM recurrence separately checked |
| Independent correctness | Exact labels but shared evaluator | Bitvector versus recursive Fraction oracle; source local-function cross-check | Independent test implementation, not new predictive model |
| End-to-end adaptation | None | 20 support updates/family vs0, same checkpoint/query | New evaluation extension, not claimed as original paper protocol |
| Original pretrained asset | Not loaded | Strict-load official PM checkpoint; zero-adaptation /20 support updates versus random same shape | Original weights, synthetic domain caveat |
| Direct-target control | One seed, mixed output result | Same240+20steps, seeds/data/init paired with FSL; family/depth diagnosis | New matched baseline using original backbone |
| Industrial datasets, sequential prediction, contrastive retrieval | Audited only | Out of predictive closure scope | No full-paper claim; gated metadata not retried |

## Observed completion

All planned48 family comparisons and2400 valid updates completed across3seeds. Official PM weights strictly loaded (epoch50;64 state entries). Original-source deepest-level reconstruction failed the oracle control; the inclusive paper port passed.96 saved prediction files passed independent recurrence/metric checks;24 main adapted checkpoints passed full-prediction rename/reload checks. Equal-marginal PI aliasing and imperfect learned AND commutative consistency remain observed limitations. FSL MUX role sensitivity partly comes from the analytic local function and is not isolated learned-backbone evidence. See CLOSURE_REPORT.md for costs, failures and scope.

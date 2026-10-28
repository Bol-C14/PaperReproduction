# TRACE claim audit — bounded pilot

FSL means **function-shift learning**. Few-shot support adaptation is a separate added evaluation, not the expansion of FSL.

| Claim | Evidence / status | Limit |
|---|---|---|
| Official lightweight code imports on CPU | Pass: torch 2.8.0+cpu, PyG 2.7.0; imports in RESULTS.jsonl | Full requirements and CUDA stack not installed/tested |
| Tutorial illustrates ordered hierarchical computation | Pass: four trace levels, node rename and edge reorder controls | Fresh random weights; not learned arithmetic |
| Function-shift labels/reconstruction are implemented faithfully on tiny AIGs | Pass: exact enumeration, contradiction/independent controls, official cov2prob oracle max error 1.2e-7 | Synthetic independent Bernoulli PIs; no sequential circuit labels |
| An actual residual-learning pilot completed | Pass: 120 optimizer steps, train residual L1 0.103736 -> 0.055526; saved weights/predictions | Reduced official encoder, plain harness/head, one seed |
| FSL beats direct learning generally | **Unsupported**: FSL non-PI MAE 0.068253 vs direct 0.080647, but terminal-output MAE 0.128100 vs direct 0.079770 | Four held-out parents; mixed result, no uncertainty estimate |
| FSL always returns valid probabilities | **False in this pilot**: 5 training-node predictions outside [0,1], min -0.048004 | Test set had none; un-clamped reconstruction recorded |
| Node renaming preserves model output | Pass on frozen tutorial/learned AIG examples, max difference 0 | Metadata/semantic roles transported; not a universal proof |
| Model learned MUX or SUB input roles | **Not tested / unsupported** | MUX semantic oracle only; SUB sensitivity was untrained. AIG learning uses commutative AND and unary NOT |
| Split avoids parent leakage | Pass: 8 train parents, 4 test, all views inherit parent; serialized topology hashes disjoint | Functional/isomorphic overlap not excluded |
| Three graph modalities give cross-layer correspondence | **Not established** | No matching/alignment objective or data audited for this |
| DAC paper results reproduced | **Not claimed** | No industrial corpus, full configurations, baselines or full task suite |
| No extra resources needed for bounded pilot | Supported by completed CPU run | Full-paper assets and compute remain separate, unresolved |

Testable next gap (not executed): repeated seeds and structurally/functionally stronger held-out families could test whether mixed FSL gains persist. A separate matched PI-identity encoding control could investigate equal-marginal-input indistinguishability. These would require a new frozen protocol; this pilot was not expanded after observing results.

## Closure tranche findings (v2; original pilot evidence retained)

| Claim | Observed result | Limit |
|---|---|---|
| Train/adapt/predict/evaluate loop now closed |3seeds,4 held-out families,240+20 updates,48 family comparisons |Reduced-data combinational PM-style graphs; adaptation is a new evaluation extension |
| Actual official weights used |Strict64-entry load, epoch50, SHA pinned; adapted output MAE0.041842 |Industrial preprocessing/provenance beyond checkpoint metadata unverified |
| Learned FSL clearly beats local calculation |Only modest main output improvement0.049009→0.047170; main node MAE worse than local |Do not omit the strong local-only baseline |
| Adaptation always helps |False: several family/metric pairs worsen |All pairs retained |
| Original PM recurrence faithful at deepest node |Failed oracle check: deepest output omitted; max error0.83673 |Paper-inclusive recurrence used as a clearly identified port correction |
| Backbone recognizes all shared-input dependencies |Counterexample: equal-marginal distinct/shared PI graphs yield identical embeddings, different exact labels |No explicit PI identity control was trained; limitation remains |
| MUX roles learned by FSL backbone alone |Not established: pipeline delta is correct, but exact local phi supplies roles |Direct learned sensitivity exists but is imperfect; AND swap inconsistency recorded |
| First-pilot metric reversal explained |NOT analytic advantage plus terminal AND error and propagation identified by preserved-weight diagnostics |Oracle scores inaccessible at inference; no single causal attribution |
| Independent end-to-end verification |640 label cross-checks,96 prediction files,2400 update journal,24 complete prediction rename/reload checks |Does not replace industrial benchmark reproduction |

Full evidence and costs: closure/CLOSURE_REPORT.md, closure/RESULTS_SUMMARY.md, closure/INDEPENDENT_VERIFICATION.json and closure/PIPELINE_CONTROLS.json.

Targeted scientific evidence: [closure/evidence_packet/EVIDENCE_PACKET.md](closure/evidence_packet/EVIDENCE_PACKET.md), including per-seed/no-adaptation tables and exact label budgets. No new training in this audit.

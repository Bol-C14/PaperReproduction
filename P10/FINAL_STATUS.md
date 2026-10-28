# Final status: partial method reproduction; expansion paused

Final scope, 2026-10-28: **a bounded independent ROVER-inspired reconstruction with actual e-graph optimization, signed value analysis, contextual rewrites, shared-DAG extraction, independent generated-RTL validation and generic synthesis. Not full-paper reproduction, original software validation or reproduction of the paper's industrial/physical headline.** The selected last mechanism gap is closed; further project expansion is paused.

## Current mechanism status

The [current coverage table](loop/MECHANISM_COVERAGE.md) maps paper sections and archived source checks to implementation and runtime artifacts. Core exercised pieces are bounded equality saturation; Create/strict Propagate/Combine with explicit care; live-class overlap filtering; interval-union and signed guard refinement; operand/result narrowing; shared, acyclic, delay-constrained DAG extraction; and scoped constant comparison folding. Implementations substitute egglog for egg and Z3 optimization for CBC, with an explicitly uncalibrated component model. These are observed subset mechanisms, not proof that all original rules, schedules or frontend semantics were recovered.

The historical `loop/ARTIFACT_MANIFEST.sha256` includes the old coverage document. Its frozen hashes are unchanged: verify that historical snapshot using Git version `96caf97b9ccafca8fe1959ff7a27767d36f67bd4`, not the newly updated current-truth coverage text. The old coverage remains recoverable there. `FINAL_AUDIT.md` and its separate manifest remain byte-for-byte unchanged. New reports do not recast historical hash verification as a check of today's documentation.

Evidence progresses through three distinct scopes; their counts must not be combined into independent performance samples:

- [Historical loop closure](FINAL_AUDIT.md): audited 96 stored configurations and 24 paired comparisons, full-domain guarded FMA behavior and guard/mux overhead, DAG sharing and objective accounting. Old stages retain their own component versions and relative delay policies.
- [Signed-union Round 3](signed_union_round3/REPORT.md): four authored kernels at 8/16 bits; 48 passing positive SMT/RTL pairs, three dual-engine negative controls, 46 actual synthesis calls and 1,858,952 concrete containment calibration checks. No general transfer-function theorem or industrial workload evidence.
- [Nested Combine Round 4](nested_combine_round4/REPORT.md): three authored families at 8/16 bits; 36 positive pairs and three negative pairs in the successful attempt, 39 actual syntheses, common absolute delay targets. Four of six kernel/width pairs improve beyond propagation alone; two tie. Failed first-attempt extraction and its additional cost remain retained. Model arrival slack is distinguished from recomputed selected-path delay.
- [Comparison closeout Round 5](comparison_closure_round5/REPORT.md): ONE signed-interval witness at 8 bits, one selected output per folding-off/on arm, two positive pairs, three dual-engine negative pairs, three definedness obligations, 16 fixed boundary probes and three actual synthesis calls. The selected scoped constant reduces generic gates 51→39; depth stays 11. This is mechanism evidence, not a new performance matrix.

## Findings that the evidence supports

Within these authored typed inputs, care-conditioned rewrites can expose safe smaller arithmetic and comparisons while preserving full-domain module behavior and keeping guard/mux costs. The new comparison union retains the identical ASSUME predicate and bottom; empty care gives no proposal. Actual dynamic unions, selected terms, raw proofs and generated RTL establish runtime use rather than merely available source code. Independent read-only checks recount gates/depth and selected DAG costs. Failed attempts, ties, a historical regression and both prescribed delay representatives remain visible. Synthesis is post-selection and never an oracle for choosing a winner.

## What remains unverified

The kernels intentionally reveal the mechanisms being implemented. Two widths and multiple delay representatives are correlated observations, not independent designs; large proof/calibration counts establish their stated correctness checks, not a population of benchmark wins. Stage freezes and preserved failures support traceability but do not remove in-sample development or selection bias. There is no licensed held-out industrial corpus, original floating-point benchmark implementation, scalability characterization or estimate of typical improvement. The one extraction timeout is evidence about this reconstruction/configuration, not a criticism of the original ROVER implementation.

The typed DSL replaces general SystemVerilog parsing/elaboration. Sequential/X/Z semantics, many signed operators, unrestricted partial predicates, complete rule coverage and exact paper scheduling remain absent. The eight-round and node budgets do not establish saturation. Interval caps can lose precision. The low-level widths and finite input contracts are ours. Z3 and parsed-RTL Yosys give separate checker paths, but both consume this authored contract; no independent frontend, separately checked UNSAT certificates, commercial EC reproduction or post-synthesis netlist equivalence certificate is supplied.

Proxy delay/area and generic `synth -noabc` gates/depth are distinct metrics. No calibrated cell library, placement, routing, STA, power, TSMC5 flow, original commercial baseline or original industrial asset release has been verified here. Historical source-access refusals were not retried or bypassed during this closeout. Source mappings refer to previously archived paper/thesis review, not a new exhaustive original-paper reread or a claim that no later source release exists.

## Go / No-Go and stop

**Go:** preserve and inspect the current public evidence, reuse it to understand the bounded mechanisms, and record the project as partial reproduction. The specific missing comparison-folding integration is now complete for the frozen witness and declared helper boundary cases.

**No-Go in the current project scope:** more same-family matrices, tuning for nicer gate numbers, claims of statistical/general superiority, original-PPA replication, or API/GPU spending. Full frontend/operator rebuilding and held-out industrial/physical evaluation require a separately scoped effort with verified assets and protocols. A future post-synthesis equivalence check could strengthen the evidence chain, but is not silently claimed complete and is not a reason to keep this project running.

After reviewed publication of this milestone, no experiments or background jobs are scheduled by this branch thread. Existing checkouts, environments, original evidence and failed-attempt logs are retained. No other paper branch is changed.

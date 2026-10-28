# Nested Assume Combine: bounded CPU mechanism closure

The new e-graph subset propagates an outer Assume through Mux value branches and combines nested Assume conditions by conjunction. This closes the specific nested-context gap exercised here. It remains an independent ROVER-inspired reconstruction on three authored combinational kernel families at 8/16 bits, not original Intel code or full-paper reproduction.

## Correctness and controlled comparison

Attempt 2 completes 18 configurations: three kernels × two widths × three arms, with two identical absolute delay targets across arms. All 36 selected outputs pass unconditional full-input-domain Z3 BV equivalence and separately parsed generated-RTL Yosys SAT equivalence. All three intentionally wrong complete modules produce counterexamples in both engines: dropped outer guard, inverted inner guard and unconditionally narrowed arithmetic. Eight separate definedness-plus-value obligations validate Create, strict Add propagation, Mux propagation and Combine, and reject OR-for-AND, dropping a condition and bottom-as-zero. These finite DSL obligations are separate from the circuit proofs and do not establish every paper rule.

The paired arms use the same fixtures, fixed costs, signed-union domain, live-class filter, eight saturation rounds, 5000-node limit, 15-second per-target exact area solver limit and same-condition Assume idempotence. The legacy arm omits the two new distinct-context mechanisms; propagate adds only Mux propagation; combine adds both. This is an idempotence-normalized legacy subset with a corrected common extractor, not a byte-identical replay of Round 3. Assume care metadata is erased from both circuit dependencies and cost accounting in all arms. Targets are D and 2D, where D is computed from the original typed AST before optimization. No synthesis result is used to select candidates, costs, targets or outputs.

## Actual generic synthesis measurements

The table reports the first prespecified delay target, including all guards and muxes. Each entry is actual generic gates / longest generic-gate path after `synth -noabc`. Neither metric is physical PPA, library area, STA or a commercial-flow result.

| Kernel | Bits | Legacy | Propagate only | Propagate + Combine |
| --- | ---: | ---: | ---: | ---: |
| nested signed product | 8 | 217 / 17 | 217 / 17 | 110 / 14 |
| nested independent bounds | 8 | 100 / 13 | 100 / 13 | 68 / 9 |
| nested false branch | 8 | 112 / 14 | 81 / 12 | 81 / 12 |
| nested signed product | 16 | 538 / 23 | 538 / 23 | 157 / 15 |
| nested independent bounds | 16 | 250 / 17 | 250 / 17 | 144 / 13 |
| nested false branch | 16 | 290 / 19 | 137 / 13 | 137 / 13 |

Second-target gate counts agree with the first; the signed-product 8-bit Combine representative has depth 13 rather than 14. Every selected term and both variants are retained. Combine contributes extra narrowing beyond propagation on four of six kernel/width pairs. On two false-branch pairs, propagation already helps and Combine adds no measured benefit. No held-out, industrial, statistical or generally optimal claim follows from these deliberately mechanism-exposing in-sample kernels.

The selected extraction proxy areas for legacy / propagate / combine are 94/94/67 and 190/190/115 for signed product; 56/56/43 and 112/112/75 for independent bounds; 56/44/44 and 112/76/76 for false branch (8-bit then 16-bit). Each solver returns equal objective bounds. Proxy area is uncalibrated and differs from synthesized gates.

An independent standard-library audit recalculates all 36 selected DAG areas and critical paths and recounts all 39 unique netlists from connectivity. Thirty model arrival values contain slack: the stored `proxy_delay` is the feasible model arrival variable, not an independently measured critical path. Use `independent_checks.json`'s `selected_dag_delay` for the recomputed path. All recomputed paths satisfy their common targets. Actual netlist depth in the table is measured separately. RTL equivalence was proved before synthesis; there is no separate post-synthesis netlist equivalence certificate.

## Attempts, budget and evidence

The protocol and code were committed before execution at `115805bc2eb8b49705940adf7c49a48b27e364c2`. Attempt 1 ran eight semantic checks and two optimizer starts. Legacy 8-bit signed product produced two passing SMT/RTL pairs; propagate stopped with minimum-delay extraction `unknown/canceled` at five seconds. Remaining matrix work was aborted, with no synthesis. All logs, counterexamples and partial results are retained under `evidence/attempt1`.

The pre-execution revision `b1df1fb` documents the failure and creates a separate attempt 2 output path. It removes the unnecessary minimum-delay solve because the targets were already fixed; adds common same-condition idempotence to avoid redundant wrapper growth; uniformly raises area-solve timeout to 15 seconds; and retains saturated graphs before extraction. No synthesis measurements had been inspected. Both protocol versions remain in Git. Attempt 2 never required a repair or discarded positive result.

Attempt 2 spends 18 optimizer starts, 36 positive SMT + 36 positive RTL SAT checks, three negative checks in each engine and eight definedness obligations. Post-selection synthesis uses 39 actual unique calls, below the frozen cap of 42. Each arm has 12 selected synthesis evaluation slots, including repeats; deduplication is explicit and no arm receives extra candidate selection. Across both attempts: 20 optimizer starts, 38 positive pairs, three negative pairs, 16 definedness obligations and 39 synthesis calls. Failed-attempt work is included rather than presented as free tuning.

Attempt 2 matrix wall time is 33.4713 s; optimizer-worker wall sum 22.6216 s; post-selection synthesis audit 7.9034 s. Attempt 1 matrix wall time is 19.5784 s. Maximum successful attempt-2 worker RSS is 112624 KiB. These exclude source authoring, transfer, dependency setup, independent read-only checking and publication review; they are not full research CPU costs. No total-runtime fairness claim is made.

The existing isolated Python 3.12.12 environment uses egglog 14.0.0, z3-solver 4.13.3.0 and unofficial YoWASP Yosys 0.63.0.0.post1107. Sequential work remained on taskset 16–23 with OMP/MKL/OpenBLAS/NumExpr limits 8. Load before attempt 2 was 0.68/0.80/1.25 with about 1.3 TiB available memory. No global dependencies, API/model calls, local LLM loading, GPU, paid resources or other paper branches were used.

`evidence/attempt2` retains the frozen source/fixture manifest, initial and final graphs, exact worker commands, journal, selections, solver bounds, SMT, generated RTL, Yosys logs, original and candidate netlists and synthesis audit. `inspect_results.py` additionally verifies the existing frozen source hashes against the exact committed Git version. It was authored after selection, performs only read-only checking and never changes the experiment. Historical `P10/loop`, reconstruction and Round 3 evidence remain unchanged.

## Scope still open

This supports nested Combine with total Boolean care predicates, signed and independent variable guards, and true/false nested branches in the typed DSL. It does not supply arbitrary SV ingestion, sequential/X/Z semantics, all signed operators, unrestricted partial predicates or a complete paper rule library. Assumption rewriting is not exported as unconditional global arithmetic equality; full-module checks remain necessary. Bounded saturation and the finite interval-union cap can miss opportunities. Original industrial assets, physical timing and commercial TSMC5 PPA remain absent. Further work should target a distinct unsupported mechanism or independently sourced, licensed held-out kernels rather than repeat this matrix.

## Provenance and public scope

The engine, circuit lowering, interval domain and extractor are derived from this repository's authored Round 3 reconstruction; `run.py` and `audit.py` reuse its proof/synthesis harness. The new rules, kernel fixtures, audit and report are authored in this branch. Installed third-party dependencies, caches, credentials, source-restricted Intel artifacts and technology libraries are not included. Public evidence contains generated research outputs and tool logs, not redistributed dependency implementations. Existing upstream source/version notices remain intact. Publication is limited to the existing `reproduction/constraint-aware-rover-tcad2025` branch after history, working-file and license/provenance review.

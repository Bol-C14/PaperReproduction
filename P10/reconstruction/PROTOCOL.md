# Frozen bounded pilot protocol v1

Frozen before solver experiments, 2026-10-28. Scope: our method reconstruction, not official ROVER. Exactly ten hand-reviewed fixtures below; no generated benchmark sweep. Setup/diagnosis budget 2 hours from 10:35 UTC; downloads <2 GB; existing CPU/RAM only. No GPU, synthesis, paid services, push or PR.

## Source-derived semantics

References use accepted-manuscript printed pages (1–14), not final journal pagination: [paper](https://spiral.imperial.ac.uk/bitstreams/de68c6e8-a66d-42d6-ae3e-16eab9fc9782/download). Recovered full text was read during asset audit. Re-access of specific pages returned 405; no retry. Cross-check exact definitions against the author's [thesis](https://samuelcoward.co.uk/assets/pdf/Thesis_Imperial.pdf), Chapter 5, which identifies itself as the TCAD extension. No local PDF obtained (403).

- Paper pp4–5 §III / thesis printed pp88–91, Eqs5.5–5.9, Table5.1: ASSUME(e,c)=e when c holds and bottom otherwise. Same-condition assumed expressions may merge only when equal on that subdomain. Bottom is distinct from every bitvector; strict arithmetic propagates bottom. Mux selects its selected branch, so creating ASSUME on the true/false branches preserves the complete mux. Propagation distributes the same assumption to operands; nested assumptions combine by conjunction. Never export a contextual equality to a global equality. Pilot represents contextual candidates, not an e-graph saturation engine.
- Paper pp6–7 §IV-A / thesis printed pp96–98, Eq5.14: unsigned interval unions represent signal bit patterns. Initialize an n-bit signal to [0,2^n-1]; narrow input ranges only using explicit guards. Arithmetic interval extensions overapproximate independently ranged operands. Truncation conservatively returns the full modulus interval if endpoints cross a modulus block. S_n splits at sign bit into two's complement signed intervals. U_n maps integer intervals back to unsigned, splitting a single modular wrap and returning full range across multiple wraps. Merge overlapping/adjacent intervals. This pilot explicitly types and extends operands; it does not implement SystemVerilog elaboration or infer mixed-expression signedness.
- Paper p8 §IV-B / thesis printed pp99–101 Table5.4: guarded unsigned comparison becomes true if minimum lhs exceeds maximum rhs; operator bitwidth may shrink only when its complete possible output fits; guard y in [0,2^i-1] permits narrowing logical shift amount to i bits (paper p10 Eq24). Signed absolute-value simplification is the motivating paper p3 Eq1, restricted here to positive signed inputs and fixed-width modular negation.
- Paper pp8–9 §IV-C, Eqs16–22 / thesis printed pp102–104 Eqs5.15–5.17: delay is operator delay plus maximum operand arrival; area counts selected nodes with sharing. ILP chooses output-closed nodes, topological constraints prevent cycles, arrival variables enforce delay target, and CBC minimizes area for each target. Greedy gives minimum modeled delay and a delay sweep yields modeled Pareto choices. **No exact calibrated operator delay functions are reconstructed here; no ILP, Pareto or physical-performance claim is tested.** This limitation is deliberate and fixed before results.

## Fixed fixtures and expected outcomes

Widths are bits; all add/multiply/negate results wrap at the explicit result width. x4 denotes all 16 bit patterns. Signed abs is `(signed x < 0 ? -x : x)` at width4, including modular INT_MIN. ZExt and SExt are explicit. Logical right shifts zero-fill and return zero when amount >= data width.

| ID | Hand-reviewed proposal / domain | Expected |
|---|---|---|
| F01 | abs(x4)->x4 under signed x>0; reinsert into original mux with else0 | valid local and full mux |
| F02 | same proposal under unsigned x>0 | invalid signedness control; e.g. x=9 |
| F03 | x8 >> y4 -> x8 >> low1(y), under unsigned y<=1 | valid shift guard |
| F04 | same proposal under unsigned y<=2 | invalid truncation/guard control; x=4,y=2 |
| F05 | 7-bit a3*b3+c3 -> 6-bit arithmetic then zero-extend7 | valid; [0,56] fits6 |
| F06 | 5-bit zero-extended a4+b4 -> 4-bit sum then zero-extend5 | invalid early-truncation control; a=b=9 |
| F07 | unsigned a4>b4 -> true, under a>=8 and b<=7 | valid refined comparison |
| F08 | signed a5+b4 assigned6 (sign-extend operands): analyze unsigned result union [0,22] U [40,63] | valid range containment |
| F09 | abs(x4)->x4 globally, despite a valid local guard signed x>0 | invalid context-escape control |
| F10 | abs(x4)->x4 under x>3 AND x<2 unsigned | reject vacuous guard; no optimization success |

## Acceptance and accounting

Independent Z3 QF_BV checker, pinned z3-solver4.13.3.0, 5-second timeout per query, deterministic seed0. It does not import the optimizer's range/guard implementation. First check guard satisfiable; UNSAT guard is a rejection, UNKNOWN a failure. Check `guard AND lhs != rhs`; UNSAT certifies this finite-width proposal. Separately check complete mux equality (or global equality for F09). Positive interval claims are independently checked using bitvector membership, not interval arithmetic. Negative controls must return SAT plus a replayed counterexample. Require every positive valid, every negative detected, and F10 rejected; report UNKNOWN/error/timeout as failures, never drop rows.

Also check ASSUME Create, Propagate and Combine using symbolic definedness plus value for F01, distinguishing bottom from zero. Ten fixture rows include these checks without adding arithmetic fixtures. No statistics or general performance claim from ten examples. Record elapsed time, CPU time, peak process RSS, solver version, source hashes, command, every attempt and all failures. Freeze protocol and fixture SHA256 before first execution. Edits after execution require a new documented attempt and must retain previous logs.

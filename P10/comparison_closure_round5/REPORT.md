# Final scoped comparison-folding witness

This closes the one remaining low-cost mechanism selected by the closeout review: value-range-proven constant comparison folding inside the e-graph, with ASSUME/bottom preserved. One authored witness, one width, one absolute timing target, two feature arms. There is no new performance matrix. The overall project remains a partial independent method reconstruction and is paused after this milestone.

## Executed mechanism

Let `a` be an 8-bit input interpreted as signed for comparisons, and `b` an arbitrary 1-bit input. The original complete output is:

```text
p = (-3 <= signed(a)) AND (signed(a) < 4)
out = p ? (signed(a) < 8) : b
```

The care-refined unsigned bit patterns are `[0,3] union [253,255]`. The comparison helper reasons on this union before any conversion to a hull and proves `signed(a)<8` true throughout this nonempty domain. The actual dynamic union joins `Assume(1,Slt(a,8),p)` with `Assume(1,K(1,1),p)`, retaining the SAME predicate; it never merges the bare comparator globally with one. The selected fold-on term contains the scoped constant. Fold-off has no such union or selected constant. Outside `p`, the complete output remains `b`; the internal comparison need not equal one.

`Ult`, `Slt` and `Sge0` constant outcomes are implemented over nonempty inclusive unsigned-encoding unions with representable thresholds. Mixed outcomes return no proposal. Empty/bottom care returns no proposal. The end-to-end witness exercises `Slt -> true`; true/false/refusal paths for the other predicates are helper-boundary evidence, not additional end-to-end benchmark claims. Direct operand refinement is limited to existing guard patterns; arbitrary relational symbolic reasoning is not supplied.

## Validation and actual costs

Source/protocol commit `52c2c2038c5d8d9020b9deaaa51f33c3a6ba58fc` preceded the one execution attempt. All checks met their frozen expectations, without repair, retry or discarded output:

- Two selected complete outputs: unconditional full-input-domain Z3 BV equivalence and separately parsed RTL Yosys SAT both UNSAT. No external care-domain input restriction.
- Three intentionally wrong complete outputs: global constant escape, wrong folded value and strict-threshold boundary mistake all SAT in BOTH engines. Retained SMT witnesses include `b=0,a=125` for escape and `a=0` for the strict boundary.
- Three definedness-plus-value obligations: actual scoped fold UNSAT; naked global constant and treating empty/bottom as one SAT. The constant-true mismatch for bottom is satisfiable without assigning any input; its empty model is not a missing counterexample.
- Sixteen fixed 4-bit helper probes cover unsigned zero/MAX, signed INT_MIN/MAX, strict equality, disjoint signed crossings, both Boolean results, refusals and empty domains. Independent concrete evaluation covers every value within each chosen probe; it is calibration for these probes, not an all-width transfer-function theorem.

| Arm | Extracted proxy area | Recomputed selected DAG delay / target | Actual generic gates | Actual generic gate depth |
| --- | ---: | ---: | ---: | ---: |
| Folding off | 26 | 6 / 6 | 51 | 11 |
| Folding on | 18 | 6 / 6 | 39 | 11 |

Original RTL also synthesizes to 51 gates/depth 11. One selected output per arm is evaluated, with the same costs, live filtering, union domain, nested Combine, eight rounds, 5000-node limit, 60-second worker limit and 15-second area-solver limit. Exact objective bounds match. There is no synthesis feedback, target adjustment, output reranking or gate-based retry. Three actual unique `synth -noabc` calls include original and both candidates, reaching the frozen cap of three. The independent read-only checker verifies the seven frozen files against Git, observes the selected scoped constant, recomputes both selected DAG costs/paths and recounts all three netlists.

Witness/checker wall 1.3500 s; optimizer worker wall sum 0.1138 s; post-selection synthesis audit wall 0.5512 s; maximum worker RSS 80412 KiB. These exclude authoring, transfer, publication and read-only review, and are not total research cost. APRIL load before execution was 0.63/0.47/0.85 with about 1.3 TiB available memory. One sequential runner used taskset 16–23 and OMP/MKL/OpenBLAS/NumExpr limits 8 in the existing Python 3.12.12 environment. Dependencies remain egglog 14.0.0, z3-solver 4.13.3.0 and unofficial YoWASP Yosys 0.63.0.0.post1107. No new dependency, model/API call, GPU or paid resource was used.

## Interpretation, evidence and stopping point

The evidence supports a scoped comparison rewrite in this typed IR and one actual complete circuit, not typical performance or automatic optimization of real RTL. The witness intentionally exposes the implemented reasoning; it is in-sample. Gate count improvement with unchanged depth is not a physical-PPA result. Generated RTL has been proved equivalent; no separate synthesized-netlist equivalence certificate is claimed.

`evidence/attempt1` retains all initial/final graphs, selected terms, dynamic unions, hashes, commands, stdout/stderr, SMT, generated RTL, original/candidate netlists, counterexamples and cost records. `inspect_results.py` is a post-selection, standard-library-only review using the earlier independent recount functions; it does not change the frozen run. `COMMANDS.md` records execution and replay restrictions. Engine/lowering/domain/extractor/proof and synthesis harnesses derive from this repository's authored Round 4 sources; installed third-party code, caches, credentials and restricted original artifacts are not redistributed.

See [current mechanism coverage](../loop/MECHANISM_COVERAGE.md) and [final project status](../FINAL_STATUS.md). The early F07 comparison fixture is no longer the only evidence for comparison folding; it remains historical and unchanged. Further same-family examples, API/GPU experiments and original-PPA reproduction are No-Go in the present scope. Project expansion pauses here.

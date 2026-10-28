# Focused skeptical closure audit

Date2026-10-28. Scope: verify archived final closure, not a new benchmark sweep. **Verdict: the available-resource independent-reconstruction loop is complete within its declared scope; headline850→337 generic gates survives.** This does not establish faithful reproduction of the complete author algorithm, original benchmark population, or physical PPA.

Executable evidence: [audit script](loop/audit_closure/audit.py), [machine results](loop/audit_closure/AUDIT_RESULTS.json), [raw replay log](loop/audit_closure/audit1.log). All1952 entries of the previous artifact manifest were rehashed successfully. No archived result was modified or dropped. No optimization or synthesis rerun was necessary; only focused SMT obligations and one FMA RTL SAT replay executed.

## Fairness of all24 pairs

The audit inspected all72 configurations from `width_matrix1` and24 integrated configurations:24 agnostic/aware pairs plus corresponding unfiltered-context/no-VRA controls. Every saved synthesis script is byte-identical:

```yosys
read_verilog design.v
hierarchy -top candidate
synth -top candidate -noabc
opt_clean
write_json mapped.json
stat
```

All netlists identify the same Yosys0.63 build70a11c6bf, invoked via the same pinned YoWASP binary. Complete original module text matches `emit(workload(name,width),'original')` for every configuration. The baseline is the extracted, globally optimized agnostic candidate, not a deliberately unsynthesized source. Gate counts were recounted from all saved netlists. Each saved SAT script independently parses original/candidate RTL, flattens the full miter and proves `mismatch=0`; there are no input `assume`, `chformal`, `-set` or care-domain restrictions.

Common algebraic rules, global VRA rules and width-dependent component costs come from identical `engine.py`/`dag_extract.py` hashes in both primary runs. The **intended treatment** is creation/propagation/refinement of branch care conditions; identical opportunities to exploit care would erase the distinction between the two arms. The baseline retains all unconditional opportunities. Inputs/workloads are generated before mode selection. Live filtering affects only context expansion, not the module input contract.

Search limits match: eight outer rounds, one egglog thread,5000-node limit,60s worker timeout,5s per extraction solve, same two policy multipliers. All96 rows completed eight rounds below the node/time caps and all extraction objective bounds matched exactly. This is matching **limits and policy**, not equal consumed CPU/e-matches or identical absolute delay targets. Each mode first finds its own dmin. The audit verified **aware target <= agnostic target in all24 pairs**, so none of the gains comes from granting the aware arm a looser modeled timing target. For FMA16, strict targets are13 versus15; relaxed targets26 versus30. A claim of an equal-absolute-target Pareto comparison remains unsupported and is not made.

## FMA850→337: actual care semantics

Canonical source files are [design.v](loop/runs/integrated_matrix1/bounded_fma_16_context_live_lambda1/design.v), [miter.v](loop/runs/integrated_matrix1/bounded_fma_16_context_live_lambda1/miter.v) and [archived SMT](loop/runs/integrated_matrix1/bounded_fma_16_context_live_lambda1/equivalence.smt2). All three inputs and output are unsigned16-bit ports.

Ignoring identity wires, actual RTL is:

```verilog
// original: all inputs/output unsigned [15:0]
wire care = a < 16'd8;
wire [15:0] product_original = a * b;
wire [15:0] sum_original = product_original + c;
assign out_original = care ? sum_original : c;

// extracted: only the care-path multiplicand is narrowed
wire [2:0] a_low = a;
wire [15:0] product_extracted = {13'd0, a_low} * b;
wire [15:0] sum_extracted = product_extracted + c;
assign out_extracted = care ? sum_extracted : c;
```

The original full input domain is48 bits, not `a<8`. The archived SMT has one assertion of whole-output inequality. Its shape is:

```text
distinct(ite(bvult(a,8), a*b+c, c),
         ite(bvult(a,8), zext(a[2:0])*b+c, c))
```

It does **not** conjoin `bvult(a,8)` as a global assumption. The new focused proofs are:

| Obligation | Result |
|---|---|
| Re-run archived full-domain mismatch assertion | UNSAT |
| care AND original_out != extracted_out | UNSAT |
| NOT care AND original_out != c | UNSAT |
| NOT care AND extracted_out != c | UNSAT |
| care AND a != zeroextend(a[2:0]) | UNSAT |
| care AND a's sign bit is1 | UNSAT |
| Original != guarded low16 of full32-bit unsigned product+sum | UNSAT |
| Outside care, original/extracted **internal arithmetic** can differ | SAT (expected) |

The last control prevents conflating branch-local equivalence with global replacement. For `a=8,b=3,c=5`, original internal arithmetic is29, narrowed arithmetic5, but **both complete outputs are5**. For `a=65535,b=65535,c=65535`, internals differ0 versus65528, but both complete outputs equal65535. For the care-path overflow case `a=7,b=65535,c=65535`, the mathematical sum524280 wraps to65528 in both implementations. Thus narrowing does not remove result overflow: product and sum remain16-bit modulo arithmetic; only a is zero-extended from3 bits under care. No signed cast or signed comparator appears in this FMA. A full32-bit reference checks multiplication/addition truncation independently.

Fresh proof files and the independent Yosys SAT replay are under [audit_closure](loop/audit_closure). No access or new software was needed.

## Guard overhead is included

The audit traversed the synthesized mux-select cone; it did not rely on source wire names surviving optimization. Both agnostic and extracted FMA netlists contain:

- 43 control-cone gates:19 AND,12 NOT,12 OR, depending exactly on input `a[15:3]`.
- 16 output-mux gates.
- No overlap between that control cone and the data-only cone.

Therefore the complete counts decompose as **850=791 datapath+43 guard+16 mux** and **337=278 datapath+43 guard+16 mux**. The guard was neither omitted from the denominator nor implemented as a free input assumption. Model costs likewise count one comparator and one mux in both arms: proxy area304 versus96 includes32 control proxy units in each. Proxy units differ from generic-cell counts and are not calibrated physical area.

## Shared DAG and no hidden oracle

For all96 configurations, the audit independently reconstructed the selected e-class→e-node mapping, checked one selected node per active class, selected-child closure, acyclicity, root reconstruction and width consistency across all representatives. It recomputed selected-node area from the frozen v4 formula (without calling `engine.cost`) and matched every reported area/objective bound. Zero-cost selected orphan classes can remain because the objective is indifferent to them; no positive-cost orphan was found, and only root-reachable terms are emitted.

Concrete sharing witness: `repeated_bounded_mul16` references one product twice. Agnostic extraction charges the selected multiply once at48 proxy units, not96; integrated extraction charges it once at6, not12. Both emitted candidate modules have **one** `*` expression feeding both add operands, thanks to structural memoization. The complete modeled DAG areas are96 and44. This verifies actual sharing in selection and RTL emission, not merely a tree-cost label.

Static source review confirms the worker/engine/extractor consume typed workloads, e-graph structure and declared proxy costs; they do not read mapped gate counts, synthesis logs, verification witnesses or external model outputs when choosing candidates. Synthesis runs after selection. Both policy outputs are recorded, including ties/losses; there is no choose-the-best-synthesized-candidate step. Historical tree and DAG results remain, including the earlier interpolation-clamp regression65→67 gates/12→13 levels. Three wrong-RTL controls retain their expected SAT failures.

This is **in-sample method development**, not blinded held-out evaluation: costs/rule coverage evolved under separately frozen stages, and earlier non-improvements informed coverage review. Final comparisons use the same final rule/cost source in both arms. The evidence supports these new kernels; it does not estimate general ROVER quality or independently validate the authors' entire rule library.

## Attempts and cost, including failures

| Scope | Attempts and outcome | Measured cost / limit |
|---|---|---|
| Earlier fixture stage |2 attempts ×10 fixtures=20 executions; all expected outcomes; first checker/emission linkage limitation disclosed and repaired |~0.260s solver-loop wall, peak58,192KiB; not end-to-end benchmarks |
| End-to-end stages |11 pilot/matrix runs,144 optimizer workers,288 configuration rows;315 DAG optimization solves;197 synthesis and197 positive RTL SAT invocations with per-run reuse |403.739s aggregate run wall;193.717s optimizer CPU; peak child105,900KiB |
| Negative RTL controls |3 Z3 SAT detections +3 expected Yosys exit1 proof failures |~0.798s RTL wall; preserved separately |
| Tool setup failure |1 YoWASP startup failed on read-only default cache; process-local workspace cache repaired it |Bootstrap/compile CPU not fully metered; no permissions changed |
| Earlier source-access failures |Audit records preserve PDF/Figshare403 and later manuscript page405/thesis403 outcomes |No files acquired through denied accesses; no bypass; transfer totals not precisely metered |
| Formatting diagnostic |Full git whitespace check flagged raw Yosys ASCII-art spaces; authored-file check passed |Raw logs retained; not a proof failure |
| This focused audit |96 archived configurations/24 pairs inspected;8 extra SMT obligations (7 UNSAT+1 expected SAT),1 positive FMA RTL SAT replay |1.875s successful audit-script wall, including0.619s Yosys replay; additional read-only diagnostics not fully CPU-metered |
| Focused diagnostic failure |1 initial read-only netlist lookup raised `KeyError: n0` because synthesis removed/renamed that source net |Corrected by traversing mux-select drivers; no result or source edit, no headline rerun |

Previous dependency payload122,801,061 bytes; **this audit downloaded/installed nothing**. Full task CPU including setup, synthesis/bootstrap and assistant authoring is not known;193.717s must not be described as full total CPU. No paid resources, API, external LLM, credentials, gated agreement, upload/push/PR or security change. Existing raw logs and manifests remain.

## Compact replay commands

```bash
cd /workspace/PaperReproduction/P10/loop
# Read-only archived full-domain SMT replay:
.venv/bin/z3 runs/integrated_matrix1/bounded_fma_16_context_live_lambda1/equivalence.smt2
# Independent parsed-RTL proof (using the new audit copy, no archive overwrite):
cd audit_closure/fma16_rtl
YOWASP_CACHE_DIR=/workspace/PaperReproduction/P10/loop/.cache \
 /workspace/PaperReproduction/P10/loop/.venv/bin/yowasp-yosys -s verify.ys
```

The audit script itself creates fresh proof artifacts and refuses to overwrite the RTL replay directory. Its first successful output is archived, rather than repeatedly running it for cosmetic statistics. No numerical correction is required. Remaining uncertainty is the explicitly limited signed/nested-context/operator/RTL subset, uncalibrated component model and original industrial/physical setting—not the complete-domain correctness or inclusion of guard overhead for the audited headline.

# P10: closed methodology loop on free resources

This tranche moves beyond fixtures: **typed arithmetic input → real egglog e-graph exploration → care-aware range refinement → constrained shared-DAG extraction → emitted Verilog → independent full-domain checks → free synthesis → matched controls**. It is our independent reconstruction, not unavailable Intel ROVER source or TSMC physical replication.

Primary evidence is [width_matrix1](runs/width_matrix1/RESULTS.jsonl) plus [integrated_matrix1](runs/integrated_matrix1/RESULTS.jsonl): 12 newly authored datapath instances, four modes, two extraction policies, **96 final configuration rows**. All are backed by Z3 whole-domain equivalence and independently parsed RTL SAT in Yosys, followed by actual generic synthesis. Reused identical original/candidate pairs are marked explicitly, not counted as fresh independent proofs. Across all stages there are288 recorded configuration rows and197 actual synthesis jobs (including repeats across protocol versions), with no failed expectation, UNKNOWN or timeout. Three intentionally wrong RTL controls produce SAT counterexamples and expected Yosys proof failures.

## What executed

The [mechanism coverage map](MECHANISM_COVERAGE.md) binds each component to manuscript/thesis pages and marks substitutions. Egglog supplies actual e-matching, union/congruence closure and constructive equality exploration. Eight rounds alternate algebraic rules, ASSUME context propagation, external fixedpoint e-class value analysis and justified dynamic width rewrites. The final optional live-class filter computes reachable expression classes and avoids unrelated context creation/propagation. This is bounded saturation; no claim all cases reach an unrestricted fixedpoint.

The extractor ports the paper's selected-node closure, topological acyclicity, shared area and arrival inequalities into Z3 integer/Boolean optimization instead of CBC. For every solve we record equal objective lower/upper bounds before accepting an optimum. It minimizes model delay, then model area at dmin and2*dmin. These are two sampled frontier points, not the entire Pareto frontier. Delay policies are relative to each mode's dmin; comparisons match search/resource policy, **not identical absolute delay targets**. Operator costs remain declared proxies; a model optimum is not a physical optimum.

Four final modes use identical new costs, circuit inputs, eight rounds,5000-node cap,60s worker cap and5s per extraction solve:

- Agnostic: algebraic rewriting and global range rules; no ASSUME contexts.
- Context: ASSUME plus refinement and full independent operand/result width reduction.
- Context without VRA: context bookkeeping, with range-driven rewrites disabled.
- Integrated: context+VRA plus the live-class relevance filter.

## Controlled outcomes

The complete24 paired rows, including both policies, are in [PAIRED_RESULTS.md](PAIRED_RESULTS.md); machine aggregation is [AGGREGATE.json](AGGREGATE.json). Below is the strict dmin policy for the integrated mode. Units are **generic one-bit cells / combinational logic levels**, not square microns, picoseconds or power.

| Kernel | Bits | Agnostic gates / depth | Integrated gates / depth |
|---|---:|---:|---:|
| Guarded shift/add | 8 |111 /18|76 /12|
| Guarded shift/add |16|270 /25|180 /16|
| Bounded FMA |8|204 /17|137 /16|
| Bounded FMA |16|850 /26|337 /21|
| Signed abs branch |8|84 /15|66 /11|
| Signed abs branch |16|189 /20|147 /15|
| Interpolation/clamp |8|65 /12|65 /12|
| Interpolation/clamp |16|67 /13|67 /13|
| Repeated bounded multiply |8|89 /11|43 /8|
| Repeated bounded multiply |16|249 /16|81 /12|
| Unconstrained multiply/add |8|183 /16|183 /16|
| Unconstrained multiply/add |16|791 /25|791 /25|

Across both policies, integrated mode reduces gate count in17/24 pairs and ties7/24; unfiltered context wins18 and ties6. These are closely related examples/widths, not24 independent workloads or an estimate of population gain. No unsupported aggregate “paper performance reproduced” claim follows.

Negative/null results matter. Interpolation/clamp is mostly already handled by synthesis/global ranges and the unconstrained control ties. Earlier frozen v2 DAG comparison had13 gate wins,10 ties and **one loss**: interpolation/clamp8 at the relaxed policy grew65→67 gates and12→13 levels. Those artifacts remain; they demonstrate model/synthesis mismatch. Live filtering reduced e-node count in10 of12 instances (e.g. guarded shift136→108, interpolation252→216 in v3), with no reduction on the unconstrained control; CPU was not uniformly better and tied model-optimal representatives sometimes synthesized differently. The v4 width rule closed an actual reconstruction gap: bounded FMA initially tied because operand narrowing was incorrectly conditional on result narrowing. Final positive gains are reported against same-v4-cost agnostic controls, not earlier baselines.

## Correctness and care conditions

No input domain restriction is passed to either complete-module checker. Z3 compares original explicit-width expression against the **actual emitted candidate AST** over all bit patterns. Yosys separately parses `design.v` and `miter.v`, flattens the miter and runs `sat -verify -prove mismatch 0 -show-inputs`. Only checked outputs are synthesized with `synth -noabc; opt_clean; write_json`. Boolean truth in guards, zero/sign behavior, explicit widths, modular overflow and oversized logical shifts are preserved by the typed encodings. ASSUME nodes remain in the e-graph; removing them is accepted only when the whole RTL passes unconditional checks.

[Negative controls](runs/negative_rtl1/RESULTS.json) intentionally widen a guard beyond a one-bit shift range, misuse signed abs, and truncate arithmetic too early. Both checkers reject all three; raw failing Yosys logs and witnesses are preserved. These are sensitivity controls on our reconstruction, not findings against the authors. UNSAT relies on the solver implementations; no separately checked proof certificates were generated. Original and candidate share our typed language contract, so this does not independently validate arbitrary SystemVerilog elaboration.

## Protocol history and repairs

Frozen protocols are [v1](PROTOCOL.md), [DAG extension](PROTOCOL_DAG.md), [live-class extension](PROTOCOL_LIVE.md), [full width rule](PROTOCOL_WIDTH.md) and [final integration](FINAL_INTEGRATION.md), with SHA256 files. They precede their respective runs. Version additions were mechanism coverage completions, not removal of losing cases or synthesis-driven candidate ranking. All old outcomes remain under `runs/`.

Setup repair: YoWASP's default cache location was read-only; using a process-local `YOWASP_CACHE_DIR` in this workspace fixed it without permissions/security changes. Static review fixed generic zero/one identities to retain explicit result resizing; corrected live reachability to ignore width/name primitives; and strengthened cache keys to include original RTL. Historical cache reuse was independently audited and never crossed original workloads. The first live pilot remains alongside its corrected pilot. No failed runtime result was relabeled as equivalence success.

Every job records source hashes, commands, solver reports, graph nodes, dynamic unions, selected expressions and resource measurements. Historical e-graph programs/unions can be replayed using `replay_graph.py`; a v1 graph was successfully replayed after later source updates. `verify.ys` and `synth.ys` reproduce every archived RTL check/metric independently of optimization source history.

## Re-run from this checkout

Pinned versions and all resolved wheel hashes: [SOURCE_VERSIONS.json](SOURCE_VERSIONS.json), [requirements.lock](requirements.lock). Egglog14.0.0; Z3 package4.13.3.0; Yosys0.63 git70a11c6bf through **unofficial** YoWASP0.63.0.0.post1107. Current sources reproduce the final v4/integrated method. Older protocols remain in their graph/program/candidate artifacts; rerunning an old run name with current source is not claimed to recreate old Python implementation timing or tie choices.

```bash
cd /workspace/PaperReproduction/P10/loop
# Existing isolated environment:
.venv/bin/python run_loop.py --run my-pilot --pilot --pilot-name bounded_fma --dag --live
.venv/bin/python run_loop.py --run my-controls --dag
.venv/bin/python run_loop.py --run my-integrated --dag --live
# Historical graph replay:
.venv/bin/python replay_graph.py runs/matrix1/guarded_shift_8_context.egraph.json
# Recheck one archived generated RTL:
cd runs/integrated_matrix1/bounded_fma_16_context_live_lambda1
YOWASP_CACHE_DIR=/workspace/PaperReproduction/P10/loop/.cache \
  /workspace/PaperReproduction/P10/loop/.venv/bin/yowasp-yosys -s verify.ys
```

Run directories must be new; existing outputs are never overwritten. Fresh compatible Linux/Python installation:

```bash
python3 -m venv .venv
.venv/bin/python -m pip download --only-binary=:all: --require-hashes -r requirements.lock --dest vendor
.venv/bin/python -m pip install --no-index --find-links=vendor --require-hashes -r requirements.lock
```

Z3 verification seed0; extraction uses pinned Optimize default tie policy; egglog one thread. There is no stochastic search or external LLM. Equal-cost selected representatives, SAT witnesses and timings need not be bit-for-bit identical. Top-level run logs contain the exact commands/outcomes for every stage.

## Remaining limits

The available-resource methodology loop is closed. Remaining distance to the paper includes the full mixed-precision rule library, integrated signed interval-union analysis, nested context coverage, complete Pareto sweep and general Slang/Verilog frontend/backend. Current kernels are12 new combinational instances, not original industrial RTL or a full floating-point subtractor. The paper's industrial suite and commercial EC/synthesis/TSMC5 context still require legitimate external assets; none were accessed or assumed. This report supports method learning and concrete mechanism effects on these free-tool circuits, not the original30%-delay/1%-area claim.

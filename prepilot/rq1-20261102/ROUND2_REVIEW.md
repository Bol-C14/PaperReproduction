# RQ1 result audit — no new EDA computation

## Audit finding

The compared pipelines share the same original input, tool executable/build, source Tcl, exported constraints, two-thread cap, 600-second timeout and exact issued `route_design` command. They run in fresh Vivado processes and separate output directories. Default adds `phys_opt_design -directive Default` before routing; this is an intentionally different tool stage, not a matched amount of computation.

Commands are in each arm's command.json and the machine audit in ROUND2_AUDIT.json. Tool logs independently confirm maximum 2 CPUs for route; Default also reports maximum 2 CPUs for physopt. All three route runs show the same named top-level routing phases. Both no-edit repetitions have identical recorded routing-phase checksum sequences. These observations support repeatability in this environment, not proof of determinism.

Default and the no-edit route have different intermediate netlists, route checksums, router starting timing, memory/timing caches after the added physopt stage, and selected routes. Those differences are effects of the pipeline and prevent interpreting the final difference as an isolated LUT-rewrite effect. Both restore checkpoint-embedded Netlist and Device caches. Fresh processes remove previous process memory, but **do not equalize OS page caches**, persistent tool data, or in-process warming caused by running physopt before route. No cache flush or randomization was attempted. Router/physopt seed settings were not explicitly frozen or inventoried; equal defaults are plausible but not experimentally established. Full inherited environment snapshots were not captured. Therefore wall-time differences are descriptive pipeline costs, not cache-normalized algorithm runtimes.

Crucially, `route_design` itself runs **Phase 14 Physical Synthesis in Router** in both conditions. The appropriate baseline label is **no explicit pre-route physopt, followed by the default optimizing router**. It is not a passive/no-optimization or physical-only control. The no-edit outputs happen to retain an identical functional export in these runs; the command does not guarantee that property on other inputs or seeds. All baseline outputs still require validation.

## Exact interpretation of the numbers

For this single state and these observed processes:

- Original to no-edit router: (−0.885) − (−1.654) = 0.769 ns.
- Original to Default+router: (−0.862) − (−1.654) = 0.792 ns.
- Difference between completed pipelines: 0.023 ns.
- Ratio: 0.769 / 0.792 = 97.09596%.

The ratio is an arithmetic description of **this observed pair of differences**. It is **not a causal contribution/share**, variance decomposition, mediation estimate, expected performance, probability, or cross-state conclusion. Router/physopt interactions mean the terms cannot be treated as independent additive mechanisms. Calling this “97.1% of Agent gain is routing” would be unjustified: no Agent was run. The matched completed-pipeline contrast is the relevant next estimand; even its reproducibility is not established by only one Default run.

The no-edit baseline repeats agree at the report's 0.001 ns precision. Default is not independently repeated, and its 0.023 ns difference is not a confidence interval or an established noise-exceeding effect. TNS improves modestly while failing setup endpoint count increases relative to the no-edit result. Do not choose a different metric after observing these tradeoffs.

## Correctness audit and small mutation controls

Original versus serialization-only: entire exported functional HDL and XDC unchanged except explicitly stripped generated comments, plus unchanged timing/route metrics. No-edit routing versus original: exact exported functional HDL identity and unchanged XDC; this is exporter-conditional modeled logical identity, not independent source-spec verification.

Default versus original: actual logical rewrite, with a narrow two-state local proof for the seven-input LUT cut and exact unchanged-remainder check. This supports a conditional Boolean logic-preservation statement when primitive/export semantics hold and remaining state/logic are as exported. It does not establish four-state X/Z behavior, analogue/timing equivalence, race/glitch behavior, full input-spec correctness, or an independent sequential-equivalence theorem for arbitrary future transforms. The original and transformed physical implementations intentionally have different delay; “equivalent timing behavior” is neither proved nor required by the intended optimization contract.

Small local mutation controls now pass: actual pair accepted; changed LUT INIT bit rejected with a counterexample; changed introduced LUT input rejected; an unrelated remaining-LUT INIT mutation rejected; an unaccounted wire addition rejected. These operate on temporary copies of exported HDL, not DCPs. See SLICE_MUTATION_CONTROLS.json and scripts/check_slice_mutations.py. No raw evidence was changed, no gate relaxed, no tool rerun. These controls increase confidence in this narrow checker, not convert it into a general equivalence platform.

## What is still needed

Prefer the available official/local validator components over new general infrastructure. A copied isolated wrapper can reuse existing export/module-renaming/testbench logic with explicit `xelab --mt 2`, an external process-group deadline and knownness/completion checks. It must reject skipped simulation as functional verification and preserve diagnostic logs. Fixing only the returned PASS string is insufficient: reset/interface stimulus and sampled output knownness/activity must be reviewed for this VexRiscv artifact; include both a real valid pair and an output-corrupting negative control. Finite simulation then supports a **sampled simulation** claim, not full equivalence. No such simulation is claimed run here. The original local script's auto threads/hour-scale timeouts remain unsuitable unchanged.

For a two-state-only scientific contract, the existing exact remainder + exhaustive-cut proof can be independently reviewed and used only for outputs exhibiting exactly that proved rewrite. A different changed slice, sequential primitive, INIT/state, black box, unexpected netlist/config/constraint edit, or parser failure remains a stop. Do not broaden the parser merely to make a new candidate pass.

All known OOC/constraint/source-integrity warnings remain in VALIDATION_CONTRACT.md and SOURCE_PROVENANCE.json. The public archive chain is verified, but that does not repair missing timing properties or erase the internal checksum warning.

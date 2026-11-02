# RQ1 controlled-action prepilot — round 2

**A no-explicit-physopt implementation rerun also produces a large WNS improvement on this one state.** The 97.1% ratio below is only an arithmetic description of observed differences, not a causal contribution or cross-state estimate. The default router itself performs internal physical synthesis; see ROUND2_REVIEW.md. This is an instrumentation result, not an engineering-capability or generalization result.

| Condition | WNS ns | TNS ns | Setup failing endpoints | Measured process wall time |
|---|---:|---:|---:|---:|
| Original checkpoint, read/report | −1.654 | −671.139 | 1,937 | combined contract audit 42 s |
| Write/reopen without implementation | −1.654 | −671.139 | 1,937 | included above |
| No edit, then `route_design` | −0.885 | −636.195 | 1,897 | 64.528 s |
| `phys_opt_design -directive Default`, then same `route_design` | −0.862 | −632.947 | 1,914 | 101.466 s |
| Independent no-edit `route_design` confirmation | −0.885 | −636.195 | 1,897 | 64.264 s |

All report WHS 0.042 ns, THS 0, WPWS 0.001 ns, TPWS 0. No constraints changed. The no-edit runs preserve the entire exported functional representation; serialization also preserves it. These are stronger bounded observations than cell counts. Default changes a LUT slice, so its complete functional-export identity check fails and the controller **stopped before Explore/AggressiveExplore**. No failed arms were dropped or replaced; their not-run status is explicit.

Comparing Default only with the original checkpoint gives 0.792 ns WNS improvement. The no-explicit-physopt router gives 0.769 ns; the observed ratio 0.769/0.792 is 97.1%. This is not an attribution of independent contributions: the router and added physopt can interact. Default's residual advantage is 0.023 ns, takes roughly 37 s more, and has more failing setup endpoints than the no-edit result. No post-hoc composite ranking or claim of a winner is made. Only the no-edit contrast received an independent confirmation, whose displayed timing matches exactly; this is two technical runs, not a variance estimate across seeds/designs. Default is not independently confirmed.

## Correctness evidence and stop

The official functional validator is finite simulation plus structural compatibility, with possible structural-only PASS when simulation is skipped. The current local version uses `--mt auto` and longer internal timeouts, so it was not launched under this round's caps. No simulation PASS or formal-equivalence claim is inferred.

After stopping the panel, source comparison isolated Default's change to one removed LUT2, one added LUT2, one replacement LUT6 and one new intermediate wire. The rest of the exported HDL is byte-identical after removing only generated Date/Command comments and the two explicitly accounted `PHYS_OPT_MODIFIED` metadata attributes. The standalone narrow checker exhausts all 128 assignments to seven cut inputs and finds zero mismatches at the changed output. LUT index ordering was checked against installed Vivado 2025.1 `LUT2.v` and `LUT6.v` models (I0 is the least-significant INIT index bit).

This is a conditional **two-state Boolean local-rewrite proof** with exact unchanged-remainder evidence, not four-state/X/Z equivalence, full original-spec correctness, timing equivalence, or an independently proved exporter. It is deliberately scoped to these actual two netlists and refuses other changes. The initial checker attempt stopped on an overly broad attribute-count assumption; it was corrected to account only for the two added instances' adjacent attributes. The successful proof and script are retained. It did not automatically reopen the stopped panel.

Recommendation: stop this batch at the instrument/contract-repair milestone. Before further logic-changing arms, establish a reviewed acceptance contract for two-state sequential equivalence versus four-state simulation, with appropriate independent negative controls. Do not add an LLM. A future bounded route-only/placement-only panel may reduce verification burden, but would be a newly frozen experiment, not a replacement of unrun arms here.

## Timing and source contract

Comparison is scoped to unchanged `clk_fpl26contest` OOC constraints, 1.570 ns period. Missing input/output delays (115/136), HD.CLK_SRC and OOC partition-pin locations limit interface and clock-model claims. Default DRC has 12 warnings and explicitly incomplete OOC connectivity coverage. These facts do not authorize adding constraints to manufacture QoR improvements.

Source chain now independently closed: existing 709 MiB archive SHA256 matches the official v1.3.0 checksum; its VexRiscv member SHA256 matches the exact input file. Its MIT assignment was read in LICENSE-BENCHMARKS.txt. Vivado's input integrity warning therefore occurs on the exact publicly released bytes; its internal cause remains unexplained. No new full archive downloaded; source file was not regenerated or edited. See SOURCE_PROVENANCE.json.

Native-agent information exposure was independently checked: the existing agent receives timing/fanout/spread analysis before model selection. No native agent has been tested; hiding that context would create another policy condition. Fixed/random online selectors, candidate generation, state-dependent ranking crossovers and cross-family generalization have not been tested. LATCH already studies action control granularity/branching, so those are not proposed novelty.

## Budget, paths and commands

This round: **272.258 s** measured serial EDA process wall time including the 42 s contract audit, far below 2,700 s. Every tool process used two threads and a 600 s timeout (+10 s termination grace); no timeout or paid call. A local shell-quoting failure prevented an initial confirmation-launch command from reaching COMPUTE_HOST; the corrected copied-script invocation ran once. Controller SSH disconnected after the confirmation, but a fresh SSH read verified exit 0 and the completed ledger, then all evidence was copied locally. No experiment outcome remains uncertain.

Remote owner directory: `/workspace/work/rq1-prepilot-20261102/`. Local owner directory: this `prepilot/` under branch `prepilot/rq1-action-panel-20261102`. No other thread directory modified. Raw evidence in gitignored `logs/`: contract/, noop_1/, default_1/, noop_confirmation/, panel_ledger.json and confirmation_ledger.json, plus controllers/STOP_REASON. Toolchain source repository remains clean at f4de013. No job remains running or queued.

Scripts in scripts/: baseline_contract.tcl, action_arm.tcl, run_guarded_panel.py, confirm_noedit.py and prove_default_lut_slice.py. Each executed arm's command.json contains the full exact argv. The three action/confirmation processes source the existing toolchain .env and use its Python, after checking MCP import, executable and RapidWright directory. No secrets printed or copied. No commits, pushes or publications.

## Next scientific decision

Continue RQ1 only if a frozen panel produces a state-dependent action-ranking crossover that survives a credible correctness contract and independent confirmation. The present result instead strongly motivates retaining both original-state and no-edit-implementation controls: otherwise tool reimplementation can be misattributed to action selection. Alternative explanations still include route-engine automatic optimization, input-state quality and uncontrolled seed/environment effects; there is no evidence of population-level agent incompetence or benchmark-wide bias.

Parent coordination: COMPUTE_HOST has existing Vivado 2025.1/RapidWright/MCP, public FPL26 DCPs and rootless OpenROAD 26Q2 container. Native yosys/abc were not located in the initial PATH inventory. Only this RQ1 directory owns the new outputs; no ongoing heavy computation competes with RQ3/RQ4.

# RQ1 completed controlled pair: no incremental WNS gain from routing_opt

**A real, contract-passing A/B comparison is complete.** On this original VexRiscv state, adding explicit `phys_opt_design -routing_opt` before the same `route_design -no_psir` gives no reported contest-clock WNS improvement. It costs more wall time. This pair therefore does not supply an attractive WNS-based choice opportunity under the frozen engineering screen; do not expand designs/models from this result.

## Actual outcomes

| Condition | WNS ns | TNS ns | Failing setup endpoints | Process wall s | Explicit physopt s | Completion route s |
|---|---:|---:|---:|---:|---:|---:|
| A: no explicit action → route_design -no_psir | −0.885 | −636.195 | 1,897 | 62.462 | 0 | 33.898 |
| B: routing_opt → same completion | −0.885 | −636.147 | 1,897 | 79.862 | 27.997 | 23.196 |

Both start from the exact original input SHA256 `8baf6451f9b20b8a82f035d14187c7350529a6ea0330e02d93c7100b19753149`, clock period 1.570 ns, initial target WNS −1.654 ns. B−A reported WNS difference is **0.000 ns**. Direct target-clock SLACK query, rather than only all-clock summary, was recorded; the returned value is −0.885 in both. Do not interpret that as exact physical zero below tool-return precision.

TNS improves by 0.048 ns in B; this is a secondary observation, not grounds to replace the predefined primary endpoint after seeing a WNS tie. Because that secondary metric differs, do not claim the entire QoR or physical state is identical, or that A strictly Pareto-dominates B. Both have WHS 0.042 ns / THS 0, WPWS 0.001 ns / TPWS 0, 2,937/2,937 routable nets fully routed, zero route-error nets, no DRC Error/Critical Warning rows. No PSIR phase executed. Existing OOC/unconstrained-interface/internal-source-checksum warnings remain as previously documented; no timing constraints changed.

B's process wall cost is 1.279× A (+17.400 s). Its explicit action cost is partly offset by shorter completion routing. These are observed whole-pipeline/stage costs, not isolated algorithm costs under equal internal cache state. The same source-hash warm-read policy, fresh processes, environment loading, tool build, two-thread cap and completion command were used; process stages are intentionally different. OS caches and undocumented randomness were not equalized. No supported explicit implementation seed was verified or set.

## Identity protocol v2 and verification

The original ROUND3 failure and raw ledger remain unchanged. v2 fixes export naming, not eligibility after looking at QoR: both snapshots use identical **short relative scratch filenames** inside each process's private working directory, and copy results to separate retained before/after names.

`identity_v2.py` verifies the exact expected short export command; it ignores only one generated Date line in a confirmed comment-only preamble. Every other header line remains compared, and the entire HDL from `timescale to EOF—including directives, attributes, comments, primitives, wiring and state parameters—is included. XDC is compared in full, including comments/commands. No broad metadata removal, parser expansion or local proof substitution occurred.

Ten pre-run copy-based boundary controls passed: real bodies under the synthetic short-command header accept Date-only variation; changed timescale, LUT INIT, added body synthesis comment, added directive, added wire, changed clock period, changed XDC comment and old wrapped command are rejected. Those are local instrument checks, not DCP simulations. Actual emitted v2 exports then passed **both** within-arm before/after identity and cross-arm original-representation/XDC identity. Runtime logs independently corroborate exact action/completion commands, 2 CPUs and PSIR absence.

This establishes unchanged exported modeled logic/constraints conditional on the vendor exporter/primitive semantics. It does not prove original-spec correctness, full interface timing signoff, independently checked exporter correctness or hardware frequency. Unlike Default, these actual outputs require no accepted logic-changing exception to the identity contract.

## Decision, costs and limitations

Both conditions passed the frozen validity contract. WNS gain **0 ps** is below the previously specified **50 ps engineering screening hypothesis**; this is not a significance or noise test. Accordingly the controller stopped after the first pair. No B/A or A/B confirmations were scheduled; one observation per condition cannot estimate within-arm variation, confidence intervals or robustness to seeds. The median field for one pair is simply that pair's value; within-arm noise ranges are null, not claimed zero. Other previous batches are not pooled as technical repeats of this protocol.

Continuation tool-process wall total **142.324 s**; controller wall **142.363 s**, versus <=900 s allowed. Each process stayed below its 290 s nominal / 300 s including kill-grace cap. Combined with the preserved earlier false-rejection baseline, round-3 tool wall is **204.864 s**. No timeout, extra candidate, new state, model/API/GPU, full dataset download or paid call. Controller exit 0; all sessions ended and no pilot process remains. Existing source toolchain checkout remains clean.

One state and two specific pipelines cannot show that all legal actions tie, refute RQ1 globally, identify an Agent capability, establish causal shares, or justify moving directly to another design. The action effect is defined **after common completion**; no intermediate-stage result is substituted for the frozen final endpoint. The useful finding is that explicit routing_opt adds no primary-metric value to the chosen completion pipeline here, despite both pipelines improving substantially over the original artifact.

Recommendation: retain this runnable instrument and negative pair as evidence. Do not spend on LLMs or repeat this sub-threshold contrast. If the parent later selects another action hypothesis, choose a mechanism expected to address a distinct observed bottleneck and freeze its correctness/cost contract before results; do not opportunistically search actions until one clears 50 ps. No additional experiment is started by this recommendation.

## Audit paths and versions

Local: `prepilot/logs/physical-only-v2/` (gitignored), including command.json per arm, before/after HDL/XDC and timing, target-clock TSV, route/DRC reports, checkpoint outputs, ledger, decision, controller logs and script hashes. Machine summary: ROUND3_V2_SUMMARY.json; controls: IDENTITY_V2_CONTROLS.json. Independent summarizer: scripts/summarize_physical_only_v2.py.

Remote: `/workspace/work/rq1-prepilot-20261102/physical-only-v2/`. Source Tcl SHA256 `07f9b9ec08abb2eea9635985ccff8383661533d606929fb40b5e5481e708b998`; identity checker `f684ae9a5ffa5335fca69cf5097bb2883763c08f6bc1411d26c8c788e9b9fb43`; controller `935ef408455da58758cbf4ae64873ef313ea8b40c0207f83621f4d27fe29b66e`. Both tool processes use installed Vivado 2025.1 build 6140274, sourced project .env Python/MCP preflight, two threads, no explicit seed.

RQ4 baseline was reviewed but not reused because it starts from a different already-rerouted checkpoint and uses a different identity screen. Its files were read-only; no other thread directory modified. Branch remains prepilot/rq1-action-panel-20261102; no commit, push or publication.

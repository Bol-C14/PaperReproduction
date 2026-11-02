# Second independent family: completed mini-ISP pair, sub-threshold action difference

**Stop model/ranker/command expansion.** The independently selected AMD mini-ISP state passes the same v2 instrument, but explicit routing_opt adds only **9 ps reported WNS improvement** to the common completion flow. It does not meet the predeclared 50 ps engineering screen. No confirmation or further design/action was run.

## Selection and source before results

Selection rule and all 19 candidate/not-selected reasons were recorded in SELECTION.json before EDA: exclude VexRiscv family, require clear public bundled license, independent design function, existing compatible toolchain, then choose smallest checkpoint by bytes. Selected AMD mini-ISP image pipeline (not CPU), 3,948,685 bytes, explicit MIT assignment in LICENSE-BENCHMARKS.txt. No candidate was selected by action gain or published optimizer result; no outcome-driven substitution occurred.

Original input SHA256 `31214db16b5a69e8e526ce499de7544a7816ac986e3af9cb98d971887fbd5fa6` matched the exact member of the existing official v1.3.0 benchmark archive, whose public/local SHA256 is `14d66b7b32171f20be9aa26eb395fdb75b881555854dfa2fa7b870f30d8b71ac`. Source https://github.com/Xilinx/fpl26_optimization_contest/releases/tag/v1.3.0. No new large download or input modification. This is the sole additional family; no third family.

## Actual comparison

| Condition | Target WNS ns | TNS ns | Setup failing endpoints | Process wall s |
|---|---:|---:|---:|---:|
| Original retained/read, no implementation | −1.686 | −2843.377 | 4,887 | observed in before snapshot |
| A: original → route_design -no_psir | −1.686 | −2843.377 | 4,887 | 63.097 |
| B: original → phys_opt_design -routing_opt → same completion | −1.677 | −2843.489 | 4,887 | 82.236 |

Both fresh processes read the same immutable original, with identical before HDL/XDC and target-clock metrics. Target clk_fpl26contest period 1.570 ns is unchanged. Both before and after snapshots preserve the entire functional-export representation under v2 (only generated preamble Date omitted); XDC is compared **in full**. Both route commands verified exactly `route_design -no_psir`, no PSIR stage, two CPUs in runtime messages, 6,837/6,837 routable nets fully routed, zero routing-error nets. Both WHS 0.023 ns / THS 0; WPWS 0.001 ns / TPWS 0; no DRC Error/Critical Warning. DRC has 53 advisory warnings (DPOP-3 ×40, DPOP-4 ×12, RTSTAT-10 ×1).

B's explicit action took 29.597 s; A/B completion routing took 30.179/19.372 s. B total process wall is 1.303× A, +19.139 s **in this one observed pair**. Cached/thermal/resource effects were not equalized; this is not a stable action-cost estimate. Same per-arm hash-read warm-input policy and fixed two-thread settings do not equalize in-process warming from the added action or OS cache state. No explicit implementation seed control was claimed.

WNS improvement 0.009 ns is below the 0.050 ns **engineering screening hypothesis**, not proven below a noise floor or statistically insignificant. TNS is 0.112 ns worse, so do not substitute a new favorable composite metric or call all QoR equal. Only one run per condition: no variation estimate, confidence interval, seed robustness or independent confirmation. The controller correctly did not take the preauthorized optional reverse-order pair; the outcome did not meet its trigger.

## Validity and interpretation

The exporter identity check is conditional on the same Vivado/primitive semantics, not independent full specification/hardware signoff. Source DCP's internal integrity warning is present despite its exact official-archive member hash match; no regeneration or warning suppression. The clock port aclk lacks HD.CLK_SRC; 100 input / 137 output ports lack I/O delay; zero unconstrained internal endpoints reported. OOC route/DRC limitations remain. Compare frozen contest internal-clock timing; no interface signoff or actual hardware Fmax claim.

Original worst setup path is reported as 2.888 ns data delay, 0.361 ns logic and 2.527 ns route (~87.5% route). That observation is post-selection diagnostic context, not an action-benefit label. A large route fraction does **not by itself demonstrate useful marginal benefit** from this specific legal routing_opt option after common completion.

Together with the first-family result (VexRiscv incremental WNS 0 ps), this second-family 9 ps observation provides no attractive controlled-choice opportunity under this particular two-pipeline action definition. It does not prove all actions equivalent, that no Agent can help, or that RQ1 is false. Unlike VexRiscv, mini-ISP's no-action completion does not improve original WNS here, so the earlier completion gain is not universal. Do not pool families/states/earlier protocol variants as random repetitions or infer a population causal contribution from two selected small examples.

Recommendation: retain a calibration/action-space finding; stop Agent/ranker/more-same-command expansion as instructed. Before any new experiment, reformulate the scientific action-space question with a mechanism/evidence reason; this result is not permission to search for a win. No new design, action, model, fee or task is scheduled by this recommendation.

## Cost, transport and reproducibility

Tool-process wall 145.334 s; controller wall 145.407 s, below this separate round's 1,200 s budget. Each process <300 s including permitted grace; no timeout/retry/tool failure. Two threads serial. Controller exit 0; source checkout clean and no job remains. All failed earlier RQ1 instruments retained, but not counted as mini-ISP samples.

SCP disconnected after some evidence transferred. Eight missing/truncated noncheckpoint files were identified against a remote SHA256 manifest, individually recovered and all bytes reverified; no experiment rerun. Remote checkpoint hashes recorded separately; large missing checkpoint was not fetched just to repair report transfer. TRANSFER_AUDIT.json / REMOTE_SHA256SUMS.txt distinguish remote checkpoint hash from locally checked report bytes. Subsequent independent local whole-HDL/XDC and timing-row checks agree with the remote ledger. No outcome is uncertain.

Local evidence: ../logs/second-family-miniisp-v1/. Remote: `/workspace/work/rq1-prepilot-20261102/second-family-miniisp-v1/`. command.json per arm, scripts.sha256, target TSV/timing/DRC/route, HDL/XDC, decision/controller receipts preserved. Tool: Vivado 2025.1 build 6140274; identity checker SHA256 f684ae9a5ffa5335fca69cf5097bb2883763c08f6bc1411d26c8c788e9b9fb43; unchanged Tcl 07f9b9ec08abb2eea9635985ccff8383661533d606929fb40b5e5481e708b998; controller 6e61b9beac0c10a1232dd9c22cda99ada68e64da60a67b78e4fa722d6d689de8. Existing project .env Python/MCP preflight used; no contents or credentials exported.

**First-pass archive is frozen and unchanged.** This second-family result is not inserted into its ZIP or Library item. First ZIP SHA256 4e995fc76a16c81cc07fcc3f15994a1d08cfcff88791a3cd4b07dbf2e020d0ee, Library ID PRIVATE_LIBRARY_REFERENCE; FIRST_PASS_HANDOFF Library ID PRIVATE_LIBRARY_REFERENCE. That archive correctly describes the first pass's one-family scope; this addendum brings completed controlled pairs to two independent families, one state/pair each. No LLM experiment, commit, push, publication or paid resource.

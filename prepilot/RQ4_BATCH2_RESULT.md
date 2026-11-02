# Batch 2 result: legal bounded route attempts, no matched pair

**Do not dispatch a future-target evaluation.** Both completed route candidates preserve their exported logical representation under the prospective timestamp-v1 screen and match WNS, but fail the frozen TNS and endpoint-count matching rules. This is a useful construction failure, not a future-adaptability effect or proof that RQ4 is false globally. No third path, tolerance change or future evaluation was attempted.

## Actual commands and the PSIR correction

Before any candidate, installed Vivado 2025.1 help showed that ordinary route_design includes PSIR. The originally staged Default/RuntimeOptimized directive paths were NOT run. Pre-outcome amendment `RQ4_BATCH2_PREEXEC_AMENDMENT.md` replaced them with:

1. `route_design -no_psir` (RouteNoPSIR).
2. `route_design -no_psir -tns_cleanup` (RouteNoPSIRTNS).

Each independently read the completed RQ1 no-op rerouted checkpoint `/home/shugu/work/rq1-prepilot-20261102/noop_1/output.dcp`, SHA256 `571d5489a1e0d5bc62d8eb38c8bfe9cc222cd8a056f96b604b98bad50d579c96`. Input hash checked before each run and after all checks, unchanged. Vivado 2025.1 build 6140274, maxThreads=2, fresh process, 290s TERM plus 10s kill grace. Script hash `53e7ff0d93a45faa3e4b01cb5ff3b7c827807546270a83250a6619122ffccf65`. Commands/export/checkpoint actions are retained in Tcl/log/journal; output root `/tmp/rq4-batch2-20261102/`.

## Measured current outcomes

| Metric | Source / RouteNoPSIR | RouteNoPSIRTNS | Frozen pair gate |
|---|---:|---:|---|
| WNS (ns) | -0.885 | -0.885 | Pass: delta 0 <=0.020 |
| TNS (ns) | -636.195 | -628.382 | Fail: 7.813 ns / mean absolute TNS = ~1.236% >1% |
| Failing setup endpoints | 1897 | 1870 | Fail: 27 / mean count = ~1.434% >1% |
| WHS / THS (ns) | 0.042 / 0 | 0.042 / 0 | Pass |
| WPWS / TPWS (ns) | 0.001 / 0 | 0.001 / 0 | Same reported values |
| LUT / FF / BRAM tile / DSP | 1906 / 1199 / 6 / 4 | 1906 / 1199 / 6 / 4 | Same reported usage |
| Route report | 2937/2937 routed, zero error nets | Same | Pass scoped vendor check |
| DRC | 12 warnings: DPIP-2 x8, DPOP-3 x3, RTSTAT-10 x1 | Same | No new reported category/count |

These are current contest internal-clock metrics, not whole-interface signoff or a closed-timing implementation. Both retain original unconstrained-I/O/clock-source/OOC validity limitations documented by RQ1. TNS cleanup changed the broader path distribution while retaining worst slack. That is a current objective effect, not measured future value.

The 0.010/0.020/0.030 ns prospective WNS sensitivity grid yields the same rejection, because the TNS/endpoint gates fail independently. No looser sensitivity threshold substitutes for the primary result.

## Logic and physical-difference evidence

For each before/after EDIF pair, exact raw bytes differ; the timestamp-v1-only transformation makes all remaining bytes identical. Cross-candidate timestamp-v1 EDIF is also identical (see result JSON). This supports unchanged exported logical representation, conditional on exporter/primitive semantics. It is NOT a formal equivalence or independent full physical-function proof. No metadata other than the declared numeric status/written timestamp was removed.

Before/after XDC full diffs contain only the generated `# Command Used: write_xdc .../before.xdc` versus `.../after.xdc` comment; all constraint command text is unchanged. This was directly inspected rather than applying a broad comment-removal rule. Source clock and timing contract remain unchanged.

Checkpoint route/placement payload bytes differ, but serialized physical database differences do not alone prove distinct semantic physical states. Tried the existing RapidWright DesignComparator with `JAVA_TOOL_OPTIONS=-XX:ActiveProcessorCount=2`, 85s timeout +5s grace. It exited 1 after ~1s before comparing: reading the DCP requested a readable EDIF conversion and failed because `vivado` was not on PATH. No physical-comparison result exists. No retry, environment/configuration change or alternative wrapper was introduced, since current matching already rejects the candidate pair. Do not describe this failure as a denied permission or a missing license.

RouteNoPSIR has identical reported timing to the source; without the physical comparison, source versus this output is NOT an accepted distinct physical state pair. RouteNoPSIRTNS has altered current timing, but is excluded by the frozen matching rules. A bigger checker effort would not fix those rules' failure.

## Cost and failures

- Candidate 1: exit 0, 11:46:29–11:47:26 UTC, 57s process wall, peak reported memory ~4.55GB.
- Candidate 2: exit 0, 11:48:13–11:49:05 UTC, 52s process wall, peak ~4.55GB.
- Candidate process wall total 109s; all opening, reports, exports and checkpoint writes included. No automatic retry or timeout.
- Two help-only sessions ~3s each; first returned help but failed to print it, second captured returned text. No design loaded by these probes.
- Physical comparator failed in ~1s; no retry. Total instrument process wall approximately 116s; exact OS CPU seconds were not collected and are not inferred from wall time.
- Measured remote window from initial environment/input check 11:44:22 to final input check 11:50:30 is 368s (6m08s), including coordination/copy/check overhead between calls; local staging preceded this by under a minute. All work stayed below 16min. Two candidate processes were serial, each under one minute; helper comparator ran after both completed.

No API/LLM/GPU/new downloaded software or financial charge. All tool sessions completed; no background task remains. Native toolchain/checkpoint/SSH/security configuration unchanged. Raw design/log artifacts copied to gitignored `prepilot/batch2_logs/`; no push or publication. Some standalone shell-controller details from the proposal were superseded by two explicitly separate checked invocations; each actual candidate had its own timeout. The proposed outer 960s controller was not executed; actual elapsed time above is the measured bound, not a claim it enforced an outer deadline.

## Recommendation

Stop this two-path construction batch. Accepted distinct-path matched pairs: zero. Future goals attempted: zero. H1/H2/H3 remain untested. Do not enlarge the checker or execute the six-process future gate to rescue a pair that fails current matching. Parent can park RQ4 behind RQ1/RQ3, or explicitly authorize a new separately frozen construction hypothesis later; this batch supplies no basis for immediate future-adaptation claims.

# RQ1 first-gate result

**Go for a bounded action-panel preparation, not yet for a paper capability claim.** An actual existing FPGA checkpoint completes read, report, write and reopen in Vivado 2025.1. No optimized arm has run, no action effect/noise estimate exists, and no LLM/API was called.

Successful command (after sourcing the existing project `.env` and checking its Python/MCP, executable and RapidWright):

```bash
run_dir=/tmp/scientific-prepilot-20261102-smoke
timeout --signal=TERM --kill-after=10s 120s "$VIVADO_EXEC" \
  -mode batch -notrace \
  -source "$run_dir/scientific-prepilot-20261102-checkpoint_smoke.tcl" \
  -log "$run_dir/vivado-attempt3.log" \
  -journal "$run_dir/vivado-attempt3.jou" \
  -tclargs \
  /workspace/work/fpl26_optimization_contest_ablation_shu/fpl26_contest_benchmarks/vexriscv_re-place_2025.1.dcp \
  "$run_dir" > "$run_dir/stdout-attempt3.log" 2>&1
```

Local script: `scripts/checkpoint_smoke.tcl`; remote copy has the longer basename shown above. Two threads set inside Tcl. Input SHA256: `8baf6451f9b20b8a82f035d14187c7350529a6ea0330e02d93c7100b19753149`.

## Observations

- Successful run remote exit code **0**, tool-internal read/report/write/reopen time **28,697 ms**; start 11:21:23 / exit 11:21:55 UTC (from log). SSH controller returned 255, so success was separately checked by a new read-only SSH call against the remote exit-code file and log, then files were retrieved. This is not an uncertain experiment outcome.
- Read and reopened counts: **3,375 hierarchical cells**, **10,951 hierarchical nets**. Counts alone are not equivalence proof.
- Route report: **2,937 / 2,937 routable nets fully routed**, **0 nets with routing errors**.
- Baseline WNS **−1.654 ns**, TNS **−671.139 ns**; **1,937** failing setup endpoints / **3,550** total. Hold WHS **0.042 ns**, THS **0 ns**.
- Check timing: **0 internal unconstrained endpoints**, but **115 inputs without input delay**, **136 outputs without output delay**. Scope subsequent comparison to the frozen contest clock/constraint contract. Do not call this whole-interface timing signoff or change constraints to manufacture improvement.
- Functional equivalence checker, full DRC, action legality for the candidate panel, action execution, repeat-noise calibration, selector comparisons and state crossovers: **not run**.

## Failures retained

Attempts 1 and 2 both exited 1 before loading a design because I referenced the wrong Tcl basename after copying it. Initial commentary attributing the first failure to a changed working directory was incorrect; direct file inspection established the basename error. Attempt 3 used a verified existing absolute filename. All attempts retained; no source DCP or existing project file changed.

## Evidence and resource ownership

Local raw evidence: `logs/scientific-prepilot-20261102-smoke/` (gitignored), containing stdout for all attempts, tool logs/journals, input hash, timing/utilization/route reports, output `noop.dcp`, and exit codes. Remote evidence: `/tmp/scientific-prepilot-20261102-smoke/`; temporary and should be copied before relying on long-term retention. Source toolchain repository clean before run, HEAD `f4de013`; no optimization script from its running jobs modified.

No background job scheduled; successful smoke completed. Only this one two-thread Vivado process was used for ~33 seconds after two failed ~3-second launches. Other threads can use COMPUTE_HOST without competing with an ongoing RQ1 run. Raw design files are not proposed for publication.

## Next bounded work

Verify the four proposed directives on this design stage; freeze a common reporting/completion protocol; implement a standalone panel runner with per-arm fresh processes and logged censoring. Run an initial four-arm panel and technical repeats only after correctness and budget treatment are settled. Then seek a second state with a changed ranking, followed by a second family. Current evidence establishes runnable infrastructure and an optimization opportunity, not state-dependent choice value or novelty.

# Batch 2 proposal — staged, not dispatched

Prior batch result remains zero accepted pairs. No tolerance alteration, retrospective canonicalized acceptance or new vendor run. Batch 2 remains pending parent allocation after RQ3 releases APRIL.

## Two paths only

Use the completed `no-op` rerouted checkpoint as the common immutable starting state: `/home/shugu/work/rq1-prepilot-20261102/noop_1/output.dcp`. Verify its SHA256 against `RQ4_RQ1_SCREEN.json` copy manifest before dispatch; the completed source is not rewritten. Both arms start from it independently; neither starts from the other's output.

1. P1 `route_design -directive Default`.
2. P2 `route_design -directive RuntimeOptimized`.

Rationale: both invoke the existing vendor router, with no synthesis, placement, phys_opt, retiming, new logic edit or global unroute command. Default versus reduced router effort may give different routes while retaining similar current timing, but there is NO assurance they will differ physically or match QoR. Existing routing is the starting point, not reset; this preserves a testable path-history question. A command-completed, logically unchanged but physically identical output is a null candidate, not a fabricated distinct state.

AMD documents rerouting on fully routed inputs and these directive names in [routing](https://docs.amd.com/r/2023.1-English/ug904-vivado-implementation/Routing) and [directive definitions](https://docs.amd.com/r/2022.1-English/ug904-vivado-implementation/Using-Directives). These references explain the choices but do not verify installed 2025.1 support. First check installed `help route_design` and reject unsupported names; do not substitute a new directive. There is no claim that generic routing guarantees unchanged logical representation (pin/other implementation remapping may occur). Accept only after the conservative logical screen, frozen clock/XDC/resource checks and native validity checks pass. Do not use Default phys_opt again in this gate, since its existing output changes logic.

Staged Tcl: `rq4_batch2_candidates.tcl`. No exact physical-only guarantee is asserted: these are route-only **candidate paths**, conditional on before/after checks. If either changes retained logical representation, reject it, preserving the reason. No third candidate and no recovery by full re-place/re-synthesis.

## Exact execution commands after parent authorization

The script must first be copied to an RQ4-owned remote directory; the command below names a proposed destination, not an already existing path. No remote file has been created for Batch 2. Environment checks use existing configuration and print no secrets.

```bash
# Local staging, only after allocation:
ssh april1 'mkdir -p /tmp/rq4-batch2-20261102'
scp prepilot/rq4_batch2_candidates.tcl april1:/tmp/rq4-batch2-20261102/

# APRIL: each candidate, fresh process; 290s TERM + 10s kill grace <=300s.
cd /home/shugu/work/fpl26_optimization_contest_ablation_shu
source .env
"$PYTHON" -c 'from mcp import StdioServerParameters'
test -x "$VIVADO_EXEC" && test -d "$RAPIDWRIGHT_PATH"
rq4_src=/home/shugu/work/rq1-prepilot-20261102/noop_1/output.dcp
rq4_root=/tmp/rq4-batch2-20261102
for rq4_directive in Default RuntimeOptimized; do
  rq4_out="$rq4_root/$rq4_directive"
  mkdir -p "$rq4_out"
  timeout --signal=TERM --kill-after=10s 290s "$VIVADO_EXEC" \
    -mode batch -notrace -source "$rq4_root/rq4_batch2_candidates.tcl" \
    -log "$rq4_out/vivado.log" -journal "$rq4_out/vivado.jou" \
    -tclargs "$rq4_src" "$rq4_out" "$rq4_directive" \
    > "$rq4_out/stdout.log" 2>&1
  rq4_exit=$?
  printf '%s\n' "$rq4_exit" > "$rq4_out/exit_code.txt"
done
```

Wrap the entire remote batch controller, including startup checks/reporting, in `timeout --signal=KILL 960s bash <RQ4-owned-controller.sh>` when actually dispatched. Controller must stop on failed environment/help/input-hash checks, run without `set -e` around candidate exit recording, and retain timeout exit codes. This is a staged command specification, not a tested controller or completed run. Do not execute until exact controller/input/script hashes are frozen and the parent releases the resource slot.

Cost ceiling: 2 threads, serial, candidate processes <=300s each INCLUDING open/report/export/write; remaining <=360s for installed-help/input checks, copy/instrument work and result screening, outer hard ceiling 960s (16 min). Max reservation 32 core-minutes; actual CPU time is measured separately. No API/GPU/new image or financial charge. Any startup/tool failure consumes the ceiling; no automatic retry or budget extension. Timeout is censored failure, not a scored output. No future-target run is part of these commands.

## Instrument revision v1, separate from the original frozen result

Known issue: DCP EDIF may be Zstandard compressed and generated status timestamps differ. Decode archive and Zstandard losslessly, then apply `rq4_timestamp_v1.py` only to the exact top-level `(status (written (timeStamp ...)))` header shape BEFORE any library/external/design content. Replace only its six numeric date/time fields by a fixed sentinel. Unknown/duplicate header shape fails closed. Do NOT remove comments, program version, names, properties, INIT/BRAM values, cell references, ordering, whitespace, or constraints. All remaining bytes must match. This is a representation comparison with an explicit metadata exception, not a general semantic checker or equivalence proof.

Four new unit tests actually passed: identical/timestamp-only positive; INIT/cell-reference/pin changes and non-timestamp text changes negative; a property named timeStamp remains significant; missing/unknown/duplicate headers reject. Tests use authored fixtures only. This does not certify all EDIF grammar corner cases; accept only the known shape. Full EDIF interpretation is explicitly out of scope. No new RapidWright wrapper or equivalence engine is needed.

This revision is prospective Batch 2 instrumentation. Original Batch 1 byte comparisons and rejection stand. The two no-op repeats would still be same-path repetitions; no metadata rule can make them independent construction paths. Default remains outside the primary current-QoR tolerance and has genuine logical changes, regardless of timestamp handling.

## Matching tolerance, display resolution and sensitivity

Primary unchanged: WNS <=0.020 ns, WHS <=0.010 ns, TNS/endpoints <=1% as v0 specifies, exact resources, identical clock/constraint/endpoint contracts and other validity checks. These are explicit pilot matching assumptions, not an industry-defined equivalence class. WNS 20 ps is ~1.27% of 1.570 ns clock period; hold 10 ps is ~24% of the observed 42 ps margin and is a potentially material confound, which must remain visible.

Existing summary reports print 0.001 ns increments (1 ps display quantization). This is not independent knowledge of physical accuracy or stochastic variance. A 23 ps versus 20 ps mismatch is not a report-rounding ambiguity; even two displayed-value rounding errors cannot bridge that gap. RQ1's two same-path reroute repeats match displayed timing, but n=2 and one state cannot calibrate universal tool noise. Future snapshots should retain raw numeric timing-path slack from the tool when feasible, plus unchanged display precision; no measurement precision beyond actual evidence is claimed.

Prospective sensitivity grid fixed before Batch 2 outcomes: WNS tolerance 0.010/0.020/0.030 ns, with ALL other primary criteria unchanged. Report eligibility counts and reasons at all three; only 0.020 determines the primary go/no-go. A pair admitted only at 0.030 is exploratory unmatched evidence and cannot replace the primary result or trigger future evaluation automatically. Do not pick a new hold/TNS threshold after outcomes. If no candidate pair passes the primary gate, stop the second small batch rather than start a larger search.

Future pressure target remains the single hypothetical G2 hold-margin scenario, not an actual requirement; no future results are collected until an accepted pair and independent parent dispatch exist.

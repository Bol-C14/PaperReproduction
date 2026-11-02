# RQ4 prepilot — completed bounded construction gates

**Current outcome: zero admissible distinct-path state pairs; no future-target evaluation and no H1/H2/H3 result.** Start with [Batch 2 result](RQ4_BATCH2_RESULT.md), [machine-readable decision](RQ4_BATCH2_RESULT.json), and [earlier artifact prefilter](RQ4_PREFILTER_RESULT.md).

Two actual serial Vivado 2025.1 paths ran with two threads: `route_design -no_psir` (57s) and `route_design -no_psir -tns_cleanup` (52s). Timestamp-only-normalized exported EDIF matched, but TNS and failing-endpoint differences exceeded the frozen 1% gates. The physical comparator failed before comparison because readable-EDIF conversion could not locate Vivado on PATH; no retry was needed to enforce the already-failed matching gate. No future experiments, model calls or paid resources followed.

## Evidence chronology

- `RQ4_PROTOCOL.md`, `RQ4_STATUS.json`, `RQ4_FREEZE.json`: initial preregistration and historical snapshot; zero implementation runs was true at that snapshot, not the final state.
- `RQ4_SELF_AUDIT.md`: static-re-scoring confound, correctness boundaries and controls.
- `RQ4_MINIMAL_CHECKER_GATE.md`, `RQ4_MINIMAL_GATE_FREEZE.json`: reduced one-pair/one-scenario plan; independent formal equivalence remained unavailable.
- `RQ4_RQ1_SCREEN.json`, `RQ4_PREFILTER_RESULT.md`: stable completed-source snapshot manifest and failed first matching gate.
- `RQ4_BATCH2_PROPOSAL.md`: historical proposed directive paths; those paths were NOT executed.
- `RQ4_BATCH2_PREEXEC_AMENDMENT.md`: before-outcome PSIR correction to the two actually executed no-PSIR paths.
- `RQ4_BATCH2_METRICS.json`, `RQ4_BATCH2_RESULT.*`: final completed-run measurements and disposition. These supersede earlier status/plans for current outcome.
- `RQ4_BATCH2_PHYSICAL_PAYLOADS.json`: preliminary source-versus-first-output serialized payload hashes only, not a complete physical comparison.

Frozen documents/scripts are retained with original bytes so their recorded hashes remain inspectable. In particular, the Tcl candidate script's original “staged” header describes its preparation time; the result reports establish the later actual invocations. Staged budget proposals are not assertions those larger experiments ran.

## Included checks and reproduction limits

Python helpers perform archive inspection, stable-copy checking, conservative byte screening, timestamp-only screening, and completed-report extraction. None is a formal equivalence checker. Eight small unit tests passed; recorded logs are `RQ4_FINAL_SCREEN_TESTS.txt` and the earlier per-instrument logs. To run only these offline fixture checks:

```bash
python3 -m unittest discover -s prepilot -p 'test_*.py' -v
```

Actual DCP-dependent analysis requires the excluded local artifacts and an appropriately licensed/configured tool environment. The public checkout does not claim to reproduce proprietary implementation runs from the small text reports alone. Paths in historical execution records identify original local/remote evidence locations; they are not portable setup instructions. No CI was added.

## Publication scope

This commit publishes the already-completed RQ4 research code, plans, audits, bounded negative results, hashes, metric extracts and fixture-test logs. It does not publish design checkpoints, full EDIF/Verilog/XDC exports, vendor installations, private configuration, credentials or Library source material. See [exclusion manifest](EXCLUDED_ARTIFACTS.json). This branch remains independent of RQ1/RQ3 and is not a merged overall study.

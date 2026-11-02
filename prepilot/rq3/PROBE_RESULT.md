# RQ3 real report probe — 2026-11-02

**Do not add models on this evidence.** Twenty real report invocations succeeded, but no naturally ambiguous decision or marginal diagnostic value was demonstrated. This is an instrument/cost result, not a negative result for information value in engineering generally.

## Execution and evidence

One Vivado 2025.1 process, `general.maxThreads 2`, 540-second timeout plus 5-second kill grace. Actual process wall time **36.861568 seconds**, remote exit **0**. Controller SSH returned 255 after disconnect; a new read verified the completed receipt, complete ledger and tool exit. No rerun. Final process check found no RQ3 jobs. An interrupted SCP was recovered by fetching the missing reports; all 20 local report hashes match the remote receipt. No outcomes remain uncertain.

Remote independent directory: `<RQ3_RUN_ROOT>/`; local scripts and raw evidence: `probe/` and `probe/public_evidence/` (sanitized; original hashes in publication manifest). Neither source DCP nor RQ1 output changed (before/after SHA256 identical).

Inputs:

| State | SHA256 |
|---|---|
| Public original VexRiscv | `8baf6451f9b20b8a82f035d14187c7350529a6ea0330e02d93c7100b19753149` |
| RQ1 no-edit route output | `571d5489a1e0d5bc62d8eb38c8bfe9cc222cd8a056f96b604b98bad50d579c96` |

Recorded launcher (machine paths replaced with role placeholders):

```bash
cd <TOOLCHAIN_ROOT>
source .env
"$PYTHON" -c "from mcp import StdioServerParameters"
test -x "$VIVADO_EXEC"
test -d "$RAPIDWRIGHT_PATH"
"$PYTHON" <RQ3_RUN_ROOT>/run_probe.py
```

`probe/public_evidence/receipt.json` records recorded Vivado argv with role placeholders; the unredacted original remains local. The controller runs `timeout --signal=TERM --kill-after=5s 540s`, invokes the absolute `report_probe.tcl`, and passes output directory plus the two input paths. No route, optimization, checkpoint writing, model invocation, or paid service occurred.

## Measured cost, milliseconds

Each state was opened once. First and warm-regenerate commands ran sequentially in the same loaded process. This is a warm-engine comparison, not cold-OS-cache calibration.

| Observation | Original first | Original warm regenerate | Updated first | Updated warm regenerate |
|---|---:|---:|---:|---:|
| Open checkpoint (once) | 16683 | — | 9701 | — |
| Timing summary | 1287 | 169 | 1298 | 165 |
| High-fanout nets, max 20 | 117 | 119 | 121 | 122 |
| Detailed setup paths, max 50 | 134 | 131 | 126 | 125 |
| Default complexity | 107 | 147 | 111 | 110 |
| Default congestion | 101 | 107 | 140 | 98 |

Reading already-generated files in Python cost **13.710–84.997 microseconds per file** in an uncontrolled OS cache. This excludes SSH transfer, parsing/model use, scheduler delay and cold-disk effects. It is not a diagnostic price. Most runtime was loading/startup rather than incremental queries; a model that already has an open state should not be charged a fresh 17-second load for every query. Conversely, cached retrieval cannot be priced as new generation. No repetitions across independent processes or congestion levels were run, so these are individual observations, not stable cost estimates.

## Information and freshness findings

- Preserve native initial timing/fanout/spread and any existing detailed-path analysis. The new probe did not delete or hide them. No agent ran or saw a reduced context.
- Detailed paths expose original WNS −1.654 ns and a worst-path split of 0.507 ns logic / 2.641 ns route; updated timing reflects the already-known RQ1 no-edit reroute improvement. These are additional representations, not demonstrated nonredundant information relative to the full native context.
- Both default complexity reports say no qualifying cells, therefore no complexity report was generated. Successful Tcl return is not useful measurement coverage. This is about the default report parameters, not proof that the design has no complexity structure.
- Original congestion report contains *Placer Final Level* and no windows above level 5. Updated report additionally exposes *Router Initial Congestion*, also with no effective windows above level 5. Thus the report contains implementation-stage historical metadata, not a newly run congestion experiment. A fresh report file/time does not mean all data were freshly measured. Missing original router-initial data must not be interpreted as zero original congestion.
- First/warm report bodies for timing, detailed paths, congestion and complexity are exactly equal within each state after excluding headers. Their raw hashes differ because Date/Command/output-path headers differ; path report header separator width also changes. Do not infer observation changes from raw file-hash differences. Fanout contents also agree after excluding Date/Command headers.
- Report labels disagree in scope: original detailed timing says `Fully Placed`, while report-design-analysis says `Routed` and RQ1 route-status counts all routable nets routed. Preserve these raw labels; do not collapse them into an assumed implementation stage or use filename `re-place` as stage evidence. Determine command legality from the frozen tool/state contract.

These observations do not establish an information-induced action change. No downstream action, utility, model selection, or causal information treatment ran. No decisive natural diagnostic ambiguity was found in these two related states. Current new-report candidates should be pruned for this pair rather than manufacture ambiguity by concealing native information.

## Revised gate and next scientific step

This section supersedes the overly restrictive crossover gate in PLAN.md. Verified action-rank crossing is a strong witness, **not necessary**: information can change whether to retain baseline, execute, stop, or validate under real cost/risk. RQ3 requires evidence of a material budget-feasible decision change beyond already-visible information, not necessarily a change in ranking among fixed interventions. It need not wait for RQ1 to find a crossover.

For this pair, stop before models. A future task can first audit a different naturally changing state or a genuinely costly diagnostic (e.g., a fresh implementation-dependent observation unavailable from already-generated metadata). Select it on ordinary engineering conditions rather than known outcome labels; freeze source, legality and validation before running. No expanded candidate run or further resource reservation is proposed here.

## Validator limits

`protocol.py` remains a receipt-check sketch. Its synthetic test does not hash the actual DCP itself, authenticate timings, implement an event ledger, charge failed calls persistently, check report semantics/stage, or validate functionality. It was not used to certify this run. Evidence here comes from the explicit process receipt, tool ledger, raw reports and input pre/post hashes; engineering validity and information value remain separate.

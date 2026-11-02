# Scientific prepilot first pass — RQ1 handoff, 2026-11-02

**Completed:** one real original-state VexRiscv paired experiment with fixed actions, shared completion, validity checks and explicit costs. **Result:** adding routing_opt gives no reported WNS gain and costs 1.279× the no-explicit-action baseline. No LLM experiment occurred.

| Latest validated comparison | WNS ns | TNS ns | Process wall s |
|---|---:|---:|---:|
| A: original → route_design -no_psir | −0.885 | −636.195 | 62.462 |
| B: original → routing_opt → same route | −0.885 | −636.147 | 79.862 |

Both preserve complete exported modeled logic and XDC, are fully routed with zero routing-error nets, meet reported hold/pulse constraints and have no DRC Error/Critical Warning. These remain exporter-conditional representation checks under the frozen OOC contest-clock contract, not independent source-spec/hardware signoff. One run per condition; no variance estimate. One design family only, with related source/rerouted states—not independent designs.

## Review order and status

1. **ROUND3_V2_RESULT.md / ROUND3_V2_SUMMARY.json:** final actual pair and no-expansion decision. Two successful processes, 142.324 s total; 50 ps screen not reached. That screen is a proposed engineering-value hypothesis, **not statistical significance or measured tool noise**.
2. **ROUND3_V2_FREEZE.md**, scripts/physical_only_arm_v2.tcl, identity_v2.py, run_physical_only_v2.py; logs/physical-only-v2/{A1_noop,B1_routing_opt}/command.json and raw reports. Exact original input hash, tool/script hashes and stage costs retained.
3. **ROUND3_RESULT.md / SUMMARY.json:** prior first-condition false rejection. Generated Command comment wrapped at long path; frozen checker stopped. Not retrospectively changed to pass. ROUND3_HEADER_DIAGNOSTIC.json / EXPORT_DIFF.txt prove the difference was only generated metadata. Versioned short-name repair passed ten positive/negative copy-based controls before new actual execution; IDENTITY_V2_CONTROLS.json.
4. **ROUND2_RESULT.md / REVIEW.md / AUDIT.json:** original versus serialization versus no-edit default-router versus Default. The 97.1% ratio is a single-state arithmetic ratio of observed WNS differences, **not causal contribution or an Agent result**. Default's 23 ps incremental observation is unconfirmed, no repeat was run. Its local two-state LUT certificate has explicitly narrow scope. The default router contains internal physical synthesis, hence is not a no-optimization control.
5. **SMOKE_RESULT.md / json:** real initial read/report/write/reopen smoke. Its two filename-startup failures and all later setup/checker failures remain in SETUP_FAILURES.json and original logs.
6. **VALIDATION_CONTRACT.md / SOURCE_PROVENANCE.json / RANDOMNESS_SUPPORT.md:** missing I/O delays, HD.CLK_SRC/OOC caveats; public input archive chain; MIT assignment; no verified explicit implementation seed. Do not call process repeats different-seed trials.

Historical NEXT_GATE/PANEL documents describe proposals and stage-specific states; the final completed-run reports above supersede their scheduling/readiness assumptions. `physical_only_arm_staged.tcl` is staged history, not a tool run. Official validator source is source-inspected, not executed. Future confirmations and new designs/models remain unrun. Do not combine these categories or treat offline controls as live experiments.

## Source, versions and reproducibility

Repo https://github.com/Bol-C14/PaperReproduction.git; base 809ca20e003c2f5d5a723c77ead8a6de532e4539; branch prepilot/rq1-action-panel-20261102. Toolchain source f4de013, installed Vivado 2025.1 build 6140274. Existing .env sourced; its Python/MCP/tool prerequisites checked without copying environment contents. All actual RQ1 EDA processes two-thread and bounded, serial. No credentials/security/SSH configuration changes.

Official archive URL https://github.com/Xilinx/fpl26_optimization_contest/releases/download/v1.3.0/fpl26_contest_benchmarks_v1.3.0.tar.gz; archive SHA256 14d66b7b32171f20be9aa26eb395fdb75b881555854dfa2fa7b870f30d8b71ac. Original member vexriscv_re-place_2025.1.dcp SHA256 8baf6451f9b20b8a82f035d14187c7350529a6ea0330e02d93c7100b19753149. The exact member matches the existing input; original Vivado integrity warning remains documented. No DCP is bundled.

Research agenda Library ID PRIVATE_LIBRARY_REFERENCE; original text SHA256 5fbe2829ca65017ba5eb05356e53069144e3879f9d9743a91f559a9729aff3cc. Literature leads are not all verified novelty claims; LATCH already covers action granularity/branching.

Raw HDL/XDC exports are included to reproduce the narrow representation checks and LUT certificate; these are benchmark-derived evidence, not private environment configuration. DCPs, caches, credentials, .env/SSH files and unrelated data are excluded. Run local read-only checkers against the unpacked folder if desired; there is no automatic execution. Actual EDA reproduction requires the separately sourced original benchmark and licensed existing toolchain; commands are recorded, not auto-launched.

## Other-route snapshots (read-only copies, not this thread's independent reruns)

`other_routes/RQ3/` copies the completed probe result, original plan marked historical, receipt and timing ledger from task-2. It records 20 report invocations, limited freshness/cost findings and no demonstrated marginal decision value; no model/action experiment. `other_routes/RQ4/` copies completed current-state candidate-construction protocol/amendment/results from task-3. Its no-PSIR/TNS-cleanup candidates fail the frozen pair-matching rules; no future-target evaluation ran. These limited negative screens **do not refute RQ3 information value or RQ4 optionality generally**. Source paths/hashes are in other_routes/SOURCES.json; stale earlier status files were deliberately not selected. Source files were not modified.

## Closeout

No RQ1 job running, no paid/API/GPU use, no commit/push/publication. Do not move to another design/model on this tie alone. The main deliverables are the working controlled-pair instrument, preserved failures, explicit completion baseline and a meaningful negative first pair. New action hypotheses require an engineering reason and a separately frozen experiment, not searching until an attractive result appears.

Verify MANIFEST.json and SHA256SUMS for every packaged file; external ZIP .sha256 authenticates the archive. RQ1 raw relative log paths preserve their original structure. Package excludes itself/manifest from the manifest's recursive listing; MANIFEST.json is additionally hashed in SHA256SUMS. ZIP integrity and all entry hashes were checked before delivery.

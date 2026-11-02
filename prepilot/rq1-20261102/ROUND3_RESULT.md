# RQ1 round 3 — stopped on an instrument false rejection

**No controlled A/B action comparison was completed.** The first baseline ran successfully in Vivado, but the frozen textual identity gate rejected it because a generated Command comment wrapped across two lines. The controller stopped before routing_opt. The actual logical body was subsequently checked read-only and is byte-identical; this is not evidence of functional failure or of an action effect.

## Input and RQ4 reuse decision

Read RQ4_BATCH2_RESULT.md, actual rq4_batch2_candidates.tcl and result JSON from the other thread without changes. Its input SHA256 571d5489a1e0d5bc62d8eb38c8bfe9cc222cd8a056f96b604b98bad50d579c96 was independently matched to local prior RQ1 noop_1/output.dcp. That is already rerouted, not the original input authorized here (8baf6451f9b20b8a82f035d14187c7350529a6ea0330e02d93c7100b19753149). It also uses an EDIF timestamp identity screen instead of this frozen functional-Verilog screen. Therefore the RQ4 result was not reused as a matched A baseline and was not mixed into this comparison. This avoided false provenance equivalence rather than duplicating identical work.

## Actual run

Only A1_noop executed: fresh original input -> `route_design -no_psir`, Vivado 2025.1 build 6140274, maxThreads=2. Process exit 0, wall 62.540 s, routing-stage timer 34.075 s, no explicit physopt. Initial target clock 1.570 ns / WNS −1.654 ns. Final target WNS −0.885 ns, TNS −636.195 ns, 1,897 failing setup endpoints. WHS 0.042 / THS 0; WPWS 0.001 / TPWS 0. Fully routed 2,937/2,937, routing errors 0, DRC Error/Critical Warning rows 0. PSIR phase absent in the actual log. XDC comparison passes.

B1_routing_opt: **not started**. Technical confirmations: **not started**. No Default run, model, new design/state family, paid call or checker platform. The 50 ps engineering hypothesis was never evaluated because there is no A/B difference. No noise claim can be made from this one process.

Exact commands in logs/physical-only-round3/A1_noop/command.json. Frozen Tcl SHA256 8f75794f272088a7a92bdeb5b29449325d618c4cbbfabcf764d69137ac6e242d; controller SHA256 cdf84c08020ae5a88b9aaf4a1856dc4b7871e39b531a14e2eabb1ab54fe2d570. Raw remote root `/workspace/work/rq1-prepilot-20261102/physical-only-round3/`; copied local gitignored logs/physical-only-round3/. Prior 20-minute global and 5-minute process ceilings not approached. No process remains running; B directory independently confirmed absent.

The controller deliberately raised RuntimeError at the failed gate. SSH returned exit 1; because the shell had `set -e`, its post-command controller_exit_code.txt line was not reached. The successful tool exit 0 and instrument failure are separate fields in ledger/traceback; no uncertain experiment outcome remains.

## Exact failure and independent diagnosis

The canonicalizer removed generated `// Date ...` and `// Command ...` lines, but not a wrapped generated path continuation. This round's longer directory causes write_verilog to emit:

```text
// Command     : write_verilog -force -mode funcsim
//               .../before_funcsim.v
```

The corresponding after export uses after_funcsim.v. The full unified diff has only changed generated Date and path-comment lines. The complete remainder beginning with the Verilog `timescale directive is exactly identical, SHA256 737696a9e6bccf55993f59c703f22fc8b597bb56e20c2791c9064c3b0fc79a01 in both files. No executable/configuration/directive line was removed by this diagnostic. Its first local draft assumed the pre-module preamble was all comments and correctly asserted on `timescale; the final diagnostic splits at the first noncomment line and includes that directive in exact-body comparison.

See ROUND3_EXPORT_DIFF.txt, ROUND3_HEADER_DIAGNOSTIC.json and scripts/diagnose_round3_header.py. The original frozen gate and ledger remain **failed**, not retrospectively edited to pass. The diagnosis is exporter-conditional representation identity, not a new independent equivalence proof.

## Minimal prospective repair, not executed

Prefer removing the incidental filename change rather than broadening the normalization rule: explicitly change the process working directory to its own output directory and export before/after using the **same short relative scratch filename**, then `file copy` each emitted file into its preserved before/after artifact name. Thus generated Command headers are short and identical both before/after and across arms; an absolute scratch path unique to each arm would not fix the cross-arm continuation problem. Keep the existing exact identity gate, timestamp/Command-header rules and all validity/budget criteria unchanged; do not drop arbitrary comments or ignore new logic/config text.

A local-only candidate is scripts/physical_only_arm_staged.tcl, explicitly marked NOT EXECUTED; no controller deployment or tool run used it. Before another run, freeze this instrumentation change and verify that any raw-header continuation is exactly the same generated command, then use the already-produced baseline for eligibility only if the parent accepts the bounded read-only diagnosis under the declared contract. Otherwise one fresh fixed-instrumentation baseline is needed. Either way do not opportunistically replace the original failed record or silently skip its cost.

Recommended decision: repair this small export-path instrumentation defect before allocating another physical-action pair. The scientific RQ1 test remains unperformed in this batch; neither an attractive action opportunity nor a meaningful negative action result was observed. No reason exists to expand to another design or model yet.

# Validation and timing contract audit

## What the current instrument can and cannot establish

Original and serialization-only exports are identical after removing only generated Date/Command header comment lines. WNS/TNS, hold/pulse metrics and route reports are unchanged. See BASELINE_AUDIT.json and raw contract logs. Serialization is not a no-edit implementation rerun; the latter executes route_design and demonstrably changes measured timing.

The source DCP emits `Vivado 12-8410` (missing/mismatched integrity checksum). Opening and rewriting succeeds; that does not resolve the original integrity warning or authenticate its origin. The source file's MD5 `d965368d886e8364ff1e7a5624c52a00` matches its bundled MD5SUM; SHA256 is separately frozen. Public-release archive authentication is a separate provenance check, not equivalent to this local manifest match.

The single constrained clock here is clk_fpl26contest, 1.570 ns. Original WNS −1.654 ns, TNS −671.139 ns; hold WHS 0.042 ns / THS 0; pulse-width WPWS 0.001 ns / TPWS 0. No internal endpoints are unconstrained for max delay. There are 115 missing-input-delay and 136 missing-output-delay ports. HD.CLK_SRC is missing, and route_design reports missing HD.PARTPIN_LOCS for OOC ports. Therefore compare the frozen contest domain/internal timing model; do not claim accurate full-interface timing, clock-source signoff or achieved hardware frequency. No I/O or clock-source constraints are added.

Default DRC yields 12 warnings: DPIP-2 ×8, DPOP-3 ×3, RTSTAT-10 ×1; no error severity in that report. Vivado explicitly warns that not every connectivity DRC runs for OOC designs. This is a scoped tool report, not complete signoff.

## Official versus local functional validator

Official source downloaded read-only from https://raw.githubusercontent.com/Xilinx/fpl26_optimization_contest/main/validate_dcps.py; snapshot SHA256 `0f5060215048205e995206cbe0e7a22392192dd0283ebbaf77e1b9107b5369f5`. Not executed or substituted into existing projects.

Official documentation describes top/module, I/O and device structural compatibility followed by finite stimulus simulation; these are not a formal sequential-equivalence proof. The inspected official source allows skipped simulation to return a structural-only pass. It compares corresponding outputs using Verilog case inequality; matching unknown outputs need not be mismatches, and no general all-output-knownness criterion was found in the inspected acceptance path. This is a possible vacuity mechanism, not a claim that this DCP has actually produced all-X outputs. The source also has special-case stimulus handling, so a broad claim of purely random testing would be inaccurate.

The longstanding COMPUTE_HOST local validator is a different version: default 200 vectors, deterministic LFSR seed DEADBEEF, heuristic reset detection, finite cycle comparisons, structural-only pass on skipped simulation; its xelab uses --mt auto and internal timeouts up to an hour. Running it unchanged would violate this round's two-thread/10-minute limits. It has not been launched. A bounded adapter would need explicit threads/timeouts, stimulus/reset review, completion checks, known-output/coverage accounting and independently specified negative controls before treating its PASS as reliable for logic-changing actions.

Current panel instead uses a conservative whole-functional-export identity gate plus unchanged XDC. If this gate passes, the exported modeled logical circuit is unchanged, conditional on Vivado's exporter and primitive semantics. If it fails, do not label the arm functionally incorrect or infer a performance winner; stop for semantic verification. Count agreement and routed status are never the equivalence criterion.

## Native-agent information exposure

Independently read local dcp_optimizer.py: perform_initial_analysis starts at line 1160 and obtains reports before model selection; the user message at approximately line 1518 includes INITIAL ANALYSIS RESULTS. A future native-agent condition must retain that initial timing/fanout/spread context. Hiding it would define a different policy condition. No native agent, model selector or random live policy has run in this experiment.

## Public design/source scope

Local LICENSE-BENCHMARKS.txt explicitly lists vexriscv_re-place and vexriscv_re-place_v2 under MIT (Spinal HDL contributors). This does not license the proprietary Vivado installation. Official clock contract independently checked at https://xilinx.github.io/fpl26_optimization_contest/benchmarks.html (Clock Domain of Interest). It requires hold/pulse-width satisfaction and identifies the target clock; the general timing summary can differ from the contest clock for multi-clock designs. Here reports identify one clock, but future states must query the target clock explicitly.

Follow-up provenance: the public-release archive chain was subsequently verified; see SOURCE_PROVENANCE.json and ROUND2_RESULT.md. This authenticates input bytes against that release but does not resolve Vivado's internal checksum warning. A narrow post-stop two-state LUT-slice proof is in DEFAULT_SLICE_PROOF.json; the panel was not resumed.

# P08 bounded measurement preflight — frozen before simulation

This is simulator/measurement preflight, not reproduction of AutoSizer's LLM or optimization mechanism.

Authorization: CPU only/current quota, no paid resources or model calls, no security/account setting changes, no push/PR. At most 20 ngspice simulation process attempts; at most 2,000,000,000 new download bytes; stop within two hours of the timestamp in `configs/budget.json`. Failed launches/decks count. No optimizer sweep, parameter tuning, new labels, or specification relaxation. The protocol will be committed locally before the first simulation; the commit hash and UTC timestamp will be recorded in the attempt ledger.

Source: AutoSizer `1b9b8f6498e2c7ad3b650bbbc78c8e3b0e1205e1`; original YAML copies remain byte-identical. Host repository branch `reproduction/autosizer-icml2026` is based on the existing paused Aspen commit `f85c69748506854273c5816d29646d6a70f5f468`. All additions are under `projects/autosizer`; no inherited file is edited. No repository instructions were found in the local ancestors or tracked AGENTS.md/SKILL.md inventory.

## Frozen circuits, points and constraints

Exactly two released circuits; one reference point each, the midpoint 1.68 of the published nine-value width grid. These are audit reference points, not claimed author optimal points.

* Inverter: W_pmos_base=W_nmos_base=1.68; actual Wp=Wn=33.6 µm, L=0.15 µm, VDD=1.8 V, CL=10 fF. Preserve the original 0–1.8 V DC sweep in 0.01 V steps and pulse/transient settings (100 ps input transition, 1 ns pulse width, 2 ns period, 1 ps nominal step, 4 ns stop). Original constraints: FoM>1 AND DC gain>20 dB AND average delay<50 ps AND dynamic power<50 µW.
* Five-transistor OTA (source actually contains six MOS instances including the bias reference): W_tail_base=W_diff_base=W_load_base=1.68; actual widths 16.8,16.8,33.6 µm; L=0.15 µm, VDD=1.8 V, VCM=0.9 V, IBIAS=20 µA, CL=1 pF. Preserve 1 Hz–10 GHz AC sweep at 100 points/decade and ±0.5 V differential AC excitation. Original constraints: FoM>0.5 AND DC gain>15 dB AND UGBW>10 MHz AND power<65 µW.

Use tt corner and explicit 27°C simulation temperature (ngspice default); retain model tnom. No other process corners, mismatch, layout or PEX are claimed. No width or specification changes after seeing results.

## Source-validated low-cost tool route

Use the official Debian ngspice 44.2+ds-1 amd64 package extracted into this workspace. Validate Debian InRelease signatures with the preinstalled Debian archive keyring, validate Packages.xz hash against InRelease, then package SHA-256 against its Packages stanza before executing the binary. Do not run package maintainer scripts or system installation. Python and PyYAML already exist; do not install LLM/optimization packages.

Use only the needed nfet_01v8 and pfet_01v8 tt models from official google/skywater-pdk-libs-sky130_fd_pr commit `f62031a1be9aefe902d6d54cddd6f59b57627436`, retaining Apache-2.0 notices. A small explicit tt library wrapper may select those models plus their upstream parameter/mismatch dependency closure and upstream scale convention. It is a documented PDK-subset port, not a replacement device model or fitted label. Missing include/parameter errors may justify dependency-closure corrections, always recorded. Stop before substituting generic MOS models or inventing constants for missing model parameters. No full PDK download.

## Original/repair separation

Original: execute generated source templates with only path/parameter/pin interpolation and explicit frozen temperature. Preserve original measurement commands and YAML FoM fallback. Record the paper/controller-normalized FoM separately, using the same original numeric thresholds; the upstream controller would normally overwrite the YAML expression. Report feasibility under both explicitly named definitions, never choose one to obtain a pass.

Repair A (inverter): replace crossing-index subtraction with physically paired propagation delays: input rise→output fall and input fall→output rise, at VDD/2. Keep all transitions, loads and thresholds unchanged. DC sweep derivative gain is preserved. Original `mean(power)` is a sample mean on adaptive time steps; also compute a time-weighted integral over the same 0–4 ns window, subtracting the same measured static-power estimate. Record both power definitions, not just a favorable one. This corrects measurement integration, not the circuit.

Repair B (OTA): retain original electrical analysis and report an independently reconstructed voltage-transfer gain/first downward unity-gain crossing and DC supply power from exported analysis vectors, if export is possible. This is a measurement cross-check, not a tuning change; leave original values visible. If the original measurement already agrees, report no defect found.

The original decks may be instrumented in separate runs to export raw vectors and operating-point voltages/currents; additions must not change circuit elements or original measurements. Extra runs count. Numerical convergence checks may refine time step or AC grid once per circuit and must be labeled diagnostic, not new benchmark outcomes. At most 20 attempts total, with early stop when the fixed point comparison and error classification are settled.

## Classification and evidence

Classify tool launch failure, PDK/model/include error, solver failure, measurement error/non-finite/missing metric, valid-but-infeasible, and valid-feasible separately. Nonzero exit status is not the only error signal; ngspice control errors can coexist with exit code zero. Missing measurements are null with explicit reasons, never zeros or replacement labels. A favorable FoM never overrides a failed individual constraint. Negative propagation delay is a measurement-invalid condition, not a pass.

Record per attempt: UTC, protocol commit, deck hash, command, timeout, wall time, process CPU/max RSS when available, exit status, stdout/stderr, original/repaired/port label, parsed metrics, constraints and error diagnostics. Retain all outcomes, dependency changes and a download/resource ledger. Do not execute upstream Python modules with API side effects. No circuit optimization or LLM mechanism result can be inferred from this preflight.

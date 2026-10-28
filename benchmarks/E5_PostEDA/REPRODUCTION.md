# Reproduction scope and observed results

## Fixed scope

- Official release: `b04e85a867e81e0817348f7b86a7ae06f83990d7`.
- DRC: Essential L1 q1, Essential L1 q3, Essential L3 q1, Reasoning L1 q1; 15 controls total.
- PPA: Mono perf L1 q1 and Multi L1 q1; initial offline score replay, four bounded RTL controls, then two actual no-op flow calibrations.
- Other tasks: 139 intentionally unselected. No selected unsuccessful case was dropped.
- Budget: zero model/API calls, USD 0 additional API cost, four CPUs, a two-hour initial setup window, 2 GB of new external asset downloads. No GPU or paid resource provisioning.

Use the [official installation guide](https://github.com/pengjas/posteda-bench/blob/b04e85a867e81e0817348f7b86a7ae06f83990d7/INSTALL.md) for the original protocol. The observed port's exact invocation, adaptations, raw artifacts and hash inventories are retained in the private audit package; this public summary does not contain reference answers or raw design evidence.

## Pinned observed tools

| Component | Pin / observed version |
|---|---|
| Benchmark release | `b04e85a867e81e0817348f7b86a7ae06f83990d7` |
| ORFS checkout | `e19b7a5176e45bae645ba2d5b46f4457e8913b1c` |
| ORFS amd64 image manifest | `sha256:864da53ae0b30abb3f7bb1d2451772adc7302bf3e6393d1697e7301cf8834c08` |
| Image ID | `sha256:5535500ecc23ac660e54e75e873d27cb47a6e05666fc29cbc8f446e8ca6d98ea` |
| OpenROAD inside pinned image | `26Q1-205-gbdb8e7c239` |
| Yosys inside pinned image | `0.61+0`, reports `UNKNOWN-dirty` build SHA |
| KLayout | `0.30.3` |
| Icarus Verilog for bounded RTL checks | `11.0` |
| Rootless executor | Podman `5.6.0` |

The image's 21 compressed layers total 1,458,411,014 bytes; its observed installed image size is 4,268,422,321 bytes. Installed size is not network download size. Sparse checkout included the exact ASAP7 platform and common support source, without pulling unrelated platforms. Controller/evidence copies are recorded separately from new external asset acquisition.

## Actual flow calibration

The unchanged official flow-function body prepared an isolated source/config workspace and invoked the original ORFS `finish` target with `NUM_CORES=4`. The LangChain tool decorator was bypassed only at the controller interface because no agent/model was used. Intermediate artifacts were retained instead of deleted. A dedicated adapter restricts the original wrapper's container-launch options; this executor substitution is explicit.

| Case | Fixed targets | Actual period (ps) | Actual power (W) | Actual area (µm²) | Recorded flow wall time | Target attained |
|---|---|---:|---:|---:|---:|---|
| Mono perf L1 q1 | period ≤225 ps | 262.88 | 0.00130 | 262.44 | 135.42 s | No |
| Multi L1 q1 | period ≤241 ps; power ≤0.002 W | 319.69 | 0.00161 | 293.163 | 73.18 s | No |

Both runs produced fresh final ODB/report artifacts. Input configuration, SDC and RTL hash comparisons were unchanged. Mono differs from its archived period by −6.30 ps (about −2.34%) and power by −0.00003 W; area matches. Multi matches all three displayed archived metrics. Numerical fidelity is therefore mixed, not universally reproduced. No output is called correct merely because a command succeeded or printed PASS.

## Controls and failures

DRC no-op counts match metadata. Six of 15 controls have zero geometric errors, but four are empty-layout controls. The additional conservative geometry policy gives 0 confirmed combined successes, 2 UNKNOWN and 13 failures. Electrical/C.7 validity remains UNKNOWN. Original C.7 script/corpus replay is not_run.

Each PPA case's unchanged RTL yields 500 matching events, while the harmful mutant yields 500 mismatches. These are finite deterministic testbench observations. Archived no-op PPA metrics also agree with initial task metadata; numeric score controls only check arithmetic.

All unsuccessful attempts remain in private evidence. Resolved infrastructure failures include unavailable rootless CPU cgroup enforcement and Podman resetting outer affinity (corrected by taskset inside the container, followed by same-case reruns), macOS metadata contaminating an initial RTL compilation, an absent temporary controller HOME, and one omitted common-platform support file in the first sparse checkout. The controller-HOME and sparse-checkout failures occurred before a complete PPA run and were not counted as successful calibrations. A failed sequencing guard also launched a corrective second case prematurely; that owned container was stopped, its partial output retained, and the second case rerun after verified first-case completion. Final runs use the verified in-container four-core restriction. No access denial or uncertain pending execution remains. No host security setting was changed.

The additional geometry audit was strengthened after its first implementation used only counts and areas; final verdicts use exact layer-region differences. The original and corrected evidence are both retained privately. This correction does not establish a connectivity/device check.

## Remaining limits

The full model/environment protocol and original Docker executor were not reproduced. The observed Podman port is runnable, but mono's metric drift needs diagnosis before live-agent use. The original C.7 extraction/device implementation and archived audited pairs are missing from the inspected release. Full LVS remains unsupported/UNKNOWN. No model experiment or further optimization search is authorized by these results.

This publication candidate contains only derived summaries and public source links. It excludes raw logs, reference/design artifacts, source snapshots, task metadata carrying reference fixes, mutation code, private absolute paths and license-uncertain source bytes. The initial private commit and its descendants must never be pushed; publication requires the separately constructed sanitized history and independent approval.

# Fixed HDL toolchain container calibration

Seven predeclared fixed reviewed mux/testbench cases were run in an immutable local Docker image built from an official Debian base digest and official Debian package repositories. Icarus is **12.0, Debian package12.0-2+b1**, matching the existing free-tool version used for calibration. Python3.13.5-1 is the in-container supervisor. No model-generated code or model/API request was executed. Paid resources/cost: **0**. No credentials were accessed, transmitted or included in inputs. V6/v7 evidence is unchanged.

## Outcomes

| Fixed case | Expected and observed |
|---|---|
| Correct Boolean mux and four-vector TB | pass, four checks |
| Reversed-select RTL | fail, explicit failed check |
| Incorrect expected relation in TB | fail, explicit failed check |
| Empty TB | unknown, no check evidence |
| RTL syntax error | task syntax failure, compiler nonzero |
| TB syntax error | task syntax failure, compiler nonzero |
| Infinite-event simulation | timeout_unknown after0.5s internal timeout |

These outcomes agree with existing mux/reference calibration semantics: actual checking is required, wrong behavior fails, compilation failures are distinguished from functional mismatches, and absent checks/timeouts cannot pass. These are new small fixed fixtures expressing the same binary mux relation, not reexecution of the full original corpus or independent validation of all published scores. No original comparator was modified.

## Actual compiler and simulator boundary evidence

Each case is launched through the v7 restricted Docker route with immutable image ID, `--pull=never`, no bind mounts, networknone, root filesystem readonly, UID/GID65534, dropped capabilities, no-new-privileges, default Docker seccomp, memory/swap/PID/CPU/FD/file/core limits and no Docker log driver. `/work` remains an8MiB noexec,nosuid,nodev tmpfs. Icarus compiles VVP bytecode; the trusted `/usr/bin/vvp` interpreter reads it without requiring executable scratch files. No security option was weakened for compilation.

The supervisor checks host canary/repository/socket absence, root write rejection, scratch positive write/read, absent credential variable names, and rejected network connection before launching actual tools. Saved `/proc/PID/exe`, UID, capabilities, NoNewPrivs, mount/network namespace identities and mountinfo capture **actual `/usr/bin/iverilog` and `/usr/bin/vvp` processes**, not merely shell wrappers. Their mount/network namespaces match the supervisor's verified boundary; their UID65534, zero effective capabilities and NoNewPrivs=1 are asserted. All containers were removed, including timeout. No unexpected exposure occurred.

## Preserved failures and bounded repair

The first image build failed because buildx tried writing its cache into a read-only home directory. Its error is preserved. Retrying once with process-local `DOCKER_BUILDKIT=0` used Docker's existing traditional builder successfully, with no daemon, permission or host-security change.

All seven primary tool outcomes matched, but the initial outer check failed an overstrict assertion demanding a compiler snapshot specifically from the very short correct baseline. Other primary cases already captured `/usr/bin/iverilog`. To remove timing ambiguity, **one diagnostic baseline retry** holds the compiler's source input in a FIFO for0.2s, then supplies exactly the original RTL bytes. This changes observation timing, not HDL or scoring. The retry captures actualiverilog and passes. Original seven inputs/results remain in their directories. Thus there were **7 primary executions+1 diagnostic retry=8 container executions**, not a larger sample. `summary.json` gives the measured sum of wrapper elapsed times, not CPU time. The current supervisor includes the source-preserving hold for reproducible inspection.

## Reproducibility and remaining limits

`image.json` records immutable local image ID, official base digest and image size. `Dockerfile`, full build log, initial failure and exact `dpkg-query` package list in each result preserve provenance. Runtime is pinned by image ID, but apt repository state was not snapshotted: rebuilding later may select newer packages. This is a structural packaged-tool reproduction, not a bit-identical rebuild guarantee. The image itself is local and not uploaded; source archive contains the recipe and evidence, not Docker layers.

```sh
# Requires existing image ID recorded in image.json and a new/empty result layout.
python3 fixme/benchmark/check_hdl_container.py
```

The check intentionally refuses to overwrite result directories. Missing Docker/image is infrastructure error, not task failure. The runner remains fixed-reviewed-recipe only and future model payloads stay local-only pending review; no API or generated-code authorization is inferred. This closes the **Icarus binary combinational compile/simulation calibration gate for this route**. It does not calibrate Verilator C++/DPI, Yosys/SVA, sequential races, X/Z fidelity, arbitrary plugins, arbitrary native submissions, container escape resistance or hostile resource/output abuse. Trusted Docker daemon/kernel and packaged tools remain assumptions. Existing host runners remain unconfined and must not execute generated payloads. No claim of production sandbox completeness or corpus-wide false-positive rate is made.

# Docker filesystem-boundary follow-up

The v6 archive and its eight-case-class evidence remain unchanged. This follow-up adds eight fixed, manually reviewed shell probe executions on Docker 28.4.0 using the Docker Official BusyBox 1.37.0 image, pinned by its registry digest in `tool_provenance.json`. It makes zero model calls and uses no paid resource. A normal official-registry image pull succeeded; no permission bypass, host/daemon security change, credential change, external publication or push/PR was performed.

## Boundary and controls

All six boundary checks and two negative controls passed. Raw scripts, hashes, command argv, output, exit status, duration and cleanup checks are retained in adjacent JSON files. Summed per-trial wrapper durations are 2.6516 seconds, not CPU time.

| Check | Observed result |
|---|---|
| Host filesystem/socket visibility | Synthetic host sibling canary, repository .git path and Docker socket absent inside container; host canary unchanged |
| Read-only root filesystem | Root file creation rejected |
| Positive scratch control | Write/read succeeds only in temporary `/work` |
| Privileges | UID65534, zero effective capabilities, NoNewPrivs=1 |
| Network | No routes; bounded request to documentation-only address fails |
| Environment | Credential variable names and synthetic environment canary absent; no real credential values inspected or passed |
| Intentional error | Exit7 retained as failure feedback, not pass |
| Timeout | One-second timeout classified timeout; trailing completion marker absent |

All eight containers were removed. There are no host bind mounts or Docker socket mounts. Payload fixtures are copied as validated plain tar members through stdin into an 8MiB tmpfs; absolute/traversal paths, symlinks and oversized inputs are rejected by construction. Per-container restrictions include `--network=none`, `--read-only`, non-root UID/GID, dropped capabilities, no-new-privileges, default Docker seccomp, 32 PIDs, 128MiB memory and swap ceiling, 0.5 CPU quota, FD/file/core limits and no Docker log driver. Only run-local container options are set; daemon and host policies are unchanged. Reviewed recipes only are enabled. Captured feedback retained by the wrapper is truncated at64KiB per stream; it is not an arbitrary-code output-abuse certification.

## Scope and remaining gate

This closes the previously demonstrated **host-filesystem visibility gap for the tested container route**. It does not retrofit isolation into the old host-based HDL runner, prove container escape resistance, or validate all resource-abuse scenarios. Docker's existing daemon is trusted and its socket remains accessible only to the host-side controller, never the payload. Do not invoke old host EDA execution for generated code.

The image contains BusyBox, not a compiler or EDA stack. `/work` is noexec, and only fixed reviewed shell recipes are enabled. No generated model code was executed. A trusted HDL toolchain image plus matching bounded calibration and reviewed execution recipe is still required before HDL generated-code execution; no unsupported claim of a ready model benchmark is made. The existing reference experiments are preserved and were not rerun.

`container_isolation.payload_provenance` classifies future payload origin locally. Model-generated, user-provided and unknown origins default to local-only pending review, execution disabled and external transmission forbidden. A caller-supplied disclosure flag does not enable transmission or execution. Credentials must never enter payloads or evidence. No pasted credential was used, persisted or transmitted during this work.

## Re-run only the fixed probes

```sh
python3 fixme/benchmark/check_container_boundary.py
```

This requires the already-running Docker daemon and pinned image. The runner uses `--pull=never`; missing image or Docker failure is an infrastructure blocker, not a functional result. No changes to daemon permissions or security settings are required or authorized. Network denials must not be bypassed.

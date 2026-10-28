# Reviewed-fixture and oracle boundary hardening

This changes only our new isolation/calibration harness. The official upstream evaluator, v6 mutation experiment, v7 boundary probes and v8 historical seven-case plus one-retry evidence are preserved. No model/API call or generated-code execution occurred. Paid resources:0. No host/daemon security or credential settings were changed.

## Chosen trust boundary

The trusted controller, source-controlled manifest, packaged tool image and reviewed oracle recipe are inside the boundary. Payload origin labels, stdout and candidate-supplied pass markers are outside the correctness boundary. `run_reviewed` now requires explicit origin and fixture ID; there is no permissive reviewed-origin default. The immutable manifest digest is frozen in the controller. Authorization checks the **complete set of file names and SHA256 bytes**, exact argv, timeout and pinned image before Docker starts. Extra/changed files, changed commands, unknown IDs and model/unknown/missing origins are rejected. The caller cannot pass a different manifest or select a new image by relabeling origin. Extending the fixture set requires a reviewed code/manifest change, not a runtime claim.

Oracle policy is taken from the manifest. A diagnostic fixture has no correctness authority even if its output contains a plausible pass marker. For the fixed mux trace oracle, the host additionally verifies the execution's manifest/fixture/image/recipe binding, exactly four ordered observation vectors, unique terminal record, strict field syntax, no unknown outputs, independent Boolean mux relation and recomputed failure count. No substring match grants pass. `fixed_oracle.evaluate_fixed` ignores the legacy in-container supervisor decision. The current in-container legacy marker decision remains visible in raw evidence to demonstrate why it is not authoritative.

This is **not cryptographic authentication of arbitrary stdout**. An arbitrary RTL or testbench could deliberately forge a complete valid transcript. Such inputs are not authorized: every payload byte here is reviewed/allowlisted, and future model payloads remain disabled. A hostile host controller could also fabricate a result dictionary; protecting the controller from itself is outside scope. Before arbitrary candidate/TB execution, an independently trusted checker/channel or different evaluation design is still required. We do not describe this as fixing the official benchmark, or as generated-testbench security.

## Predeclared fresh run and observations

The new plan and full fixture manifest were committed before execution. This was a **fresh 13-container hardening calibration**, not historical replay:

* Seven fixed FIFO-instrumented mux cases: correct passes; wrong RTL and wrong expected checker relation fail; empty TB is unknown; RTL/TB syntax diagnostics are task syntax failures; infinite simulation is unknown timeout.
* Three fixed result-authenticity controls: a fake pass-marker-only TB, malformed result line and duplicate terminal line all remain unknown. The fake marker's legacy supervisor decision is pass; the host ignores it and assigns no correctness authority.
* Two fixed output-flood controls exercise actual in-container simulator feedback and host Docker-client feedback. Both remain unknown, with output_limit states rather than pass.
* One fixed outer timeout remains unknown and its container is removed.

All13 expected decisions matched; wrapper elapsed durations sum to19.9263seconds, not CPU time. Six local pre-execution rejection checks cover missing origin, unknown origin, model origin, changed bytes, changed argv and missing fixture ID; no Docker execution occurs for these. Six explicitly **synthetic, offline** compiler-state envelopes test compile timeout, output limit, resource/signal termination, missing tool, explicit syntax diagnostic and internal tool error. These establish taxonomy behavior, not empirical claims of real compiler crashes/OOM. Actual syntax/timeout/flood controls supply tool evidence separately. `results/summary.json` declares `schema_version=1`, `run_type=fresh_hardening_calibration_not_historical_replay` and explicit container count; synthetic and host-side checks are separate lists.

The v8 historical record remains7 primary executions+1 compiler-snapshot retry=8. Its old entry points are now deliberately disabled with a pointer to the fresh checker; a rerun of seven FIFO cases must never masquerade as reproducing the historical8-run observation history. Old source remains in git history and archived fixtures. The new checker refuses to overwrite its results directory.

## Output and error bounds

The host Docker CLI child has an OS RLIMIT_FSIZE of128KiB per stdout/stderr temporary file; retained feedback is capped at64KiB. If a stream exceeds the retained limit or the child hits the OS file ceiling, state is output_limit and the container is cleaned up. This limit is applied only to the CLI child, not as a host security configuration change.

Inside the container, compiler/simulator feedback goes to temporary files, never unbounded `communicate()` pipes. Each inherited Docker file-size limit is1MiB; a polling monitor terminates the process after either stream exceeds64KiB or its wall budget. Feedback retained is capped at64KiB. Polling can overshoot64KiB up to the OS ceiling, so64KiB is not claimed as an exact maximum written. The supervisor and CLI have separate bounded storage layers; Docker/kernel buffering remains a trusted runtime assumption. No claim of comprehensive hostile resource-abuse safety is made.

Compile timeout/output/resource/infrastructure states are unknown, distinct from task syntax failure. Only a completed nonzero compiler with an explicit syntax diagnostic receives task_syntax_failure. Signal termination and unrecognized nonzero exit cannot be relabeled syntax failure. Nonzero simulator exits, malformed evidence and truncated envelopes cannot pass.

## Precise isolation claim

No **submitted workspace, credential or Docker-socket exposure** was observed in these reviewed probes. Docker-managed `/etc/hosts`, `/etc/hostname`, `/etc/resolv.conf`, proc/dev and other runtime mounts exist; we do not claim the container has no mounts or no host-derived metadata. Actual process UID/capability/no-new-privileges/namespace/mountinfo snapshots remain recorded. New snapshots include Seccomp filter-mode status; this is evidence of reported filter mode, not a measurement or proof of individual seccomp rules. Default Docker policy is used without daemon changes.

## Reproduction and offline review

```sh
# Review existing evidence without executing Docker or HDL:
python3 fixme/benchmark/verify_harness_hardening.py
# Fresh calibration only in a clean result layout and with the pinned local images:
python3 fixme/benchmark/check_harness_hardening.py
```

Offline verification regrades all13 saved results under the execution-binding-aware host oracle, checks file hashes/manifest, six authorization rejections and synthetic taxonomy outcomes. The original13 run used the frozen manifest and authorization; subsequent addition of explicit input/recipe fields to wrapper output is an evidence-format improvement only. `executed_container_wrapper.py` preserves the executed wrapper form without those extra fields. Binding-aware regrading was performed offline, with no repeat container trials. No observed results were edited.

## Delivery and push status

A pattern/sensitive-filename scan of all3905 unique blobs reachable from the branch HEAD plus staged changes found no credential-pattern matches, sensitive environment/credential filenames, or blobs over50MiB. Match content was never printed. This is a bounded static disclosure check, not a proof that arbitrary private data is absent; reviewed scope contains this paper's code, public-source evidence and local fixed calibration artifacts. Docker images/caches and the supplied chat credential are excluded.

The requested push was **not attempted**: authorized GitHub repository metadata reports `Bol-C14/PaperReproduction` as `visibility=public`. The instruction requires private visibility and forbids new publication. Repository visibility, credentials and permissions were not changed. Work is committed locally and retained in the same Library archive; remote head equality is not claimed. Wait for parent resolution/new environment before further work.

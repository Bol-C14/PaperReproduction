# G3 — reproduction and actual results

## Outcome and status

`metadata_audit` complete. Six reference executions are `reference_calibration`; six no-op controls and one auditor-written alternative are `offline_replay`. The paper-protocol run is `resource_blocked`: execution node lacks a rootless CPU-quota controller, and no paid Daytona/model experiment was authorized. No `live_pilot`, `partial_method_reproduction`, leaderboard reproduction, or 4.0 execution is claimed.

All 3 preselected tasks remain in the denominator. The other 86 registered 2.0 tasks were excluded before results because this is a bounded CPU micro-audit. None was swapped in or silently dropped. No model/API request, paid resource, push, external communication, credential/network/host-security change, or privileged container was used.

## Frozen scope and budget

- Paper: `2601.11868v1`; experiment dataset: `terminal-bench@2.0`, registry commit `69671fbaac6d67a7ef0dfec016cc38a64ef7a77c`.
- Selection frozen at `2026-10-28T23:35:49.859782+00:00`: `log-summary-date-ranges`, `regex-log`, `cancel-async-tasks`.
- Harbor: `0.25.0`, commit `2f424cd003ee1a94b5ed262471d5e36e4948f93f`; modern harness, not a recovered paper-era harness environment.
- 4.0 protocol only: commit `452bf305c6daa62fc59061d22133a7cbc7c1572e`; it supplies no experimental tasks or scores here.
- Initial budget: 2-hour setup, 2 GB downloads, maximum 4 CPU threads globally for this task, 12 main cells, zero model calls/paid dollars. The two novel settings are cooperative affinity `[0]` versus `[0,1]`, both with enforced 2 GiB memory and 128 processes. One container executes at a time; bounded metadata probes used one extra CPU at most.
- Task agent and verifier timeouts: 900 seconds each; build startup: 600 seconds; outer cleanup: 60 seconds. Infrastructure time, solution time and verifier time are separate in every result.

**Accounting deviation:** the 12 planned main cells completed, plus one explicit alternative control. There are also 30 earlier failed/incomplete attempt records, including partial no-op executions. An absolute all-attempt cap was not enforced across setup retries. These records are preserved and enumerated in `metrics/calibration.json`; they are not relabeled successful trials. Setup finished within the initial two hours. Download transport bytes were not metered; source-pack/image/cache inventories are retained, but exact compliance with the 2 GB transfer cap is not asserted. No runtime dependency downloads occurred.

## Actual main-grid results

Values are control outcomes, not agent capability scores. Original pytest assertion files are unchanged. Acceptance requires inspecting reward plus structured pytest results; semantic correctness is assessed separately against actual artifacts/events.

| Task | Affinity CPUs | Reference upstream reward | Independent reference check | No-op reward | Solution wall s | Verifier wall s |
|---|---:|---:|---|---:|---:|---:|
| log-summary-date-ranges | 1 | 1 | pass | 0 | 9.225 | 2.128 |
| log-summary-date-ranges | 2 | 1 | pass | 0 | 8.605 | 2.124 |
| regex-log | 1 | 1 | FAIL | 0 | 1.507 | 1.977 |
| regex-log | 2 | 1 | FAIL | 0 | 1.519 | 2.016 |
| cancel-async-tasks | 1 | 1 | pass | 0 | 1.552 | 15.840 |
| cancel-async-tasks | 2 | 1 | pass | 0 | 1.524 | 15.848 |

Both settings yield identical accept/reject conclusions: 3/3 references accepted upstream, 0/3 no-ops accepted, and only 2/3 references accepted by independent semantics. The alternative regex receives upstream reward 1 and passes only the 10 independent cases tested here; universal correctness is not established. Reference replay is calibration; the alternative is an auditor control, not an evaluated model solution.

The one-versus-two CPU comparison is a **new offline resource experiment**, not a leaderboard reproduction. One observation per cell, cooperative affinity rather than CPU quota, different container startup delays and no model generation prevent a statistical performance claim. Solution times, verifier times, and total wall times are in [resource_comparison.csv](metrics/resource_comparison.csv); total wall time is not pure CPU execution time.

## Independent evidence and sandboxed probes

1. **Log artifact:** recompute bracketed severity counts from all 164 actual log files using independent Python date/count logic; validate all 15 rows of `summary.csv`. Both reference CSVs pass; absent no-op artifacts fail.
2. **Regex semantics:** the accepted upstream reference wrongly matches three zero-prefixed IPv4 cases and a two-line IP/date case. Both resource settings reproduce all four mismatches. The stricter alternative passes the upstream fixture and the 10 independent cases tested; this is not a universal correctness proof. Source inspection identifies missing leading-zero and cross-line coverage; no upstream test or solution was altered to hide the defect.
3. **Async side effects:** the independent checker imports final `run.py`, records filesystem start/cleanup events, checks active-set concurrency and launches a real SIGINT trial. In each setting, normal completion starts/cleans 5 jobs with peak 2, while cancellation starts/cleans only 2 jobs. Expected cancelled child exit `-2` is recorded, not called an infrastructure failure. No stdout message counts are used for this independent verdict.
4. **Stale reward:** all six no-op trials begin verification with a deliberately seeded reward file containing `1`. Upstream Verifier removes it and each obtains reward 0 with failed pytest tests and missing artifacts.
5. **Fresh reset:** all four initial input manifests per log/async task, and five for regex including the alternative, are identical. All expected output, hidden-test and solution paths are absent before execution. Four log resets each contain exactly the same 164 input-file hashes. A new disposable container is created for each trial; containers are removed afterward.
6. **Test/reference isolation:** exact-content scans of `/app`, `/root`, `/tmp`, `/tests`, `/solution` in fresh images find no frozen test/reference files and no git directories. This is bounded evidence for those roots and byte-identical content, not proof against transformed leaks elsewhere. Runtime preflight sees only loopback, no home/socket mounts, zero effective capabilities and `NoNewPrivs=1`. Complete mount observations are private raw evidence. Reference material is uploaded only for calibration, and tests only after the agent phase; future live agents must receive a separate allowlisted package.
7. **Timeout liveness:** in one disposable no-op regex container, `sleep 2; touch /app/late-marker` with `timeout_sec=1` raises a timeout but returns after about 2.275 s and the marker later exists. This observation applies specifically to this AffinityPort → Harbor 0.25.0 → Podman/podman-compose execution chain. It does not establish a flaw in the original Docker harness or paper protocol. Trial teardown still removes the disposable container; future live-agent evaluation requires a tested descendant kill/reap boundary.

## Ports and reproducibility limits

The original rootless `--cpus 1` invocation fails because only memory/pids controllers are delegated. Outer host `taskset` leaves container affinity at `0-191`; neither is counted as enforcement. The port prefixes every execution command with **in-container** `taskset`, asserts `os.sched_getaffinity`, and reads memory/process limits from cgroup files. Arbitrary code can widen its own affinity, so this is unsuitable as a hostile-agent CPU boundary.

Online dependency preparation and offline task execution are separate. Derivative images retain original task-image content and preinstall pytest 8.4.1 / pytest-json-ctrf 0.3.5. Original `test_outputs.py` and async `test.py` SHA256s match the frozen dataset; the verifier launcher replaces online installation with direct invocation. The log solution's apt line moves to preparation; its computation is unchanged. Regex verification runs Python 3.12 from the Ubuntu image instead of the original launcher's downloaded 3.13; the other task runtimes are 3.13.7. These are ports, not exact environment reproduction.

The adapter reuses upstream Harbor lifecycle/downloads, OracleAgent, NopAgent and Verifier. It adds in-container affinity, native Podman uploads for podman-compose's missing `cp`, and precreated empty staging directories so capabilities remain dropped. It calls `stop(delete=False)` because this removes containers while retaining prepared local images. Immutable final image IDs, original registry digests and exact package inventories are recorded. Rebuilding with mutable apt repositories is not byte-identical reconstruction; retained image IDs are the rerun basis.

Failures are preserved: compose memory string/int conflict; banner-prefixed JSON; upstream cleanup deleting local images; missing compose copy/tar fallback; read-only-mode root preventing new staging directories under dropped capabilities; rejected `--pull never` spelling; trailing compose diagnostics after expected failing JSON. See [COMMANDS.md](logs/COMMANDS.md) for all revisions. No failed attempt is converted into a task correctness result.

## Re-run and deliverables

Run the scripts only in the dedicated execution node scope, using an unused result directory. The current script refuses overwrite. Reuse retained prepared images, then invoke:

```sh
R=${REPRO_ROOT:?Set REPRO_ROOT to a dedicated execution root}
export PATH="$R/envs/terminal-bench/venv/bin:$PATH"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
python "$R/tools/terminal-bench/calibrate-v7.py"
```

This is the actual final command, but its existing output path must be changed for a fresh run. Full historical preparation/launch commands are in [logs/COMMANDS.md](logs/COMMANDS.md). Local `scripts/summarize.py` recomputes and checks the public summary from the private archive; `scripts/write_report.py` generates this report. Python compile and Bash syntax checks were performed. No extra evaluation is needed to inspect these results.

Deliverables: [REVIEW.md](REVIEW.md), [manifest.json](manifest.json), [raw evidence inventory](RAW_EVIDENCE.md), [bounded next experiment](NEXT_EXPERIMENT.md), and [minimal EDA package template](eda/minimal_task/README.md) with REQUIRED placeholders, not a runnable production task; see [rerun/regrade rules](eda/CHANGE_RULES.md).

## Remaining blockers

- Exact paper protocol: unavailable CPU quota controller, modern rather than recovered paper-era harness, preparation/runtime deviations, and no model/provider budget. This is `resource_blocked`, not a completed replication.
- Live pilot: no authorized model/endpoint/caps; cooperative CPU affinity and demonstrated timeout descendant survival are insufficient for untrusted agent execution. No such agent ran.
- Redistribution: the frozen 2.0 commit has no root LICENSE file. Current web licensing metadata is insufficient for those exact bytes. Original task/reference/test assets stay private. Harbor and 4.0 declare Apache-2.0; the paper declares CC-BY-4.0; installed OS/Python dependencies retain their package-specific licenses in the images.
- Scope: 86 tasks unrun; no model rankings, full-benchmark correctness or statistically meaningful resource speedup inferred. Exact network transfer-byte accounting remains unknown.

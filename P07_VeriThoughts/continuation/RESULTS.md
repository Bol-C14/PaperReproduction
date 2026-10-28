# Fixed benchmark CPU continuation completed

The previously blocked exact benchmark is now verified and inspected. Empty golden discovery was observed in **0/291** released records; stored candidates also had **0/291** empty discoveries. The unchanged upstream defect remains demonstrable on an explicitly mutated empty-check input, but this complete fixed-file inventory supplies no evidence that actual released benchmark rows trigger it. No score inflation or training-data generalization follows.

The preregistered **32 rows / 96 frontend calls all returned 0**, with no timeouts or replacements. These calls perform only `read_verilog`; successful reads do not establish hierarchy elaboration, question accuracy or behavioral equivalence. The exact old content-independent sample was retained, including the invalid/unsupported-outcome policy. Textual module-token warnings affected seven golden rows and four candidate rows; inspecting every warned token line showed the extra occurrences in comments. No duplicate discovered names occurred.

## Original-entrypoint control results

All six complete official evaluator processes exited normally; the labels below come from their written evaluation JSON, not the process exit status. Five Yosys invocations occurred: three reached SAT, while two stopped earlier on invalid/missing candidate modules. The empty-check control invoked no Yosys process.

| Input | Original written success | Additional guarded success | Evidence |
|---|---|---|---|
| Real row 1, gold vs itself | true | true | 50-step SAT success |
| Real row 1, actual released stored candidate | true | true | 50-step SAT success; agrees with this one stored publisher label |
| Real row 1, syntax-legal PWM output forced low | false | false | SAT model / proof failure |
| Real gold, syntactically illegal candidate | false | false | Candidate syntax error |
| Real gold, empty candidate | false | false | Candidate module absent |
| Mutated comment-only gold, illegal candidate | **true, zero checks** | **false** | Upstream empty-loop acceptance; synthetic malformed-input negative control |

The two successful sequential checks retain the original `clk2fflogic`, `-seq 50`, `-set-init-zero` assumptions. They are bounded results, with no parameter sweep, induction or independent unbounded oracle. Question and reasoning text are absent from the formal inputs. This is a real stored-pair evaluator/control pilot, not fresh model generation, teacher reconstruction or paper-score replication.

## Provenance and environment

Started from preserved branch HEAD `521a602a90ed50fab4af449796cc2c3299b4a536`; protocol frozen at `2a0376ea4def1c5734dceabc5c8023963e4071ce` before any HDL execution. Benchmark revision `83179e5d881234f47fd783d03af22510cd9c6c35`, 571089 bytes, 291 LF-terminated rows; SHA256 `7090ba304cb5bc07c797ffc94b01ae6006324baa1ea472d472ce0338d81584ca`; Git blob `9f486e6165e9a635087e3eeaa6990949d927537a` matches independently fetched revision API metadata. Dataset is public, not gated, with MIT card metadata. Its full per-design license lineage remains unverified, so input RTL and raw derivative logs stay outside the public candidate payload.

APRIL ran Yosys 0.41 at original commit `c1ad37779eea6211866a466026322416fb3a832f`, built from the identical verified archive and optional-feature flags as the cloud pilot. Binary SHA256 `3142ddb7105ed63c89018469e1c20dced0c37d16cc44cab1b3e70288456fb810`. Disclosed substitutions: host Linux 5.14 / GCC 11.5 instead of the old Debian container, dedicated Python 3.9 venv with NumPy 1.26.4, one CPU affinity core and per-process address-space/time limits instead of original container isolation. No method passes, module naming/renaming or SAT horizon were changed. A logging-only adapter ran the byte-identical upstream script through argparse/main; its subprocess return codes, logs and written labels are retained.

Build: 341.58 s wall, 675.13 s user+system CPU, 840224 KiB peak RSS, two workers; successful exit and installation verified. Frontend calls: 0.641 s summed wall / 0.439 s child CPU. Controls: 13.017 s summed wall / 12.933 s child CPU. These exclude network and orchestration latency. Experiment peak memory was not separately measured; the 4 GiB limit is per-process virtual address space, not measured RSS or a cgroup aggregate cap. No API requests, fresh candidates, GPU activity or paid cost.

## Failures and evidence corrections

- Initial default-sandbox SSH was blocked by local network permission; authorized execution then succeeded. No policy/security changes occurred.
- One SCP transfer disconnected, leaving a verified zero-byte bundle. Only that known failed transfer was retried; source-data transfer had succeeded. The bundle exported `HEAD`, so the initial named-branch pull failed without changing checkout; a verified HEAD fetch/fast-forward succeeded.
- Frontend attempt 1 failed before any HDL invocation because its relative Yosys executable path was resolved under a sample working directory. The same frozen runner and samples ran once as attempt 2 with an absolute executable path. The original failure log and generated pre-launch files remain preserved. No failed scientific outcome was rerun or replaced.
- Control SSH disconnected during execution. Inspection found the complete six-case ledger and results, so the experiment was **not repeated**. The outcome is confirmed, not uncertain.
- Raw selected-hash output inherited the old `not_accessible_not_inspected` metadata string. Actual row hashes and inventory were already present before execution. `selection_verified.json` corrects only that stale status field, retaining all hashes and indices; raw output remains preserved.
- Original interactive-shell no-TTY warnings accompany successful Yosys calls and do not mean proof failure. Original pass@5/pass@10 output is invalid at one completion and is excluded.

All prior research files remain byte-identical; `.gitignore` and the top README are deliberately updated for the new phase. All six continuation freeze hashes, including the exact input and unchanged runners, were verified. [Machine summary](results_summary.json), [frontend ledger](frontend_ledger.json), [control ledger](controls_ledger.json), [raw evidence manifest](raw_evidence_manifest.json).

## Method status and bounded closeout

Complete: exact public asset recovery; exhaustive static reachability; all 32 preregistered frontend checks; a real released pair through the original checker; legal/behavioral/syntax/empty/zero-check controls. Not run: fresh V-to-Q or Q-to-V generation, reasoning validation, feedback regeneration, SFT or published pass@k reproduction. The old eight synthetic controls were not repeated.

No blocker remains for this completed CPU phase. Optional next minimal method-transfer pilot requires a centrally approved shared batch: up to three serial `Client.chat` requests, max_tokens 2048 each, aggregate at most USD 0.25 under the shared USD 10 ledger and its conservative cost quote. Use released Q -> fresh V -> original check -> at most one actual checker-feedback regeneration; an optional third request could reconstruct V -> Q. The model must be the centrally allowed service and explicitly identified as replacing official models. Do not enable a batch, alter shared client/credentials or call around its ledger. Parent-directed notification via the local task messaging API returned “thread not found”; this request is handed back in the final result instead. No push or PR.

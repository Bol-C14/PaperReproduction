# Actual reproduction record — G2 SWE-Pro

Window: 2026-10-28 through 2026-10-29 UTC. Status: **reference_calibration**, partial scope; one Open Library task **resource_blocked**. Paper-protocol reproduction, live_pilot, offline_replay and partial_method_reproduction are **not_run**. The explicitly amended three-case conditional controls are complete. Reference replay is calibration, not an agent result.

## Pins and budget

See `manifest.json` for paper/hash, Git/HF commits, Parquet hashes, image digests, licenses and tool versions. Branch: `reproduction/benchmark-swe-pro`, based on `809ca20e003c2f5d5a723c77ead8a6de532e4539`. No push, author contact, credentials change, paid service or model call occurred.

Initial setup cap was two hours, four CPU threads and 2,000,000,000 downloaded bytes. Four tasks were selected before outcomes, in `selected_ids.txt`. Manifest-only OCI inspection showed 3,719,872,176 bytes of unique compressed layers for all four; the initial qutebrowser pair requires 1,386,533,181 bytes. The first delegated increase to 3.9 GB was rejected by automatic approval review, and no bypass followed. Direct user approval at 2026-10-28 23:46:02 was then accepted for one bounded retry. The first Open Library image transferred layers but failed to unpack; the second imported successfully. Their native outcomes are recorded separately in `image_pull_attempts.json`. No exact transport-byte meter was installed: layer counts and the sum of all four manifests (3,748,102,657 compressed bytes before deduplication) are not claimed as total wire-byte measurements. No repeated layer pull was attempted to repair the incompatible image. Setup stayed below two hours; no verifier reached its 3,000-second timeout.

## Actual preparation and audit commands

The existing strict `ssh -o BatchMode=yes -o StrictHostKeyChecking=yes april1` connection was used. Below, `APRIL_ROOT` denotes the pre-existing shared paper-reproduction directory, and `PRIVATE` denotes the private sibling evidence directory. This avoids making a particular home path part of the deliverable contract. Private native logs preserve actual absolute command arguments.

```bash
# APRIL: official source only, no submodule models installed
 git clone --depth 1 https://github.com/scaleapi/SWE-bench_Pro-os.git "$APRIL_ROOT/checkouts/swe-pro"
 git -C "$APRIL_ROOT/checkouts/swe-pro" rev-parse HEAD
 cd "$APRIL_ROOT/checkouts/swe-pro/v2"
 sha256sum -c SHA256SUMS

# APRIL assets/swe-pro: anonymous metadata-only OCI inspection
 python3 scripts/inspect_oci.py

# Actual image pulls, each by linux/amd64 child-manifest digest
 timeout 600 podman pull ghcr.io/scaleapi/swe-bench_pro-v2@sha256:7fd32c336a00abc46d028a1289db175d92ef8e4aaa2573ce2d5a3637d6db6a32
 timeout 600 podman pull ghcr.io/scaleapi/swe-bench_pro-v2@sha256:ca6ba92316b90aa0227bc18c97fb0b458d415f216416fe3c3b0ad526f41cc017

# Mac: all V1/V2 metadata, independent V2 file comparison
 python3 scripts/audit_metadata.py --private "$PRIVATE" --out metadata_audit.json

# APRIL: repaired local port, already-cached images only; missing images recorded
 G2_ROOT="$APRIL_ROOT" python3 "$APRIL_ROOT/assets/swe-pro/scripts/calibrate.py"
```

The first checksum invocation mistakenly ran from the repository root and verified no V2 files; the corrected invocation above ran from `v2` and all 6,436 entries passed. The first local repository copy lacked promised Git blobs. It was retained as an incomplete copy; a sparse clone of the existing authorized remote was used for this branch. No upstream files were edited.

`audit_metadata.py` requires the observed controller DuckDB 1.4.4. PyArrow 19.0.0 failed with `Repetition level histogram size mismatch`; no record was skipped. DuckDB read 642/731 unique non-null task IDs. All 642 V2 gold/test patches and parsed test lists agree with independent checksummed upstream files. No Parquet dependencies were installed globally.

## Execution history, including unsuccessful attempts

| Batch | Selected controls | Outcome |
|---|---:|---|
| CPU cgroup | 8 on the two cached tasks, including partial/alternative | All failed before startup: rootless user cgroup lacked CPU controller. No tests ran. |
| Host-affinity port | Same 8 | Tests ran, but `/logs/verifier` could not be created under mode-555 container root with capabilities dropped. Required artifacts missing; all excluded. Host affinity also failed to propagate into runtime. |
| Verified port | Reference and empty on all four fixed tasks | Four usable records on cached images; four resource-blocked records on the missing images. |
| Directly approved Open Library retry | Two exact image pulls | `00bec1e7` import failed on UID/GID120012366; `03095f26` imported successfully. Neither was approval-denied on this retry. |
| New Open Library baselines | Two usable controls, two blocked records | `03095f26` reference passes 3/3, empty passes 1/3; `00bec1e7` tests never started. |
| Explicitly amended conditional stage | 6 evaluated, 2 not_run | Three frozen partials rejected; three frozen alternatives accepted; fourth-case candidates remain not_run. |

The repaired runner keeps the original image user and uses a unique project-specific output directory bound at `/logs/verifier`. It does not chmod unrelated paths, mount host home or a socket, enable capabilities/privilege, or change host networking. Every container and exec workload sets affinity inside the namespace using `os.sched_setaffinity(0,{0,1,2,3})`; recorded `/proc/self/status` confirms `0-3`. Merely applying taskset on the controller was demonstrably insufficient. Each grader retains `--network none`, `--cap-drop ALL`, `no-new-privileges`, 4 GB memory and a 512-process limit. There is no agent process and no model endpoint.

Only a supplied source diff enters the pristine grader before the unchanged verifier. The gold/solution directory itself is never mounted. The full upstream tests directory enters only after pre-grading isolation probes. Exact per-task test/config hashes are in `metadata_audit.json`. The local port applies patches strictly with `git apply`; upstream PatchReplayAgent also permits 3-way/fuzzy fallback. These successful reference applications needed no fallback. The local verifier is offline, whereas official V2 permits verifier networking; this port cannot establish compatibility for Go dependency-fetching cases.

## Usable actual outcomes

| Fixed task prefix | Patch | Required tests passing | F2P / P2P passing | Resolved |
|---|---|---:|---:|---|
| qutebrowser 01d1d149 | reference | 49/49 | 3 / 46 | yes |
| qutebrowser 01d1d149 | empty | 46/49 | 0 / 46 | no |
| qutebrowser 0833b5f6 | reference | 10/10 | 1 / 9 | yes |
| qutebrowser 0833b5f6 | empty | 9/10 | 0 / 9 | no |
| Open Library 00bec1e7 | reference, empty | not evaluated | exact image cannot unpack UID/GID | resource_blocked |
| Open Library 03095f26 | reference | 3/3 | 2 / 1 | yes |
| Open Library 03095f26 | empty | 1/3 | 0 / 1 | no |

Resolution was recomputed from every required test ID in the unchanged config and parsed `output.json`, with non-empty required sets, then compared with the reward. Exit status or a printed PASS was not used alone. Private raw stdout/stderr and parser results are retained. This is three reference acceptances and three empty rejections; there is no four-task success-rate claim and no model performance claim.

## Evidence, recovery and remaining work

`attempts.json` enumerates 44 records: 8 startup failures, 8 logging failures, 8 initial repaired-baseline records (including 4 then blocked), 4 directly approved continuation-baseline records (2 usable, 2 still blocked), 8 original planned/not_run records, and 8 current conditional-stage records (6 usable, 2 not_run). Historical plans and superseded blockers are not erased. `current_baselines.json` identifies the latest state without erasing superseded attempts. `private_evidence_index.json` hashes private source snapshots and raw logs; it contains metadata, not payload text. Resolve private paths relative to `PRIVATE` (the directory immediately beside the repository). Recheck the package with `python3 scripts/verify_evidence.py --private "$PRIVATE"`; it recomputes required-test coverage, checks affinity/history/network observations and verifies indexed private hashes. Raw native commands, output.json, reward and run-script stdout/stderr are under `april-final/results/swe-pro` , `april-approved/results/swe-pro` and `april-conditional/results/swe-pro`; approved native pull logs are in `april-approved/logs/swe-pro`. Earlier batches remain intact. No reference patches or hidden test bodies are committed to this report branch.

The interrupted job was inspected before continuing, then observed complete; no duplicate was submitted. All G2 grader containers were removed. Before resuming, inspect processes, existing record.json files and cached digests again. The runner resumes completed records; use a separate run directory to preserve any deliberate new attempt. The direct approval resolved the old download denial; the remaining blocker is now a native rootless import failure. The subsequent explicit conditional amendment allows only the three calibrated cases despite the blocked fourth pair; original gate and original refusal log remain preserved. The current reports are ready for parent independent audit, not publication.


## Directly approved continuation: actual commands and remaining incompatibility

The following commands were executed once after inspecting processes and cache. The first command failed with exit125 during layer unpack; because the shell used `&&`, its second pull had not executed. That second target was then submitted once separately and succeeded. No retry of the failed import was made.

```bash
timeout 600 podman pull ghcr.io/scaleapi/swe-bench_pro-v2@sha256:03205f63224d992c930df7a2b898353d9d3dface4ab4d921eebc73dc909c1ba6
timeout 600 podman pull ghcr.io/scaleapi/swe-bench_pro-v2@sha256:5f97b029a351c71f9850d38a843794a9a2074472760c62ac174b9ef28aa564e4
G2_ROOT="$APRIL_ROOT" G2_RUN=approved-open2-baselines \
G2_TASKS=instance_internetarchive__openlibrary-03095f2680f7516fca35a58e665bf2a41f006273-v8717e18970bcdc4e0d2cea3b1527752b21e74866 \
python3 "$APRIL_ROOT/assets/swe-pro/scripts/calibrate.py"
podman unshare cat /proc/self/uid_map /proc/self/gid_map
# Mac: prepare/hash controls; git apply checks only, no solution execution
python3 scripts/prepare_candidates.py --private "$PRIVATE"  # historical path; helper now retained privately
```

Exact failure: insufficient namespace UIDs/GIDs for `120012366:120012366` on `/app/node_modules/hpack.js/.npmignore`; `lchown` returns invalid argument. Existing maps are namespace IDs 0–65536 (full host mapping retained privately). The failed manifest remains `image not known`. Read-only checks found no `docker`, `nerdctl`, `apptainer` or `singularity` executable in the APRIL shell PATH. No mapping edits, privileged mode, ownership flattening, altered image, service installation or paid runtime was attempted.

Eight private gold-derived control patches were frozen in `candidate_manifest.json`. A strict application check against pinned base source passed for each. Six now have separate actual grader outcomes in `conditional_controls.json`; the frozen preparation manifest is retained unchanged. Reference-derived alternatives are explicitly reviewer controls, not blind reimplementations. The `03095f26` alternative adds a string-value guard to match its prose. Its actual isolated-function probe and native tests both pass; an AST-identity check links the observed non-string emission in the partial function to the reference function. This is bounded alignment evidence, not a whole-application proof.


## Completed three-case conditional study

After confirming restored Mac execution, Git and remote state showed the previous commit/upload had not happened and no conditional jobs existed. The explicit amendment was then committed (`76ec876`) before any outcome. Six already-frozen patch payloads were uploaded privately; the blocked case's payloads were not sent for grading. No new image or model call occurred.

The same local port ran with `G2_RUN=conditional-controls3`, `G2_VARIANTS=partial,alternative`, `G2_TASKS` equal to the exact three eligible IDs, and host-side paths for `G2_BASELINE_FILE`, `G2_PATCH_ROOT`, `G2_GATE_AMENDMENT` and `G2_SEMANTIC_CHECK`. The launcher set these from the predeclared amendment JSON. The runner verified all four image digests and every selected hidden-verifier file hash, all three usable baseline pairs, and each frozen candidate hash before grading. Each record carries the amendment SHA256 and four-case denominator. Actual native commands, parser JSON, rewards, semantic logs and unchanged-verifier stdout/stderr are retained under `PRIVATE/april-conditional`.

| Task | Partial required passing | Alternative required passing | Conditional result |
|---|---:|---:|---|
| qutebrowser 01d1d149 | 46/49 | 49/49 | partial rejected, alternative accepted |
| qutebrowser 0833b5f6 | 9/10 | 10/10 | partial rejected, alternative accepted |
| Open Library 03095f26 | 1/3 | 3/3 | partial rejected, alternative accepted |
| Open Library 00bec1e7 | not_run | not_run | infrastructure-blocked case retained |

Independent probe evidence is reviewed in `SEMANTIC_REVIEW.md`; tests are not replaced or edited. All six workloads again verified CPU0–3, absent fixing object and external network unreachable. No timeout or new infrastructure failure occurred in these six runs. No partial passed; concrete missing behavior, rather than reference-diff size alone, supports their negative classification. These are results conditional on three native cases, not a correctness estimate over all four selected tasks.

The candidate-construction helper and full pre-sanitization Git history are private. The reviewable public tree contains hashes, bounded reports, sanitized records and grading/probe code, with no reference/hidden-test/patch payloads. See `PUBLIC_HISTORY.md` for the publication-boundary procedure. Nothing was pushed or published.

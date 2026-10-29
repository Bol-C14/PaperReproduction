# Reproduction record

Current status (2026-10-29): native Planner live_pilot completed; Placer/Checker/backend remain not_run. See [Planner milestone](pilot/PLANNER_MILESTONE.md). Historical proposal details below describe earlier stages, not additional executed results.

Initial calibration date: 2026-10-28 UTC; superseding Planner milestone: 2026-10-29 UTC. Branch `reproduction/benchmark-pdagent`, inherited baseline `809ca20`. No unrelated changes; sparse checkout of benchmarks. Status: metadata_audit, offline_replay and native reference_calibration at initialization scope. At that historical stage live pilot and full-flow reproduction were not_run and API spend was USD0. Current live-pilot totals are recorded above and in the milestone; full-flow remains not_run. The earlier clean calibration head was preserved remotely; this new delta awaits independent review before push.

## Frozen selection and caps

Before experiments, selection.json fixed RPT1, RPT2, TC_03, TC_11 and bp_fe:1:1 (five paper tasks). Metadata inventory of other IDs is not execution. Caps: two-hour setup, 2GB download, four CPU threads, 300 seconds per native control, zero paid calls. Recovery inspected saved files/processes before resuming. A controller outage around21:28–22:32 interrupted work; recovered downloads were reused rather than duplicated. No benchmark jobs remained after recovery.

## Source acquisition and paths

Paper `https://arxiv.org/html/2606.17253v7`; official leaderboard cloned from `https://github.com/fenggev56/PDAGENT-BENCH`; dataset API tree/info and pinned resolve URLs from `fenggev566/PDAgent-Bench_open`; linked harness cloned from `https://github.com/fenggev56/OpenLayout`. Exact revisions and hashes are in manifest.json. QA and references remain outside the reproduction repository in controller `evidence-private/dataset`.

APRIL root `$APRIL_ROOT`, with isolated `checkouts/pdagent`, `assets/pdagent`, `tools/pdagent`, `results/pdagent`. Existing projects/global dependencies were not changed. The public payload excludes upstream artifacts, dataset answers, collateral, PDFs and databases. Native runner scripts are original audit glue and consume the separately pinned upstream initialization Tcl.

Acquisition commands (actual URL forms):

```sh
git clone --filter=blob:none --no-checkout https://github.com/Bol-C14/PaperReproduction.git PaperReproduction
git -C PaperReproduction sparse-checkout init --cone
git -C PaperReproduction sparse-checkout set benchmarks
git -C PaperReproduction switch -f -c reproduction/benchmark-pdagent origin/HEAD
git -C PaperReproduction branch --unset-upstream
git clone https://github.com/fenggev56/PDAGENT-BENCH.git upstream-pdagent
git clone --depth 1 https://github.com/fenggev56/OpenLayout.git upstream-openlayout
curl -L --fail https://arxiv.org/html/2606.17253v7 -o evidence-private/paper-v7.html
```

The attempted `origin/main` checkout failed because the remote has no main branch; no files were overwritten. HF files were downloaded by urllib from `/resolve/794fbb0c3fdf8613ac7384dd5262d67f902986ee/<path>`; per-file sizes/hashes and complete remote inventory are recorded in logs. Full release size from recursive inventory: 619,046,872 bytes. Only QA/documents and bp_fe collateral were acquired, not the full release. Runtime installation fetched49.1MB apt indices and71.1MB dependencies, plus64,047,394-byte OpenROAD package and the Ubuntu image; artifact sizes are below2GB, with no exact network-byte accounting claimed.

## Offline controls

```sh
python3 analysis/evaluator_controls.py /path/to/pinned/OpenLayout logs/evaluator_controls.json
python3 analysis/qa_schema_controls.py /path/to/private/dataset logs/qa_schema_controls.json
sips -s format png /private/report/images/Report_images01.pdf --out /private/rendered/RPT1.png
sips -s format png /private/report/images/Report_images02.pdf --out /private/rendered/RPT2.png
```

Run from this directory, replacing paths with the pinned private source locations. Metric controls execute unmodified upstream functions. QA controls are explicitly hypothetical literal/substring alternatives because official QA checkers are not released; their outputs are not official correctness grades. Report references and negative interpretations were manually inspected, with no numeric judge score claimed. Public QA logs contain hashes, not answer text. See REVIEW.md for detailed findings.

## Native released open-subset calibration

Rocky9.7 x86_64 APRIL, Python3.9.25, rootless Podman5.6.0/crun. Ubuntu22.04 manifest digest `sha256:8a2321a92b438238f93b4346fff61bc4259c99fdd4d9b52ee86f153fee0c344f`; OpenROAD `26Q2-1164-g08f67ee5ec`. Package obtained through the public API linked from official OpenROAD installation docs at `https://vaultlink.precisioninno.com/api/releases/26Q2-1164-g08f67ee5ec/openroad_26Q2-1164-g08f67ee5ec_amd64-ubuntu-22.04.deb/download`. Containerfile and package/runtime records are in logs. Built image ID `080c40706b37fb2fece6a61412d17c0e025ee87af82af28e79aa90f5d02a78ac`.

```sh
podman build --tag localhost/pdagent-openroad:26Q2 $APRIL_ROOT/tools/pdagent
python3 $APRIL_ROOT/checkouts/pdagent/native_calibration_affinity.py
python3 $APRIL_ROOT/checkouts/pdagent/probe_db.py
```

All actual argv are in native_results.json/readback.json. Candidate runs have network disabled, read-only rootfs, dropped capabilities, no-new-privileges, PID/memory limits, temporary tmpfs, task data read-only, one per-control output mount, and no home/reference/credential mounts. Four-core process affinity and OpenROAD thread count4 enforce the CPU bound without changing host security settings. No model/generated untrusted solution was evaluated.

The pinned native binary is a chosen released OpenROAD version; the paper does not provide an exact matching OpenROAD build. This version choice is a reproducibility deviation, not evidence of exact paper toolchain replication.

The first attempt used `--cpus=4`: all three controls failed before OpenROAD startup (rc126), because rootless cpu controller delegation was unavailable. This is infrastructure failure, not task incorrectness. A second recorded attempt replaced only that unsupported resource option with taskset affinity and preserved isolation. No seccomp disabling or privileged mode was used.

Completed native reference and alternative each produced an18,473,879-byte DB. Fresh readback verified33,199 instances,39,512 nets and11 macros in each. Both had rc0 and no timeout. The keyword-only control also had rc0 but no DB/facts and was rejected by the custom artifact check. These are initialization results only.

Reference: official `openlayout/scripts/floorplan_init.tcl`. Valid alternative changes only `report_design_area` to `eval [list report_design_area]`. Negative prints the upstream completion marker without performing design operations. Headers set paths to isolated /data and /out and threads4. No upstream source edits. Independent DB readback checks instance/net/macro counts in a fresh protected OpenROAD process.

| Selected task | Actual result | Status and boundary |
|---|---|---|
| RPT1 | PDF rendered, reference/negative semantics reviewed; no judge grade | reference_calibration only |
| RPT2 | PDF rendered, displacement observations reviewed; causal density inference not established by image alone | reference_calibration only |
| TC_03 | literal/substring sensitivity controls executed; official checker unavailable | offline_replay of novel schema probe; official task not_run |
| TC_11 | same; accepted option token versus option text probed | offline_replay of novel schema probe; official task not_run |
| bp_fe:1:1 | native reference/alternative initialization and keyword-only negative; see raw results/readback | reference_calibration of init; macro-placement/routing/agent task not_run |

No timeouts occurred in completed native controls. The full 16-task suite, original ten commercial flows,210 commercial scripts, all unselected QA tasks, model calls, post-route scoring and LVS were not run. The native initialization is a current released open-flow calibration, not a translation of commercial-tool tasks and not reproduction of original full-flow results. Paid/judge calls and missing commercial assets remain blockers for their respective protocols; bounded follow-up is proposed in NEXT_EXPERIMENT.md.

## Full-workflow follow-up boundary

See WORKFLOW_FEASIBILITY.md. A fresh protected OpenROAD DB probe confirms all11 macros are unplaced at(0,0). The pinned releases have no reference candidate coordinates/placed DB. The advertised --no-llm outer mode still starts model-driven macroflow for this11-macro case. No arbitrary placement or model path was substituted. Full workflow remains not_run/resource_blocked pending a provenance-pinned valid reference placement (or separately approved live pilot); no routed artifact or post-route score exists.

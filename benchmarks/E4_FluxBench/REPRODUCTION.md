# E4 reproduction record

## Completed scope

Public arithmetic replay: `offline_replay`. Open-tool synthesis-stage port: `reference_calibration`. Authorized single physical-flow extension: `partial_method_reproduction`, initially stopping at a validated CTS checkpoint and routing timeout; a later authorized same-case retry produces routed artifacts/GDS while still failing setup timing. This is neither exact paper-protocol reproduction nor a live-agent result.

The new local branch is `reproduction/benchmark-fluxbench`, based on `809ca20e003c2f5d5a723c77ead8a6de532e4539` in Bol-C14/PaperReproduction. No remote repository was created and no push was performed. The base contains prior work; only `benchmarks/E4_FluxBench` is changed.

## Pins and input contracts

Paper: https://arxiv.org/html/2607.17528v3 . Current release: https://fluxbench.net/ with public leaderboard generated 2026-09-08T14:16:10Z. See manifest for exact asset versions/hashes. Original benchmark code/dataset/container/tool pins are unavailable, not silently replaced.

PicoRV32: `YosysHQ/picorv32@ef203c2b0a3fb793280f5114941416c425c5b461`, upstream default parameters, ISC source in `results/port-v1`. This source revision was resolved during audit, not claimed as the paper's revision. Yosys 0.41 (`c1ad37779ee`, g++11.5.0); Icarus 13.0 stable (`v13_0-dirty`, exact binary hashes recorded). Existing installations were reused unchanged. No container was used. The tool-license families are ISC and GPL respectively; binaries are not redistributed.

Selection and budgets were saved before launching the port in `SELECTED_TASKS.json`: one design task, four-thread environment cap, 120-second timeout per subprocess, zero model/API calls, zero paid cost, two-hour active setup and two-GB download ceilings. Interruptions caused elapsed idle time; public inputs downloaded were under one MB, no large tools or images installed. No randomness in the program/testbench; no seed sweep. The declared 10-ns clock documents stimulus only: no timing constraint was applied to synthesis and no 350/700-MHz closure was attempted.

## Commands

From this directory, replay public arithmetic using only the standard Python library:

```sh
python3 analysis/audit.py results/public_measurements.json
```

The original successful audit used the byte-pinned `leaderboard-data.js` snapshot outside the publication tree. The derived numeric JSON includes the necessary fields to reproduce the same scores; its byte hash differs. `score_audit.json` retains the original snapshot hash and per-record deltas. Re-running overwrites that output, so preserve a copy if retaining original-run provenance.

Actual execution host invocation:

```sh
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 python3 ${E4_WORK_ROOT}/checkouts/fluxbench/port.py
```

The initial 13 subprocess commands, durations, exit codes and hashes are in `results/port-v1/summary.json`; raw output logs accompany it. `analysis/port.py` uses the pinned source under `assets/fluxbench`, and existing Yosys/Icarus paths. It strips model/provider environment variables from child processes. This trusted upstream RTL calibration uses isolated task directories; no evaluated agent, secret-bearing workspace or external solution is executed.

The runner intentionally has a unique `port-v1` output location. Inspect existing summary and processes before rerunning. Use a new run directory for a new experiment rather than merging results.

## Actual results

- 52/52 reported scores match at tolerance 0.001; maximum error 0.0000491511691365 points. All 24 historical records and all 28 newer records are retained; none selected away after viewing outcomes.
- 17/17 own-scorer controls pass. These are synthetic tests, not official harness tests.
- Default and no-ABC synthesis variants produce identical hashes and pass structural checks, independent netlist reload and 1000-cycle RTL differential simulation, each with 333 fetches.
- Default synthesis: 3.146 s; no-ABC: 3.137 s. No ABC phase appears in this tool build, so this pair does not test a real mapping difference. Those durations are one-run measurements and exclude controller interruptions. Both complete within caps.
- Negative observed address comparison: nonzero exit, explicit bus mismatch at cycle 4. This corrupts the observed bus in the testbench, not the synthesized RTL, and only demonstrates comparator sensitivity.
- Invalid Verilog: nonzero exit plus parser diagnostic. Neither negative was inferred solely from an exit code; inspect the logs.
- No experiment subprocess timeout or infrastructure failure occurred during the final port. Earlier setup/transport failures are listed below.

The generated netlists and JSON design databases remain on execution host at `results/fluxbench/port-v1` (26 MB total run directory including compiled simulation files). Their hashes are recorded. To keep the public payload small, logs, testbenches, constraints, upstream licensed RTL and summary are preserved locally; netlists are reproducible from the commands. No final GDS exists or is claimed valid.

## Failures, exclusions and deviations

Commercial original runs at both frequencies: `resource_blocked`, missing licensed technology/harness/runtime. NVDLA: excluded because it is a later distinct protocol. Live pilot: `not_run`, initial phase prohibits model calls. The initial phase excluded a physical port. Parent instruction later authorized exactly one bounded physical extension using E3 tools; its incomplete result is detailed below. No shared installation or dependency was changed. Clock gating and ECO gates remain unvalidated. Unsupported Token ROI normalization remains unknown.

First local clone inherited missing partial-clone objects, causing failed checkout; no user work was present in this newly created checkout. Auto-review initially rejected sparse/index repair, then allowed one retry after reflog and file-state evidence. The branch switch and index repair succeeded; later tracked-only diff was clean. Broad untracked enumeration still tried to lazy-fetch an unrelated upstream `.gitignore` and failed DNS. No reset, destructive checkout or deletion of prior work was used after recovery. Local commit is restricted to E4 paths.

Controller transport failed twice during setup and interrupted file-transfer/probe calls. Some writes initially had uncertain outcomes. Recovery inspection confirmed both scorer files and original score output existed, no residual benchmark processes, and an empty execution host port results directory before launch. Successful scoring was not rerun. The initial port ran once. Hash inspection revealed an ineffective default/no-ABC contrast. Before a follow-up was launched, selection was amended to add one no-ABC/no-alumacc variant. Its netlist hash differs, and reloading plus the same 1000-cycle/333-fetch simulation pass; see `alternative2-summary.json` and `analysis/alternative.py` for four additional commands. No failed or identical-output variant was omitted. No accounts, credentials, security settings, model endpoints or upstream repositories were modified.

## Publication sanitization

The original unpublished commit is retained only on a private local ref. Original evidence is preserved outside this publication directory. Nine initial public files plus the subsequent physical evidence derivatives were transformed to remove execution usernames and host absolute paths; `PUBLIC_DERIVATIONS.json` links each original SHA-256 to its sanitized derivative. Portable runners require `E4_WORK_ROOT`; logs display placeholders instead of host roots. Public raw-log files are consequently sanitized derivatives, not byte-identical originals. The proposed replacement commit must not descend from the original sensitive commit.

The finite program performs a simple fetch/add/jump loop. It does not exercise stores, data-dependent branches, backpressure or interrupts; none of these simulations establishes whole-CPU equivalence.

## Single physical-flow extension: actual execution

The frozen case is `PICO_PHYSICAL_PORT_001` in PHYSICAL_SELECTION.json. Tool image ID `080c40706b37fb2fece6a61412d17c0e025ee87af82af28e79aa90f5d02a78ac`, OpenROAD `26Q2-1164-g08f67ee5ec`; exact image digest, ABC binary and asset hashes are in `results/physical-v1/environment.json`. The existing E3 asset files were mounted read-only. Their contents, generated Liberty simulation models and container layers are excluded from publication. No new downloads occurred. Four-CPU affinity and an 8-GB container cap applied, with network disabled and isolated output mounts.

Actual command sequences and failures are preserved under `results/physical-v1/*-runs*.json`, with sanitized stdout/stderr logs. Reproduction scripts require `E4_WORK_ROOT` and use existing tool paths; inspect saved state before rerunning. Execution order was physical_map.py, physical_finish_map.py (partial failure), physical_validate_map.py (partial failure), physical_recover_map.py (successful finite calibration), physical_flow.py (SDC compatibility correction followed by routing CLI failure), physical_resume.py (route timeout), physical_readback.py, and physical_validate_checkpoint.py. The prepared physical_validate_final.py was not executed because no routed artifacts existed.

- A source-relative-path preflight failed; preflight.log is retained.
- ABC exported scalar bus pins and a synthetic clock. wrapper.v reconstruction restored the original interface and clock connection before any physical run. The first mapped design still contained generic `$dff` cells.
- Liberty behavioral import failed on CLKGATETST_X1's missing function. The recovered import skips unsupported unused cells but requires hierarchy completeness for every instantiated cell. Its initial simulation failed at cycle zero. Additional generic-FF lowering and procedural cleanup recovered a netlist containing no generic cells; the finite loop passed. This does not prove every functional behavior.
- OpenSTA rejected `remove_from_collection`. The correction explicitly selected the same non-clock inputs, preserving clock and delay constraints; the failed floorplan attempt is retained.
- Floorplan: 0.660 s; placement: 5.500 s; CTS: 4.957 s. Logs include placement legality checks. The first routing attempt rejected deprecated layer arguments (1.220 s); existing `set_routing_layers` already expressed the frozen layer range, so only duplicate obsolete options were removed.
- Resumed detailed route: **timeout at 300.008 s**. Last captured progress reported 4117 violations during iteration three; no final DRC or routed database exists. No further routing attempt was run. The timeout killed the client but left its container active briefly; timeout-cleanup.json records verified-owner cleanup. Public runners now add a container name and ownership-checked stop on timeout; this post-run hardening was not another experiment.
- Independent reread used cts.odb, SHA-256 `8e354cbf16135268c6608838b01f79aec0b5b2f3f6db93673146925b5405406a`, and SDC SHA-256 `17f7b8fa4b3f81cae2c1480e9344a261e381b8de51164e795e7c6491f89d4d42`. Facts: 12699/12699 instances placed, 149 clock buffers, zero routed nets, 12624 unwired multi-terminal nets, clock 10.000 ns. Area 18601 um², placement-estimated setup/hold WNS -5.94/+0.01 ns, setup TNS -217.70 ns. Thus setup timing fails and routing is incomplete.
- Independent CTS netlist export plus behavioral-cell import/compile/simulation passed 1000 cycles and 333 fetches. It is not whole-CPU equivalence or physical signoff. Post-route functional validation remains not_run.

All mapping failures, compatibility failures and the selected route timeout are included. The source and constraints were not tuned after observing outcomes; compatibility fixes and one mapping-lowering recovery were recorded explicitly. There was no architecture sweep, model experiment, API call or score assigned to this port. Final GDS requires matching cell GDS/layer map, which were not found or downloaded. PDN, LVS, ECO, extracted timing/power and complete routed connectivity remain unverified.

Physical setup and execution remained within the original two-hour active-setup/two-GB download bounds; no material enlargement was made. A requested future increase to the route limit is a proposal only.

The first physical-evidence archive transfer included diagnostic stdout before the tar stream and failed local extraction. A clean read-only transfer recovered the same saved files; no experiment was rerun for this. Original physical logs remain privately preserved; publication derivatives use portable placeholders and original-hash linkage.

## Authorized 1200-second same-case retry and terminal-artifact checks

The parent approved exactly one longer routing attempt; `ROUTE1200_SELECTION.json` was written before launch. The old CTS hash and SDC hash were rechecked and no residual E4 process/container was present. The new directory is `results/fluxbench/route1200-v1`, separate from the 300-second attempt. It adds a global-route ODB checkpoint before detailed route; no objective or selection was changed.

Actual sequence: `analysis/route1200.py`, `route1200_readback.py`, `route1200_functional.py`, `route1200_extract.py`, `route1200_streamout.py`, then independent KLayout scripts `route1200_gds_validate.py` and `route1200_gds_crosscheck.py`. All require the existing pinned tools/assets and portable work-root paths; exact container/command records accompany results. The KLayout container commands are in the probe and validation command JSON records. Route output hashes and unchanged SDC are checked before reread/measurement. No live model is involved.

| Selected routing attempt | Limit | Recorded client wall | Outcome | Paid/API cost | CPU measurement |
|---|---:|---:|---|---:|---|
| Original `physical-v1` | 300 s | 300.008417 s | timeout; no final routed ODB | $0 | full CPU total unavailable; container cleanup recorded |
| Authorized `route1200-v1` | 1200 s | 363.538396 s | completed; router final violations 0 | $0 | detailed router reports 1240 s, elapsed 343 s, peak 1314.40 MB |

Recorded client wall sum: 663.546813 s. This excludes the first timeout's brief orphan-container cleanup interval, whose exact CPU/wall overrun was not measured. Global-route/container overhead is included in each client wall record but not the detailed-router-only CPU footer. Auxiliary readback/extraction/streamout/validation durations are recorded individually; they are not rolled into router CPU totals. No new paid services or model APIs were used.

Independent routed readback (1.869 s) confirms 12699/12699 placed instances, 149 clock buffers, 12624 routed nets and zero multi-terminal signal/clock unwired nets (power/ground excluded). The final router explicitly reports zero violations, not just a successful exit or empty file. Fresh route-netlist cell import/compile/simulation passes 1000 cycles, 333 fetches; this still excludes stores, data-dependent branches, backpressure and interrupts.

OpenRCX extraction (2.989 s) uses pinned `rcx_patterns.rules`, SHA-256 `2f65fafbe2c704b378563c53a680b93cef080c2799997019d43df7d1e5a563e9`; `extracted.spef` is 16663331 bytes, with 12624 `*D_NET` entries and SHA-256 `44c962c45122690b5b091c2bfb81759ae0bd5e8c3bba8c377eae1a221517f39e`. Extracted setup/hold WNS is -1.00/+0.09 ns and setup TNS -35.73 ns. No timing closure is claimed. This research-model extraction is not foundry signoff, and its difference from placement estimates is not a design improvement. The report command produced a deprecation warning for `-group_count`; its detailed path and negative slack are retained.

Official compatibility evidence is in `results/nangate-gds-probe-v1`: source repository/commit, Apache platform license hash, BSD streamout-script license hash, matching Git blobs for all three existing Liberty/LEFs, KLayout 0.30.3 and exact existing ORFS image digest. Source GDS SHA-256 is `7fdbd7f4e46283fdd9b9a369e1cae1a7f6f742c8e75cfe943c17f451626fe8e8`; layer-map file SHA-256 is `45382e7c1ad2c3727fec79fc0249dceff8ce8fab8ef815017ad5de3350a87a12`. Only file paths were adapted; the layer-map text is unchanged. All 12699 instances/32 masters have matching nonempty source GDS cells. No new image/tool installation was made; selected source downloads total 952222 bytes plus small API listings. Full private evidence archive transfer was about 19 MB, still well below the original 2-GB bound.

Official pinned streamout harness SHA-256 `3d6a851764ab590a55ad51f6726b6954562560c9cd2d098d8bc53caad8a51209` produces `final.gds` (12142354 bytes), SHA-256 `50942bd7be0275d15e2b73ba0dc01d800eee6f927e0aae202e42a7f09e21b2c0`. Independent positive and truncated-file controls pass their respective criteria. GDS structure: one top, 39 cells, no empty cells, 12699 standard-cell instances, five used top routing-metal layers, stable roundtrip facts. The streamout DBU warning (DEF 2000 units/um vs GDS 0.0001 um) was not ignored: all 108721 top standard-cell/via transforms and direct routing polygon geometry on layers 11-21 match after exact factor-five scaling. This is a transfer/structure verification, not LVS or complete DRC.

The official root `LICENSE` URL initially returned 404; the actual `LICENSE_BUILD_RUN_SCRIPTS` was then located from the official directory listing. The pre-existing image lacks the assumed `/opt/ORFS`/RCX-script paths, so source was resolved from the pinned official repository and usage verified from installed primary help. A shell-quoting metadata probe failed before remote execution and was corrected with structured arguments. These metadata failures did not rerun or alter the selected routing case.

All routed ODB/DEF/netlists, SPEF, GDS and raw logs are retained privately on execution host and controller; their recorded hashes were verified after transfer. Public evidence contains sanitized logs/metadata and our scripts, with original-hash linkage. Library GDS, models, container layers, final design GDS and other large carriers are excluded from the proposed public payload. New results are committed separately from reviewed base `ac8cffbf50dd42b3261eb63296891a4d73e5e337` and require exact-head delta review before any push. No push was made.

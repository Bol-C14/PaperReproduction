# E4 reproduction record

## Completed scope

Public arithmetic replay: `offline_replay`. Open-tool synthesis-stage port: `reference_calibration`. Authorized single physical-flow extension: `partial_method_reproduction`, stopping at a validated CTS checkpoint and routing timeout. This is neither exact paper-protocol reproduction nor a live-agent result.

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

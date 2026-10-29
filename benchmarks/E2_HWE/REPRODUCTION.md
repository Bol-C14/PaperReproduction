# HWE-Bench reproduction ledger

Scope: four frozen tasks, two repositories; current-release audit and offline reference calibration. **The original offline phase used no API, agent or GPU.** A later separately released one-case live pilot is documented in LIVE_PILOT.md; it used two requests and USD 0.00280638. No push occurred. Shared prior API spend was USD 0.04806425 against USD 10; the saved post-pilot total is USD 0.05087063. The initial bound is two hours of setup, 2,000,000,000 downloaded bytes, four CPU threads per running paper task, sequential simulations here.

Source pins, dataset SHA-256, task base commits and test/reference hashes are in `selection.json`. Immutable image digests, raw registry manifests and compressed layer sizes are in `raw/oci/`. Four images share 29 layers totaling **1,951,015,228 compressed bytes**. This is an exact registry layer-size sum, not an on-wire measurement or unpacked disk estimate. Extra source/data overhead must also fit the setup bound; no whole-repository image-pull script is used.

## Commands and isolation

Controller: macOS, dedicated branch `reproduction/benchmark-hwe-bench` in existing `Bol-C14/PaperReproduction`. A local clone of the prior controller initially failed checkout because inherited DeepCell checkpoint objects were unavailable. Sparse checkout of `benchmarks` recovered the new checkout without changing the source checkout or its branch. Parent commit is `107d3015cb9a210f1e9a28a7910c0981eacc7600`; remote branch names were rechecked and the requested HWE branch was absent.

Choose an execution workspace root `WORK_ROOT`; this task owns the relative directories `checkouts/hwe-bench`, `assets/hwe-bench`, `logs/hwe-bench`, and `results/hwe-bench`. Rootless Podman 5.6.0 is installed, Docker absent, initial image store empty. System Python is 3.9.25; the full upstream package requires Python ≥3.12. Native replay therefore extracts unchanged `runtime_files` methods and executes their files with Podman rather than installing the full Docker/Harbor Python stack. This is an **orchestration port**, not exact paper-protocol reproduction. It preserves each record's native simulation script and image. The offline controller requested four host-affinity CPUs and MAKEFLAGS/NUM_JOBS/OpenMP were four. Container masks were not measured in that phase; a later host-only control allowed192 CPUs, so the offline wall times are not guaranteed four-core performance. Before the live pilot, the grader was corrected to taskset inside all three containers and real container/child probes verified CPU0–3. Containers receive no host credentials, no host proxy, no external network and only the task-specific read-only verifier inputs.

Reproduce source controls without model dependencies:

```sh
python3 scripts/evaluator_controls.py --upstream /path/to/pinned/hwe-bench --output raw/controls-local
python3 scripts/image_manifest_probe.py --selection selection.json --output raw/oci
```

On APRIL, using the privately held pinned repository-specific JSONLs:

```sh
python3 scripts/native_replay.py \
  --upstream "$WORK_ROOT/checkouts/hwe-bench/upstream" \
  --datasets /path/to/private/hwe-data \
  --selection selection.json --images raw/oci/summary.json \
  --root "$WORK_ROOT/results/hwe-bench/native"
```

The replay script records each image pull, command, return code, timeout, duration and raw log path. Its labels require later adjudication; neither process exit nor parsed PASS alone establishes hardware correctness. Reference patches/tests stay outside evaluated-agent access. No evaluated agent has been launched.

## Actual results

Status: **reference_calibration** for the four selected tasks; **offline_replay** for source and mutant controls; paper-protocol reproduction remains **not_run**. The subsequent single-case extension has status **live_pilot**, separately reported in LIVE_PILOT.md.

| Selected task | Base / reference exit | Behavioral evidence reviewed | Base / reference seconds |
|---|---:|---|---:|
| Ibex 45 | 1 / 0 | Real LSU error classification fails before the patch and passes after it | 2.021 / 1.972 |
| Ibex 48 | 1 / 0 | Decoder output/legality mismatch before the patch; output check passes after it | 2.022 / 2.021 |
| CVA6 1482 | 1 / 0 | Spike/CVXIF software executable built and ran; behavioral fail-to-pass; not whole-core RTL | 182.712 / 182.562 |
| CVA6 2017 | 134 / 0 | CSR value assertion fails before the patch; explicit simulator finish after the patch | 7.337 / 5.581 |

All eight phases completed without timeout. Fresh `git apply --check` succeeded for all reference patches. Actual upstream report AST scoring on the saved logs yields one FAIL→PASS and zero NONE/SKIP→PASS transitions per task. Correctness is supported by the inspected simulator behavior plus applicability and process evidence, not a marker alone. CVA6 2017 has image-prepared runtime baseline `d87707a81fe8926dda2deff844797a491811983a`, distinct from its dataset base `90d780eb14bb99624ad9a377b5140f1781647a33`; both are preserved in the manifest.

Per-repository base+reference wall times: **Ibex 8.036 s; CVA6 378.192 s**. Image pull wall times: Ibex 21.836 s; CVA6 37.629 s. These are observed wall times, not measured CPU-seconds or stable performance estimates. CVA6 1482 rebuilds its native Spike flow separately in both fresh containers. There are no postselection exclusions, missing selected outcomes, simulation timeouts or native infrastructure failures in the successful resumed run. All four selected tasks, and all 70 records in the two inspected repository files, have no declared pass-to-pass checks; this audit does not extend that claim to the other files.

Fresh images retain 882, 892, 6,532 and 6,843 reachable ancestors respectively, with no remotes. None of the 7, 3, 2 and 3 candidate fixing/merge commit objects checked is present. No `/home` patch/test files were found by the bounded image scan before verifier mounts. These checks do not prove absence of all possible answer clues, renamed files, submodule history or inaccessible lower-layer content.

Eleven source-level scoring controls matched the release semantics on both Mac and APRIL. The history fixture retained its baseline ancestor and pruned an unreachable future commit; these source fixtures remain separate from the native task evidence.

### Implementation sensitivity controls

On the calibrated **Ibex PR 48 compressed-decoder task only**, we kept the official hidden test unchanged, applied each implementation in a fresh immutable image, ran the official native test, then built a separate exhaustive combinational probe. The probe covers all 65,536 lower-16-bit inputs with upper input bits zero and compares the decoded instruction and compressed/illegal flags. A separate contract checks all 31 members of the HINT family described by the task, using the ADD encoding equation rather than reference-vector equality alone.

| Implementation | Official upstream report | Differences from reference / 65,536 | HINT-family contract failures / 31 |
|---|---|---:|---:|
| Reference | valid | 0 | 0 |
| Alternative equivalent expression | valid | 0 | 0 |
| Partial family repair | valid | 480 | 15 |
| Overfitted repair | valid | 45,000 | 30 |

Each control compiled and ran successfully; each complete vector set has 65,536 rows. The alternative's vector SHA-256 equals the reference's. The partial and overfitted fixes therefore demonstrate actual native acceptance despite violations of other inputs in the described bug family. This conclusion goes beyond the source-only log anomalies. Official score semantics and tests were not modified. This is **offline evaluator sensitivity**, not an agent result or proof of general hardware correctness. The 480/45,000 counts are differences from the reference vectors; the independently specified contract fails on 15/31 and 30/31 HINT-family inputs. The alternative equivalence evidence covers only 65,536 two-state inputs with the upper 16 input bits zero. It is not universal ISA, four-state/formal, or full-chip equivalence.

`raw/final/` contains public outcome summaries and the hash index for **80 private evidence files**. Complete native logs, hidden scripts, fixes, mutant patches and vectors remain privately held. Public paths in the evidence index are relative bundle members, resolved through the custodian; no host location is published. The private evidence archive SHA-256 is `9ca3e0d0141656e97d0450f98a2f680b5c18ff34878e2554d4688bdc4428f96c`. Private mutant driver and generated-script hashes are recorded for review. Neither reference answers nor hidden test contents enter the public Git payload.

Re-score the saved private logs without changing upstream rules:

```sh
python3 scripts/adjudicate_logs.py --upstream /path/to/pinned/hwe-bench \
  --evidence /path/to/private/final-evidence --output raw/final
```


## Failures and deviations

* Initial sandboxed SSH could not access the existing control socket; authorized escalation succeeded. No host keys or credentials were changed.
* Initial local GitHub DNS failure was followed by authorized network access; the pinned clone completed.
* A source SCP was cancelled after the local clone became available; its incomplete duplicate is not an authoritative source.
* The first native launch attempted extraction before archive transfer completion. Extraction failed with EOF and no simulation started. This controller sequencing error is recorded; recovery verified the archive hash and saved process/log before launch. A subsequent pre-pull AppleDouble parsing failure was corrected. The execution service then became unavailable; after the parent confirmed restoration at 22:32:50, the verified corrected driver completed successfully. See `raw/infrastructure_failures.json`.
* Native Podman replay and AST controls are narrower than executing the full upstream Docker/Harbor stack. No alternative simulator, toy hardware task, or published reference outcome is silently counted as fresh reproduction.

There is no 417-task model score, paper-table reproduction, or independent proof of general hardware correctness. The bounded single-case live pilot does not support those claims.


Local preservation note: normal `git commit` failed while validating missing inherited DeepCell checkpoint objects. The new HWE payload itself passed integrity checks. To preserve the exact already-published parent without unrelated downloads, local commit creation uses `git write-tree --missing-ok`, `git commit-tree -p` that exact parent, and a compare-and-swap branch update. The inherited `P13_DeepCell` subtree hash must match the parent exactly; only `benchmarks/E2_HWE` may appear in the commit diff. This leaves the source clone's preexisting missing-blob limitation explicit rather than fabricating or deleting checkpoint files. Public raw fixture logs intentionally preserve trailing blank lines; whitespace validation permits that EOF convention while still checking other whitespace errors.


## Single live extension and closure

See LIVE_PILOT.md and live_pilot/summary.json for the separately authorized one-case result, pre-run byte-protocol amendment, exact driver/shared-Client hashes and no-retry rules. Two requests and three file tools completed; cost was USD0.00280638, pending/unknown zero. The official reproducer passed and the independent HINT contract had0/31 failures. One reference difference remains in the65536-input two-state, upper-half-zero domain, outside the HINT family. No further calls or spare attempts are authorized in this closeout. Raw prompts/responses, generated solution, hidden/reference tests and vector details remain private with portable hash linkage only.

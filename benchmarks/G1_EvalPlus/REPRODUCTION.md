# G1 EvalPlus reproduction

**Status: offline_replay.** The frozen 20-task/60-program current-release cached replay is complete; 19 tasks calibrated successfully and HumanEval/32 is quarantined as evaluator-invalid. Test reduction is a **partial_method_reproduction**. Original-paper protocol, new input generation and live model evaluation remain **not_run**. API/cloud cost: **$0**. No upstream edits, publication or push occurred.

## Pins, provenance and selection

Paper: arXiv:2305.01210v3, 2023-10-30. Harness: official v0.3.1, `e5d0ed0bab96280b60b637ec7f15b5e4841b0cb2`. Dataset: HumanEval+ v0.1.10. Cached model release: v0.1.0; one `0.py` greedy program per model/task. `SELECTED_TASKS.json` was committed before execution. It is a purposive sample covering documented fixes/paper examples, not a random benchmark sample. ChatGPT and CodeGen-2B are development models; GPT-4 is held out. All 60 source members are pinned by archive member and SHA-256 in `results/{development,held_out}/sample-pins.json`.

| Asset | Bytes | SHA-256 |
|---|---:|---|
| HumanEvalPlus-v0.1.10.jsonl.gz | 925932 | `272720b90ac375502c8ed23cd791c2a93dfb22a911641a494da74a426c09f101` |
| chatgpt_temp_0.0.zip | 117185 | `456a49813ad3afac920b92e53d921cf0a2693f06cb980a85a2ef2e55a717dd47` |
| codegen-2b_temp_0.0.zip | 120671 | `9e5a3c8327401098e8d85d1a079bc1d9aed76bef8edefdd704ee14782109bf4f` |
| gpt-4_temp_0.0.zip | 109561 | `7281a89bfd683ec83ea8bdaf19e2c2d230cda2a4818ddb0761974a52f1172520` |

Harness and dataset repositories specify Apache-2.0; inherited evaluator code carries MIT notices. License texts are retained. Cache archives contain no separate LICENSE/README; repository licensing context is known, archive-specific rights remain unresolved. Cached source, archives, hidden inputs, reference answers, independent oracle implementations and full witness outputs are retained privately and excluded from the Git payload. No restricted/previously rejected redirect was used; ordinary official release URLs succeeded.

Runtime: Python 3.12.12, bubblewrap 0.6.3, NumPy 2.1.3, psutil 6.1.1, tempdir 0.7.1, appdirs 1.4.4, wget 3.2, tqdm 4.67.1, termcolor 2.5.0. No container image or model server. Exact pins are in manifest and per-phase `pins.json`.

## Commands and execution boundary

The controller used the existing SSH connection and dedicated `evalplus` directories beneath the authorized APRIL reproduction root. The adapter root is an environment variable, not a private path in public source:

```bash
export EVALPLUS_REPRO_ROOT=<authorized-reproduction-root>
ISOLATION_ONLY=1 <venv-python> <adapter-dir>/replay.py
REPLAY_PHASE=development <venv-python> <adapter-dir>/replay.py
<venv-python> <adapter-dir>/reduce.py
REPLAY_PHASE=held_out <venv-python> <adapter-dir>/replay.py
REPLAY_PHASE=combined <venv-python> <adapter-dir>/replay.py
python3 analysis/summarize.py
```

Use the retained private `spec_oracles.py` helper with the worker for full execution; its source answers are deliberately excluded from the publication payload. Public summary reconstruction needs only the committed sanitized verdict vectors. The upstream `trusted_exec`, `untrusted_check` and exact AST-extracted `greedy_cover` function were reused. No universal harness or model-generation stack was installed. `reduce.py` avoids importing unrelated generation dependencies; greedy function hash is pinned in `frozen-reduction.json`.

Sandbox checks preceded any cached execution: isolated mount/user/PID/network namespaces; host home and credentials absent; no network route; read-only runtime/harness; clean environment; synthetic correct/wrong/exception/loop assertions; memory and resource limits. Four allowed CPU cores/threads; outer address space 2 GiB; candidate limit 1 GiB; outer CPU 120 s, wall 180 s; controller timeout 190 s; file size 16 MiB and 128 open files. Current upstream per-input limit is `max(1 s,4*reference_time)`, with its normal aggregate task cap plus collection slack. There is no host writable mount. No seccomp/cgroup process-count bound was validated; this is host isolation for pinned cached programs, not proof against hostile Python reflection or grader manipulation. Hidden evaluator fixtures never entered a future generation-agent environment.

Caps were declared before experiments: 20 tasks, 60 unique cached programs, four CPU threads, two-hour initial setup, 2 GB downloads, $0 paid API/cloud. Main data/cache transfer was 1,273,349 bytes; package/source setup was tens of MB, not near 2 GB (exact transitive build-download total was not metered). Work completed within about 32 minutes of initial setup. There were 60 original paired program replays and 57 reduced-suite replays of the same programs, plus reference/synthetic controls; no new samples were generated.

## Actual paired results

All 20 selected tasks and all 60 program hashes are retained. Nineteen reference implementations pass both suites, including independent finite-input output checks. Task 32 fails evaluator calibration and is not counted as a model failure. On the 19 calibrated tasks:

| Cached model | Base pass | Base + full augmented pass | Base pass + augmented failure |
|---|---:|---:|---|
| ChatGPT | 13/19 | 12/19 | HumanEval/140 |
| CodeGen-2B | 5/19 | 4/19 | HumanEval/124 |
| GPT-4, held out | 15/19 | 14/19 | HumanEval/124 |

All three newly rejected programs were privately reexecuted on valid witnesses; independently expressed specification checks agree with the reference. The observed faults are space-run replacement, rejection of a valid month-end date, and an exception on a malformed date. Public evidence contains task/model/index/input hash and confirmation, never hidden inputs or outputs. These are local false accepts by base tests relative to checked task behavior, not global model error rates.

Three full augmented runs timed out and remain explicit: ChatGPT/163 recorded 747/982 inputs; GPT-4/129 118/189; GPT-4/163 442/982. Each also fails base tests, so its conjunction verdict is definitely non-passing without treating unexecuted augmented inputs as failures or successes. No selected task had an outer infrastructure failure. Some task-32 vectors are short for a different reason: evaluator bookkeeping, not timeouts.

### Evaluator and data controls

In pinned `unsafe_execute`, successful `find_zero` residual checks execute `continue` before `details[i]` and progress are recorded. At completion, `untrusted_check` rejects the missing vector entries. A separate reference-only three-input diagnostic observed valid residuals but returned `('fail', [])`. Task 32's full reference replay records base `fail` with 0/100 verdicts and plus `fail` with 7/788; all raw results are preserved. No upstream fix was applied.

Contracts were checked on all 311 base and 14,793 plus inputs across the 20 tasks. Only task 32 violates its embedded contract: 69/788 plus inputs. This contract includes a stricter Newton convergence test; a Horner-order residual check disagrees on seven reference outputs. Floating arithmetic/order/contract analysis remains open; these seven are **not** claimed as independently proven oracle defects.

The independent HumanEval/99 checker initially mishandled binary-float conversion and Decimal precision: 10 apparent mismatches and four unknowns. The checker was corrected, original records retained, and a separate reference-only check then matched all 715 inputs with zero unknowns. No candidate outcome was changed or silently rerun because of this checker correction. Independent finite-input checks support the 19 calibrated reference tasks, not formal correctness or absence of false rejects.

## Reduction and held-out validation

Development-only selection was frozen **before** GPT-4 execution. Upstream greedy set cover was reused exactly. The sample-kill criterion is a direct bounded reproduction; coverage uses observed reference line arcs rather than coverage.py branch requirements; implementation mutation uses the first eligible comparison edit rather than a full mutmut population. These latter criteria are explicit ports. Input mutation/generation was not rerun.

For calibrated19: 211 base plus 14,005 augmented inputs reduce to 211 base plus **29** augmented inputs in the combined suite. Separate criteria retain 15 sample-kill, 23 arc-cover and seven mutant-kill inputs. The 20-task original frozen file remains intact; task32's entries are quarantined by the reference-only validity gate.

Projected and actual combined-suite reexecution agree: ChatGPT 12/19, CodeGen-2B 4/19, GPT-4 15/19. Thus development decisions are preserved, while the reduced held-out suite misses GPT-4/124, which the full augmented suite rejects. Actual rerun completed all 57 valid cached programs; 32 is explicitly retained as evaluator-invalid. This is neither a reproduction of the paper's full 47x result nor a new model ranking.

Eleven comparison mutants exist on calibrated tasks: seven killed, four surviving **unresolved**, eight tasks without eligible comparison. Nineteen equivalent forwarding-wrapper controls pass; task32's wrapper is evaluator-invalid. Equivalent controls are excluded from killed-mutant denominators. Surviving mutants are not silently called equivalent.

Paired task bootstrap (20,000 draws, seed 20261028) gives GPT-4 minus ChatGPT full-suite difference 10.5 percentage points, descriptive 95% interval [0,26.3]. Two discordant tasks favor GPT-4, none favor ChatGPT. The purposive sample and endpoint at zero preclude robust general rank claims. Full comparisons are in `summary.json`.

## Evidence, deviations and completion

Sanitized verdict vectors, package/asset/sample pins, frozen reduction, control assertions and command logs are committed. Original per-task stdout/stderr, witness inputs/outputs and logs remain in private controller `private-evidence` plus APRIL; `RAW_EVIDENCE_INDEX.json` pins the originals. The helper oracle stays private. No secret/environment file was read or published.

Setup deviations: an initial local clone lacked source Git objects; a clean GitHub checkout succeeded. Initial sandbox SSH could not access the existing control socket; escalated SSH succeeded. pip had transient retries, then succeeded. A diagnostic first had shell quoting failure; a corrected reference-only diagnostic succeeded. One witness diagnostic initially surfaced a candidate exception as a process failure; the targeted follow-up recorded that exception explicitly. An execution-environment disconnect occurred before the reduced-run command started; recovery checks confirmed no job/log existed, then it was launched once. None was an automatic approval-policy denial. No duplicate active jobs remain; upstream checkout was verified clean at closeout.

Original-paper dataset/harness reconstruction, full branch/mutmut TSR, generation ablations, historical aggregate scores and a complete false-reject audit remain outside completed evidence. `NEXT_EXPERIMENT.md` bounds the remaining work. No paid requests are pending.

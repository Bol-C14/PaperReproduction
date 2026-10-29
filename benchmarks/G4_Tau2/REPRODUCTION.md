# G4 — τ²-bench reproduction record

## Outcome and status

**reference_calibration**, not live_pilot or partial_method_reproduction. Metadata audit is complete. All performance experiments are **not_run** under the explicit initial zero-model authorization. API calls 0; agent/user/judge cost USD 0. No push, external communication, privileged service or credentials change.

Artifacts live on branch `reproduction/benchmark-tau2` in `benchmarks/G4_Tau2`. The operator supplies private `TAU2_REPRO_ROOT`; its concrete value is withheld: source in `checkouts/tau2/{upstream,paper}`, environment `envs/tau2`, tools `tools/tau2`, logs `logs/tau2`, results `results/tau2`, paper HTML `assets/tau2/paper-v1.html`. The deliverable repository is Bol-C14/PaperReproduction only. Parent independent review is still required before publication.

## Protocol frozen before results

Paper v1, earliest public code `37199f36924c8896f5e048360691f8476cd89ba1` = peeled v0.1.0. Public current-main audit `122e2432b82d740e8f313f46f0a071729c404f39`; later v0.1.3 comparison `5ba9e3e56db57c5e4114bf7f901291f09b2c5619`.

Before execution, `scripts/selection.json` was saved at 2026-10-28T23:38:08.374670+00:00, selecting small-set indices 0,2,8,10,12,19 using metadata only. It includes every selected ID, action length, absence from main-set IDs and all 14 excluded small cases with reasons. No exclusions or replacements after results. Main 114 and full 2285 tasks are metadata-only and not executed. Persona labels are source labels, not independently sampled groups.

Initial caps: 2 setup hours, 2GB downloads, maximum four CPU threads, zero model calls, zero paid resources. Executable jobs are sequential, taskset CPUs 0–3, OMP/BLAS threads 4, timeout 180 seconds per sandbox invocation. All execution completed within the setup window; no timeout. Download traffic was not metered at the socket: public upstream Git pack is 444.52 MiB; public controller repository repair fetched roughly 454 MiB; minimal wheels were tens of MiB, and Python 3.13.12 already existed. These observed components are below the download cap, but no exact total network-byte claim is made. Working-tree expansion uses more disk than compressed downloads: APRIL checkout tree 2,093,866,045 bytes, environment 319,458,533 bytes, paper assets 1,733,381 bytes. Disk footprint is not a transfer counter. No model weights downloaded.

## Actual setup and execution

Existing strict SSH used throughout:

```sh
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes ${REPRO_SSH_HOST} ...
```

The first sandboxed controller SSH attempt could not access its existing control socket (`Operation not permitted`); normal approved elevated SSH then succeeded. No host-key bypass, key installation or SSH configuration change. No approval denial occurred.

APRIL setup commands (run against the absolute shared root above):

```sh
git clone https://github.com/sierra-research/tau2-bench.git "$ROOT/checkouts/tau2/upstream"
git -C "$ROOT/checkouts/tau2/upstream" worktree add ../paper 37199f36924c8896f5e048360691f8476cd89ba1
uv venv --python 3.13 "$ROOT/envs/tau2"
uv pip install --python "$ROOT/envs/tau2/bin/python" pydantic loguru docstring-parser deepdiff python-dotenv toml pytest rich litellm tenacity PyYAML addict langfuse==2.60.7 redis
uv pip install --python "$ROOT/envs/tau2/bin/python" pandas tabulate
```

Set `ROOT="$TAU2_REPRO_ROOT"` using an operator-provided private directory. Exact installed pins are `logs/dependencies.txt`; this is a minimal contemporary runtime, not an install of the historical full `pdm.lock`. Python 3.13.12, bubblewrap 0.6.3, uv 0.10.8, Git 2.47.3. Native Linux/glibc versions and all source/state/policy/data/PDM-lock hashes are in `results/source-audit.json`. No container image is used; this is a bubblewrap namespace sandbox.

`audit_sources.py` is metadata-only and runs on the host. The completed private source-executing checks below used `scripts/run_isolated.sh`. The reference verifier programs `calibrate.py` and `check_reward.py` and raw outputs remain private, excluded from the public payload. These commands record completed runs; public numeric projections are not replay inputs:

```sh
bash "$ROOT/tools/tau2/run_isolated.sh" /scripts/calibrate.py > "$ROOT/logs/tau2/calibration.log" 2>&1
bash "$ROOT/tools/tau2/run_isolated.sh" -m pytest tests/test_environment.py -q -p no:cacheprovider > "$ROOT/logs/tau2/upstream-environment.log" 2>&1
bash "$ROOT/tools/tau2/run_isolated.sh" -m pytest tests/test_domains/test_telecom -q -p no:cacheprovider > "$ROOT/logs/tau2/upstream-telecom.log" 2>&1
bash "$ROOT/tools/tau2/run_isolated.sh" /scripts/check_metrics.py > "$ROOT/logs/tau2/metrics.log" 2>&1
bash "$ROOT/tools/tau2/run_isolated.sh" /scripts/check_reward.py > "$ROOT/logs/tau2/full-reward.log" 2>&1
```

Source is mounted read-only at `/work`, dependencies at `/packages`, Python at `/runtime`, verifier scripts at `/scripts`, only result output writable at `/out`; no host home mounted. Environment is cleared, HOME=/tmp, all network namespaces unshared, no secrets provided. Read-only `/usr`, `/lib`, `/lib64` supply native runtime; `/proc`, `/dev` and temporary `/tmp` are namespace-local. No evaluated model/solution runs here. Reference data is deliberately verifier-only; **do not reuse this source mount as an evaluated-agent workspace**. Future agent staging must exclude reference actions, assertions, tests and fixing commits. The existing bubblewrap utility was reused; no privileged service provisioned.

## Actual task results

All following entries occur in both default tool ownership and solo tool ownership. Solo reassigns tool requestors to assistant; it is a replay transformation, not a live no-user agent. Responses are generated by real upstream tools from task initialization and replayed by the official evaluator, not invented reference traces. The actions themselves are the official task's reference actions. We do not fabricate missing natural-language conversations.

| Small index / task suffix | Reference reward | No-op | Drop last action | Corrupt response | Invalid phone state |
|---|---:|---:|---:|---|---|
| 0 / abroad, provider roaming on, phone off | 1 | 0 | 0 | rejected | rejected |
| 2 / abroad, provider and phone roaming off | 1 | 0 | 0 | rejected | rejected |
| 8 / airplane mode on | 1 | 0 | 0 | rejected | rejected |
| 10 / SIM PIN lock, transfer | 1 | 0 | 0 | rejected | rejected |
| 12 / overdue bill suspension | 1 | 0 | 0 | rejected | rejected |
| 19 / MMS SMS+storage permissions | 1 | 0 | 0 | rejected | rejected |

Rewards in the table respect selected reward basis. Locked-SIM environment reward alone is 1 for no-op; required ACTION component makes combined reward 0. Drop-last equals no-op for one-action tasks 0,8,10, so these are redundant controls. Invalid response replaces the final recorded response with CORRUPTED_RESPONSE; invalid state appends set_user_info with nonexistent phone number before evaluator state synchronization. Both fail with ValueError, not a numeric success/failure score. The public `results/calibration.json` retains all 60 numeric outcomes and exception types. Exact assertion checks, reference responses, state hashes and tracebacks remain in private originals, outside the public whitelist. Tool errors on successful nominal trajectories: 0.

Full official `EvaluationType.ALL` verification: 36 nominal rows match separately computed selected-basis rewards, and 24 reference trajectories overridden with MAX_STEPS or TOO_MANY_ERRORS receive 0 (`results/full-reward.json`). Selected task NL assertion lists are checked empty before calling the aggregator, so no judge/model invocation occurs. The reference fixture termination label AGENT_STOP is a controlled evaluator input, not evidence that an agent ran.

Official tests: **6 environment + 49 telecom = 55 passed**. Numeric reward, assertion/action breakdown and exception structure support the contract findings; exit code/PASS text alone is not the correctness criterion. No broad model/user/LLM tests were run.

## Failures and deviations retained

- Initial local clone of the existing PaperReproduction checkout had missing source Git objects and checkout failed. No unrelated deletions were committed. Scoped sparse checkout plus public `git fetch --refetch origin` restored missing objects; no push. This was infrastructure failure, not a benchmark result.
- First calibration attempt failed at import because pandas was omitted from the minimal environment; zero task rows executed. Original traceback retained privately, outside the public whitelist. Installed pandas/tabulate only in `envs/tau2`, then reran the same selection. Latest dependencies differ from historical lock: this limits exact runtime reproduction.
- Remote `rg` was unavailable, so subsequent bounded inspections used ordinary file reads/grep; no installation of a global utility.
- A source-audit counting expression initially compared a list to a tuple; repaired before final reporting, regenerated and checked totals 114/2285/20. This affected metadata only, not reward/task execution.
- A guessed `tests/test_domains/telecom` path did not exist; the actual official suite is `tests/test_domains/test_telecom`. No task or test failure was hidden by the path correction.

## Metrics and what remains unmeasured

For task n trials and c successes, pass@k is `1-C(n-c,k)/C(n,k)`, while pass^k is `C(c,k)/C(n,k)`. The upstream function named `pass_hat_k` implements the latter. `scripts/check_metrics.py` validates both identities using all binary outcomes of lengths 1..6 and all legal k: 642 checks. Example n=4,c=2,k=2 gives pass@2=5/6 but pass^2=1/6. This is algebraic calibration, not synthetic or actual model reliability.

No live trials, model score, uncertainty interval, simulator variance estimate or cost-performance comparison is available; all are null/not_run. Reference rewards must never enter model pass metrics. `NEXT_EXPERIMENT.md` freezes a proposed 48-episode paired pilot, accounting, uncertainty and hard caps, pending parent release. Full historical model performance and 114-task reproduction remain unexecuted.

## Public evidence boundary

`PUBLICATION.md` defines the answer/trajectory boundary and `PUBLIC_WHITELIST.json` exhaustively lists the allowed G4 files. Public reward files are numeric projections; raw logs and replay inputs remain private. Paths in scripts and resource logs now use operator-provided `TAU2_REPRO_ROOT` rather than machine locations. No reference action sequence, expected argument dictionary or raw task asset is in this payload.

Recount the main-set reward-basis inventory without task text or network:

```sh
python3 scripts/recount_inventory.py
```

The source-hash-bound inventory contains 114 task IDs and component labels only. It verifies 94 ENV_ASSERTION-only and 20 ENV_ASSERTION+ACTION cases. Source extraction can additionally be checked using an authorized pinned asset with `--source`; that asset is not part of this payload. Original numeric outcomes are preserved field-for-field, with receipt in `logs/numeric-evidence-receipt.json`.

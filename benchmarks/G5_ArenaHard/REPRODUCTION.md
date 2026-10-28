# Reproduction checkpoint

**Paused, incomplete.** Parent requested scheduling pause to restore at most five active paper projects. No new run/install/download may start until this same G5 task is resumed. No G5 prepare/replay process remained at checkpoint; no process was killed.

## Scope and actual results

- Offline only: zero model calls, judge API calls, paid compute or publication/push.
- Budget frozen before acquisition: <=2 hours initial preparation, <=2 GB downloads, <=4 CPU threads. Requested dataset files total **329,079,830 bytes**, all 61 succeeded. Source Git transfer and isolated Python dependency downloads add overhead but remain well below the cap; exact transport-level byte accounting was not instrumented.
- Environment: Python 3.11.15; NumPy 1.26.4, pandas 2.2.3, scikit-learn 1.3.2, SciPy 1.13.1; full lock in `logs/environment.txt`. No container used. Upstream and dataset declare Apache-2.0. No global packages changed.
- Controls: 12/12 explicit expected-verdict/weight/orientation checks passed; see `metrics/controls.json`.
- Prompt identity: 500/500 IDs and exact prompt strings match historical source after UID field adaptation (`metrics/schema_port.json`).
- Frozen pilot: lexicographically first 50 IDs, four preselected candidates plus baseline; 606 weighted battle rows; 100 upstream battle-row bootstrap rounds, seed 42. Separability **8/10=80%** within this five-model pilot cohort only.

| Pilot model | Score (%) | Bootstrap 95% interval (%) |
| --- | ---: | ---: |
| gpt-4-turbo-2024-04-09 | 84.507 | 78.724–88.832 |
| claude-3-opus-20240229 | 59.058 | 51.115–65.981 |
| claude-3-sonnet-20240229 | 53.986 | 46.195–61.410 |
| gpt-4-0314 (fixed anchor) | 50.000 | 50.000–50.000 |
| llama-2-70b-chat | 19.149 | 13.336–24.595 |

Main selection: paper Table 1 footnote's 20 models, all 500 prompts, primary GPT-4-1106-preview and secondary Gemini-1.5-Pro-API-0514. Full manifests, question IDs and exclusions are in `sources/selection-plan.json`, `metrics/selected_questions.json`, `metrics/data_quality.json`, and `metrics/matched_questions.json`. No duplicates found by the recorded parser. Primary Mixtral has one invalid record; Gemini has invalid judgments and one missing Mistral-large record. The frozen common complete intersection is 223 questions. Full primary estimates are **not validated/not reported**; matched bootstrap, judge/order sensitivity, human alignment and Brier calculations are **not_run**.

## Execution and deviations

`analysis/prepare.py` obtains only the frozen HF revision; no model text is executed. `analysis/replay.py` imports unchanged historical `get_battles_from_row`, `compute_mle_elo` and `get_bootstrap_result`. The explicit UID schema port is a port, not byte-identical historical reproduction. All 500 prompt identities were verified. Cached response availability does not prove original generation parameters or endpoint behavior.

Three replay attempts are retained: (1) the fixed cache uses `uid` rather than historical `question_id`; (2) a driver Series iteration bug was fixed to use `.index`; (3) pilot completed, then main upstream-versus-closed-form maximum-error assertion failed (`assert err < .0001`). Main upstream bootstrap completed before that assertion but its primary statistics were not saved; no main ranking is accepted. Do not remove or loosen the threshold until diagnosing the discrepancy. A separate small pilot diagnostic independently recovered the same four scores. The isolated environment was installed successfully; an attempted `python -m pip freeze` failed because uv-created venv has no pip; `uv pip freeze --python ...` subsequently recorded versions without installing pip.

The initial local clone from another task had missing Git objects. It was preserved separately; this branch was instead freshly cloned from Bol-C14/PaperReproduction. No upstream code edits, credential changes, new services, network changes, API calls or pushes occurred.

## Resume commands (templates, not executed after pause)

Set `APRIL_ROOT` to the approved project root from the private checkpoint; use existing strict `ssh april1`. Within its isolated arena-hard project:

```bash
export OPENBLAS_NUM_THREADS=4 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
"$APRIL_ROOT/envs/arena-hard/bin/python" \
  "$APRIL_ROOT/checkouts/arena-hard/replay.py" \
  --assets "$APRIL_ROOT/assets/arena-hard" \
  --upstream "$APRIL_ROOT/checkouts/arena-hard/upstream" \
  --out "$APRIL_ROOT/results/arena-hard"
```

First instrument point estimates and analytical rates on the failing main cohort without new downloads; diagnose before rerunning all analysis. Preserve upstream source and frozen sampling. `logs/replay*.log` are path-redacted copies; original logs and all data remain on APRIL, with private local copies of logs outside Git. Source summary JSON is official cached output, not recomputed raw human votes. No pickle was executed; copied pickle was excluded from the deliverable.

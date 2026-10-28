# Reproduction results

Status: **offline_replay**. Completed the frozen primary cached-ranking analysis and supported matched-cache/order sensitivity. No live agent, model generation, judge calls or BenchBuilder curation reruns occurred. Full original-paper reproduction and actual human alignment are not established.

## Versions and resource use

Paper: arXiv 2406.11939v2, 2024-10-14. PDF SHA-256 `09a311cf02974d088ed0b2b830b8424eee3fe4f42295ba3b8f2ad7b8d1000c3a`. Paper-era source snapshot: `19412d70c6e05f02740c5ffdf2b0c22795d06637`; current-release audit: `196f6b826783b3da7310e361a805fa36f0be83f3`. The former is an adjacent release, not a certified experiment commit. Data: HF `15f3746e21432264ce9b453999bde4f3c946d2e6`, only `arena-hard-v0.1`. Source/data declare Apache-2.0; copied source keeps LICENSE. The later venue is ICML 2025, independently verified against [PMLR](https://proceedings.mlr.press/v267/li25h.html); target remains arXiv v2. CCF unknown, because a dated official list was not verified.

Frozen preparation caps: two hours, 2 GB downloads, four CPU threads, zero paid/model/judge calls. All **61** selected data files succeeded, **329,079,830 bytes**. Source Git and dependency downloads add overhead; exact wire-level totals were not instrumented, but acquired data, approximately 50 MB source history and approximately 80 MB dependency wheels remain below the ceiling. No global packages, credentials, network or services changed. No push or publication.

APRIL Python 3.11.15; NumPy 1.26.4, pandas 2.2.3, scikit-learn 1.3.2, SciPy 1.13.1. Complete lock: `logs/environment.txt`. No container or GPU used. Private location record and original logs remain outside this Git package; commands with a portable root variable are in `logs/COMMANDS.md`.

## Frozen input, exclusions and independent checks

Table 1 footnote's 20 models, baseline GPT-4-0314, primary GPT-4-1106-preview; secondary fixed cache directory Gemini-1.5-Pro-API-0514. Five verdicts, strong weight 3, two swapped games, no style control. Pilot: lexicographically first 50 IDs and four preselected candidates; main: all 500 IDs, regardless of pilot. Selection-plan SHA-256 `ff9b26c4c0aeb277d28a1817978a72f5555eccb81cfa34d7ba44bb4727a37528` reverified unchanged.

Explicit port: cache `uid` becomes historical `question_id`; all 500 IDs and exact prompt strings match historical source. Answers use `messages[].content.answer` wrappers where present. Every judgment input contains the corresponding fixed prompt, candidate answer and baseline answer; **zero linkage mismatches** across 37,998 game records. No answer text was executed. All 61 data hashes were rechecked.

Primary: 9500 records, no missing/duplicate records, one record with an invalid verdict. Secondary: 9499 records, **893 invalid two-game records**, **one missing record**, no duplicates. Frozen common-complete intersection: **223/500** questions; excluded IDs are preserved. Invalid primary games contribute zero weight according to upstream behavior. Records with at least one valid game can still contribute that game to the full-primary analysis. No imputation.

Released answers contain **11 exact `$ERROR$` markers**: Claude Opus 1, Mistral Medium 4, Gemini Pro 4, Vicuna 2. No empty/missing assistant content. IDs are enumerated in `metrics/answer_content_checks.json`. These released failures remain in the frozen analyses with their cached judgments; they were not repaired or dropped after observing results. Their original infrastructure cause is unknown.

Every secondary file internally names judge `gemini-1.5-pro-api-preview`, differing from its `0514` directory. Endpoint revision is **unverified**; cross-judge statements here mean fixed-cache comparisons, not verified API-snapshot experiments. See `metrics/judge_identity.json`.

Twelve expected-outcome controls validate ties, slight/strong weighting, invalid verdicts and both positions. Independent raw-verdict code validates primary scores and selected first/second/final paired-bootstrap draws; maximum recomputation discrepancy 7.11e-15 percentage points. All saved intervals and matched separability counts were independently recomputed; see `metrics/verification.json`.

## Numerical failure and correction

The original main run failed `error < 0.0001` percentage points. It was not accepted on exit status or a PASS string. Independent raw counts and scalar likelihood roots matched. A stricter solve of the same matrix likelihood lowered the original fit discrepancy from **0.000764376** to **4.18617e-8** percentage points; the original threshold was retained. This diagnoses function-convergence precision. Accepted estimates use the exact unregularized star-graph likelihood solution; upstream verdict conversion and bootstrap row sampling are retained. Historical fit/bootstrap outputs remain separately saved. Both separate 167/190 pairs. This numerical port is not a bitwise historical reproduction. Full derivation and failed diagnostic attempts: `NUMERICAL_DIAGNOSIS.md`.

## Actual ranking results

Pilot: 50 questions, four candidates plus anchor, 606 weighted rows; 100 upstream row bootstrap rounds, seed 42; **8/10 separable pairs**. It is calibration/replay, not live-agent evidence.

Main: 500 prompts, 20 models including anchor, **27,919 weighted battle rows**. Corrected likelihood with the historical 100-round row-bootstrap design separates **167/190=87.9%** pairs; the paper's Table 1 reports 87.4% (166/190 rounded). This is not an exact table match. Finite bootstrap rounds, input revision and row ordering differ or are not certified identical; no post-hoc sampling was used to match the headline.

The full-primary paired-prompt bootstrap uses **1000 rounds, seed 20261028**, retaining all comparisons, both games and weight replicas together. It separates **152/190=80.0%** pairs. Confidence intervals are marginal percentile intervals; no simultaneous-pair coverage or topic-cluster independence claim.

| Model | Score % | Historical row-design 95% CI | Paired-prompt 95% CI |
| --- | ---: | ---: | ---: |
| gpt-4-turbo-2024-04-09 | 82.626 | 80.679–84.329 | 79.861–85.304 |
| claude-3-opus-20240229 | 60.357 | 58.084–62.496 | 56.239–64.270 |
| gpt-4-0314 | 50.000 | 50.000–50.000 | 50.000–50.000 |
| claude-3-sonnet-20240229 | 46.802 | 44.395–49.686 | 42.511–50.716 |
| gpt-4-0613 | 37.902 | 35.392–39.922 | 33.919–41.523 |
| mistral-large-2402 | 37.711 | 35.209–40.150 | 33.940–41.627 |
| qwen1.5-72b-chat | 36.115 | 33.992–38.614 | 32.439–40.091 |
| mistral-medium | 31.895 | 29.827–33.676 | 28.395–35.624 |
| gpt-3.5-turbo-0613 | 24.821 | 22.640–26.928 | 21.678–28.227 |
| dbrx-instruct-preview | 24.627 | 22.616–26.835 | 21.344–27.947 |
| claude-2.0 | 23.993 | 21.940–25.970 | 20.688–27.110 |
| mixtral-8x7b-instruct-v0.1 | 23.401 | 21.384–25.042 | 20.114–26.510 |
| yi-34b-chat | 23.147 | 21.073–25.224 | 20.116–26.565 |
| claude-2.1 | 22.767 | 20.419–24.708 | 19.603–25.833 |
| gpt-3.5-turbo-0314 | 18.052 | 16.124–20.000 | 15.224–21.045 |
| gemini-pro | 17.803 | 16.336–19.092 | 15.099–20.755 |
| tulu-2-dpo-70b | 14.987 | 13.417–16.692 | 12.722–17.455 |
| starling-lm-7b-alpha | 12.802 | 11.427–13.974 | 10.583–15.140 |
| llama-2-70b-chat | 11.553 | 10.215–13.077 | 9.653–13.675 |
| vicuna-33b | 8.627 | 7.391–9.819 | 6.899–10.483 |

The anchored 50% baseline has no resampling variation by construction; this does not mean its true performance is known without uncertainty.

## Supported cache and order sensitivity

On the frozen **223-prompt** common-complete intersection, both-cache analyses use the same 1000 paired question-index draws. This deliberately avoids comparing judge caches on different retained prompts, but missingness may be selective: results do not extend automatically to the excluded 277 prompts.

| Fixed cache | Both positions separability | First only | Second only |
| --- | ---: | ---: | ---: |
| GPT-4-1106-preview | 125/190 (65.8%) | 119/190 (62.6%) | 112/190 (58.9%) |
| Gemini preview (directory labeled 0514) | 119/190 (62.6%) | 104/190 (54.7%) | 96/190 (50.5%) |

Both-position cache rankings agree on **173/190=91.1%** point-order pairs; Spearman **0.9188**. Paper §3 signed all-pair confidence agreement = **0.5474**; official notebook's different conditional/half-credit definition = **0.9370**. These are judge-cache agreement, not human agreement. Pairwise probabilities and paired-difference 95% intervals are saved in `metrics/paired_rank_uncertainty.csv`.

Across 4237 question–candidate pairs per cache, swapped games disagree in outcome direction **1350** times for GPT and **1722** for Gemini; five-level outcomes disagree **1873** and **1975** times. Max absolute first-minus-second model score difference is **14.12** and **32.24** percentage points, respectively. This is observed cached order sensitivity, not causal isolation of position bias or newly repeated judge calls.

## Unsupported human checks and separate summary replay

Official notebook JSON summary replay uses its own **different 20-model cohort**: 160/190 separable pairs (84.2%). Against its released human-hard-distribution summary, signed all-pair agreement is 0.6947, conditional half-credit 0.9552 and Spearman 0.9008. These are computations on source summaries, not new human evidence or reproduction of paper Tables 1/3/9. Original version-matched paired human votes, style-control data and endpoint provenance were not established. Actual human alignment remains **unknown**; human Brier, raw-human CI, style control, fresh annotation, held-out curation validation and live agent runs are **not_run**. No pickle was deserialized. Some cached marginal score arrays are sorted, so matching their array positions cannot reconstruct paired resamples.

## Failure and scheduling ledger

All unsuccessful selected checks remain visible: initial local Git clone had missing objects (fresh remote clone used); uv venv had no pip for `python -m pip freeze` (uv freeze recorded versions); replay attempt 1 exposed UID schema difference; attempt 2 exposed a driver Series-index error; attempt 3 exposed numerical mismatch; strict-fit diagnostic initially used an incorrect rating sign; verification exposed the judge-label mismatch and an answer-wrapper schema difference. Failed logs are retained, with original private paths redacted only in public copies. The original frozen plan and data were preserved through the parent-requested pause; no running process was killed. This exact task resumed when a slot opened. No scheduled/run timeout occurred.

The final scope is complete offline cache analysis with explicitly unsupported original-paper claims, not full curation/generation/human-alignment reproduction. Reports, manifest, scripts, source evidence and logs are locally committed for parent independent audit; publication requires separate authorization.

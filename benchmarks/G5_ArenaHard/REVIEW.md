# Arena-Hard / BenchBuilder — review checkpoint

Status: **offline_replay**. The frozen cached-ranking analysis is complete; this is not live-agent evaluation or full-paper reproduction. The parent resumed this same task after the documented scheduling pause.

## Identity and contribution

Target: [arXiv 2406.11939v2](https://arxiv.org/abs/2406.11939v2), revised 2024-10-14. The later publication is an **ICML 2025 conference paper**, PMLR 267:34209–34231, verified against the [official proceedings](https://proceedings.mlr.press/v267/li25h.html). That later paper is not silently substituted for the requested arXiv version. CCF: **unknown**, because no dated official CCF list was verified in this checkpoint. Paper type: benchmark/data-curation and evaluation-methodology research. Contributions: automated prompt curation, released open-ended prompt set, and statistical model-ranking evaluation; not an HDL verification method or a new general-purpose agent.

## Mechanism and evidence

BenchBuilder combines embeddings, UMAP/HDBSCAN topic clustering, model annotations of seven prompt qualities, cluster/prompt filtering and stratified sampling. The evaluated benchmark compares each candidate against GPT-4-0314, using GPT-4-1106-preview, five verdicts and two games with swapped answer order. Strong preferences receive weight 3 in the inspected release. Upstream Bradley–Terry fitting and percentile bootstrap intervals produce rankings.

The code snapshot is `19412d70c6e05f02740c5ffdf2b0c22795d06637`, an adjacent paper-era release, not a certified experiment commit. The current release `196f6b826783b3da7310e361a805fa36f0be83f3` defaults to a changed v2.0 protocol; those prompts/judges are excluded. HF cached data revision is `15f3746e21432264ce9b453999bde4f3c946d2e6`.

| Claim or issue | Evidence and interpretation |
| --- | --- |
| Model-ranking quality | Paper §§3,5,6 and Appendix A define confidence-aware comparisons. The completed full-primary replay separates 167/190 pairs (87.9%) under the historical row-bootstrap design. The paper reports 87.4%; this is near but not exact agreement, and no seed/data equivalence is asserted. |
| Confidence agreement definition mismatch | Paper §3 assigns +1/-1/0 across all unordered pairs. `notebook/benchmark_statistics.ipynb` cells 46–52 instead exclude human-overlap pairs and assign 0.5 to prediction-overlap pairs. Both definitions must be reported separately on resume. |
| Curation threshold mismatch | Paper §4.2 describes prompt score >=6 and cluster mean >=5. Historical `BenchBuilder/README.md` describes a GPT-3.5 first pass (<5/<3) and GPT-4 second pass >=6/>=6; its example CLI uses cluster threshold 3. These are distinct documented recipes; exact curation is not established. |
| Model cohort mismatch | Notebook `arena_to_arena_hard.json` contains 20 models different from Table 1's footnote (for example command-r/gemma variants instead of several paper models). Notebook-summary replay must identify its own cohort. |
| Headline human alignment | Tables 1,3,9 use different human distributions and style controls; their agreement and correlation figures are not interchangeable. Raw version-matched human votes have not been recovered; no full human-alignment replication is claimed. |
| Cached judge sensitivity | All 19 primary candidate files are present. Primary has one invalid two-game record; secondary Gemini has 893 invalid two-game records plus one missing record. Frozen all-model/two-judge complete intersection is 223/500 prompts. Missingness can be selective; matched sensitivity cannot describe all 500 without this limitation. |
| Judge endpoint provenance | The Gemini directory is labeled `gemini-1.5-pro-api-0514`, but all 19 files internally label the judge `gemini-1.5-pro-api-preview`. Endpoint snapshot is unverified. Sensitivity results compare fixed released caches; they do not certify named API versions. |
| Prompt-selection model overlap | GPT-4-Turbo annotates selection; GPT-4o, Claude Opus and Gemini contribute annotation validation, and some also occur as evaluated models or judges. This cohort is not an independent held-out model-family validation. No new prompt selection was performed. |

## Prior-work boundaries

The paper's own related work places LLM judging after MT-Bench, AlpacaFarm, AlpacaEval and WildBench; Bradley–Terry and Brier scoring are established statistical tools. The defensible distinction is the curation pipeline and its benchmark-quality application, not inventing model judging, pairwise ranking or bootstrap uncertainty. DynaBench/LiveBench/LiveCodeBench already address evolving evaluation in different settings. This is a bounded primary-source comparison, not an exhaustive novelty clearance.

## Observed results and limits

Twelve deterministic evaluator controls passed. All 500 cached question IDs and prompt texts exactly match the historical source question set after explicit `uid -> question_id` adaptation. All 61 downloaded-file hashes and the pre-download selection-plan hash were rechecked. All 37,998 cached judge inputs contain the frozen question and both corresponding released answers; the answer cache includes 11 explicit `$ERROR$` records, retained and enumerated rather than removed.

The original full fit failed numerical validation. Independent raw counts, scalar likelihood roots and a stricter solve of the same matrix likelihood establish an optimizer function-convergence precision issue; maximum discrepancy falls from 0.000764376 to 4.18617e-8 percentage points without widening the threshold. Accepted results use the exact star-graph MLE, retaining historical approximate results separately. Both versions separate 167/190 pairs. See [numerical diagnosis](NUMERICAL_DIAGNOSIS.md).

| Analysis | Prompts | Bootstrap unit / rounds | Separated pairs |
| --- | ---: | --- | ---: |
| Full primary GPT cache | 500 | weighted battle row / 100 | 167/190 (87.9%) |
| Full primary GPT cache | 500 | paired prompt / 1000 | 152/190 (80.0%) |
| Matched GPT cache, both positions | 223 | paired prompt / 1000 | 125/190 (65.8%) |
| Matched Gemini preview cache, both positions | 223 | paired prompt / 1000 | 119/190 (62.6%) |

The changed uncertainty unit matters more than the numerical correction. Weighted row resampling treats replicated strong preferences and same-prompt judgments as separate observations. Prompt resampling retains their dependence. Neither analysis resamples the source topic clusters, so within-topic correlation remains a limitation; percentile marginal intervals are not simultaneous 190-pair coverage guarantees.

On the fixed 223-prompt intersection, judge-cache point ordering agrees for **173/190 pairs (91.1%)**, Spearman **0.9188**. Paper-style signed all-pair confidence agreement is **0.5474**; notebook-style conditional half-credit agreement is **0.9370**. These are different definitions and neither is human alignment. Across swapped games, candidate outcome direction disagrees on 1350/4237 comparisons in the GPT cache and 1722/4237 in the Gemini cache. This quantifies cached order sensitivity, not a causal estimate of pure position bias.

The official notebook's separate 20-model JSON summary cohort has 160/190 separable pairs (84.2%). Its cached human-distribution summary comparison gives signed agreement 0.6947 and conditional half-credit 0.9552; it is a different cohort/date/protocol and has no newly verified paired human data. **Actual human alignment remains unknown; raw-human Brier and style-controlled human claims are not_run.** Sorted marginal bootstrap arrays in some summaries also cannot reconstruct a shared paired draw index. No human labels were manufactured or inferred from LLM judgments.

The paper's historical dollar cost, curation quality agreement and generalization claims were not remeasured. No curation API, live generation or live judge was run. Full response text and judge inputs remain outside the public Git package. Failed attempts, missing/invalid verdicts and the pause are retained. This establishes a bounded released-cache analysis with a documented schema/numerical port, not exact reconstruction of all original experiments.

## EDA translation (proposal, not run)

Construct a versioned HDL task bank with frozen specifications, hidden tests/formal properties and reference solutions outside agent access. Keep task-selection models separate from evaluated held-out models/families. Run candidates in isolated workspaces under fixed tool versions and budgets. Primary outcome must be executable compile/elaboration/simulation/formal correctness; report timeout, tool error and invalid output explicitly. Only functionally valid designs enter a secondary PPA comparison under common constraints and seeds. Rank correctness first, then report paired task/seed bootstrap uncertainty, separability and held-out ranking stability; cluster by circuit family where appropriate. LLM preferences may describe explanation quality but never override HDL verification. Missing human judgments remain missing.

# Arena-Hard / BenchBuilder — review checkpoint

Status: **metadata_audit; bounded offline_replay pilot only**. Scheduling-paused by parent on 2026-10-28. This is not completion or a full-paper reproduction.

## Identity and contribution

Target: [arXiv 2406.11939v2](https://arxiv.org/abs/2406.11939v2), revised 2024-10-14. The later publication is an **ICML 2025 conference paper**, PMLR 267:34209–34231, verified against the [official proceedings](https://proceedings.mlr.press/v267/li25h.html). That later paper is not silently substituted for the requested arXiv version. CCF: **unknown**, because no dated official CCF list was verified in this checkpoint. Paper type: benchmark/data-curation and evaluation-methodology research. Contributions: automated prompt curation, released open-ended prompt set, and statistical model-ranking evaluation; not an HDL verification method or a new general-purpose agent.

## Mechanism and evidence

BenchBuilder combines embeddings, UMAP/HDBSCAN topic clustering, model annotations of seven prompt qualities, cluster/prompt filtering and stratified sampling. The evaluated benchmark compares each candidate against GPT-4-0314, using GPT-4-1106-preview, five verdicts and two games with swapped answer order. Strong preferences receive weight 3 in the inspected release. Upstream Bradley–Terry fitting and percentile bootstrap intervals produce rankings.

The code snapshot is `19412d70c6e05f02740c5ffdf2b0c22795d06637`, an adjacent paper-era release, not a certified experiment commit. The current release `196f6b826783b3da7310e361a805fa36f0be83f3` defaults to a changed v2.0 protocol; those prompts/judges are excluded. HF cached data revision is `15f3746e21432264ce9b453999bde4f3c946d2e6`.

| Claim or issue | Evidence and interpretation |
| --- | --- |
| Model-ranking quality | Paper §§3,5,6 and Appendix A define confidence-aware comparisons. The completed 50-prompt, four-candidate pilot separates 8/10 pairs including the anchored baseline; this small selected cohort cannot establish the paper's 20-model headline. |
| Confidence agreement definition mismatch | Paper §3 assigns +1/-1/0 across all unordered pairs. `notebook/benchmark_statistics.ipynb` cells 46–52 instead exclude human-overlap pairs and assign 0.5 to prediction-overlap pairs. Both definitions must be reported separately on resume. |
| Curation threshold mismatch | Paper §4.2 describes prompt score >=6 and cluster mean >=5. Historical `BenchBuilder/README.md` describes a GPT-3.5 first pass (<5/<3) and GPT-4 second pass >=6/>=6; its example CLI uses cluster threshold 3. These are distinct documented recipes; exact curation is not established. |
| Model cohort mismatch | Notebook `arena_to_arena_hard.json` contains 20 models different from Table 1's footnote (for example command-r/gemma variants instead of several paper models). Notebook-summary replay must identify its own cohort. |
| Headline human alignment | Tables 1,3,9 use different human distributions and style controls; their agreement and correlation figures are not interchangeable. Raw version-matched human votes have not been recovered; no full human-alignment replication is claimed. |
| Cached judge sensitivity | All 19 primary candidate files are present. Primary has one invalid two-game record; secondary Gemini has many invalid verdicts plus one missing record. Frozen all-model/two-judge complete intersection is 223/500 prompts. Missingness can be selective; matched sensitivity cannot describe all 500 without this limitation. |
| Prompt-selection model overlap | GPT-4-Turbo annotates selection; GPT-4o, Claude Opus and Gemini contribute annotation validation, and some also occur as evaluated models or judges. This cohort is not an independent held-out model-family validation. No new prompt selection was performed. |

## Prior-work boundaries

The paper's own related work places LLM judging after MT-Bench, AlpacaFarm, AlpacaEval and WildBench; Bradley–Terry and Brier scoring are established statistical tools. The defensible distinction is the curation pipeline and its benchmark-quality application, not inventing model judging, pairwise ranking or bootstrap uncertainty. DynaBench/LiveBench/LiveCodeBench already address evolving evaluation in different settings. This is a bounded primary-source comparison, not an exhaustive novelty clearance.

## Observed results and limits

Twelve deterministic evaluator controls passed (tie, slight/strong preference, invalid verdict, and both positions). All 500 cached question IDs and prompt texts exactly match the historical source question set after explicit `uid -> question_id` adaptation. The pilot's maximum absolute upstream-vs-star-graph analytical score discrepancy was 3.10e-7 percentage points.

The main 20-model run stopped at the same numerical validation assertion before saving trusted primary results. It is unresolved. No separability, order sensitivity, judge agreement or human-alignment result from that main run should be cited. All selected models/questions remain frozen; failure logs are retained. Results are cached-answer/judgment replay, not live-agent evaluation, not regenerated judge judgments, and not BenchBuilder pipeline reproduction.

## EDA translation (proposal, not run)

Construct a versioned HDL task bank with frozen specifications, hidden tests/formal properties and reference solutions outside agent access. Keep task-selection models separate from evaluated held-out models/families. Run candidates in isolated workspaces under fixed tool versions and budgets. Primary outcome must be executable compile/elaboration/simulation/formal correctness; report timeout, tool error and invalid output explicitly. Only functionally valid designs enter a secondary PPA comparison under common constraints and seeds. Rank correctness first, then report paired task/seed bootstrap uncertainty, separability and held-out ranking stability; cluster by circuit family where appropriate. LLM preferences may describe explanation quality but never override HDL verification. Missing human judgments remain missing.

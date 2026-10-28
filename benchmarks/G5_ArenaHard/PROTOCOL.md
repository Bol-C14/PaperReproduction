# Frozen offline protocol

Frozen before response/judgment downloads. Preparation ceiling: 2 hours, 2 GB total downloads, four CPU threads, zero model/judge API calls or paid resources. Paper: arXiv 2406.11939v2 (2024-10-14). Source: 19412d70c6e05f02740c5ffdf2b0c22795d06637 (paper-era release snapshot, not certified author experiment commit). Current audit: 196f6b826783b3da7310e361a805fa36f0be83f3. Data: HF 15f3746e21432264ce9b453999bde4f3c946d2e6; only arena-hard-v0.1.

Use the paper Table 1 footnote's 20 models and baseline GPT-4-0314. Primary judge GPT-4-1106-preview, secondary Gemini-1.5-Pro-API-0514. Fixed five verdicts, strong preference weight 3, two swapped games, no style control. First pilot: first 50 question IDs sorted lexicographically, GPT-4-Turbo, Claude Opus, Claude Sonnet, Llama-2-70B. Main: all 500 prompts for all selected models, regardless of pilot rankings. No outcome-driven selection.

Report all missing files, duplicates, invalid verdicts, missing IDs, failed and not-run checks. Main primary uses valid upstream game semantics; matched judge/order sensitivity uses the common complete valid two-game question intersection for all 19 evaluated models and two judges. Baseline is fixed at 50%. Do not silently impute failures.

Use upstream get_battles_from_row and compute_mle_elo unchanged, 100 battle-row bootstrap rounds (seed 42) for protocol replay. Add 1000 paired question-cluster bootstrap rounds (seed 20261028), retaining both positions, strong-weight replicas and all model comparisons together, as a separate uncertainty sensitivity. Separability: strict non-overlap of 95% marginal intervals / all unordered model pairs. Confidence agreement: paper section 3 signed all-pair metric; also report notebook's different conditional/half-credit definition separately. Order sensitivity compares first/second/both outcomes after orientation correction; disagreement is not causal proof of position bias.

Official notebook JSON cached ranking summaries may support offline summary replay only; human raw-battle, style-control and annotation pipeline reruns remain not_run unless corresponding versioned evidence is available. Never deserialize pickle or execute model answers. No live-agent claims.

## Post-freeze execution notes

Frozen selection and missing-data rule are unchanged (selection-plan SHA-256 ff9b26c4c0aeb277d28a1817978a72f5555eccb81cfa34d7ba44bb4727a37528). Historical fit precision failed numerical validation for the main cohort. See NUMERICAL_DIAGNOSIS.md: exact star-graph likelihood scores replace approximate point estimates for accepted calculations; unchanged historical fit/bootstrap outputs are separately preserved. This changes numerical implementation, not the model/judge/prompt selection.

The full-primary 1000-round question bootstrap was also completed on the original 500 prompts, retaining the one invalid game's upstream exclusion. Matched cross-cache/order sensitivity follows the pre-frozen common-complete rule (223 prompts). The Gemini directory is named gemini-1.5-pro-api-0514 but every internal record is labeled gemini-1.5-pro-api-preview; do not infer the underlying API snapshot. Human alignment remains unknown without original paired human data; cached JSON summary comparisons are explicitly separate.

# EvalPlus scientific review — preparation checkpoint

Status: **offline_replay**, with **partial_method_reproduction** of reduction. The frozen cached replay is complete. Original-paper protocol and live model evaluation are **not_run**.

## Measured result and scientific assessment

Across calibrated19, identical cached programs pass base versus full augmented tests at ChatGPT 13→12, CodeGen-2B 5→4 and held-out GPT-4 15→14. Three valid witness failures were independently adjudicated privately. Development-only combined reduction retained 29 augmented inputs plus 211 base inputs, preserving development outcomes; actual reduced-suite reexecution accepts GPT-4/124 even though full augmentation rejects it. This demonstrates the mechanism and a held-out loss of discrimination under a small, explicitly bounded port; it neither reproduces the paper's full aggregate figures nor evaluates newly generated model outputs.

A material current-release defect was observed in the pinned evaluator: successful root checks for HumanEval/32 skip verdict bookkeeping, so correct references can return `fail, []`. All 20 selected tasks remain recorded; task32 is quarantined as evaluator-invalid rather than model-wrong. Additionally 69/788 of its plus inputs fail the shipped contract. Floating summation-order differences in seven residual checks require further numerical analysis. This finding concerns v0.3.1, not evidence that the 2023 paper used that defect.

Nineteen independent reference-control suites and equivalent-wrapper controls pass. Three augmented candidate runs time out with partial vectors; all already fail base tests, so no unknown augmented outcomes are counted as successes. A corrected independent numeric checker matched all 715 task99 inputs; initial checker failures remain in raw evidence. Eleven bounded comparison mutants yield seven killed and four unresolved survivors; equivalent wrappers are a separate category.

Rank uncertainty is substantial: full-suite GPT-4 minus ChatGPT is 10.5 points with paired-task bootstrap interval [0,26.3]. Purposive19 cannot establish a population ranking or the original paper's rank changes. See REPRODUCTION and structured summary for denominators, exclusions, commands and limits.

## Scope and paper claims

[Paper v3](https://arxiv.org/html/2305.01210v3), dated 2023-10-30. Venue is NeurIPS 2023, volume 36, Main Conference Track, verified against the [official proceedings](https://papers.nips.cc/paper_files/paper/2023/hash/43e9d647ccd3e4b7b5baab53f0368686-Abstract-Conference.html). Type: benchmark construction and automated testing methodology with empirical LLM evaluation. Contribution and venue are distinct; CCF category remains **unknown** until a dated official list is checked.

The paper combines ChatGPT seed generation with type-aware **input** mutation, filters inputs by hand-written preconditions, and compares generated-program outputs against reimplemented references. Suite reduction greedily preserves branch coverage, **implementation** mutant kills, and development-model sample kills, with model exclusion for cross-validation. Input mutation creates new inputs; implementation mutation changes a program to challenge tests. They are different mechanisms and denominators.

Reported findings include more test-detected wrong solutions and model-order changes, plus a much smaller reduced suite. These are empirical finite-suite observations, not proof of correctness. This bounded experiment does not reproduce their full aggregate numbers. Budget is fixed at $0 and 60 cached programs over 20 tasks; no new LLM sampling is authorized.

## Source findings and protocol drift

Pinned harness v0.3.1 uses HumanEval+ v0.1.10, while the paper and old model caches precede both. The README records contract, input and oracle corrections across releases. Current-release rescoring cannot establish an exact paper-protocol result without the corresponding historical dataset and harness.

Appendix A specifies a per-input minimum timeout of 200 ms and a reference-time factor of four. Current `evalplus/config.py` defaults to 1 second and factor four. Current evaluator also caps aggregate task runtime (normally 60 seconds plus collection slack) and special-cases root finding through a polynomial residual. These semantics must be recorded and evaluated separately from original-paper settings. The dataset loader accepts `version` parameters but uses `HUMANEVAL_PLUS_VERSION` when forming metadata; do not assume an argument alone switches the dataset version. Use explicit pinned file paths/hashes.

Reduction code preserves empirical kill sets via greedy set cover; the optimum is not guaranteed. The inspected mutation/sample collectors expect legacy `success` and tuple-shaped results, whereas current `untrusted_check` returns `pass`/`fail` with vectors; top-level current result shapes must be checked before running old TSR tools. The current root-oracle failure above has been measured; legacy TSR collector compatibility remains a source-level concern, avoided here by direct calls to the pinned greedy reducer.

## Prior-work boundaries

Differential testing, contracts, fuzzing/type-aware mutation, mutation analysis and greedy test-suite reduction all have substantial prior art explicitly cited by the paper. The distinctive contribution is their combination and empirical application to LLM-code benchmark inadequacy, plus curated oracles/contracts. Claims of universal novelty in automated testing would exceed this evidence. The paper's assertion that traditional methods are inapplicable to arbitrary semantically constrained dynamic-language inputs is broad; comparison against well-tuned property-based or grammar/constraint-guided generators would be necessary to isolate the LLM seed benefit.

## Threats and required interpretation

Reference agreement is an operational oracle, not independent ground truth. A base-pass/plus-fail program is a false accept **relative to the stronger suite** until a valid-input witness and intended behavior are independently adjudicated. False rejects require checking contracts, ambiguous specifications, numerical tolerances and runtime limits; they cannot be inferred to be zero from reference replay. Missing/failed/timed-out tasks cannot be counted as correct. A surviving implementation mutant is not necessarily equivalent; keep proven equivalent and unresolved survivors separate. Reduction fit on development samples must remain frozen before looking at GPT-4 held-out results. Twenty purposive tasks support local mechanism checks, not new global model rankings; paired task bootstrap and discordance counts are needed for rank uncertainty.

Reference replay, cached rescoring, new model evaluation and new mutation controls must have separate statuses. Here reference calibration and cached replay have been executed; original paper-protocol and live generation remain `not_run`. Cached archive licensing is unresolved beyond repository Apache-2.0 context; archives and source remain private pending parent review. Paper source snapshot remains private and is excluded from Git.

## Sequential RTL adaptation

A sequential RTL port needs an explicit cycle-indexed state-transition oracle, bounded traces and reset assumptions (polarity, synchronicity, duration, initialization and post-reset observation). Define latency/valid-ready protocol, X/Z handling, race-free sampling edges and simulator scheduling. Python unbounded integers require explicit width, signedness, overflow/truncation and shift semantics; tolerances generally become exact bit-vector comparisons. Generate legal input traces and stateful contracts rather than independent calls, mutate reset/timing/data sequences separately from RTL implementation mutants, preserve temporal/assertion and state-transition coverage, and classify equivalent mutants by bit-vector/temporal equivalence over stated assumptions. Passing finite simulation traces must not be labeled formal equivalence.

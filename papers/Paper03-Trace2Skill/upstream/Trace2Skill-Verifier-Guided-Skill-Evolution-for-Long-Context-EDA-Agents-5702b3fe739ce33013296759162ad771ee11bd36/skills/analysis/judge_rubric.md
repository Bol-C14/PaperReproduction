# CVDP Agentic Heavy — LLM Judge Rubric

This rubric is used by an LLM judge to score a candidate analysis report against the golden report. The judge evaluates analytical quality, not just factual accuracy (which is covered by deterministic checkers).

## Judge Prompt Template

```
You are evaluating a failure analysis report for the CVDP agentic heavy benchmark.
You will be given:
1. A GOLDEN REPORT (the reference analysis, verified as correct)
2. A CANDIDATE REPORT (the report to evaluate)

Score the candidate report on each criterion below using a 1-5 scale.
For each criterion, provide a brief justification citing specific sections of the candidate report.

Output your scores as a JSON object with keys matching the criterion IDs.
```

## Scoring Criteria

### C1: Pipeline Funnel Identification (1-5)

Does the candidate correctly identify and present the pipeline funnel (what fraction of rollouts survive each stage)?

| Score | Description |
|-------|-------------|
| 5 | Correct funnel with all stages, identifies the biggest drop-off, and explains its significance |
| 4 | Correct funnel with most stages, identifies the bottleneck |
| 3 | Mentions stage survival rates but not as a coherent funnel |
| 2 | Only mentions final pass rate, not intermediate stages |
| 1 | No pipeline analysis |

### C2: Dominant Failure Mode Identification (1-5)

Does the candidate correctly identify the single most important failure mode and explain why it matters?

| Score | Description |
|-------|-------------|
| 5 | Correctly identifies the dominant failure mode, quantifies it, and explains its causal role in the failure pipeline |
| 4 | Correctly identifies the dominant failure mode with quantification |
| 3 | Identifies a failure mode but not the most important one, or identifies it without quantification |
| 2 | Lists multiple failure modes without prioritizing |
| 1 | No failure mode identification |

### C3: Root Cause Distinction (KG vs UK vs BI vs EI) (1-5)

Does the candidate correctly distinguish between knowledge gaps, unreliable knowledge, behavioral issues, and environment issues?

| Score | Description |
|-------|-------------|
| 5 | Correctly classifies all failed tasks with evidence, maps each to an improvement method (SFT/RL/infra) |
| 4 | Correctly classifies most tasks, provides evidence for classifications |
| 3 | Attempts root cause classification but conflates categories (e.g., calls a behavioral issue a knowledge gap) |
| 2 | Mentions "knowledge" or "behavior" but without systematic per-task classification |
| 1 | No root cause distinction |

### C4: Sometimes-Pass Analysis (1-5)

For tasks where some rollouts pass and others fail, does the candidate compare passing vs failing rollouts and identify what distinguishes them?

| Score | Description |
|-------|-------------|
| 5 | For every SP task: compares trajectories, identifies the specific decision point or code difference, explains why variance occurs |
| 4 | Compares pass/fail for most SP tasks with some trajectory evidence |
| 3 | Notes which tasks are SP but doesn't compare trajectories |
| 2 | Mentions pass rate variance without analysis |
| 1 | No sometimes-pass analysis |

### C5: Causal Narrative (1-5)

Does the candidate connect failure modes into causal chains rather than presenting them as independent findings?

| Score | Description |
|-------|-------------|
| 5 | Presents a clear causal chain (e.g., "B1 → E1 → no file read → wrong fix → reward 0") with quantitative evidence for each link |
| 4 | Presents causal relationships between 2+ failure modes with some evidence |
| 3 | Mentions that failure modes are related but doesn't quantify the causal links |
| 2 | Presents findings as an independent list |
| 1 | No causal analysis |

### C6: Evidence Citation (1-5)

Does every claim cite specific evidence (rollout indices, tool call sequences, error messages, Docker stderr)?

| Score | Description |
|-------|-------------|
| 5 | Every diagnostic claim cites specific rollouts, tool calls, or error messages |
| 4 | Most claims cite evidence, a few are unsupported |
| 3 | Some claims cite evidence, many are general assertions |
| 2 | Occasional evidence but mostly unsupported claims |
| 1 | No evidence cited |

### C7: Actionability (1-5)

Does the candidate map findings to concrete improvement methods?

| Score | Description |
|-------|-------------|
| 5 | Every failure is mapped to a specific improvement method (RL for behavioral, SFT for knowledge, infra for environment) with justification |
| 4 | Most failures mapped to improvement methods |
| 3 | Mentions "could be improved" without specific methods |
| 2 | Generic recommendations ("improve the model") |
| 1 | No improvement recommendations |

### C8: Behavioral Pattern Analysis (1-5)

Does the candidate correctly identify and quantify behavioral patterns (B1-B7)?

| Score | Description |
|-------|-------------|
| 5 | All relevant patterns identified with correct counts, explains which are pathological vs benign (e.g., B5 step exhaustion in Opus is thoroughness, not a problem) |
| 4 | Most patterns identified with approximate counts |
| 3 | Some patterns mentioned but not all, or counts are significantly off |
| 2 | Mentions "behavioral issues" generically |
| 1 | No behavioral pattern analysis |

### C9: Cross-Cutting Analysis (1-5)

Does the candidate analyze patterns that cut across tasks (task type × failure mode, project × pass rate, etc.)?

| Score | Description |
|-------|-------------|
| 5 | Multiple cross-cutting analyses with tables/matrices, identifies unexpected correlations |
| 4 | At least one cross-cutting analysis with data |
| 3 | Mentions cross-task patterns without structured analysis |
| 2 | Only analyzes tasks independently |
| 1 | No cross-cutting analysis |

### C10: Report Completeness (1-5)

Does the candidate cover all required sections per the SKILL.md document template?

| Score | Description |
|-------|-------------|
| 5 | All sections present: exec summary, pipeline funnel, phase distribution, tool usage, errors, patterns, cross-cutting, per-task deep dives, root cause summary, key takeaways |
| 4 | Most sections present, 1-2 minor sections missing |
| 3 | Core sections present but several missing (no deep dives or no cross-cutting) |
| 2 | Only basic metrics present |
| 1 | Minimal or unstructured output |

## Scoring Weights

| Criterion | Weight | Rationale |
|-----------|-------:|-----------|
| C1: Pipeline funnel | 0.5 | Automatable — doesn't differentiate diagnosis from metrics |
| C2: Dominant failure mode | 1.5 | The most important single finding |
| C3: Root cause distinction | 3.0 | The core diagnostic capability BLADE measures — highest weight |
| C4: Sometimes-pass analysis | 2.0 | The sharpest diagnostic — hardest to get right |
| C5: Causal narrative | 2.0 | Distinguishes diagnosis from description |
| C6: Evidence citation | 1.0 | Quality assurance |
| C7: Actionability | 2.0 | Maps diagnosis to improvement (SFT/RL/infra) |
| C8: Behavioral patterns | 1.0 | CVDP-specific analysis |
| C9: Cross-cutting analysis | 0.5 | Partially automatable |
| C10: Report completeness | 0.5 | Structural completeness |

**Total weighted score**: Sum of (score × weight) for each criterion.
**Maximum**: 5 × 14.0 = 70.0
**Passing threshold (suggested)**: 42.0 (60% of max)

## Calibration Results (2026-03-23)

Calibrated on GPT-5 rollout data with two reports of known quality:

| Report Type | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 | Weighted Score |
|-------------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|---------------:|
| **Golden report** (root cause + deep dives + causal chains) | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 4 | 5 | **68.0 / 70.0** |
| **Script-only report** (automated metrics, no diagnosis) | 5 | 4 | 1 | 3 | 2 | 3 | 2 | 4 | 4 | 3 | **35.0 / 70.0** |
| **Spread** | | | | | | | | | | | **33.0 points (47%)** |

**Key findings from calibration:**
- The spread concentrates on C3 (root cause: 5 vs 1), C5 (causal narrative: 5 vs 2), and C7 (actionability: 5 vs 2) — these are the criteria that separate human/LLM diagnosis from automated metrics
- C1 (pipeline funnel) and C9 (cross-cutting) score identically because the script now auto-generates these — hence their lower weights
- C4 (sometimes-pass) shows partial separation (5 vs 3) because the script generates comparison tables but doesn't explain *why* some rollouts pass and others fail
- The 47% spread (33/70) cleanly separates the two quality levels with no overlap zone

**Scoring benchmarks:**
- **Script-only report**: ~35/70 (50%) — correct numbers, automated tables, no diagnosis
- **Good human analysis**: ~55-65/70 — correct root causes, evidence-backed narratives, may miss some cross-cutting patterns
- **Golden report**: ~65-70/70 — the reference standard
- If the judge scores the golden report below 60/70, the rubric needs recalibration

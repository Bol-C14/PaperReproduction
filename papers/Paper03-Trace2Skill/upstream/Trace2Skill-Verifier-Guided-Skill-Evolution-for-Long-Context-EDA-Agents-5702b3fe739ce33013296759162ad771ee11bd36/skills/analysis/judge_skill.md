# LLM Judge Evaluation — CVDP Agentic Heavy Benchmark

You are an independent LLM judge evaluating two failure analysis reports for the CVDP agentic heavy benchmark. This benchmark tests whether LLM agents can fix bugs and modify RTL (Verilog) code in complex chip design projects.

## Your Task

You will evaluate **two reports** that analyze the same rollout data (GPT-5 model, 18 rollouts across 6 chip design tasks, 44.4% pass rate). Both reports analyze the same data but differ in depth:

- **Report A** = A script-generated automated analysis (metrics, tables, patterns)
- **Report B** = A human-enhanced analysis (same metrics plus root cause classification, per-task deep dives, causal narratives, improvement recommendations)

Score **each report independently** on 10 criteria using a 1-5 scale. Then compare them.

---

## Scoring Criteria (1-5 each)

**C1: Pipeline Funnel Identification**
Does the report show cumulative survival through workflow stages (started → wrote files → compiled → ran simulation → passed) and identify the biggest drop-off?
- 5 = Correct funnel with all stages, identifies biggest drop-off, explains its significance
- 3 = Mentions stage survival rates but not as a coherent funnel
- 1 = No pipeline analysis

**C2: Dominant Failure Mode Identification**
Does it identify the single most important failure mode, quantify it, and explain its causal role in the failure pipeline?
- 5 = Correctly identifies dominant mode, quantifies it, explains causal downstream impact
- 3 = Identifies a failure mode but not the most important one, or without quantification
- 1 = No failure mode identification

**C3: Root Cause Distinction (most important criterion)**
Does it classify each failed task into one of: Knowledge Gap (model doesn't know how), Unreliable Knowledge (sometimes knows, sometimes doesn't), Behavioral Issue (knows but makes poor decisions), Environment Issue (infrastructure problem)? Does it map each to an improvement method (SFT for knowledge, RL for behavior, infra fix for environment)?
- 5 = All failed tasks classified with evidence, each mapped to improvement method
- 3 = Attempts classification but conflates categories
- 1 = No root cause distinction

**C4: Sometimes-Pass Analysis**
For tasks where some rollouts pass and others fail, does it compare the passing vs failing trajectories and identify what specifically distinguishes them?
- 5 = For every mixed task: compares trajectories, identifies the specific decision point, explains variance
- 3 = Notes which tasks are mixed but doesn't compare trajectories
- 1 = No sometimes-pass analysis

**C5: Causal Narrative**
Does it connect failure modes into causal chains (e.g., "compile-no-run → can't verify fix → submits untested code → harness catches error") rather than listing findings independently?
- 5 = Clear causal chain with quantitative evidence for each link
- 3 = Mentions relationships but doesn't quantify
- 1 = Findings presented as independent list

**C6: Evidence Citation**
Does every diagnostic claim cite specific evidence (rollout indices, tool call sequences, error messages)?
- 5 = Every claim cites specific rollouts, tool calls, or error messages
- 3 = Some claims cite evidence, many are general assertions
- 1 = No evidence cited

**C7: Actionability**
Does it map findings to concrete improvement methods (RL training for behavioral issues, SFT data for knowledge gaps, infrastructure changes for environment issues)?
- 5 = Every failure mapped to a specific improvement method with justification
- 3 = Mentions "could be improved" without specific methods
- 1 = No improvement recommendations

**C8: Behavioral Pattern Analysis**
Does it correctly identify and quantify behavioral patterns (path thrashing, repeated reads, write without read, no verification, step exhaustion, early exit, compile without running simulation)?
- 5 = All relevant patterns identified with counts, explains which are pathological vs benign
- 3 = Some patterns mentioned but not all, or counts significantly off
- 1 = No behavioral pattern analysis

**C9: Cross-Cutting Analysis**
Does it analyze patterns across tasks (e.g., task type vs failure mode, project vs pass rate)?
- 5 = Multiple cross-cutting analyses with tables, identifies unexpected correlations
- 3 = Mentions cross-task patterns without structured analysis
- 1 = Only analyzes tasks independently

**C10: Report Completeness**
Does it include all required sections: executive summary, pipeline funnel, phase distribution, tool usage, errors, behavioral patterns, cross-cutting analysis, per-task deep dives, root cause summary, key takeaways?
- 5 = All sections present with depth
- 3 = Core sections present but several missing
- 1 = Minimal or unstructured output

---

## Scoring Weights

| Criterion | Weight |
|-----------|-------:|
| C1: Pipeline funnel | 0.5 |
| C2: Dominant failure mode | 1.5 |
| C3: Root cause distinction | 3.0 |
| C4: Sometimes-pass analysis | 2.0 |
| C5: Causal narrative | 2.0 |
| C6: Evidence citation | 1.0 |
| C7: Actionability | 2.0 |
| C8: Behavioral patterns | 1.0 |
| C9: Cross-cutting analysis | 0.5 |
| C10: Report completeness | 0.5 |
| **Total weight** | **14.0** |
| **Max weighted score** | **70.0** |

---

## REPORT A (Script-Generated Automated Analysis)

```
# CVDP Agentic Heavy — Failure Analysis Report

**Model:** GPT-5
**Rollouts:** 18 (6 tasks)
**pass@1:** 44.4%
**pass@k:** 66.7%
**Consistency:** 16.7%

## 1. Executive Summary

Across 18 rollouts on 6 tasks:

**Pipeline funnel:** 18 started → 16 wrote files (88.9%) → 17 compiled (94.4%) → 9 ran vvp (50.0%) → 8 passed (44.4%)

- Mean steps used: **17.3** (median: 18)
- Mean tokens: **317516**
- Mean Docker verification time: **64.9s**

### Self-Verification Behavior

- **72.2%** of rollouts read an existing testbench file
- **50.0%** ran vvp to self-test
- **0.9** mean compile→run feedback loops per rollout
- vvp self-test outcomes: **7** pass, **2** fail

## 2. Workflow Phase Distribution

| Phase | Description | Count | % |
|-------|-------------|------:|---:|
| P0 | No tool usage | 0 | 0.0% |
| P1 | Explore only (ls/cat/pwd) | 1 | 5.6% |
| P2 | Wrote files (echo) | 0 | 0.0% |
| P3 | Compiled (iverilog) | 5 | 27.8% |
| P4 | Tested (vvp/simulation) | 4 | 22.2% |
| P5 | Passed verification | 8 | 44.4% |

**Bottleneck:** Among failed rollouts, most stall at **P3** (Compiled (iverilog), 5 rollouts).
The model compiles but never runs simulation. This is a behavioral issue (B7: compile-no-run) — the model doesn't understand that iverilog only compiles, vvp is needed to execute.

## 3. Pipeline Funnel

| Stage | Rollouts | % | Drop from previous |
|-------|--------:|---------:|-------------------:|
| Started | 18 | 100.0% | — |
| Wrote files (echo) | 16 | 88.9% | -2 (11.1%) |
| Compiled (iverilog) | 17 | 94.4% | — |
| Ran simulation (vvp) | 9 | 50.0% | -8 (47.1%) |
| Passed verification | 8 | 44.4% | -1 (11.1%) |

## 4. Tool Usage Breakdown

| Tool | Total Calls | Calls/Rollout | Error Rate |
|------|------------|---------------|------------|
| ls | 112 | 6.2 | 0.0% |
| cat | 113 | 6.3 | 57.5% |
| echo | 32 | 1.8 | 0.0% |
| pwd | 0 | 0.0 | — |
| iverilog | 42 | 2.3 | 66.7% |
| vvp | 12 | 0.7 | 25.0% |
| xcelium | 1 | 0.1 | 0.0% |

## 5. Tool Error Breakdown

| Error Type | Description | Count | % of All Errors |
|------------|-------------|------:|----------------:|
| E_other | Other error | 64 | 66.7% |
| E3:compilation_error | iverilog compilation error | 28 | 29.2% |
| E4:simulation_error | vvp simulation error | 3 | 3.1% |
| E1:path_not_found | File/directory not found | 1 | 1.0% |

## 6. Behavioral Patterns

| Pattern | Description | Rollouts | % |
|---------|-------------|--------:|---------:|
| B7:compile_no_run | Compiled (iverilog) but never ran simulation (vvp) | 8 | 44.4% |
| B5:step_exhaustion | Used all available steps (max_steps) | 7 | 38.9% |
| B3:write_without_read | Wrote to a file never read first | 3 | 16.7% |

## 7. Cross-Cutting Analysis

### 7.1 Task Type × Best Phase Reached

| Task Type | P0 | P1 | P2 | P3 | P4 | P5 | pass@k |
|-----------|------:|------:|------:|------:|------:|------:|-------:|
| CD | 0 | 0 | 0 | 1 | 1 | 2 | 50.0% |
| CM | 0 | 0 | 0 | 0 | 0 | 2 | 100.0% |

### 7.2 Project × Pass Rate

| Project | Rollouts | Pass Rate | Mean Steps | Mean Tokens |
|---------|--------:|---------:|-----------:|------------:|
| axi4_lite | 3 | 33.3% | 19 | 433933 |
| enso | 9 | 55.6% | 17 | 327771 |
| reckon | 3 | 0.0% | 14 | 283511 |
| ultraembedded_biriscv | 3 | 66.7% | 19 | 204340 |

## 8. Per-Task Breakdown

| Task ID | Type | pass@1 | Best Phase | Steps (mean) | Files Written | Patterns |
|---------|------|-------:|------------|-------------:|---------------|----------|
| axi4_lite_0002 | CD | 33% | P5 | 19 | axi_ram_rd_if.v | B3, B5, B7 |
| enso_0007 | CM | 100% | P5 | 14 | parser.sv | — |
| enso_0017 | CD | 0% | P4 | 18 | constants.sv, parser.sv | B7 |
| enso_0037 | CM | 67% | P5 | 20 | constants.sv, timestamp.sv | B5, B7 |
| reckon_0001 | CD | 0% | P3 | 14 | spi_slave.v | B7 |
| biriscv_0001 | CD | 67% | P5 | 19 | biriscv_divider.v, tb_divider.v | B3, B5, B7 |

## 9. Sometimes-Pass Analysis

### axi4_lite_0002 (1/3 pass)
| | Passing | Failing |
|---|---|---|
| Phase | P5 | P4, P3 |
| Mean steps | 20 | 18 |
| Patterns | B5, B7 | B3, B5, B7 |
Failing r0 stderr: 10 failed, 3 warnings in 13.30s
Failing r1 stderr: docker compose run timed out after 600s

### enso_0037 (2/3 pass)
| | Passing | Failing |
|---|---|---|
| Phase | P5 | P3 |
| Mean steps | 20 | 20 |
| Patterns | B5, B7 | B5, B7 |
Failing r0 stderr: Preprocessor failed with 1 errors.

### biriscv_0001 (2/3 pass)
| | Passing | Failing |
|---|---|---|
| Phase | P5 | P4 |
| Mean steps | 18 | 20 |
| Patterns | B3, B5, B7 | B5 |
Failing r0 stderr: Failed 1 of... 1 failed in 23.21s

## 10. Fix Quality & Iteration Effectiveness
- Mean file rewrites per rollout: 1.3
- Rollouts with improving vvp FAIL count: 2/18
- Rollouts with zero-byte writes: 0/18

## 11. Key Takeaways
- 8/18 rollouts compiled but never ran vvp (B7). Behavioral issue — highest-leverage RL target.
- 7 rollouts hit max_steps.
- Task-level: 1 always-pass, 3 sometimes-pass, 2 never-pass out of 6 tasks
- Overall: pass@1=44.4%, file mod rate=88.9%, compile rate=94.4%, vvp rate=50.0%
```

---

## REPORT B (Human-Enhanced Diagnostic Analysis)

Report B contains everything in Report A (sections 1-11 above are identical), PLUS the following additional sections:

```
## 12. Root Cause Classification

### Cross-Cutting Summary Table

| Bucket | Tasks | Avg pass rate | Improvement method |
|--------|------:|--------------:|-------------------|
| SP unreliable knowledge | 3 (axi4_lite_0002, enso_0037, biriscv_0001) | 56% | RL + light SFT |
| NP knowledge gap | 1 (enso_0017) | 0% | SFT domain data |
| NP behavioral + environment | 1 (reckon_0001) | 0% | Mixed: EI + BI |
| Always-pass | 1 (enso_0007) | 100% | No action needed |

### Per-Task Root Cause

| Task | Pass Rate | Root Cause | Evidence |
|------|-----------|------------|----------|
| enso_0007 | 3/3 | Always-pass | Solved consistently in 13-15 steps |
| enso_0037 | 2/3 | UK: Unreliable knowledge | R0 failed on include path; R1/R2 fixed it |
| biriscv_0001 | 2/3 | UK: Unreliable knowledge | R0 vvp timeout (infinite loop); R1/R2 correct termination |
| axi4_lite_0002 | 1/3 | UK: Unreliable knowledge | R0 wrong testbench ($from_myhdl); R1 docker timeout; R2 passed |
| enso_0017 | 0/3 | KG: Knowledge gap | Sandbox vvp PASSED but cocotb harness failed — model doesn't understand the two test differently |
| reckon_0001 | 0/3 | BI+EI | iverilog doesn't support ref ports; R1/R2 never attempted a fix |

## 13. Per-Task Deep Dive — Never-Pass Tasks (2)

### enso_0017 (0/3 pass) — Knowledge Gap
- Model edited constants.sv and parser.sv. Sandbox vvp showed PASS on all 3 rollouts.
  But Docker harness (cocotb/pytest) failed — it tests comprehensive protocol compliance
  the iverilog testbench doesn't cover. The model's fix passes the simple test but fails
  the comprehensive one.
- Improvement: SFT on cocotb harness behavior.

### reckon_0001 (0/3 pass) — Behavioral + Environment
- R0: Wrote spi_slave.v, iverilog hit "ref ports not supported" and "tbench.h not found".
  The ref port error is from the existing testbench, not the model's code.
- R1/R2: Only explored (ls/cat), never wrote a fix. Gave up early.
- Improvement: EI (task may need Xcelium) + BI (RL to discourage giving up).

## 14. Per-Task Deep Dive — Sometimes-Pass Tasks (3)

### enso_0037 (2/3 pass) — Unreliable Knowledge
- Passing R1/R2: Correct compilation command resolving includes. Docker: all 10 tests passed.
- Failing R0: Include file ./constants.sv not found — wrong compilation approach.
- Variance is in tool-use (compilation strategy), not code quality.

### biriscv_0001 (2/3 pass) — Unreliable Knowledge
- Passing R1/R2: Correct divider FSM with proper done-signal. Created custom testbenches.
- Failing R0: vvp timed out at 120s twice — divider entered infinite loop.
- Variance is in RTL logic quality (termination condition).

### axi4_lite_0002 (1/3 pass) — Unreliable Knowledge
- Passing R2: Correct fix, compiled on second attempt.
- Failing R0: Used $from_myhdl testbench (unsupported in standalone iverilog).
- Failing R1: Docker compose timed out at 600s.

## 15. Diagnostic Summary

GPT-5 at 44.4% pass@1 has two systemic weaknesses:

1. Compile-no-run (B7) at 44.4%: The model compiles but never runs vvp, so it can't
   verify its fixes. This is the highest-leverage RL target.

2. Unreliable knowledge on 3/6 tasks: Include path issues, infinite loops, wrong
   testbench references. The model can solve these tasks but does so inconsistently.

Causal chain: B7 → model can't verify → submits untested fix → harness catches error.
If B7 were eliminated, many P3 failures would become P4 or P5.

Comparison: Claude Opus achieves 72.2% with only 16.7% B7 vs GPT-5's 44.4%.
The 28pp pass@1 gap correlates directly with the 28pp B7 gap.
```

---

## Required Output Format

Please produce your evaluation in EXACTLY this format:

```
## Judge: [Your model name]

### Report A (Script-Generated) Scores

| Criterion | Score (1-5) | Justification |
|-----------|:-----------:|---------------|
| C1: Pipeline funnel | ? | [1 sentence] |
| C2: Dominant failure mode | ? | [1 sentence] |
| C3: Root cause distinction | ? | [1 sentence] |
| C4: Sometimes-pass analysis | ? | [1 sentence] |
| C5: Causal narrative | ? | [1 sentence] |
| C6: Evidence citation | ? | [1 sentence] |
| C7: Actionability | ? | [1 sentence] |
| C8: Behavioral patterns | ? | [1 sentence] |
| C9: Cross-cutting analysis | ? | [1 sentence] |
| C10: Report completeness | ? | [1 sentence] |

**Report A weighted score:** [calculate: sum of (score × weight) for each criterion] / 70.0

### Report B (Human-Enhanced) Scores

| Criterion | Score (1-5) | Justification |
|-----------|:-----------:|---------------|
| C1: Pipeline funnel | ? | [1 sentence] |
| C2: Dominant failure mode | ? | [1 sentence] |
| C3: Root cause distinction | ? | [1 sentence] |
| C4: Sometimes-pass analysis | ? | [1 sentence] |
| C5: Causal narrative | ? | [1 sentence] |
| C6: Evidence citation | ? | [1 sentence] |
| C7: Actionability | ? | [1 sentence] |
| C8: Behavioral patterns | ? | [1 sentence] |
| C9: Cross-cutting analysis | ? | [1 sentence] |
| C10: Report completeness | ? | [1 sentence] |

**Report B weighted score:** [calculate: sum of (score × weight) for each criterion] / 70.0

### Comparison

| Metric | Report A | Report B |
|--------|--------:|--------:|
| Weighted score | ?/70 | ?/70 |
| Percentage | ?% | ?% |
| Spread | [B minus A] points |

### Which report is better and why? (2-3 sentences)
[Your assessment]
```

---
name: cvdp-agentic-heavy-failure-analysis
description: >
  Deep failure analysis for CVDP agentic heavy benchmark rollouts.
  Analyzes multi-turn tool-use trajectories from NeMo-Gym, classifies failures
  by workflow phase, tool errors, behavioral patterns, and root cause
  (knowledge gap, unreliable knowledge, behavioral issue, environment issue).
  Produces per-task diagnostic reports with causal narratives, sometimes-pass
  comparisons, cross-model behavioral signatures, and improvement-method mapping
  (SFT vs RL vs infrastructure). Supports single-model analysis and multi-model
  comparison.
triggers:
  - cvdp agentic analysis
  - cvdp heavy analysis
  - agentic heavy failure analysis
  - chip design benchmark analysis
  - cvdp tool usage analysis
  - analyze cvdp rollouts
  - compare cvdp models
---

# CVDP Agentic Heavy Failure Analysis Skill

## Overview

This skill produces a **diagnostic failure analysis** for CVDP agentic heavy benchmark rollouts. It goes beyond surface-level characterization (phase reached, tools used) to answer *why* the model fails, *what knowledge or behavior is missing*, and *what improvement method would address each failure*.

The CVDP agentic heavy benchmark tests whether LLM agents can solve complex, multi-file hardware design tasks — bug fixing, spec-to-RTL, code modification, and testbench generation — by navigating a sandbox with filesystem and simulator tools (`ls`, `cat`, `echo`, `iverilog`, `vvp`, `xcelium`, `pwd`).

**Use when:**
- You have NeMo-Gym rollout JSONL from the CVDP agentic heavy benchmark
- You want to understand not just *what* failed but *why* and *what would fix it*
- You need to distinguish tool-usage failures from capability failures from knowledge gaps
- You want to compare multiple models' behavioral signatures on the same tasks
- You want to identify which phase of the workflow is the bottleneck and why

**Do NOT use when:**
- For non-agentic CVDP data (single-turn copilot tier), use the matching single-turn analysis skill with `--taxonomy cvdp`
- You only need aggregate pass rates — just count `reward == 1.0`
- Your rollout data is from a different benchmark format (SWE-bench, Terminal Bench)

---

## Prerequisites

- Python 3.8+
- Rollout JSONL files from `ng_collect_rollouts` (one JSON object per line, one per rollout)
- Optionally: `matplotlib` for plot generation (`pip install matplotlib`)

---

## Input Data Schema

Each line in the rollout JSONL is one rollout. Key fields:

```json
{
  "reward": 0.0,
  "task_id": "cvdp_agentic_heavy_1x3_router_0001",
  "category": "cid016",
  "difficulty": "hard",
  "docker_exit_code": 1,
  "docker_stderr": "FAILED ...",
  "execution_time": 4.65,
  "_ng_task_index": 0,
  "_ng_rollout_index": 0,
  "response": {
    "output": [
      {"type": "reasoning", "summary": [{"text": "..."}]},
      {"type": "message", "content": [{"text": "..."}]},
      {"type": "function_call", "name": "ls", "arguments": "{\"path\": \".\"}", "call_id": "call_1"},
      {"type": "function_call_output", "call_id": "call_1", "output": "{\"output\": \"src/\\nrtl/\\n...\"}"}
    ],
    "usage": {"input_tokens": 5000, "output_tokens": 3000, "total_tokens": 8000}
  },
  "responses_create_params": {
    "input": [
      {"role": "developer", "content": "<system_message>"},
      {"role": "user", "content": "<prompt>"}
    ]
  },
  "verifier_metadata": {
    "task_id": "...",
    "context_files": {"path/to/file.v": "...contents..."},
    "harness_files": {"src/test_runner.py": "..."},
    "patch": {"path/to/file.v": "@@ diff @@"}
  }
}
```

### Key Fields for Failure Classification

| Field | Type | Use |
|-------|------|-----|
| `reward` | float | 1.0 = pass, 0.0 = fail |
| `response.output` | list | The agent trajectory — interleaved function_call and function_call_output items |
| `docker_exit_code` | int | 0 = harness passed, 1 = harness failed |
| `docker_stderr` | string | Harness output — compilation errors, test results, assertion messages |
| `execution_time` | float | Docker verification time in seconds |
| `verifier_metadata.patch` | dict | The golden patch (correct fix) — for comparing against the model's changes |
| `verifier_metadata.context_files` | dict | All source files in the sandbox |
| `_ng_task_index` | int | Groups rollouts by task |
| `_ng_rollout_index` | int | Distinguishes repeats of the same task |

### Derived Dimensions (Computed During Analysis)

| Dimension | Derivation |
|-----------|------------|
| **Task type** | Inferred from prompt keywords: "fix"/"debug" → Bug Fix (CD), "modify"/"add feature" → Code Modify (CM), "testbench"/"write a test" → Testbench Gen (S2R), "complete"/"TODO" → Code Completion (CC) |
| **Project name** | Extracted from task_id: `cvdp_agentic_heavy_{project}_{number}` |
| **Context size** | `sum(len(v) for v in context_files.values())` — proxy for task complexity |
| **Simulator type** | Inferred from harness files: presence of `iverilog`/`vvp` commands vs `xrun`/`xcelium` |

---

## Failure Taxonomy

The taxonomy has four layers, applied in order: (1) workflow phase reached, (2) tool errors encountered, (3) behavioral patterns exhibited, and (4) root cause classification.

### Layer 1: Phase-Based Classification

Each rollout is classified by how far the model progressed through the expected workflow:

| Phase | Code | Description | Detection |
|-------|------|-------------|-----------|
| No tool usage | P0 | Model produced text-only answer, zero tool calls | `len(fn_calls) == 0` |
| Explore only | P1 | Used ls/cat/pwd but never wrote files | Has ls/cat/pwd calls but no echo calls |
| Wrote files | P2 | Used echo to modify files but never compiled | Has echo calls but no iverilog calls |
| Compiled | P3 | Used iverilog but compilation failed or never ran vvp | Has iverilog calls but no vvp calls |
| Tested | P4 | Ran vvp/simulation but final verification failed | Has vvp calls, Docker still failed |
| Passed | P5 | All phases complete, verification passed | `reward == 1.0` |

**Pipeline funnel**: Report cumulative survival — what fraction of rollouts reached each stage. The biggest drop-off identifies the systemic bottleneck.

### Layer 2: Tool Error Classification

| Error | Code | Description | Detection |
|-------|------|-------------|-----------|
| Path not found | E1 | File/directory not found errors | `"file not found"` or `"no such directory"` in tool output |
| Path escape | E2 | Sandbox escape attempt | `"escapes sandbox"` in tool output |
| Compilation error | E3 | iverilog returned non-zero | iverilog output contains `"error"` or non-zero exit |
| Simulation error | E4 | vvp crashed or timed out | vvp output contains `"Error"` or timeout |
| HTTP error | E5 | Tool endpoint returned 4xx/5xx | `"HTTP"` in tool output |
| Wrong extension | E6 | Model used .sv when file is .v or vice versa | echo target extension doesn't match any file in context_files |

### Layer 3: Behavioral Patterns

| Pattern | Code | Description | Detection |
|---------|------|-------------|-----------|
| Path thrashing | B1 | Model tries 3+ path variations of the same filename | 3+ unique full paths sharing one basename |
| Repeated reads | B2 | Model reads the same file 3+ times without writing | Same cat target 3+ times with no echo between |
| Write without read | B3 | Model writes to a file it never read | echo target never appears in a prior cat call |
| No verification | B4 | Model wrote files but never compiled/tested | Has echo calls but no iverilog calls |
| Step exhaustion | B5 | Model used all max_steps without completing | `num_steps >= max_steps` |
| Early exit | B6 | Model gave text answer before using half the step budget | `num_steps < max_steps // 2` and no echo calls |
| Compile no run | B7 | Model compiled (iverilog) but never ran simulation (vvp) | Has iverilog calls but no vvp calls |

### Layer 4: Root Cause Classification

After classifying phase, errors, and patterns, classify each **failed task** (not each rollout — aggregate across all rollouts for the task) into exactly one root cause category:

| Category | Code | Description | Typical Evidence | Improvement Method |
|----------|------|-------------|-----------------|-------------------|
| Knowledge Gap | KG | Model lacks specific RTL/tool knowledge it cannot work around | NP (never-pass) task. Model makes the same wrong approach across all rollouts. Error stems from domain-specific misunderstanding (e.g., iverilog SV subset, struct syntax, FSM coding style). | SFT with domain data |
| Unreliable Knowledge | UK | Model has the knowledge but applies it inconsistently | SP (sometimes-pass) task where passing rollouts show genuine understanding. Failing rollouts make subtle errors (wrong signal width, off-by-one cycle, wrong reset polarity). | RL + light SFT |
| Behavioral Issue | BI | Model has sufficient knowledge but makes poor agentic decisions | Failures caused by workflow problems (path thrashing, early exit, compile-no-run, perseveration) rather than wrong RTL logic. Passing rollouts (if any) did the same fix but with better tool-use discipline. | RL training |
| Environment/Task Issue | EI | External constraints prevent success regardless of model capability | Harness timeout, missing simulator, broken test infrastructure, task requires Xcelium but only iverilog available. | Not fixable by model |

---

## Analysis Workflow

The analysis proceeds in 5 phases. Each phase builds on the previous one.

### Phase 1: Aggregate Metrics

Compute standard multi-level metrics:

| Metric | Definition |
|--------|-----------|
| **pass@1** | Average per-task pass rate, averaged across tasks |
| **pass@k** | Fraction of tasks with >= 1 successful rollout |
| **Consistency** | Fraction of tasks with 100% pass rate |
| **File modification rate** | Fraction of rollouts that used echo at least once |
| **Compile attempt rate** | Fraction of rollouts that called iverilog |
| **Self-test rate** | Fraction of rollouts that called vvp |
| **TB discovery rate** | Fraction of rollouts that read a testbench file (tb_*.v, test_*.py) |
| **Mean feedback loops** | Average iverilog→vvp cycles per rollout |

**Slice by:**
- **Task type** (CD / CM / CC / S2R)
- **Project** (enso, axi4_lite, reckon, etc.)
- **Context size** (small < 50KB, medium 50-500KB, large > 500KB)

Report the **pipeline funnel**: what % of rollouts survive to each phase (P0→P1→P2→P3→P4→P5). The biggest drop-off is the systemic bottleneck.

### Phase 2: Failure Classification

For every failed rollout (`reward == 0.0`):

**Step 1**: Classify phase (P0-P4) using the detection logic table.

**Step 2**: Identify all tool errors (E1-E6) and behavioral patterns (B1-B7).

**Step 3**: For each **task** (not rollout), classify root cause (KG / UK / BI / EI) by reading trajectories across all rollouts. This step requires human/LLM judgment — the script computes phases and patterns; root cause classification requires reading what the model actually did.

**Step 4**: Validate totals. Phase counts must sum to total rollouts. Every failed task must have exactly one root cause classification.

#### Adapting the Taxonomy

After first-pass classification:
1. If `E_other` exceeds 30% of errors, inspect 10-20 examples and split into specific categories.
2. If a behavioral pattern appears in >80% of rollouts, it's pervasive and should be noted as systemic, not per-task.
3. If a task has mixed rollout phases (e.g., P1 on one rollout, P4 on another), classify by the **best** rollout's root cause — the model has demonstrated it can reach that phase, so lower-phase failures are behavioral inconsistency.

### Phase 3: Per-Task Deep Dive & Concrete Examples

For every task that is **never-pass** (NP: 0/k) or **sometimes-pass** (SP: 1 to k-1 out of k), perform a deep analysis.

#### 3a. Read the Trajectory

For each failed rollout, reconstruct what the model did:
- What files did it read (cat calls)?
- What files did it write (echo calls) and what did it change?
- Did it compile? What were the errors?
- Did it run vvp? What were the results?
- Did test results improve across iterations?
- What did the model say in its reasoning blocks?

For sometimes-pass tasks, **also read the passing trajectory** to understand what distinguished success from failure.

#### 3b. Compare Against Golden Patch

If `verifier_metadata.patch` is available:
- **File overlap**: Did the model edit the same files as the golden patch?
- **Direction**: Was the model's change in the right area (same module, same signals) but with wrong logic?
- **Magnitude**: Was the fix too large (rewrote entire file when only 3 lines needed changing) or too targeted (changed one line but missed related changes)?

#### 3c. Write the Per-Task Entry

For each task:

```markdown
### {task_id}
- **Pass rate**: X/k
- **Root cause**: {KG | UK | BI | EI} — {specific description}
- **Behavior codes**: {B1/B2/.../B7, if behavioral issue — list all that apply}
- **Phase reached**: {best phase across rollouts}
- **Golden patch**: {brief description of the correct fix, if known}
- **What model did wrong**:
  1. {specific error with evidence from trajectory}
  2. {second specific error}
- **Why this happened**: {causal explanation linking behavior to root cause}
```

For sometimes-pass tasks, add:

```markdown
- **Passing vs failing**: {what passing rollouts did differently}
- **Root cause of variance**: {why some attempts succeed and others don't}
```

#### 3d. Concrete Example Selection

For each failure category (KG, UK, BI, EI) with >1 task, select 2-3 examples:
- **Best contrast**: A task where one model passes and another fails — show both trajectories
- **Clearest root cause**: A task where the failure mechanism is unambiguous
- **Sometimes-pass**: A task where pass/fail differ by one specific decision

Each example must include: task ID, model, phase reached, the critical tool calls, what the model should have done, and what it actually did.

### Phase 4: Cross-Cutting Analysis

#### 4.1: Task Type × Failure Mode

Build a matrix: rows = task types (CD, CM, CC, S2R), columns = root cause (KG, UK, BI, EI). Look for:
- Do bug fix tasks (CD) have different failure profiles than testbench generation (S2R)?
- Is knowledge gap concentrated in specific task types?

#### 4.2: Pipeline Funnel Comparison

If comparing multiple models, show side-by-side funnels:
```
             Model A    Model B    Model C
Started:     100%       100%       100%
Wrote files: 94%        89%        50%
Compiled:    89%        83%        39%
Ran vvp:     72%        50%        0%
Passed:      72%        44%        0%
```

The funnel immediately shows where each model's pipeline leaks.

#### 4.3: Context Size vs Success

Bin tasks by context size (total bytes of all source files):
- Small (<50KB): typically single-module designs
- Medium (50-500KB): multi-module designs
- Large (>500KB): full SoC subsystems

Report pass@1 per bin. If pass rate drops sharply above a threshold, the model hits a context window or comprehension limit.

#### 4.4: Sometimes-Pass Analysis (the Sharpest Diagnostic)

For tasks where some rollouts pass and others fail for the same model:
- Compare passing vs failing trajectories step by step
- Identify the **decision point** where they diverge
- Classify the divergence: different file read order? Different fix strategy? Lucky vs unlucky compilation?
- Measure **answer diversity** across rollouts: high diversity (>50% unique file diffs) = genuine capability gap; low diversity (<20% unique) = systematic bias

#### 4.5: Iteration Effectiveness

For rollouts that ran vvp multiple times:
- Did the vvp FAIL count decrease across iterations? (Track the progression: [16, 8, 0] = improving; [3, 6, 3] = not improving)
- What fraction of rollouts show improvement? This measures whether the model can learn from simulation feedback within a single episode.
- **Reasoning-action gap**: Did the model identify the correct root cause in its reasoning but fail to implement the fix? (Read reasoning blocks alongside tool calls.)

#### 4.6: Cross-Model Behavioral Signatures

When comparing multiple models, identify each model's **distinctive behavioral pattern**:
- Which model has the highest path thrashing rate? (poor codebase navigation)
- Which model has the highest compile-no-run rate? (doesn't understand iverilog→vvp loop)
- Which model has the highest early exit rate? (gives up too quickly)
- Which model iterates most effectively? (vvp FAIL count decreasing)
- Which model perseverates? (high iteration count but zero improvement)

#### 4.7: Hardest and Easiest Tasks

Rank tasks by pass rate across all models:
- **Bottom 3**: What makes them hard? (large context? complex multi-file interaction? requires Xcelium? obscure RTL pattern?)
- **Top 3**: What makes them easy? (small context? simple single-file bug? clear error message?)
- Do the easy tasks share a task type or project?

### Phase 5: Document Assembly

Assemble the analysis into a structured markdown document:

```markdown
# CVDP Agentic Heavy — Failure Analysis Report

**Model / Date / Dataset / max_steps / num_repeats**

## Executive Summary
- Aggregate metrics table (pass@1, pass@k, consistency)
- Pipeline funnel (one-line: X% started → Y% wrote → Z% compiled → W% tested → V% passed)
- Root cause distribution (KG: N tasks, UK: N, BI: N, EI: N)
- 3-5 key findings (the most important diagnostic insights)

## 1. Aggregate Metrics
- Overall metrics
- Per-task-type breakdown
- Per-project breakdown
- Pipeline funnel chart
- Pass count distribution (0/k, 1/k, ..., k/k histogram)

## 2. Failure Breakdown
- Phase distribution table (P0-P5 with counts and %)
- Tool error table (E1-E6 with counts)
- Behavioral pattern table (B1-B7 with counts and %)

## 3. Root Cause Analysis
- Cross-cutting summary table:

| Bucket | Tasks | Avg pass rate | Top behavior codes | Improvement method |
|--------|------:|--------------:|-------------------|-------------------|
| SP behavioral | ? | ? | B1:?, B3:?, B7:? | RL |
| SP unreliable knowledge | ? | ? | — | RL + light SFT |
| NP behavioral | ? | ? | B5:?, B6:?, B7:? | RL |
| NP knowledge gap | ? | ? | — | SFT domain data |
| NP environment/task | ? | ? | — | Not fixable by model |

- Per-category analysis with concrete examples

## 4. Per-Task Deep Dive — Never-Pass Tasks (N)
- One entry per NP task (see template in Phase 3)

## 5. Per-Task Deep Dive — Sometimes-Pass Tasks (N)
- One entry per SP task with pass/fail comparison

## 6. Cross-Cutting Analysis
- 6.1 Task type × root cause matrix
- 6.2 Context size vs success
- 6.3 Iteration effectiveness
- 6.4 Hardest and easiest tasks

## 7. Cross-Model Comparison (if multiple models)
- Side-by-side pipeline funnels
- Behavioral signature per model
- Per-task pass rate matrix (models × tasks)
- Which model wins on which task type?

## 8. Key Takeaways
- Ordered by impact (highest-leverage intervention first)
- Each finding: what the problem is, the evidence, what improvement method applies
- Distinguish knowledge gaps (SFT) from behavioral issues (RL) from environment issues (infra)
```

---

## Classification Guidelines

These guidelines encode important nuances learned from analyzing CVDP agentic heavy rollouts across 6 models.

**1. Root cause is per-task, not per-rollout.** A task with 3 rollouts at P1, P3, and P5 is "sometimes-pass" — classify by what the passing rollout demonstrates, not what the worst rollout shows.

**2. Phase reached is not the root cause.** P3 (compiled but never ran vvp) could be: knowledge gap (doesn't know iverilog ≠ vvp), behavioral (ran out of steps before reaching vvp), or environment (iverilog version doesn't support required syntax). Read the trajectory to distinguish.

**3. NP ≠ knowledge gap automatically.** Many never-pass tasks fail due to behavioral issues (path thrashing, early exit) rather than knowledge gaps. If the model's reasoning shows it understands the problem but wastes steps on wrong paths, that's behavioral. Read the trajectory before classifying.

**4. SP ≠ unreliable knowledge automatically.** A 1/3 pass could be luck — the model brute-forced a fix that happened to work. Read the passing trajectory: does it show genuine understanding (correct reasoning, deliberate approach) or did the model stumble into the right answer? If luck, classify as KG despite having a pass.

**5. Distinguish "doesn't know" from "knew but didn't use."** If the model mentions the correct approach in its reasoning but doesn't implement it, that's behavioral (reasoning-action gap), not a knowledge gap. If the model never mentions the correct approach at all, that's a knowledge gap.

**6. iverilog limitations are knowledge gaps, not environment issues.** iverilog doesn't support full SystemVerilog (packed structs, typedef enum with explicit casts, interface ports). If a model generates valid SystemVerilog that iverilog rejects, that's a knowledge gap about iverilog's language subset — not an environment issue. The task is designed for iverilog.

**7. Perseveration (B5 + zero improvement) is behavioral, even when it looks like a knowledge gap.** If the model rewrites the same file 10 times with the same struct-based approach and iverilog rejects it every time, the root cause is behavioral perseveration (won't pivot to a different strategy), not just a knowledge gap. The knowledge gap is upstream, but the behavioral failure to adapt compounds it.

**8. Compile-no-run (B7) is the highest-leverage behavioral fix.** A model that compiles but never runs vvp has zero chance of passing — it can't verify its work. This is purely behavioral (the model doesn't understand the iverilog→vvp loop) and is directly addressable via RL. Across our experiments, B7 rates ranged from 6% (Sonnet) to 67% (Super v3).

**9. Check the harness timeout before blaming the model.** If `docker_stderr` contains "timed out after 600s", the model's fix may have caused an infinite simulation loop — or the harness timeout may be too short for a correct but slow fix. Check whether the same task passes for other models within the timeout. If yes, it's the model's fix quality. If no model finishes, it may be an environment issue.

**10. Respect chronological order of tool calls.** When diagnosing a failure, always check whether errors occurred *before* or *after* the model's echo writes. An iverilog error at step 12 that is followed by echo writes at steps 14-15 means the error is from the *original* code, not the model's fix. The model's fix may be correct but it never re-compiled after writing. Misattributing a pre-write error to the model's code is a common analysis mistake — it turns a behavioral issue (B7: never re-compiled) into a false knowledge gap.

**11. Count compilation attempts, not just final result.** "Compiled successfully" vs "compiled on the 3rd attempt after 2 failures" is meaningful. Multiple failed compilations followed by success shows the model can self-correct (positive signal). Multiple failures with no success shows a persistent knowledge gap. A single failure followed by giving up shows a behavioral issue (low persistence). Always report the full iverilog attempt sequence.

**12. Docker stderr PASS does not mean reward=1.0.** The CVDP harness has two grading paths: (a) the iverilog/vvp testbench run by the model during the rollout, and (b) the cocotb/pytest harness run by Docker during verification. These test *different things*. The iverilog testbench (written by the project or the model) may check basic functionality, while the cocotb harness tests comprehensive corner cases, timing, and protocol compliance. If Docker stderr shows `PASS!` from the iverilog testbench but `reward=0.0`, the cocotb pytest harness failed on conditions the iverilog testbench doesn't cover. Do not classify this as "sandbox passes but harness fails" without checking which test produced the PASS output — it may be the iverilog testbench output captured in stderr, not the cocotb verdict.

---

## CVDP-Specific Analysis Notes

### Common RTL Failure Patterns

These patterns were discovered from analyzing rollouts across 6 models on T1_easy tasks. They represent the most frequent root causes and should be checked first when diagnosing failures.

1. **typedef enum + iverilog**: iverilog rejects SystemVerilog `typedef enum` with explicit cast errors. Models that generate `typedef enum logic [1:0] {IDLE, RUN, DONE} state_t;` will always fail compilation. The fix is `localparam`. This is the single most common knowledge gap.

2. **Struct member selection**: iverilog doesn't support packed struct member selection (`data.field`). Models that use SystemVerilog structs will get "Member X is not a member of struct type" errors. This affects enso_* tasks heavily.

3. **Compile but never run**: Models that call iverilog but not vvp have zero chance of knowing whether their fix works. This behavioral pattern (B7) is the single highest-leverage RL target.

4. **Path thrashing on multi-directory projects**: Projects with nested structures (`hardware/src/`, `hardware/tests/`, `src/`, `rtl/`, `tb/`) cause models to try multiple path guesses before finding files. Models that use `ls` systematically before `cat` avoid this.

5. **Write without read on confident models**: Strong models (Opus, Sonnet) sometimes write to files they never read — inferring the fix from other files or the prompt alone. This works when the inference is correct but causes failures when assumptions about the file's structure are wrong.

6. **Docker compose timeout**: The `axi4_lite_0002` task's harness runs 10 test cases and can timeout at 600s if the model's fix causes slow simulation. Models that pass self-test (vvp) but fail Docker verification often have a correct-but-slow fix or a fix that passes trivial self-tests but fails comprehensive harness tests.

7. **Zero-byte writes**: `echo` with empty content overwrites the target file with nothing. This destroys the original file and guarantees harness failure. Detected by checking echo calls where `content` is empty or whitespace-only.

### Task Type Characteristics

| Type | Code | Typical Difficulty | Key Challenge |
|------|------|-------------------|---------------|
| Bug Fix | CD | Easiest — small targeted change | Finding the right signal/condition to change without breaking other functionality |
| Code Modify | CM | Medium — must preserve interface | Understanding the existing module's interface contract and testbench expectations |
| Code Completion | CC | Medium — fill in blanks | Matching the expected behavior from surrounding code context |
| Testbench Gen / Spec-to-RTL | S2R | Hardest — generate from description | Reading the full spec, understanding all required outputs, writing complete code |

### Formatting-Only Failures (High ROI)

Quantify rollouts where the model's RTL fix is logically correct but fails due to formatting/syntax:
- `.sv` extension when file is `.v` (E6)
- `typedef enum` when `localparam` is needed (iverilog limitation)
- `input logic [7:0]` port syntax rejected by iverilog (use `input [7:0]`)

These represent **correct capability with wrong surface form** — the highest-ROI fix because the model already understands the problem. Addressable via the agent-facing SKILL.md or light SFT.

---

## Lessons from Real Analyses

These patterns were discovered from 5+ rounds of experiments across 6 models (Claude Opus/Sonnet, GPT-5, Nemotron Super/Super v3/Ultra) on T1_easy CVDP tasks.

### 1. The bottleneck shifts by model tier

Weak models (Nemotron Super 49b) stall at P1 — they can't navigate the codebase and give up early. Mid-tier models (GPT-5, Super v3) stall at P3 — they write and compile but never run vvp. Frontier models (Opus, Sonnet) reach P4-P5 but fail on genuinely hard RTL logic. The diagnostic approach must adapt: for P0-P1 bottlenecks, focus on behavioral analysis; for P3-P4, focus on knowledge gaps.

### 2. Sometimes-pass comparison is the sharpest diagnostic

Comparing passing vs failing rollouts for the same task, same model reveals exactly what distinguishes success from failure. On `enso_0017`, Opus r0 passed by writing both `parser.sv` and `constants.sv` with localparam-based constants. Opus r1 failed with a typedef syntax error in `constants.sv:201` — the exact pitfall the agent-facing SKILL.md warns about. This immediately identified unreliable knowledge (sometimes applies the correct pattern, sometimes doesn't).

### 3. Perseveration is distinct from knowledge gap

Nemotron Ultra 253b ran 118 steps on `enso_0037` with 7.8 feedback loops but never improved. It kept rewriting the same struct-based approach that iverilog kept rejecting. The knowledge gap (doesn't know iverilog struct limitations) is upstream, but the behavioral failure (won't pivot after repeated failures) is the proximate cause and is independently addressable via RL.

### 4. Compile-no-run (B7) predicts zero reward with 100% accuracy

No rollout in our experiments that compiled but never ran vvp achieved reward=1.0. B7 rates varied enormously: 6% (Sonnet) to 67% (Super v3). Eliminating B7 via RL is the single highest-leverage behavioral intervention.

### 5. Context size has a sharp threshold, not a gradual slope

Tasks with context <50KB have dramatically higher pass rates than tasks >500KB. The drop-off is sharp, not gradual — suggesting the model hits a comprehension limit rather than a gradual degradation. Large-context tasks also exhibit more path thrashing (B1).

### 6. Strong models fail differently than weak models

Weak model failures are mostly behavioral (can't navigate, gives up early, doesn't use the right tools). Strong model failures are mostly capability-based (understands the workflow but generates the wrong RTL fix). This means the **same benchmark produces different training signals** depending on the model tier — RL for weak models, SFT for strong ones.

### 7. Task difficulty varies more by project than by task type

`enso_*` tasks (Ethernet NIC) are consistently easier than `reckon_*` (neuromorphic processor) or `axi4_lite_*` (AXI bus), regardless of whether the task type is CD, CM, or S2R. Project-specific complexity (codebase size, design style, SystemVerilog usage) matters more than task category.

### 8. Docker timeout failures need manual inspection

When `docker_stderr` shows "timed out after 600s", it could mean: (a) the model's fix causes an infinite simulation loop (model's fault), (b) the fix is correct but slow (harness timeout too short), or (c) the harness itself is broken (environment issue). Always check whether other models pass the same task within timeout before classifying.

---

## Writing Quality Guidelines

### Executive Summary
- Lead with the pipeline funnel — it's the single most informative visualization
- Use specific numbers: "67% of failures are P3 (compile-no-run)" not "most failures are compilation-related"
- Include the root cause distribution (KG/UK/BI/EI) with improvement methods
- The reader should know the key findings without reading the rest of the report

### Root Cause Analysis
- Name root causes by **mechanism**, not symptom: "iverilog rejects packed struct member selection" not "compilation error"
- Every classification must cite evidence from the trajectory: which tool calls, which error messages, which reasoning blocks
- For sometimes-pass tasks, the pass/fail comparison IS the evidence — always include it

### Per-Task Deep Dives
- Each entry must be self-contained — a reader shouldn't need to look at raw data
- Show the critical decision point: the specific tool call or reasoning block where the model went wrong
- For behavioral issues, specify which behavior code(s) and what the model should have done instead
- For knowledge gaps, specify what knowledge is missing and where the model's understanding breaks down

### Key Takeaways
- Order by impact (highest-leverage intervention first)
- Each recommendation maps to an improvement method: RL for behavioral, SFT for knowledge, infra for environment
- Distinguish "the model can't do X" (knowledge gap) from "the model doesn't do X consistently" (unreliable knowledge) from "the model knows X but makes poor decisions around it" (behavioral)

### What Makes a Good Analysis
- **Diagnostic, not descriptive**: "P3 at 67%" is description. "67% of rollouts compile but never run vvp because the model doesn't understand that iverilog only compiles — it doesn't execute. Sonnet avoids this (6% B7) by always calling vvp after iverilog, while Super v3 never does (67% B7)." is diagnosis.
- **Causal, not correlational**: Connect failure modes into chains: "path thrashing (B1) → file not found (E1) → never reads target file → writes to wrong path → harness grades original buggy file → reward 0.0"
- **Contrastive**: The best evidence comes from comparing passing vs failing rollouts for the same task, or comparing strong vs weak models on the same task. Always include contrasts when available.
- **Quantified**: Every claim backed by a number. Every number cites its source (which rollouts, which tasks).
- **Actionable**: Every finding maps to an improvement method. If you can't say whether it's RL, SFT, or infra, the diagnosis is incomplete.

---

## Quick Start

### Single-Model Analysis

```bash
python scripts/analyze_cvdp_agentic_rollouts.py \
  --input /path/to/rollouts.jsonl \
  --output /path/to/analysis.md
```

### Comparison with Reference Model

```bash
python scripts/analyze_cvdp_agentic_rollouts.py \
  --input /path/to/candidate_rollouts.jsonl \
  --reference /path/to/baseline_rollouts.jsonl \
  --output /path/to/comparison.md
```

### CLI Options

| Flag | Description |
|------|-------------|
| `--input` | Path to target model rollout JSONL (required) |
| `--reference` | Path to reference model rollout JSONL |
| `--output` | Output markdown file path (required) |
| `--model-name` | Target model display name (default: inferred from filename) |
| `--reference-name` | Reference model display name (default: inferred from filename) |
| `--plots-dir` | Directory for plot PNGs (default: `<output>_plots/`) |
| `--no-plots` | Disable plot generation |

---

## Files in this Skill

```
cvdp_agentic_heavy/
├── SKILL.md                                    # This file — methodology & playbook
└── scripts/
    └── analyze_cvdp_agentic_rollouts.py        # Analysis script (phases, patterns, metrics, report)
```

### What Runs as Code vs What the LLM Does

| Step | Executor | Input | Output |
|------|----------|-------|--------|
| Parse trajectories, classify phases (P0-P5) | **Script** | Rollout JSONL | Phase counts, tool counts, pattern flags |
| Classify tool errors (E1-E6) and patterns (B1-B7) | **Script** | Rollout JSONL | Error/pattern counts per rollout |
| Aggregate metrics, pipeline funnel | **Script** | Parsed rollouts | Metrics JSON + markdown tables |
| Root cause classification (KG/UK/BI/EI) per task | **LLM** (follows Phase 2) | Trajectories + golden patch + script output | Per-task root cause labels |
| Per-task deep dive with causal narrative | **LLM** (follows Phase 3) | Trajectories + reference solutions | Deep dive entries |
| Cross-cutting analysis and summaries | **LLM** (follows Phase 4-5) | Per-task entries + metrics | Final report |

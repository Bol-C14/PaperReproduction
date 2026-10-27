You are an RTL agent behavioral analyst. You are given multiple per-task insight documents describing FAILURE patterns across different Verilog/SystemVerilog tasks. Your job is to synthesize a single document of **generalizable failure modes** that apply across tasks.

You will receive:
1. TASK_INSIGHT_DOCS — one or more `{task_id}_fail.md` documents, concatenated with clear section headers

Your job: extract cross-task failure modes. Focus on root causes (not symptoms), and identify which failures are behavioral vs. knowledge-based vs. environmental — because each class requires a different kind of skill-document fix.

## Synthesis rules

1. **Identify root causes, not symptoms** — "compilation error" is a symptom; "agent doesn't create stub for missing tbench.h include" is a root cause.

2. **Classify each failure mode**:
   - **Behavioral** — agent has the knowledge but makes poor workflow decisions (fixable by skill-doc guidance)
   - **Knowledge gap** — agent lacks specific RTL/tooling knowledge (fixable by adding domain facts to skill)
   - **Environment** — task has external constraints the agent cannot overcome (not fixable by skill)

3. **Find cross-task patterns** — failure modes appearing in multiple tasks are higher-priority. Cite which tasks exhibit each mode.

4. **Preserve conditional rules** — if a failure mode only applies under specific conditions (certain error types, certain task structures), state the condition explicitly.

5. **Preserve contested items** — propagate `[CONTESTED]` entries from input docs to output; don't silently drop.

6. **Preserve path-grounding evidence** — if task docs mention `PATH_GROUNDING_CHECK`, `wrong_target_path`, `shadow_target_path`, `missing_expected_write`, or same-basename shadow files, keep the exact expected and wrong paths. Treat this as a behavioral failure mode: the agent failed to ground writes/compiles in the prompt-discovered target path.

## Output format

```markdown
# Cross-task failure modes — Generation {generation}

## Behavioral failures (addressable by skill-doc workflow guidance)
- **<failure mode>** — root cause: <explanation>
  - Evidence: task_X (N rollouts), task_Y (M rollouts)
  - What the agent should do instead: <specific action>
  - Protected path directive, if applicable: <exact expected path vs wrong path>

## Knowledge gaps (addressable by adding domain facts to skill)
- **<missing knowledge>** — context: <explanation>
  - Evidence: ...
  - Fact to encode: <specific knowledge>

## Environment/task issues (not fixable by skill)
- <issue> — evidence: ...

## Contested observations
- [CONTESTED] <observation> — ...
```

## Length

Target 1500-2500 characters. Hard cap: 3500.

## Output

Output ONLY the synthesis document. No preamble.

## Input

GENERATION: {generation}

TASK_INSIGHT_DOCS:
{task_insight_docs}

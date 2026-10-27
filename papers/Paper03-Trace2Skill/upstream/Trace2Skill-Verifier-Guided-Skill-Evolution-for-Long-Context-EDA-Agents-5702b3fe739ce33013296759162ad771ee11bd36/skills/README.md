# Skills — Single Source of Truth for LLM Prompts

> **TL;DR:** every markdown file under `skills/` is a prompt fed to an LLM somewhere in this pipeline. They're kept here (not hardcoded in Python) so you can edit behaviour without code changes and diff prompt edits in git.

## Per-CID rollout skills

As of April 21, 2026 the rollout skills are split per CID (task nature). Each of the seven agentic-heavy CIDs has its own seed skill that becomes the starting point for a dedicated GA evolution run on that CID's train tasks.

**Taxonomy note — the official CVDP CID labels and the actual task content in the compiled dataset do not perfectly align.** We've named the seed files according to what the tasks really ask the agent to do:

| Folder | CVDP label | Actual task content (observed in compiled data) |
|---|---|---|
| `cid003_spec_to_rtl/` | spec_to_rtl | ✓ Write new RTL module from spec |
| `cid004_rtl_refine_design/` | rtl_refine_design | ✓ Enhance/modify existing RTL |
| `cid005_code_completion/` | code_completion | ✓ Integrate submodules into top-level / fill gaps |
| `cid012_rtl_debugging/` | rtl_debugging | ≠ Actually: write **new testbench** from scratch for given DUT |
| `cid013_testbench_generation/` | testbench_generation | ≠ Actually: **extend existing TB** with checker logic |
| `cid014_testbench_completion/` | testbench_completion | ≠ Actually: add **SVA assertions** to existing RTL |
| `cid016_verification_bug_fix/` | verification_bug_fix | ✓ Fix broken RTL so verifier tests pass |

Each `SKILL.md` is task-nature-specific because the agent's optimal workflow diverges meaningfully: writing a new TB is qualitatively different from fixing a regression, and a generic skill can only go so deep on either.

## What is a "skill"?

A **skill** is an instruction document given to an LLM to shape how it behaves. In this codebase the word is used a little loosely and covers three kinds of documents:

1. **Rollout skills** — the system-prompt-like document the RTL *rollout agent* (Haiku) reads before attempting each Verilog task
2. **Analysis skills** — methodology documents for *offline* post-hoc analysis (legacy — kept for historical eval comparisons; the GA loop no longer uses these)
3. **Optimizer meta-prompts** — short prompts that tell other LLMs how to do optimizer-internal jobs: mutation, crossover, compression, and each of the 3 oracle layers

## Directory layout

```
skills/
├── README.md                       ← this file
├── rollout/                        ← what the agent (Haiku) reads before a task
│   ├── _base.md                       Generic fallback (used if CID-specific file absent)
│   ├── cid003_spec_to_rtl.md          Write new RTL module from spec
│   ├── cid004_rtl_refine_design.md    Enhance / modify existing RTL
│   ├── cid005_code_completion.md      Integrate submodules / fill gaps
│   ├── cid012_stimulus_tb_generation.md   Write NEW TB from scratch for DUT
│   ├── cid013_testbench_checker_extension.md   Add checkers to existing TB
│   ├── cid014_sva_assertions.md       Add SVA to existing RTL
│   ├── cid016_rtl_bug_fix.md          Find/fix bugs that fail verification
│   ├── rtl_agent_skill_minimal.md     520 chars — LEGACY SEED (the pre-CID-split minimal)
│   └── rtl_agent_skill.md             10.5K — LEGACY strong reference (pre-CID-split)
├── analysis/                       ← offline eval (post-hoc, not in the GA loop)
│   ├── analyzer_skill.md              35K — behavioral failure analyzer methodology
│   ├── judge_skill.md                 15.8K — how to score analyzer reports
│   └── judge_rubric.md                8.9K — 10-criterion C1–C10 rubric
└── optimizer/                      ← meta-prompts the GA loop uses every gen
    │── mutation_system.md             Opus mutation system prompt
    │── crossover_system.md            Opus crossover system prompt
    │── compress_system.md             Safety-net: shrink output back within char budget
    │── task_insight_refine.md       ← LAYER 1: per-rollout refinement (CONFIRMS/EXTENDS/CONTRADICTS/NEW)
    │── pass_cross_synthesis.md      ← LAYER 2: cross-task success synthesis
    │── fail_cross_synthesis.md      ← LAYER 2: cross-task failure synthesis
    │── oracle_handoff.md            ← LAYER 3: KEEP/ADD/REMOVE/CHANGE handoff to Opus
    └── oracle_synthesis.md            Legacy single-shot oracle (fallback if 3-layer fails)
```

## Static vs. dynamic

Every file under `skills/` is **static** — it's read at run start and does not change during the run. A static skill is versioned in git and evolves only through deliberate human / AI-assisted edits.

Their **dynamic** counterparts are produced *during* a run and live under `optimizer/outputs/<run_name>/`. The correspondence:

| Static input under `skills/` | Dynamic output under `outputs/<run>/gen<N>/` |
|---|---|
| `rollout/rtl_agent_skill_minimal.md` (seed) | `individuals/ind<I>.md` (mutated per gen), final `optimized_skill.md` |
| `optimizer/task_insight_refine.md` (L1 prompt) | `task_insights/<task>_{pass,fail}.md` (L1 output, refined per rollout) |
| `optimizer/pass_cross_synthesis.md` (L2 prompt) | `cross_task/pass_synthesis.md` (L2 output) |
| `optimizer/fail_cross_synthesis.md` (L2 prompt) | `cross_task/fail_synthesis.md` (L2 output) |
| `optimizer/oracle_handoff.md` (L3 prompt) | `oracle_feedback.md` (L3 output — Opus's input for next gen) |
| `optimizer/mutation_system.md` | (Opus inputs are captured in `llm_calls.jsonl` + `prompts/<call_id>_*.txt` when debug mode is on) |

## What uses what (call map)

```
┌────────────────────────────────────────────────────────────────┐
│  rollout                                                       │
│  ─────────────────────────────────────────────────────────     │
│  rtl_agent_skill_minimal.md   ──►  Haiku 4.5 (rollout agent)   │
│  ( mutated version per gen )                                   │
│                                                                │
│  optimizer (every generation)                                  │
│  ─────────────────────────────────────────────────────────     │
│  task_insight_refine.md      ──►  GPT‑5  (Layer 1, per rollout)│
│  pass_cross_synthesis.md     ──►  GPT‑5  (Layer 2)             │
│  fail_cross_synthesis.md     ──►  GPT‑5  (Layer 2)             │
│  oracle_handoff.md           ──►  GPT‑5  (Layer 3)             │
│  mutation_system.md          ──►  Opus 4.6 (mutation)          │
│  crossover_system.md         ──►  Opus 4.6 (crossover)         │
│  compress_system.md          ──►  Opus 4.6 (shrink if oversize)│
│                                                                │
│  optimizer (fallback path, only if 3-layer fails)              │
│  ─────────────────────────────────────────────────────────     │
│  oracle_synthesis.md         ──►  GPT‑5  (single-shot oracle)  │
│                                                                │
│  analysis (offline only, not in the GA loop)                   │
│  ─────────────────────────────────────────────────────────     │
│  analyzer_skill.md           ──►  GPT‑5  (behavioral analyzer) │
│  judge_skill.md + rubric.md  ──►  GPT‑5  (judge)               │
└────────────────────────────────────────────────────────────────┘
```

## The 3-layer oracle prompts in detail

These four prompts are the load-bearing part of the optimization loop — they're what turn raw rollouts into something Opus can splice into the next-gen skill.

### `optimizer/task_insight_refine.md` (Layer 1)

Called once per rollout. Maintains a running `{task}_{pass|fail}.md` document per task+outcome pair. Implements the **CONFIRMS / EXTENDS / CONTRADICTS / NEW** classification protocol:

- **CONFIRMS** — new rollout matches an existing insight → append rollout id as evidence
- **EXTENDS** — new rollout is a variant or finer-grained case → nest as sub-bullet
- **CONTRADICTS** — new rollout challenges an existing insight → rewrite as conditional rule, or mark `[CONTESTED]` with evidence on both sides
- **NEW** — genuinely new observation → fresh entry with evidence

Key property: **the document accumulates across all rollouts of the (task, outcome) pair within the generation.** Each call reads the existing doc, incorporates the new rollout, and writes back. Evidence counters (`[3 rollouts]`) and IDs (`evidence: ind0_r0, ind1_r2, ind2_r1`) are preserved.

### `optimizer/pass_cross_synthesis.md` + `fail_cross_synthesis.md` (Layer 2)

Called twice per generation (once for pass, once for fail). Reads **all** per-task insight documents of that outcome and extracts generalizable patterns:

- **Pass synthesis** groups patterns into *Universal principles* + *Task-pattern detectors* (conditional rules)
- **Fail synthesis** classifies failure modes as *behavioral* (fixable by workflow guidance), *knowledge gap* (fixable by adding facts), or *environment* (not fixable by skill alone)

`[CONTESTED]` items propagate — Layer 2 never silently resolves them.

### `optimizer/oracle_handoff.md` (Layer 3)

Called once per generation. Fuses both Layer-2 syntheses with the per-task scoreboard into a single document with the structure Opus expects:

- **KEEP** — guidance that's working, cite supporting tasks
- **ADD** — new guidance, each with a **"Suggested text:"** block that Opus can literally splice into the skill
- **REMOVE** — counterproductive guidance with evidence
- **CHANGE** — existing guidance that needs modification, before→after
- **Open questions** — CONTESTED items carried through as diagnostic guidance, not hard rules

The output of this step — `oracle_feedback.md` — is the document that ends up in Opus's user message for the next generation's breeding. On the April 18 run, **the winning skill's Rule 7 was lifted verbatim from one of the ADD directives' "Suggested text" blocks**, which is the strongest empirical evidence we have that the oracle → Opus → skill handoff actually works.

## The legacy `oracle_synthesis.md`

Pre-April 18, this was the single-shot GPT-5 prompt that turned Python-aggregated rollout stats into mostly-mechanical feedback. It's preserved as a fallback: if any of the 3 layers fail (returns empty, exception, etc.), `run_optimizer.py` catches the failure and calls `build_contrastive_oracle()` which uses this prompt. In the healthy case it never runs. Kept so the run can degrade gracefully instead of crashing.

## Rollout skills: minimal vs. full

| File | Chars | When to use |
|---|---|---|
| `rollout/rtl_agent_skill_minimal.md` | 520 | **Default seed for GA runs.** Deliberately sparse — gives Opus room to improve. The skill is meant to be evolved, not hand-written. |
| `rollout/rtl_agent_skill.md` | 10,574 | Strong reference skill. Used for non-optimizer evaluation baselines or as a fallback if the minimal seed produces pathological initial behavior. Too strong for optimization: Sonnet hits 83% baseline with it, leaving no headroom. |

Both files go into the `SKILL.md` that Haiku sees in the Docker sandbox.

## Editing guidance

- **To change LLM behaviour:** edit the relevant `.md` file. No code changes needed. Module-level `_load_prompt(...)` calls re-read at every run.
- **To A/B test a prompt variant:** copy `foo.md` → `foo_v2.md`, reference it from a custom config (or swap the `_load_prompt("foo.md")` to `foo_v2.md` in a branch), and diff the run outputs.
- **To add a new skill:** create the `.md` in the appropriate subdirectory, add a loader line where it's consumed, and update this README's inventory + call map.
- **Placeholders:** Layer 1–3 prompts contain `{task_id}`, `{outcome}`, `{existing_doc}`, `{new_rollout}`, `{generation}`, `{scoreboard}`, etc. Don't rename these without also updating the corresponding `.replace("{...}", ...)` calls in `optimizer/streaming_oracle.py` — they're matched by literal string. The validator (`optimizer/validate_3layer.py`) will catch missing substitutions but not spelling drift.

## Relationship to the NeMo-Gym-CVDP submodule

The submodule at `NeMo-Gym-CVDP/` contains its own copies of the rollout and analysis skills under `data/` and `analysis/` — this is so the submodule remains a standalone artifact usable outside this parent repo.

Parent-repo code (`optimizer/`, `eval/`) reads from `skills/` **first**, and falls back to submodule copies only if `skills/` is missing the file. This gives us a single editable source in the parent repo while keeping the submodule self-contained.

**Rule:** edit `skills/` as the source of truth. When a skill that also exists in the submodule changes meaningfully (e.g., the rollout agent skill), consider propagating the change to `NeMo-Gym-CVDP/data/` too if you expect people to use the submodule standalone. For parent-repo optimization workflows, editing `skills/` alone is sufficient.

## Quick reference — one generation's flow

```
User kicks off optimizer with a config
                │
                ▼
Config names a seed:  skills/rollout/rtl_agent_skill_minimal.md
                │
                ▼  (mutated each gen via Opus)
┌──────────────────── Generation N loop ────────────────────┐
│                                                           │
│  evolving skill  ──►  Haiku 4.5 rollout agent             │
│                       (reads as SKILL.md in Docker)       │
│                                │                          │
│                                ▼                          │
│                       rollouts.jsonl                      │
│                                │                          │
│                                ▼                          │
│   ┌──────────  3-LAYER STREAMING ORACLE  ──────────┐      │
│   │                                                │      │
│   │  L1  task_insight_refine.md  ─►  GPT-5         │      │
│   │      updates  gen<N>/task_insights/*.md        │      │
│   │      once per rollout                          │      │
│   │                                                │      │
│   │  L2  pass/fail_cross_synthesis.md  ─►  GPT-5   │      │
│   │      produces  gen<N>/cross_task/*_synth.md    │      │
│   │                                                │      │
│   │  L3  oracle_handoff.md  ─►  GPT-5              │      │
│   │      produces  gen<N>/oracle_feedback.md       │      │
│   │      (KEEP / ADD / REMOVE / CHANGE)            │      │
│   └────────────────────────────────────────────────┘      │
│                                │                          │
│                                ▼                          │
│   Opus 4.6 breeds next-gen individuals, with oracle       │
│     mutation_system.md    + oracle_feedback.md            │
│     crossover_system.md   + oracle_feedback.md            │
│     compress_system.md    (safety net for oversize)       │
│                                                           │
└───────────────────────────────────────────────────────────┘
                │
                ▼
Back to the top of the loop with the new population
```

For a fuller picture see `AGENT_CONTEXT.md` (project-wide memory) and `pdf/cvdp_nat.tex` (technical reference document).

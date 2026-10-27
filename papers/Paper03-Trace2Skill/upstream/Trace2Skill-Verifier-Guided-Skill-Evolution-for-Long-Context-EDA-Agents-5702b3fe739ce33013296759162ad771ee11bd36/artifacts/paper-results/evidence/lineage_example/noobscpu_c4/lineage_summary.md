# Release-safe C4 lineage summary

This is an allow-listed, abstracted view of one completed C4 task-local lineage.
It retains the generation relationship, hashes, numerical selection evidence,
mutation-health metadata, and high-level lesson changes needed to inspect the
Trace2Skill loop. Full oracle, mutation-handoff, and evolved-skill text is
deliberately excluded: it contains task paths, module names, and build/harness
details inferred from restricted verifier context.

## Generation 4 survivor

- Population outcome: 6/16 passing rollouts; candidate pass fractions were
  1/4, 2/4, 3/4, and 0/4.
- Selected candidate: individual 2 (`child_gen4_2`).
- Skill SHA-256: `b1d4934e5e21282627f3d2bf725c2324cae9f3db1343209b68a90e0836981753`.
- SelectQ: 0.818482; pass@1: 0.75; SkillQ: 0.596722;
  AgentProgressQ: 0.481760; AgentVarianceQ: 0.164100;
  AgentAdherenceQ: 1.0.
- The adherence field is the implementation default: historical skill-monitor
  observations were absent for every C3/C4 candidate, so it did not distinguish
  this survivor from its peers.
- The full allow-listed decision record is `gen4_survivor_decision.json`.

## Abstracted oracle-to-mutation changes

The generation-4 oracle requested that the next skill preserve successful
reconnaissance and tight compile/simulate iteration while strengthening:

- edit/validation path grounding;
- diagnosis at the module that produced a visible error;
- stable source/include composition instead of trial-and-error churn;
- alignment between local validation and visible build evidence; and
- a compile-success gate before simulation.

It requested removal or revision of guidance that encouraged shadow-path edits,
partial builds that masked errors, broad include rewriting, or simulation after
a failed compile. These themes are paraphrases; no task-specific filenames,
hidden-verifier output, grader composition, or exact generated prose is included.

## Mutation and generation 5 evaluation

- Three generation-5 children were produced from the generation-4 survivor.
  `gen4_mutation_health.jsonl` records their output hashes, integration coverage,
  validity checks, sanitizer issue codes, and model settings without prompt or
  response text.
- Child slot 1 has SHA-256
  `a5315d0940c6142b5b68813b67ea8d347993b977eaf231b148447218237749ce`
  and was evaluated as generation-5 individual 1.
- That child passed 4/4 repeats and was the generation-5 winner: SelectQ
  1.104479, SkillQ 0.894462, AgentProgressQ 0.820000,
  AgentVarianceQ 1.000000, and AgentAdherenceQ 1.0.
- The other generation-5 candidates passed 1/4, 1/4, and 3/4 repeats. These
  values are independently present in `evidence/c4/quality_records.jsonl`.

This lineage demonstrates the recorded handoff structure and a successful
next-generation child. It is qualitative process evidence, not proof that the
textual changes caused the aggregate C3/C4 difference.

# C3/C4 NoobsCPU action-trace example

These are real, allow-list-sanitized action traces. Both started from the same
seed skill on the same task and scheduler coordinate, but the model samples
were independent. The pair illustrates a mechanism; it is not by itself a
causal estimate of runtime feedback.

| Condition | Task | Gen. | Ind. | Repeat | Reward | Pass rate | SelectQ | SkillQ | AgentProgressQ | AgentVarianceQ | AgentAdherenceQ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C3 sparse | `NoobsCpu-8bit_0002` | 1 | 0 | 2 | 0 | 0.00 | 0.050342 | 0.500000 | 0.301300 | 0.984700 | 1.000000 |
| C4 dense | `NoobsCpu-8bit_0002` | 1 | 0 | 2 | 1 | 0.25 | 0.296404 | 0.500000 | 0.251960 | 0.170900 | 1.000000 |

The C3 rollout made 18 tool calls: 15 inspection calls, one write, one compile,
and one simulation. It reached the tested phase but failed the final check and
made no runtime-verifier calls.

The C4 rollout made 32 tool calls: 19 inspection calls, four writes/edits,
three compiles, three simulations, and three permitted verifier-feedback
executions. Its allow-listed feedback progression was:

| Feedback execution | Compile OK | Simulation OK | Tests | Partial score | Verifier pass |
|---:|---:|---:|---:|---:|---:|
| 1 | no | yes | 0 / 1 | 0.0 | no |
| 2 | no | yes | 0 / 1 | 0.0 | no |
| 3 | yes | yes | 1 / 1 | 1.0 | yes |

The final task-level context is stronger than this single pair: across all 80
NoobsCPU rollouts, C3 passed 0 while C4 passed 35. All 35 C4 passes had at
least one executed verifier-feedback call. Those totals are recomputed from
the packaged evidence by `scripts/validate_paper_results.py`; the traces here
only expose one concrete action sequence behind that aggregate.

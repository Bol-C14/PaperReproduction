# Bounded next experiment — NOT RELEASED

Status: **not_run**. Initial authorization is zero model calls and zero spend. Parent independent review and explicit release are required before any endpoint call. No paid cloud, model download, or new service.

## Proposed public-payload pilot

Use the six already frozen `scripts/selection.json` tasks with the original source pin, manual policy, default user-simulator mode versus `llm_agent_solo` + `dummy_user`. First verify exact registry/CLI names against the pin. This is a small-set live pilot, not the 114-task paper result. Reference actions, evaluator assertions, hidden tests and fixing commits remain in the verifier process and outside agent-accessible inputs. A model sees only upstream-approved policy, tool schemas, task ticket or user scenario appropriate to its role, prior visible turns, and public synthetic tool responses. Never transmit home files, environment variables, credentials or unrelated projects.

Model request: dated `gpt-4.1-2025-04-14` for agent and simulator, temperature 0, if the authorized shared client's route supports that exact snapshot. An alias or replacement is a separately labeled port and requires an amended protocol. Keep runtime secrets in the shared client; do not copy them into this worktree or sandbox. Resolve routing, streaming/tool-call support and accounting before release without reading secrets.

Freeze trials 0..3 and seeds 300..303; pair each task/trial across modes. Total cap **48 episodes: 24 default, 24 solo**. Concurrency 1, four CPU threads, two wall-clock hours. Proposed hard spend ceiling **USD 5 total** including user simulation, agent, retries and any necessary judge; this is a proposal, not authorization. Aggregate token ceilings: 1,000,000 input and 250,000 output, with provider-specific preflight cost reservation; the USD ceiling takes precedence. Per-message output cap 512, per-episode max_steps 40, max_errors 3, request timeout 60 seconds, no automatic transport retry. All are bounded pilot deviations from the original default 200 steps/10 errors and must be reported. Stop before a request if its maximum possible charge cannot be reserved under the remaining ceiling. If the shared client cannot enforce these caps, remain blocked.

Default mode has a separate simulator cost/randomness stream; solo mode has no user LLM. Report user and agent calls, tokens, cost, termination, failed/aborted episodes and simulator errors separately. Four temperature-zero repeats are not guaranteed independent. Label source/provider request seeds separately from harness scheduling seeds. Never infer a user-simulator failure solely from agent failure; manually review tool grounding, instructions and premature stop/transfer.

## Analysis fixed before observations

For each task with n completed eligible trials and c successes:

- pass@k = 1 - C(n-c,k)/C(n,k): at least one of k successes.
- pass^k = C(c,k)/C(n,k): all k succeed.

Use k=1..4 only when n≥k. Average task-level estimates with equal task weights; no pooling reference controls as agent trials. Report missing/aborted trials explicitly, available-case coverage, and a pessimistic sensitivity analysis treating unresolved selected trials as failure. Invalid infrastructure episodes remain a separate flag and require a protocol decision before replacement; never silently resample.

For pass^1/pass@1 report task-specific Wilson 95% intervals (descriptive given repeated-run dependence). Report paired Default−Solo deltas and paired bootstrap intervals by resampling whole tasks with all their paired trials, fixed bootstrap seed 300 and 10,000 replicates. Apply the same task-cluster bootstrap to pass@k and pass^k. With only six tasks, these intervals are exploratory and do not cover task-selection bias. Inspect simulator-error sensitivity separately; no causal claim from the mode delta alone.

Advance to paper-protocol reproduction only after this pilot, a separate frozen sample from original tasks.json (or full 114 tasks), historical runtime verification and renewed budget approval. Do not optimize prompts against the held-out main tasks.

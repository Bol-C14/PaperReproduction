# G3 — Terminal-Bench scientific review

Audit date: 2026-10-28 UTC. Paper: [arXiv:2601.11868v1](https://arxiv.org/html/2601.11868v1), submitted 2026-01-17. Paper type: benchmark/dataset, evaluation infrastructure, and empirical error analysis. Contribution: a curated task collection and evaluation protocol; Terminus 2 is a comparison scaffold, not a newly trained model. Venue: arXiv preprint; no conference/journal acceptance established from the versioned record. CCF: unknown; no venue classification inferred from authors or topic, and no dated official CCF list was used.

## Paper protocol and claims

The paper evaluates 89 tasks with six scaffolds across 32,155 trials and reports a best average resolution rate of 63%. Acceptance checks final environment properties. Appendices document auditing, judge rubrics, adapters, tasks and Terminus 2. The paper acknowledges contamination, dependency/resource variability and residual verifier defects. Table 2's caption says 74 tasks while the main text says 89; resolve this denominator inconsistency against original configuration/results before numerical replication. These are author claims, not reproduced results. [Versioned paper, §§2–6 and Appendices A–I](https://arxiv.org/html/2601.11868v1).

## Mechanism and novelty boundaries

The useful mechanism is packaging realistic task state with an executable acceptance contract and a resettable environment. This does not itself prove that acceptance equals real task completion: both undercoverage and rejection of valid alternatives remain possible. A reference solution only demonstrates existence of one accepted path, and a failing no-op only rules out an already solved initial state.

Prior-work collisions: SWE-bench supplies execution-backed software evaluation; WebArena/OSWorld cover interactive actions; MLE-bench/MLGym cover ML workflows; MAST informs taxonomy lineage. Novelty should rest on breadth, curation and empirical comparison. This is a scope comparison, not an exhaustive priority search. [Paper related work](https://arxiv.org/html/2601.11868v1).

## Release history reviewed through 4.0

| Release/policy | Material protocol consequence | Official source |
|---|---|---|
| 2025-09-09 timeout policy | Changed time budgets invalidate leaderboard comparability | [Timeouts](https://www.tbench.ai/news/leaderboard-integrity-and-timeouts) |
| 2025-11-07 2.0 + Harbor | Separate new dataset/harness release | [2.0](https://www.tbench.ai/news/announcement-2-0) |
| 2026-04-19 integrity policy | Passing trials require ATIF; reward hacks score zero; task-specific advantages are prohibited | [Integrity](https://www.tbench.ai/news/leaderboard-integrity-update) |
| 2026-05-06 2.1 | Fixes 28 of 89 tasks; dependency drift, resource mismatches, specification errors | [2.1](https://www.tbench.ai/news/terminal-bench-2-1) |
| 2026-07-30 3.0 | New 74-task collection; agent/verifier containers separated and artifacts transferred | [3.0](https://www.tbench.ai/news/terminal-bench-3-0) |
| 2026-07-30 continuous protocol | Reuse, regrade, or rerun according to which task contract changed | [Versioning](https://www.tbench.ai/news/continuous-benchmarks) |
| 2026-08-28 4.0 blog | Flat 8-hour agent limit, resource recalibration, 8 removals and 19 fixes | [4.0](https://www.tbench.ai/news/terminal-bench-4-0) |

4.0 protocol checkout is pinned to `452bf305c6daa62fc59061d22133a7cbc7c1572e`. The GitHub release displays August 26 whereas the blog index dates its announcement August 28; these are different release/announcement timestamps. [Release](https://github.com/harbor-framework/terminal-bench/releases/tag/v4.0.0). No 3.0 or 4.0 tasks are substituted into our frozen 2.0 experiment.

## Static evaluator audit of the frozen sample

- `log-summary-date-ranges`: the reference computes from input logs; the verifier compares a fixed ordered CSV. Independent checking must recompute all periods from the *actual* pinned logs and count bracketed severities rather than incidental message words. Exact row order is specified. Public hardcoded expected counts can be copied if solution/test material leaks.
- `regex-log`: acceptance is one aggregate `re.findall` equality over 25 sample lines. The instruction's prohibition on zero-prefixed octets is not explicitly tested by those samples. Some invalid-date examples also contain an invalid IP, so those examples do not independently isolate calendar validity. An independent stricter solution and held-out semantic cases are needed.
- `cancel-async-tasks`: the original tests count stdout messages and timing; those are weaker evidence than observing actual bounded active jobs and cleanup effects. The independent checker records start/cleanup events to a file for normal completion and SIGINT, including queued jobs. It is not a proof across all awaitables, exception paths, or scheduler loads.

## Isolation and interpretation limits

The 2.0 task protocol copies tests after the solution into the same container. Temporal hiding reduces direct test access during execution but cannot fully protect a verifier from an adversary who can modify its interpreter or executable search path. Our offline containers have no network, no host home/socket mounts, no Linux capabilities, no privilege escalation, a memory/process cap, and fresh task state. These controls are calibrated for audited reference/no-op scripts. Cooperative CPU affinity can be widened by arbitrary hostile code; it is not an enforced live-agent quota. No live-agent evaluation is authorized by this audit.

Runtime evidence, failures, and the two-setting comparison are in [REPRODUCTION.md](REPRODUCTION.md) and [metrics](metrics/). A three-task purposive sample cannot validate the 89-task leaderboard, its confidence intervals, model rankings, cost claims, or human difficulty estimates.

## Observed verifier/reference disagreement

In the 1-CPU reference replay, `regex-log` receives upstream reward 1 while independent cases reject four outputs: three addresses with a zero-prefixed octet (`01.2.3.4`, `1.02.3.4`, `1.2.3.04`) and an IP/date split over two lines. The last case demonstrates a line-boundary defect as well as missing leading-zero coverage. This is a concrete failure of this frozen reference/test combination, not evidence that every Terminal-Bench task is defective. The stricter alternative passes only the upstream fixture and 10 tested independent cases; universal correctness is unproven. It is an auditor-written semantic control, never a live-agent result.

The pinned 4.0 `tasks/vf2-speedup-networkx/task.toml` independently confirms separate verification (`environment_mode = "separate"`), an 8-hour agent budget, and artifact transfer (`artifacts = ["/app/"]`). Our proposed EDA package narrows the export allowlist further; it does not claim to reproduce that 4.0 task.

The timeout-child survival observation is confined to this AffinityPort → Harbor 0.25.0 → Podman/podman-compose chain, not an established defect in the original Docker harness or paper protocol. Cooperative CPU affinity is not an adversarial CPU quota. The extracted EDA package is a template containing REQUIRED placeholders, not a runnable production task.

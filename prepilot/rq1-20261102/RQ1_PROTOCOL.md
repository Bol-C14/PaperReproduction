# RQ1: controlled action opportunities — first gate

Goal: determine whether a small real FPGA action panel contains reproducible differences that can support claims about action choice. This is a new experiment, not a rerun of the completed paper reproductions. No result is presumed.

## Frozen starting scope

One existing VexRiscv checkpoint (`vexriscv_re-place_2025.1.dcp`, 1,815,178 bytes), Vivado 2025.1 build 6140274, two threads, fresh process per arm. Start with checkpoint read/report/write/reopen before spending on optimization. Baseline timing, route status and utilization are measured, not taken from old logs. The source DCP remains read-only by convention; outputs go to an isolated directory.

Candidate panel, pending actual design-stage and Vivado-help admissibility checks:

1. No-op: reopen initial checkpoint, identical reporting and output handling.
2. `phys_opt_design -directive Default`.
3. `phys_opt_design -directive Explore`.
4. `phys_opt_design -directive AggressiveExplore`.

These directives are exposed by the existing VivadoMCP implementation. Exposure does not prove each is accepted on this particular routed state. Verify applicability before freezing the candidate set. Preserve rejected candidates and reasons; do not silently replace failed arms. If physical optimization leaves incomplete routing, use the same predeclared completion procedure for every arm including no-op, or report outputs as incomplete rather than compare invalid QoR. Do not add retiming or an uncalibrated RapidWright edit to this first panel.

## Comparability and cost

Each arm opens exactly the same immutable input in a fresh process; no arm starts from another arm's output. Expose the same legal panel to all selectors. Freeze constraints, executable, thread count, action scripts, reporting and timeout before execution. Record process wall time, diagnostic time, action/completion time, exit code, failure stage, output/checkpoint identity and timing/route/DRC evidence. Retain startup failures as setup cost, separate from action outcomes. Timeouts are censored outcomes, not zero-valued successful scores.

First run one no-op smoke under 120 seconds; this is readiness evidence only. After it succeeds, calibrate no-op twice more and repeat the leading non-noop at least twice, recording randomized execution order. Do not invent a Vivado seed option; establish supported seed controls from this tool version or report uncontrolled nondeterminism explicitly. Two-thread execution and repeated processes are controlled but do not prove determinism.

Selection controls: fixed no-op; a fixed optimization rule chosen before outcomes; uniform random selection from the frozen legal set using recorded selection RNG seeds. These selectors consume the same panel and execution budget; uniform random performance can initially be calculated from a fully executed finite panel, explicitly as a panel-derived expectation rather than an online-agent rollout. Full-panel data are evaluation-only and unavailable to selectors. Add no LLM until the panel shows an unresolved decision problem.

## Evidence and decisions

Measure WNS/TNS and feasible timing under frozen clock constraints, route completion, utilization and reported DRC/unconstrained paths. DCP reload and tool validity checks do not prove functional equivalence. Before claiming an optimization preserves function, identify and execute an appropriate independent check or narrow the correctness claim to the actual tool evidence. No absolute Fmax claim from WNS alone.

Continue if action differences exceed observed repeat variation and there is a realistic path to legal, comparable outputs. A one-state difference demonstrates action sensitivity, not state-conditioned capability or generalization. Expand only then to two design families with two states each, looking for action-ranking changes that a fixed rule cannot explain.

Reframe if one fixed rule dominates across states: study attainable headroom or measurement validity instead of claiming engineering intelligence. Stop if legal actions tie within noise, validity cannot be checked, or implementation dominates the time budget.

Alternative explanations: fixed recipe effectiveness; tool randomness; different completion work; leakage of action outcomes; design-family identity; censored timeouts; constraint mismatch; insufficient correctness evidence. Disconfirmatory evidence and all failures remain part of the record. The best observed panel member is a finite-panel reference, never a global reachable optimum.

## Scientific review refinements

Prefer state-dependent action-ranking crossovers over merely different mean action gains. Candidate generation is outside the fixed-panel estimand and must be evaluated separately. Distinguish preserving the original artifact, serializing/reopening it, and rerunning implementation without an edit: these are different controls with different costs and noise. The current smoke performs serialization/reopen only, and does not rerun placement/routing. Do not repeatedly redefine the score until a ranking crossover appears.

After identifying an apparent winner in exploratory panel runs, use independent confirmation runs for its effect estimate to limit winner's curse. Design family is the unit for cross-design generalization; states are nested within family and repeat runs/seeds are technical repetitions. A single family with many technical runs is not many independent designs.

Official reuse lead verified read-only on 2026-11-02: https://github.com/Xilinx/fpl26_optimization_contest (public preliminary example agent, Apache-2.0 file present). Avoid claiming action-granularity or branching novelty: https://arxiv.org/abs/2610.16625 already reports those comparisons. No new upstream code was executed based on this web inspection.

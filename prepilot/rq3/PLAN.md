# RQ3: diagnostic information value — gate-first prepilot

## Shared smoke update (supersedes initial snapshot below)

Read RQ1 `prepilot/SMOKE_RESULT.md` and `RESOURCE_INVENTORY.md` after coordinator update: third attempt succeeded (remote exit 0; 28.697 s tool / approximately 32 s wall). VexRiscv is **routed**, 2,937/2,937 nets routed, zero route errors; filename does not establish a placed state. Initial two basename failures were resolved by RQ1. It has 115 inputs without input delay and 136 outputs without output delay; freeze the contest constraint contract, do not claim full interface signoff or equate routing with functional equivalence. Source/constraint provenance, checker and legal interventions remain open.

**Execution plan correction:** reuse RQ1’s validated routed-state action panel and its evidence matrix. The placed-state action list below is conditional only on finding a genuinely placed state and is not authorized for this routed input. Do not duplicate smoke or compete with RQ1’s allocated 2-thread serial 45-minute panel. Next RQ3 resource request is one 10-minute report/help-only probe *after* its job finishes; a full additional matrix needs coordinator allocation. No RQ3 remote experiment ran.

## Initial status (2026-11-02; before shared smoke update)

Design and protocol preparation only; no real diagnosis, optimization, or model run completed here. Source material `libfile_cea4366ce9208191960e7908cc321217` was materialized and read locally. Treat its literature and causal claims as hypotheses.

Branch `prepilot/rq3-information-value`, base `809ca20`; independent worktree `<RQ3_WORKTREE>`. Original worktree's untracked `prepilot/` was left untouched. No repository-level AGENTS.md or .agents found; vendored Trace2Skill rules do not govern this new directory.

APRIL `<COMPUTE_HOST>` read-only check: reachable; 2026-11-02 11:22 UTC load 0.74/0.49/0.37, 11 users, approximately 1.34 TB available RAM. This is a snapshot, not a reservation. Vivado not in noninteractive PATH. Existing shared log shows Vivado 2025.1 started, then failed because `checkpoint_smoke.tcl` was absent (exit 1). It does not establish checkpoint readability. No new remote jobs started.

## Concrete candidate and acceptance gates

Use an immutable placed FPL26 checkpoint and legal physical implementation interventions. Candidate already present: `<TOOLCHAIN_ROOT>/fpl26_contest_benchmarks/vexriscv_re-place_2025.1.dcp` (shared input digest `8baf6451f9b20b8a82f035d14187c7350529a6ea0330e02d93c7100b19753149`, must rehash before use). Other design families exist on APRIL. Availability is verified; provenance, redistribution license, contest rules, constraints, actual checkpoint stage and legal commands remain unverified. Do not download/redistribute or claim a public reusable dataset until checked.

Gate 0: existing RQ1 coordinator establishes real open/reopen, tool version, source/constraint digests, legal checker and report availability. Do not duplicate its smoke or old cleaned reproduction.

Gate 1 (before agents): shortlist 4–6 immutable states from at least two genuinely different design families, based on natural logs/engineering condition rather than known action winners. Fixed actions proposed for placed states: retain original; default physical optimization then standard route; fanout-focused physical optimization then standard route; standard route without physical optimization. Exact directives require installed 2025.1 `help` and contest-rule confirmation. No RTL/constraint changes, timing exceptions, or waived violations. Every action starts from the same DCP. Route and checker are identical. Reject an action as unsupported instead of silently replacing it per state.

Evaluate full action panel under coordinator-approved runtime cap, capturing route completion, setup/hold, timing coverage, DRC and equivalence/contest checker. Prefer contest-authoritative objective; until verified, no scalar QoR claim. Invalid outputs cannot win; retain baseline is a real zero-intervention option. Define practical effect threshold from two repeats' measured variation and engineering relevance *before* checking action differences. Stop if no supported checker.

Proceed only if at least two states have different verified best legal actions, with regret beyond that threshold, AND baseline-visible evidence does not already deterministically distinguish them. Action crossover alone is insufficient: a source/netlist feature may reveal the answer for free. Gate failure is a useful negative result, not a reason to hide timing or remove ordinary inspection.

## Visibility contract

All arms get exactly the same task, source/constraints normally available to the engineer, state metadata, action panel, existing reports/logs including timing report, and permitted free inspection. Publish a machine-readable inventory with digest, creation time, generating command and state ID before randomization. Newly invoking a tool costs time even when its output could be inferred from source. Never hide existing reports, DCP properties, or baseline timing merely to manufacture uncertainty. All free inspections are logged and equal across arms. If unrestricted inspection leaks a diagnosis, count it as available baseline evidence and reassess the gate.

Extra queries are allowlisted newly generated measurements: detailed critical-path logic/net delay, hierarchical fanout/complexity, congestion (only if supported at that state stage). Coarse-vs-detailed is an interface choice disclosed as such, not a native FPL capability claim. A report with action results, recommended winner, future checker outcome, or any post-intervention measurement cannot be a diagnostic input.

## Randomize information first; acquisition second

Stage I isolates information USE: paired same state and action panel, randomly offer no extra report or one candidate report. Equal total budget; reported diagnostic cost is deducted even for randomized provision. Agent/model settings fixed; commitment to action happens before outcome exposure. Also retain a baseline-information-only policy. Report treatment effect on verified regret and action change, not quality of prose. Include measured latency and token overhead in usage.

Stage II only after Stage I establishes useful information: compare no-extra-diagnosis, random-diagnosis, selected-diagnosis and sufficient-information reference. All arms may decline action/retain baseline, use remaining time for allowed execution, and share the same fixed deadline. Random policy has a preregistered query distribution plus a cost-matched random stratum. Selected policy must record choice and expected decision relevance before query. Reference gets the prespecified union of useful pre-action reports, pays actual generation cost and is a sufficient-information comparison, not an omniscient upper bound. A separate zero-cost reference can be labeled only as a descriptive bound.

Pair across exact state, budget and execution conditions. Decompose (i) randomized-report utilization gap; (ii) chosen-query benefit at fixed downstream policy; (iii) end-to-end selected policy. A bad result with useful assigned evidence diagnoses utilization failure; good downstream use plus poor query choices diagnoses acquisition failure. Never select the reference report from held-out action outcomes.

## Budget and validity

Predeclare a common elapsed deadline after Gate 1 calibrates real tool costs, plus CPU/RSS, tool time, cache status, queue wait and tokens. Record both operational latency (includes observed contention) and uncontended sensitivity; no fictitious fixed report prices. Alternate run order, bounded worker count (proposed 1 job, 2 tool threads), repeated cost calibration, identical cache policy; never charge cold generation to one arm and cached retrieval to another. Tool startup/open cost must be consistently included or amortized and reported. Timeouts exhaust that arm's budget. Failed diagnostic time still counts.

State ID is SHA256(DCP bytes + constraints digest + tool/version + action-history digest), not a filename. Each report records parent state, query, start/end timestamps, generation status, cache state and bytes digest. Mutation invalidates previous reports; historical reports remain visible with explicit stale labels but cannot be treated as current measurements. A changed checkpoint under the same path is rejected. Cost/evaluation ledger is evaluator-only; agents cannot see future outcomes, winner labels, full-action matrix, sibling-arm transcripts or hidden diagnostic outputs. Split by design family, not seeds, names, or checkpoint variants; variants/seeds remain nested replicates. Report family-level effects and raw per-family results; 2 families is feasibility evidence, not generalization.

## Alternatives, leakage and stopping

Apparent benefit may be generic extra reasoning time, report length, identifier memorization, routing stochasticity, privileged oracle data, or cost skew. Controls: time/token matched no-information prompt, report-order counterbalance, identifiers randomized without removing engineering evidence, paired repeated tool runs, evaluator isolation and true cost ledger. Selected-vs-random alone cannot establish acquisition skill if it merely buys more reports.

Stop before model expansion if: all states prefer one query/action; free baseline evidence already suffices; diagnostics do not change verified actions; marginal benefit disappears after real costs; reports are unavailable at the decision stage; or checker/provenance remains unresolved. If Stage I effect is absent but reports clearly discriminate action outcomes, investigate utilization separately without claiming VOI success. If only historical replay can run, label it replay; it cannot establish online information acquisition or changing-state validity.

## Resources and next actions

Current preparation: Mac Python standard library only, $0, no API. Next coordinator allocation request: one APRIL worker / 2 Vivado threads; first 10-minute read-only report/help probe after shared checkpoint smoke, then propose a separately capped 4–6 state action-matrix job based on measured runtimes. Do not start that matrix this round. No paid license acquisition, LLM API or GPU requested. Exact version-specific command availability, dataset permission, legal action/checker and shared smoke remain blockers for execution. First milestone is Gate 1 crossover/ambiguity table, not agent performance.

Primary command references (current web docs, 2026.1; installed 2025.1 help takes precedence): [AMD report_design_analysis](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/report_design_analysis), [physical optimization](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Physical-Optimization-phys_opt_design), [congestion report staging](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Report-Design-Analysis-Congestion-Report). These establish proposed mechanisms, not diagnostic value for these checkpoints.

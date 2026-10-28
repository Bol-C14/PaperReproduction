# Real optimization tranche — frozen before pilot

This phase supersedes only the prior stop milestone. Earlier preflight files and
its closed gate remain unchanged. Local parent commit: `eb5b12d`. Creation UTC and
two-hour deadline, exact limits and source hashes are in `configs/protocol.json`.
Commit this protocol and implementation before the first new simulator call.

## Scientific question and fidelity

Can the released circuit templates support a real propose/simulate/parse/check/
update optimization loop? Does a transparent numerical range-feedback policy help
relative to equal-budget random and GP controls? This does not test an LLM's
circuit understanding, algorithm decisions or reflection. No external model calls,
credentials, paid services, downloads, system changes, pushes or PRs are allowed.
Existing official Debian ngspice/SKY130 assets and installed CPU libraries suffice.

Paper anchors: final paper §3.1 specifies target-normalized FoM and individual
constraints; §3.4–3.6 describe discrete search ranges, numerical inner algorithms
and outer history/boundary feedback; §4.1 describes 10-sample initialization for
GP BO, Matérn ν=2.5 and UCB β=2.0. The author implementation in
`advanced_search_methods_test.py:804` encodes variables as integers and fits GP
search from prior results. We preserve these broad numerical ingredients but use
scikit-learn instead of missing scikit-optimize. Fixed kernel choices and sequential
exact acquisition over this tiny discrete grid are port choices, not a claim of
running the authors' exact baseline or orchestrator.

## Tasks and measurements

Use only the same released inverter and five-transistor OTA. All original numeric
constraints, grid widths, scaling, topology, supply, load, bias, tt model files and
27°C temperature remain frozen. Full variable grids have 81 and 729 combinations.
The inverter uses the previously checked paired response edges and time-weighted
0–4 ns supply power minus the same static estimate. OTA retains original gain,
first downward unity crossing and supply power. Controller-normalized FoM is the
search objective, and every individual source constraint determines feasibility.
The original YAML fallback FoM stays visible separately. No objective/threshold
changes after results. No old fixed-point labels are used as search observations.

## Matched-budget arms

Each main arm gets 36 attempted simulations, including failed ones, on each task
and each seed 11,29,47. Stop-on-first-feasible is disabled, so trajectory quality
and first feasibility are both visible. No cross-run simulation cache. The same
10 random central-domain points (indices 1..7 in each variable) initialize every
arm for a given circuit/seed; all are resimulated and charged. Subsequent points
are unique within a run.

* `random_full`: uniform random unseen full-grid points after initialization.
* `gp_full`: sequential GP-UCB on the full grid after identical initialization.
* `gp_frozen`: the same GP-UCB restricted to initial indices 1..7 throughout.
* `adaptive_gp`: the same GP engine, with numerical outer range feedback after
  attempts 12 and 24. This is an explicitly new heuristic control, not an LLM.

GP: normalized index inputs, standardized target, Constant(1) × Matérn(ν=2.5,
length_scale=0.35) + white noise 1e-6, no hyperparameter fitting, UCB μ+2σ. This
fixes otherwise unspecified port hyperparameters and bounds CPU cost. Missing or
invalid metrics are excluded from GP fits and consume the same budget; no zero
labels are fabricated. Before three valid observations, use random unseen points.

Adaptive rule: rank valid incumbents by feasibility, then normalized total
constraint violation, then FoM (feasible candidates rank by FoM). At each outer
checkpoint retain history, calculate feasibility, best-FoM improvement, invalid
counts, top-design boundary concentration and variable distributions. Set each
variable's box around the incumbent with index radius 2; radius 4 if there is no
feasible design or improvement is <0.1%. If the incumbent is at a current boundary,
include at least the next available full-grid index beyond that boundary. Clip to
the released domain. Exhausted current boxes expand to the full grid, recording
the reason. Keep every variable active; active-variable fixing is available in
the future LLM schema but not claimed as exercised here. No unmeasured sensitivity
or circuit-understanding output is invented.

## Pilot, scaling, validation and independent oracle

First run inverter seed 11, random and adaptive, 18 attempts each, with six common
initial points and outer checkpoints 6 and 12. Pilot checks require no harness
exceptions, valid electrical results, exact debit accounting, actual range-update
events and proposals after the updates. Inspect before main scaling. Pilot outputs
remain separate and are not pooled into main comparisons or used to tune rules.

Main: 4 arms × 2 tasks × 3 seeds × 36 = 864 attempts. Pilot: 36. Independently
validate the preselected best feasible main candidate (or least violating if none)
from each of 24 runs using original source measurements and a separately exported
refined-grid measurement run: 48 additional calls. Recompute constraints and
waveform measurements outside the optimizer. Do not replace a failed validation
with another winner or adjust constraints.

Finally enumerate all 81 inverter grid points in a separate held-out run using
the same corrected measurement definition. These data are forbidden to the
optimizers and run only after all main trajectories finish. This supplies a finite
grid optimum/feasible-set reference for the small real circuit, not a global
continuous optimum or an OTA oracle. Total planned calls: 1,029; hard cap: 1,100.

Keep every deck/stdout/stderr and a write-before-launch ledger. A process error,
timeout, missing measurement, solver failure and valid infeasibility have different
statuses. Attempts/unique points/valid results/feasible points/actual process calls
are counted separately. Maximum child wall time 20 s, CPU 15 s, address space
2 GiB; whole-phase two-hour deadline. Run serially with explicit minimal environment
and requested single-thread numerical libraries. No reruns to improve results.

Report per-seed best feasible FoM, first-feasible attempt, feasible fraction,
regret to the post-hoc inverter grid oracle, invalid counts, decision/range logs,
wall/CPU/memory and all substitutions. With only three seeds, comparisons are
descriptive, not statistically conclusive or reproduction of the paper's 24-task
success rate. Negative results stand.

## LLM boundary

Prepare requests for circuit understanding, initial ranges, inner algorithm/batch
decisions and outer regeneration using the actual netlist/specs/history and original
prompt references. Validate JSON decisions, variable coverage, released domains,
supported method names and remaining-attempt caps. Archive real measured feedback
requests after numerical runs. No response is generated or consumed as model
evidence. The live controller must fail closed before candidate execution in this
tranche, even if a response file exists. No heuristic/replay is labelled LLM.

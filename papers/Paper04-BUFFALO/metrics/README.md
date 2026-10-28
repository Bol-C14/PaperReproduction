# Metric provenance

- `preflight.json` is the **historical initial audit** before source recovery/tool build. Its zero experiment counts and absent executables describe that moment only. `logs/preflight.stdout.json` is its direct captured output.
- `pilot.json`: 34 actual STA comparisons on two synthetic fixtures; `aes_pilot.json`: 17 on the real-connectivity AES cut with assumed geometry.
- `candidates.csv`, `summary.json`, `budget_curves.json`: derived from those two result files; recompute with `src/summarize.py`.
- `smoke.json`, `rc_control.json`: successful setup/sensitivity checks, excluded from baseline comparisons. The failed ANSI smoke is retained under `runs/debug-smoke-ansi` and logs.
- `costs.json`: complete process counts, training/nontraining separation and limited build wall interval.
- `reward_audit.json`: numerical pseudocode counterexample; no policy training.
- `paper_table_iv_transcribed.csv`: original preprint numbers manually transcribed, **not reproduction results**. `paper_table_audit.json` is a recomputable arithmetic check of that transcription.
- `provenance.json`: tool/library pins, hashes, bounded artifact-search outcomes; parent-reported paper hash is explicitly not independently verified here.

Per-candidate STA output and query order are under `runs/`; `src/verify_archived.py` independently reaggregates all51 comparison cases using Python standard library. `decoded_tree.json` derives from archived sequences; Verilog/SPEF/SDC and raw engine output preserve evaluated inputs/results.

Closeout: `logs/config-contract.stdout.json` records a nondefault SDC/score test and153 default input byte comparisons, with zero added STA. Historical `max_slew_ps`, `max_transition` and validity fields refer to the declared Y-output-slew checks only; A input-pin slews were not measured.

`units_audit.json` independently checks old Liberty/path units and identifies original .5fF endpoint-load extrapolation. `envelope.json` and `envelope.csv` contain12 explicitly predeclared local-study calls, separate from earlier comparison/diagnosis. `envelope_verification.json` rechecks raw outputs, same-implementation area/delay/Pareto groups, and368 independently interpolated arcs. Corrected1.44fF cases remain separate from .5fF replays. Counterfactual target-feasibility flags are arithmetic on fixed measured arrivals, not new or faithful paper-target STA results.

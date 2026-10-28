# CircuitFusion methodology closure

Read `REPORT.md` for the completed controlled result, `SUMMARY.json` for the machine-readable outcome, `MECHANISM_COVERAGE.md` for paper coverage, and `EXECUTION.md` for commands/failures/substitutions.

`prepare.py` performs real sequential Verilog parsing, register-cone extraction, Yosys/ABC synthesis and formal checks. `checks.py` audits representation and split integrity. `native_check.py` compiles a separate gate evaluator. `train.py` executes the frozen controls and downstream proxy tasks. `verify_results.py` independently reconstructs rank/retrieval/regression metrics from local checkpoints. `check_external_summary.py` records a truthful external-only summary correction; `report.py` compiles the outcome without selecting or retraining models.

All scripts run with `../.venv/bin/python` from this directory, or the explicit repository-root commands in `EXECUTION.md`. Prior results live outside this directory; interrupted closure protocol 1.0 is preserved in `attempt1/`; corrected protocol 1.1 outputs are in `results_v1_1/`. Do not combine their results or rerun to seek favorable metrics. Preparation regenerates current data files, so preserve snapshots before future changes.

The summaries are coarse behavioral heuristics, explicitly not LLM summaries. Targets are Boolean gate count and combinational gate depth, explicitly not physical PPA. Models start randomly. This is a mechanism port plus new baselines, not original model execution or original paper reproduction. No weights, paid services or external model calls are used.

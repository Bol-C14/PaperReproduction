# Exact commands and evidence

Working directory `/workspace/PaperReproduction`, existing branch
`reproduction/autosizer-icml2026`. No repository initialization or checkout of other
paper branches occurred in this tranche. No dependencies or assets were downloaded.
Relevant instructions were searched in workspace ancestors, `.agents` and the
existing repository; no AGENTS.md/SKILL.md applied.

Protocol/code freeze commit: `118247d5917e9b7bb430f90bbe7281d17357276a`.
Post-search validation/checker code was committed at `d0a667b` before those runs.
The simulation engine and search policy were unchanged after the freeze.

```sh
python -m py_compile projects/autosizer/experiments/optimization_v1/scripts/*.py
python projects/autosizer/experiments/optimization_v1/scripts/search.py pilot > projects/autosizer/experiments/optimization_v1/logs/pilot_driver.log 2>&1
python projects/autosizer/experiments/optimization_v1/scripts/check_pilot.py
python projects/autosizer/experiments/optimization_v1/scripts/search.py main > projects/autosizer/experiments/optimization_v1/logs/main_driver.log 2>&1
python projects/autosizer/experiments/optimization_v1/scripts/validate_and_oracle.py > projects/autosizer/experiments/optimization_v1/logs/validation_oracle_driver.log 2>&1
python projects/autosizer/experiments/optimization_v1/scripts/independent_checks.py > projects/autosizer/experiments/optimization_v1/logs/independent_checks.log 2>&1
python projects/autosizer/experiments/optimization_v1/scripts/aggregate.py > projects/autosizer/experiments/optimization_v1/logs/aggregate.log 2>&1
python projects/autosizer/experiments/optimization_v1/scripts/controller_adapter.py > projects/autosizer/experiments/optimization_v1/logs/controller_bridge_checks.log 2>&1
```

All 1,029 subprocess commands, timeouts, UTC timestamps, candidate indices, width
values, code/deck hashes and outcome records are in `logs/attempts/NNNN/attempt.json`.
Each invokes the already verified local `ngspice -n -b circuit.spice` with the
recorded deck/cwd, explicit minimal environment, 20 s wall/15 s CPU/2 GiB child
limits. Parent numerical libraries are limited to one thread during search.
Stdout/stderr and source/refined decks are retained; selected validation folders
also retain DC/transient/AC exports. No request was sent to an LLM.

The stage gate is closed in `results/PHASE_CLOSED.json`; no search, validation or
oracle command may launch further simulations after closure without a new
authorized protocol. Independent rescoring and reading preserved data launch none.
`aggregate.py` may regenerate local analytical outputs, but must not be interpreted
as permitting live model use or new experiments.

Source/config/version pins are in `configs/protocol.json` and
`configs/execution_manifest.json`. `results/comparison.json`, `analysis_per_run.json`,
`paired_differences.json`, `oracle_summary.json`, `validation_summary.json`,
`correctness_checks.json`, `independent_waveform_checks.json` and
`resource_ledger.json` provide machine-readable evidence. Pilot outputs are kept
separately from the main comparison. All prior preflight evidence is preserved.

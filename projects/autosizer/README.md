# AutoSizer P08

The latest tranche closes a real CPU-only numerical optimization/feedback loop:
four matched-budget controls, two released circuits, three seeds, independent
winner validation and a held-out inverter grid. It used 1,029 ngspice attempts,
zero new downloads and zero model calls. Live LLM-generated circuit understanding
and decisions remain unexecuted; this is not reproduction of the paper's LLM
controller or 24-task result.

* [Optimization results and remaining mechanism gap](experiments/optimization_v1/RESULTS.md)
* [Mechanism coverage map](experiments/optimization_v1/MECHANISM_COVERAGE.md)
* [Live-controller interface boundary](experiments/optimization_v1/CONTROLLER_INTERFACE.md)
* [Optimization protocol and commands](experiments/optimization_v1/COMMANDS.md)

The earlier six-attempt fixed-point preflight is preserved below as a separate
historical phase; its reference inverter was power-infeasible and its OTA point
was feasible. No old result was overwritten or pooled into the new comparison.

* [Results and limitations](RESULTS.md)
* [Frozen pre-execution protocol](PROTOCOL.md)
* [Pinned commands and setup](COMMANDS.md)
* [Attempt ledger](logs/attempts.json)
* [Independent vector checks](results/vector_crosschecks.json)
* [Resource ledger](results/resource_ledger.json)
* [Prior asset audit](provenance/ASSET_AUDIT.md)

This branch inherits the existing Aspen base unchanged. All AutoSizer additions
are confined to this directory. No external push or PR was performed.

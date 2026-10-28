# AutoSizer P08

Bounded CPU-only simulator and measurement preflight, completed with six ngspice
attempts. One released OTA reference point is nominally feasible; the inverter
reference point remains infeasible under both original and integrated power
measurements. No LLM or optimizer was run; this is not reproduction of AutoSizer's
reflective mechanism or its 24-task result.

* [Results and limitations](RESULTS.md)
* [Frozen pre-execution protocol](PROTOCOL.md)
* [Pinned commands and setup](COMMANDS.md)
* [Attempt ledger](logs/attempts.json)
* [Independent vector checks](results/vector_crosschecks.json)
* [Resource ledger](results/resource_ledger.json)
* [Prior asset audit](provenance/ASSET_AUDIT.md)

This branch inherits the existing Aspen base unchanged. All AutoSizer additions
are confined to this directory. No external push or PR was performed.

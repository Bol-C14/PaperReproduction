# P07 VeriThoughts: bounded CPU evaluator pilot

Local branch `reproduction/verithoughts-neurips2025`. No external push or PR.

- [Pilot result and interpretation](P07_VeriThoughts/pilot/RESULTS.md)
- [Frozen protocol](P07_VeriThoughts/pilot/PROTOCOL.md)
- [Reproduction commands](P07_VeriThoughts/pilot/REPRODUCE.md)
- [Setup and resource ledger](P07_VeriThoughts/pilot/SETUP_AND_RESOURCES.md)
- [Machine results](P07_VeriThoughts/pilot/runs/attempt1/results.json)
- [Initial asset audit](P07_VeriThoughts/ASSET_AUDIT.md)

The unchanged evaluator and faithful port agreed on eight frozen synthetic controls. A bounded pass missed a delayed sequential divergence, empty module discovery accepted invalid candidate HDL, and per-module matching rejected a top-level-equivalent helper rewrite. These are controlled mechanism findings, not measured error rates in the released dataset. No model, API, GPU, or training was used.

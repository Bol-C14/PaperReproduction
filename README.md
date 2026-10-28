# P07 VeriThoughts: bounded CPU evaluator pilot

Fresh generation: [one public PWM question produced a fresh candidate accepted by the original 50-step checker](P07_VeriThoughts/generation_plan/RESULTS.md). One API call cost USD 0.0005443; the frozen initial-pass stop rule left feedback and retry unexecuted.

CPU phase: [Mac/APRIL fixed-benchmark continuation](P07_VeriThoughts/continuation/RESULTS.md) verifies the exact 291-row file, completes all 32 preregistered frontend samples, and checks a real stored pair with negative controls. New work remains local; training and feedback comparisons remain unexecuted.

Local branch `reproduction/verithoughts-neurips2025`. No external push or PR.

- [Pilot result and interpretation](P07_VeriThoughts/pilot/RESULTS.md)
- [Frozen protocol](P07_VeriThoughts/pilot/PROTOCOL.md)
- [Reproduction commands](P07_VeriThoughts/pilot/REPRODUCE.md)
- [Setup and resource ledger](P07_VeriThoughts/pilot/SETUP_AND_RESOURCES.md)
- [Machine results](P07_VeriThoughts/pilot/runs/attempt1/results.json)
- [Initial asset audit](P07_VeriThoughts/ASSET_AUDIT.md)

The unchanged evaluator and faithful port agreed on eight frozen synthetic controls. Empty module discovery accepted invalid candidate HDL, establishing a scoped input-validation defect. Delayed divergence illustrates the disclosed bounded-check limitation; rejecting a helper-omitting rewrite is expected under the paper's per-module contract. These observations do not establish published errors or dataset error rates. See the [adversarial claim review](P07_VeriThoughts/pilot/ADVERSARIAL_REVIEW.md). No model, API, GPU, or training was used.

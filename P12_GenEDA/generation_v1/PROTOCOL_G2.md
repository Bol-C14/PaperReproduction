# Frozen extension G2 — language-prior sufficiency

Frozen before any held-out G1 metric was computed or inspected. The first G1 seed's **training-only** diagnostics had language NLL about 2.40 and repetitive, malformed text even on training records. This cannot isolate circuit-representation quality from an inadequate decoder language prior. G1 results and the seed-23 pre-training manifest-check failure are retained.

G2 retains the same model architecture, tokenizer, data/family split, caps, seeds 17/23, learning rates, five arms, interventions and independent evaluator. Increase language pretraining from 160 to **1600 steps** and the two task stages from 40/80 to **120/240 steps**. No changes based on held-out quality, no additional hyperparameter search, no early stopping by test metrics. Exactly one full G2 attempt per seed after fixing the JSON-list/Python-tuple comparison defect. Both protocols use the same source-data manifest; assert its semantic identity before training.

Source changes merely parameterize budgets/output directories and make manifest comparison JSON-canonical. The first implementation snapshot and failure log remain inspectable. Shared pretraining remains within seed, examples/updates remain matched between arms, and the non-aligned control's differing trainable parameter count remains disclosed.

Projected CPU model time is below 30 minutes from the measured G1 pilot; keep the two-hour continuation cap and existing CPU/RAM. No external decoder, API, gate access or model download is introduced. G2 is still a tiny decoder trained from scratch on one project family; fluent templates or improved train loss alone cannot establish semantic alignment. Stop after the two fixed-budget seeds and independent scoring, including scientific negatives.

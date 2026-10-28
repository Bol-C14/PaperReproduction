# G1 implementation corrections before the full run

The 10-step feasibility pilot exercised only answer-text language pretraining and completed in 1.62 seconds with peak RSS 317,488KiB. No alignment/generation quality outcome was used for selection. Its original manifest is preserved as `results/split_manifest_pilot.json`.

Before full training, a prompt assembly whitespace typo (`This designis` instead of `This design is`) was corrected. This changes prompt formatting, not examples, labels, grouping or targets. The final manifest is regenerated and frozen before the first full run.

The shuffled-control permutation was strengthened to a seeded single cycle, ensuring every training row receives a different row's vector. This is a design-integrity correction before any shuffled-control outcome; no quality-based tuning occurs.

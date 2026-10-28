# TRACE closure results — all prespecified comparisons

FSL means function-shift learning. Few-shot support adaptation is a separate added evaluation; official checkpoint comparisons are transfer with unknown inherited pretraining cost.

Primary score is the mean terminal-output MAE across four held-out families; ± is sample SD across three seeds, not a confidence interval. Family data and seeds are paired. No best-seed or best-family selection.

| Track | Stage | Macro output MAE ± SD | Macro non-PI MAE ± SD | Worst family output MAE | Adaptation time per family (s) |
|---|---|---:|---:|---:|---:|
| scratch_pretrain/direct | no_adapt | 0.115395 ± 0.009236 | 0.076228 ± 0.002839 | 0.145564 | 0.000 |
| scratch_pretrain/direct | adapt | 0.083105 ± 0.008398 | 0.055397 ± 0.005687 | 0.104864 | 1.011 |
| scratch_pretrain/fsl | no_adapt | 0.048243 ± 0.001094 | 0.031990 ± 0.003489 | 0.071678 | 0.000 |
| scratch_pretrain/fsl | adapt | 0.047170 ± 0.001908 | 0.031978 ± 0.002865 | 0.068113 | 0.983 |
| transfer_official/fsl | no_adapt | 0.044879 ± 0.000000 | 0.028271 ± 0.000000 | 0.079718 | 0.000 |
| transfer_official/fsl | adapt | 0.041842 ± 0.000215 | 0.027760 ± 0.000043 | 0.065954 | 0.978 |
| transfer_random/fsl | no_adapt | 0.300723 ± 0.214000 | 0.156644 ± 0.085956 | 0.422234 | 0.000 |
| transfer_random/fsl | adapt | 0.218462 ± 0.177123 | 0.116639 ± 0.066433 | 0.337513 | 0.973 |

Local-only (no learned weights): macro output MAE **0.049009**, macro non-PI MAE **0.028684**.

| Track | Family | Output MAE no-adapt → adapt (seed mean) | Non-PI MAE no-adapt → adapt | FSL oracle-predecessor output MAE after adaptation |
|---|---|---:|---:|---:|
| scratch_pretrain/direct | ripple_carry | 0.080585 → 0.072469 | 0.053171 → 0.045453 | n/a |
| scratch_pretrain/direct | comparator | 0.145564 → 0.091933 | 0.073313 → 0.045111 | n/a |
| scratch_pretrain/direct | priority_selector | 0.111101 → 0.104864 | 0.122831 → 0.088258 | n/a |
| scratch_pretrain/direct | reconvergent_mux | 0.124330 → 0.063151 | 0.055596 → 0.042766 | n/a |
| scratch_pretrain/fsl | ripple_carry | 0.024623 → 0.024018 | 0.009439 → 0.008907 | 0.003112 |
| scratch_pretrain/fsl | comparator | 0.050618 → 0.050118 | 0.009221 → 0.008793 | 0.043226 |
| scratch_pretrain/fsl | priority_selector | 0.046051 → 0.046431 | 0.091505 → 0.091612 | 0.003666 |
| scratch_pretrain/fsl | reconvergent_mux | 0.071678 → 0.068113 | 0.017796 → 0.018598 | 0.046372 |
| transfer_official/fsl | ripple_carry | 0.020094 → 0.020119 | 0.005164 → 0.005189 | 0.000022 |
| transfer_official/fsl | comparator | 0.041438 → 0.043004 | 0.005084 → 0.005392 | 0.035242 |
| transfer_official/fsl | priority_selector | 0.038265 → 0.038291 | 0.086621 → 0.086642 | 0.000023 |
| transfer_official/fsl | reconvergent_mux | 0.079718 → 0.065954 | 0.016215 → 0.013815 | 0.050942 |
| transfer_random/fsl | ripple_carry | 0.251802 → 0.272169 | 0.135785 → 0.114378 | 0.118464 |
| transfer_random/fsl | comparator | 0.422234 → 0.337513 | 0.152800 → 0.139611 | 0.077045 |
| transfer_random/fsl | priority_selector | 0.215392 → 0.086955 | 0.178613 → 0.111633 | 0.043573 |
| transfer_random/fsl | reconvergent_mux | 0.313465 → 0.177211 | 0.159379 → 0.100935 | 0.057473 |

## Diagnosis without metric selection

FSL teacher-predecessor scores below use true intermediate marginals. They isolate one-step residual error and are unavailable at real inference. A difference from recursive output error is evidence consistent with propagation; it is not an independently controlled causal attribution.

| FSL track | Stage | Recursive output MAE | Oracle-predecessor output MAE | Mean absolute recursive–oracle prediction gap | Outside-range nodes / evaluated nodes |
|---|---|---:|---:|---:|---:|
| scratch_pretrain | no_adapt | 0.048243 | 0.024587 | 0.027443 | 0 / 6432 |
| scratch_pretrain | adapt | 0.047170 | 0.024094 | 0.027051 | 0 / 6432 |
| transfer_official | no_adapt | 0.044879 | 0.021375 | 0.024984 | 0 / 6432 |
| transfer_official | adapt | 0.041842 | 0.021557 | 0.023781 | 7 / 6432 |
| transfer_random | no_adapt | 0.300723 | 0.093555 | 0.217818 | 879 / 6432 |
| transfer_random | adapt | 0.218462 | 0.074138 | 0.154148 | 676 / 6432 |

Per-depth MAE/teacher MAE and counts are retained for every seed/family/stage in summary.json. Per-parent records and raw predictions are retained in predictions/.

## Ordered-role controls

Exact MUX target delta is 0.54 for the select/data swap; exact AND target delta is zero. Predictions below are reported, not asserted accurate.

| Track | Mean MUX prediction delta | Mean absolute AND port-swap difference |
|---|---:|---:|
| scratch_pretrain/direct | 0.402776 | 0.028166 |
| scratch_pretrain/fsl | 0.539962 | 0.000107 |
| transfer_official/fsl | 0.540000 | 0.000000 |
| transfer_random/fsl | 0.545014 | 0.013940 |

## Cost

Valid run: 158.65 s wall, 159.69 s process CPU, peak RSS 357684 KiB, 2400 optimizer updates, one CPU thread, CUDA initialized=False.
Six 240-update pretraining runs consumed 90.48 s; 48 twenty-update family adaptations consumed 47.34 s. Saved batched-query inference times exclude adaptation, exact-label generation and model loading.
Batched inference (48 query graphs/family) median 0.0472 s. All models have417,761 parameters (including source unused parameters).

Two interrupted harness attempts are archived and excluded from aggregate scores. Their consumed resources are additional to this valid-run budget; see ATTEMPTS.jsonl and RESOURCE_LEDGER.md. Original checkpoint inherited training cost is unknown. No new package/dataset/checkpoint downloads or paid resources were used in this tranche.

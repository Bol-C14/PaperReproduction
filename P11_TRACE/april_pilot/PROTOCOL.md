# Official PM predictive CPU pilot, frozen before data inspection

Base reproduction branch HEAD: 2f33a6bc2135c521af86a0277e3cd3ce8a79b66d.
Official source: b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70.
Dataset revision: 5477721c19229f8a21dc2d789a571becb55fbc0f; PM predictive
iccad_dc_pm.npz SHA256 6a05e443aeb824b0b47f53e8355572fbafc3aa18f400540ce0306a3791e6ed36.
Checkpoint SHA256 19fe1e95857072e5eb838802ee21260ffe48345df85785f9f6ddd0e784cad7c0.

Use the official seed208 torch permutation and 90/10 validation split. In the
first32 validation entries select the first8 circuits with at most4096 nodes;
record every size exclusion and selected name before inference. No score-based
selection. One graph per forward, CPU two threads, 15-minute inference limit.
This departs from official batch128/drop_last evaluation and is a bounded subset,
not a benchmark score. Checkpoint training overlap with validation is unknown.

Strictly load official weights into unchanged AST-extracted official classes.
Use official parsing tensor semantics without PyG/Lightning orchestration. Preserve
stored edge order, input grouping and all labels. Verify assumptions; stop if invalid.
No training, new synthetic data, LLM calls or GPU. Retain all raw predictions.

Compare (1) unchanged original reconstruction, (2) inclusive deepest-level correction,
(3) zero residual/local independence. For mechanism diagnostics separately zero
positional embeddings and freeze predecessor representations at their initial state
instead of propagating computed intermediate states. These are inference lesions,
not retrained architecture ablations or causal evidence about training benefits.
Report residual prediction change and residual MAE, so analytic local role dependence
cannot be mistaken for learned operand-role performance. Preserve original model.

Report all non-PI and terminal-node MAE, per-circuit values, global weighted MAE,
raw ranges, and independent scalar truth-table reconstruction agreement. No final
clamping, hyperparameter selection, adaptation or repeat of closed v1/v2 matrices.

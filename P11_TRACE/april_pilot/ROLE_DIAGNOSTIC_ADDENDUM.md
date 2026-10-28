# Operand position diagnostic supplement

Added after the primary eight-circuit evaluation, before supplementary results.
The primary no-position lesion also removes the operator positional vector, so it
does not isolate distinctions among operand roles alone. A single further forward
pass per selected circuit collapses positions1–9 to the original position1 vector,
preserving position0 (the operator). Data selection, source, checkpoint, labels and
recursive reconstruction stay unchanged. No training or tuning.

Record residual MAE and probability MAE, and independently reverse operands within
every target edge group. With equal operand positional vectors the neural shift
must be invariant to these reversals within1e-5. This is a structural control, not
a correctness score for swapped circuits: the swapped circuit's true global labels
are not available. All reversals retain source identities and target grouping.

This post-hoc lesion tests dependence of this checkpoint on operand distinctions.
It does not estimate the benefit of training with positional roles, and it does not
repair or resolve the previously established equal-marginal PI-identity aliasing.

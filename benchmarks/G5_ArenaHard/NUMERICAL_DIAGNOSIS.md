# Numerical consistency diagnosis

The retained third replay attempt failed the original `error < 0.0001` percentage-point assertion for the full primary cohort. This threshold was **not widened**. The pilot alone had passed, with discrepancy 3.10e-7 percentage points.

For this star comparison graph, every candidate is compared only with the fixed GPT-4-0314 anchor. Its unregularized Bradley–Terry maximum-likelihood win probability against the anchor equals `(candidate weighted wins + 0.5 * weighted ties) / weighted comparisons`. Strong preferences contribute weight 3. The two games must first be oriented to the same candidate.

`analysis/diagnose.py` independently parses raw verdicts, counts weighted candidate/baseline wins and ties, verifies every upstream-converted count, and solves each scalar likelihood score equation with Brent root finding. Raw-count and scalar-root estimates agree to <1e-10 percentage points. This excludes a likelihood-normalization, weighting or data-alignment explanation for the observed discrepancy.

Historical `compute_mle_elo` uses sklearn's unregularized L-BFGS fit with `tol=1e-8`. Its maximum discrepancy from the independently verified count solution is **0.000764376 percentage points**. Increasing `max_iter` from 100 to 2000 and changing `tol` to 1e-12 still stops after 11 iterations with the same estimates. Thus the iteration budget or that gradient-tolerance change alone does not resolve it.

Solving the **same matrix mean binary log-loss**, fixing the baseline coefficient at zero, with SciPy L-BFGS-B `ftol=1e-15`, `gtol=1e-12`, gives maximum discrepancy **4.18617e-8 percentage points**, gradient infinity norm **4.64015e-11**, and 12 iterations. Its reported stopping reason is relative reduction of function value. This supports function-convergence precision as the source of the historical numerical discrepancy. The reconstructed strict diagnostic initially used the wrong sign in its final rating conversion; those failed diagnostics are retained, and the sign was corrected before acceptance.

Accepted ranking estimates use the exact star-graph MLE, with unchanged upstream verdict conversion and bootstrap row sampler. Each full-primary and matched/order calculation is also validated against independent scalar likelihood roots, retaining the original threshold. This is a documented numerical implementation deviation, not a claim of bitwise historical reproduction. Unchanged historical fit/bootstrap outputs remain separate under `*_upstream_original_*` filenames. Both historical and exact 100-round row bootstrap outputs separate **167/190 pairs**; the correction did not change that count.

Evidence: `metrics/numerical_diagnosis.json`, `metrics/verification.json`, `logs/replay-attempt3-numerical-assertion.log`, and retained diagnostic failure logs. No raw answer text was executed or sent to an additional model.

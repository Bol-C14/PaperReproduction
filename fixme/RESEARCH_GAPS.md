# Research gaps and interpretation

The paper provides a useful taxonomy and an executable-oracle emphasis. This
pilot tests evaluators, not model capability. It neither verifies nor refutes
the original model rankings or aggregate results.

1. **Version correspondence:** 482 pinned directories versus 747 published tasks.
   Need the exact paper-time commit, full dataset manifest and absent multimodal
   examples before claiming aggregate comparability. New README model results
   cannot substitute for the original ten-model experiment.
2. **Metric reconstruction:** no original per-candidate outputs, random seeds,
   complete hyperparameters or exact coverage databases were reconstructed.
   Published 38.15% mean functional and 65.73% syntax rates remain reference claims,
   not reproduced measurements. No synthetic aggregation or digitized bars are used.
3. **Evaluation strength:** current Text RTLFix labels fragment matching as functional
   pass without applying code. A pair-only response demonstrates that limitation.
   Current generic simulation success can accept an empty testbench; pass-marker
   precedence can also override printed error text. These observations concern
   this pinned evaluator, not necessarily the toolchain used for the paper.
4. **Assertion adequacy:** proving a true invariant does not show useful specification
   coverage. Constant properties remain unknown because they cannot kill the selected mutant; reset assumptions, vacuity,
   property counts, reachability and mutation sensitivity need explicit tests.
   This pilot handles only one combinational CRC relationship.
5. **End-to-end causality:** the paper explicitly decouples subsets. Its reported
   cross-metric correlations motivate hypotheses, but do not identify within-task
   causal error propagation. A next experiment should align designs and randomly
   intervene on specification interpretations while holding model/tool seeds fixed.
6. **Coverage ablation:** test weaker versus enhanced TB on identical wrong models,
   pairing per-case results. This pilot kills one mux mutant, demonstrating the
   mechanism on one case without reproducing the paper's aggregate ablation.
7. **Portability:** differential VCS/Verilator/Icarus runs on sequential/X/Z cases
   and VC Static/Yosys temporal property comparisons are needed. Lack of proprietary
   tools is explicitly unresolved; unsupported features must retain unknown states.

Next bounded expansion: two L2/L3 cases per family, a clock/reset case, a wide DPI
port, and one meaningful temporal property with supported free formal frontend.
Only expand after oracle disagreement and failure classifications are understood.

Full-data reconciliation is now in DATA_COVERAGE.md. All five public history trees
are identical; 265 directory-count deficits are multimodal, 50 present MM keys are
empty placeholders, and explicit overlays recover 26 specs plus one filename
matching failure. This narrows the remaining asset problem without proving why
original assets are absent. Generic EDA coverage beyond the four pilot design
inputs remains open; the read-only all-case audit is not an EDA benchmark run.

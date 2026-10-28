# Post-run diagnostic, no additional fitting

The first G2 seed's standalone-answer language-pretraining NLL decreased to about 0.57, while conditional task-training NLL remained around 2.6 and training generations remained malformed. This creates an unresolved decoder-context adequacy issue rather than evidence isolating circuit-feature utility.

After both fixed G2 seeds complete, load only the checkpoints created locally in this run (safe numeric NPZ, `allow_pickle=False`). On the same first 16 frozen training rows, compare teacher-forced answer NLL with BOS-only input versus the actual signal/interface prompt and a zero graph token. Do not train, select examples by quality, change parameters or run another aligned-method budget. This contrast jointly changes context and absolute answer positions; it must not be described as isolating position embeddings or proving a specific cause. It tests whether the scratch language prior is sufficient in the conditional-generation interface.

The main generation/evaluation result remains a scientific negative or inconclusive result as supported by the controls. This diagnostic cannot rescue semantic-alignment claims.

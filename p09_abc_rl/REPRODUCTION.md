> Historical preflight record. The authorized APRIL real CPU pilot subsequently completed; see [APRIL_REPORT.md](APRIL_REPORT.md) and [APRIL_PROTOCOL.json](APRIL_PROTOCOL.json). The earlier blocker is resolved for this pilot.

# P09 bounded CPU gate — completed, behavioral pilot blocked

Branch: `reproduction/abc-rl-iclr2024`. Base: `f85c69748506854273c5816d29646d6a70f5f468`. Protocol frozen at `2026-10-28T10:35:06Z` in commit `088ba14` before tests. All changes are inside `p09_abc_rl/`; inherited ASPEN files and other branches are preserved. No push or PR.

**Outcome: seven deterministic contract tests and real-checkpoint structural loading pass. End-to-end policy inference and circuit reproduction have not run. Actual ABC evaluations: 0/20.** This is preflight/unit-gate evidence, not a numerical or behavioral reproduction of ABC-RL.

## Original, repairs and port

- `upstream/` preserves the twelve audited source/README snapshots at upstream revision `db6186cb4018963b5bc15926772c3edc0c2873f1`, plus its GPL-3.0 license. The original implementation is not edited or imported by the unit gate.
- `port/repairs.patch` and generated `port/repaired/` separately fix scorer checkpoint propagation, CPU safe/strict state loading, rollout horizon, and training-only rounding behavior. CPU device/local-BERT-path options are port conveniences. `port/build_repaired.py` reproduces these copies and the reviewable diff.
- `port/mechanism.py` and `port/retrieve.py` are small newly implemented contract helpers: cosine nearest neighbor, exponent gate and train-bank/model-identity checks. Synthetic vectors occur only in unit tests; no learned policy or circuit result is manufactured from them. They do not yet extract real graph embeddings or wire automatic retrieval through the complete upstream evaluation command.
- No novel search algorithm or method improvement is claimed. No full training or evaluation is attempted.

## What was verified

| Gate | Observed original | Repair / result |
|---|---|---|
| Supplied checkpoint in scorer | Actual AST assignment constructs `Trainer(None)` | Patched AST passes supplied model path. Separately, actual repaired Trainer strictly loads all26 keys from the downloaded real checkpoint; every loaded tensor equals the supplied tensor. |
| Rounding | Actual upstream `torch.round` expression gives gradient `[0,0]` | Repair skips rounding only while training, yielding gradient `[1,1]` in the tiny probe. Eval retains exactly the rounded output. |
| Rollout horizon | At depths0,1,8,9:11,10,3,2 commands | Repaired extracted function produces10,9,2,1. Captured ABC command construction uses deterministic RNG and a stubbed runner/log, with no EDA execution. |
| Gate and retrieval | Distance/exponent direction checked; beta0 flattens priors | Train-only manifest rejects held-out leakage, mismatched encoder/checkpoint, zero norms and malformed banks. Does not validate embedding usefulness. |
| Budget semantics | Root rollout occurs before100-row loop | Retained as documented original behavior; any future executable pilot must count initialization/baseline as actual calls. |
| Search-only interpretation | Flattened probabilities plus `argmax` chooses action0 at rollout start | beta0 alone is not proven pure MCTS. Future control must explicitly make rollout action selection policy independent. |

Rounding is a **training defect in the inspected current source**, not an immediate obstacle to running an existing policy. Removing it during inference would unnecessarily change the released encoder's values; the repair retains it in eval. Existing checkpoint history is unknown: no claim is made that it was trained by this exact source or that its graph weights were learned. Repaired future training would need retraining and is outside this phase.

Checkpoint payload:1401370bytes, SHA256 `d4747eeff16c7247acf8f1480a33f2239a1a51adaac78a0a6e915c5ba12164f5`. Loaded with PyTorch2.6.0+cpu, `weights_only=True`, `map_location='cpu'`. Its26 tensor keys match the released two-layer GCN/head module structurally. It contains no BERT state. The structural check uses explicitly fail-closed placeholders for `BertModel` and `SparseTensor`, only to permit module construction and state loading; either would throw if used for inference. That is **structural state compatibility, not end-to-end CPU inference compatibility**. Details: `results/checkpoint_inspection.json`, `results/structural_loading.json` and logs.

## Exact blocker and remaining implementation work

The required source asset `https://huggingface.co/google-bert/bert-base-cased/resolve/main/config.json` returned **HTTP403** on the first ordinary public GET. Headers/log are saved. No alternate endpoint, token, gate acceptance or retry was used. Without the exact external BERT model/tokenizer used by the released architecture, the real policy cannot produce recipe embeddings. No replacement random/zero recipe features were used. Under frozen protocol gate3, this prevents gate4 and all circuit evaluations.

Action/target/status: obtain the public `google-bert/bert-base-cased` configuration, tokenizer and weights; **denied by HTTP403**, not an automatic approval rejection. The successful safe checkpoint download and unit work are independent and complete. Required next-phase resource is an authorized local copy or ungated public mirror with verified model identity/revision. A smaller/new recipe encoder would be a separately labeled retrained mechanism port, not a compatible substitution for the current policy.

Even after that asset is supplied, `abc_py`, `torch_sparse`, the native ABC executable and a verified library/circuit loading contract still need setup. These are unresolved engineering preflight items, not demonstrated hardware incompatibilities; they were not installed after gate3 failed. Official BerkeleyABC HEAD was identified read-only as `ba65576141a5a0f605d2876ad5041e3ec7dfbf59`, but no source build/download was performed. No full inference readiness is claimed.

Before resuming, close scorer-bank drift: use a declared train-only bank, checkpoint hash and encoder identity; the exposed TTSPLIT5001 source lists22 training circuits while the paper lists23. Do not silently call either bank the checkpoint's proven training history. Reconcile beta naming/scaling, count every call and repair the baseline control. Then freeze a new timestamp/commit before any actual circuit run.

The conditional pilot remains the frozen two-circuit, three-evaluated-recipes-per-arm design, with14 synthesis calls plus4 CEC and2 reserved diagnostic calls. A real policy encoder and native equivalence checks are mandatory. Mapped7nm ADP is the paper objective; node/depth metrics would be an explicitly labeled proxy. Do not interpret observed rewards as counterfactual rewards for unchosen actions.

## Commands and evidence

From repository root, on the existing prepared environment:

```bash
python3 p09_abc_rl/port/build_repaired.py
p09_abc_rl/.venv/bin/python p09_abc_rl/tests/test_contract.py
p09_abc_rl/.venv/bin/python p09_abc_rl/tests/check_structural_loading.py
python3 p09_abc_rl/verify_artifacts.py
```

The checkpoint payload lives in ignored `p09_abc_rl/assets/nn_model.pt`; it is intentionally not committed. Re-obtain only from the pinned author-linked URL recorded in `COMMANDS.md`, then verify its hash. `configs/installed.lock` records installed distributions; pip logs record distribution filenames and public indexes. Environments/assets are ignored, while text snapshots, patch, scripts, configs, checksums, logs and results are committed. Installation/download commands and source validation are in `COMMANDS.md`. Resource usage is in `results/resource_ledger.json`.

No API/LLM calls, GPU work, training, paid resource, credential access/change, security-setting change, push or PR. No EDA metric or equivalence result exists in this phase. Lack of those results is explicit; this is not a failed reproduction claim.

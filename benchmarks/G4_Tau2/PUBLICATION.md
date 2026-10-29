# Publication boundary and history reconstruction

This package is a proposed public payload for independent review. It has not been pushed. `PUBLIC_WHITELIST.json` lists every allowed G4 path; `manifest.json` hashes every other file on that list. Files outside the list must not be included by a recursive copy of the private execution directory.

Allowed: paper/source/version hashes, original code license, evaluator-only version diff, dependency pins, sanitized disk sizes, terse official test outputs, algebra-only metric checks, six-task selection/exclusions as metadata, numeric reward projections, and a 114-row inventory containing task ID and required reward-component labels only.

Excluded: raw task assets, reference or hidden expected action sequences and arguments, expected state/assertion contents, agent/user message histories, reference tool responses, raw calibration/full-reward logs, exception bodies/tracebacks, source paper/README/CHANGELOG copies, and the original reference verifier programs. These originals and their complete commit history are retained privately for parent review. The original source/data are publicly available upstream, but availability upstream does not authorize redistributing answer material in this evaluated-agent-facing package. Neither this payload nor the private verifier directory is an evaluated-agent workspace. Only role-appropriate policy/tool/task inputs may be staged for a future agent.

`results/calibration.json` and `results/full-reward.json` are **numeric projections**, not reference trajectories. They retain every selected condition and result but cannot independently replay tool execution. Public provenance hashes and a private archive/history receipt preserve the chain to the original evidence. Independent raw replay remains a private review action. No expected action list is needed to recount component labels offline:

```sh
python3 scripts/recount_inventory.py
```

The inventory is bound to original tasks.json SHA-256 `192a2c143b3b512c37c3775fdf6c5040c33717388620c38b140c731dc6153cd7` and code commit `37199f36924c8896f5e048360691f8476cd89ba1`. Offline recount checks 114 unique IDs, 94 assertion-only and 20 assertion-plus-ACTION cases. To independently verify extraction, an authorized reviewer may pass the pinned task asset via `--source`; the script validates its hash and exact ID/label projection without printing its contents. The inventory/hash alone cannot prove correct extraction from an unavailable source asset.

Locked-SIM wording: the intentionally isolated environment component accepts no-op with reward 1; the complete official reward correctly rejects it with reward 0 because ACTION is required. Paper §3.3 does not explain these released ACTION exceptions. We make no blanket claim that the official evaluator falsely accepts the task.

Unpublished commit `a8a6c79c26cde572ee4da75aacc0e38e304f7cd0` is superseded. Its original package and delta history bundle were preserved privately before editing; archive hashes are in `logs/numeric-evidence-receipt.json`. The public replacement is reconstructed directly on clean parent `809ca20e`, not committed on top of the superseded G4 commit, so the removed G4 bytes are not ancestral. The parent receives a separate history receipt with the exact replacement head, parent, changed-path whitelist, and ancestor check. Keep original bundles and full-history exports private; any later publication must use the corrected branch and this whitelist.

No model/API execution was performed during publication correction. The original 60 controls, 60 aggregator checks, 55 official tests, 642 formula checks and $0 spend remain unchanged.

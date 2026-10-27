# F_progress versus final verification

`rollouts.csv` is a strict allow-list extraction from the archived run
`public_oss24_seed_sparse_r4_20260518_200118/baseline`. It contains 96 rows:
24 public task identifiers, four repeats per task, 51 verifier passes, and 45
failures. Rows are sorted by `(cid, task_id, repeat_index)`.

Columns:

- `passed`: final binary verifier outcome (`reward > 0`).
- `f_progress`: the archived, adjusted per-rollout progress score. This is
  `F_progress`, not the repeat-aggregated `AgentProgressQ` statistic.
- `f_progress_strict`: a post-hoc diagnostic recomputation that removes final
  outcome/verifier inputs before scoring. The copied record has `reward=0`,
  final verifier stderr and service stderr removed, and final verifier result
  fields cleared. Path grounding is then recomputed from that same scrubbed
  record. This column was not used during the reported optimization run.

The original no-monitor score is
`0.40 V + 0.20 X + 0.15 H + 0.15 E + 0.10 eta`. Its path adjustment is
`round(F_base * (0.55 + 0.45 P_path), 4)`, where `P_path` is 1.00 with no
path issue, 0.60 with a noncritical issue, and 0.15 with a critical issue.
The archived `f_progress` definition consumes the final reward and hidden
verifier output; its association with `passed` is therefore descriptive and
outcome-conditioned, not an independent predictive calibration. The strict
column is provided to make that limitation measurable.

## Provenance

The run metadata did not record a source commit. The scoring code is inferred
from the preserved clean worktree at commit
`1d2b582869afc11272e1c894e108527ca8255796` because it reproduces every
archived score exactly.

| Source | SHA-256 |
|---|---|
| `cid003/result.json` | `f53694a40e9c7dbeaab69b2229dcb3449d2a713316c3049763623c1e0bb5ecde` |
| `cid003/rollouts.jsonl` | `2afa67a35360d1625bd49948d248448ac6eef58ba8f39b05280ffdb418ab803b` |
| `cid004/result.json` | `cab9da945bfcb33149a0d5139139e6ffcbbc1b3a9acdf5783835d1931409521b` |
| `cid004/rollouts.jsonl` | `859f1130a24d064b9b6a290bdf6022f8cdd3dad58401b71903e444d0893e92f2` |
| `cid005/result.json` | `65d0fe39ef2bf400dda51feb62bfa3933ea2385e2e4702a690faa5c9351a6335` |
| `cid005/rollouts.jsonl` | `6fdc918895cea76e5d6e76cdb621e47bbdeab8fcc81b8209c2df44fec1f32098` |
| `cid016/result.json` | `e262d191e98cdd73b608119be82288a44ab02ff6a31e7e2178cc348a7247e8c1` |
| `cid016/rollouts.jsonl` | `5dd947dacd16651d56c648099747a44a7d11e12d16e306114aa17041c9b4bf60` |
| `eval/convert_rollouts.py` | `dd5097eee4a5d7d6450e3819957e2dc55aeb73d2a2edd06f818f9966d80a245f` |
| `optimizer/path_grounding.py` | `d75423377310a728c08078fff708cce3aabe59b9f7fd94493b381b518532d9ab` |
| `optimizer/fitness.py` | `82d6d44cf07888aa3d8e710b3fae4bf2a6b0821624ee2ed1bbae15956291b5d4` |

The raw rollout JSONL files are intentionally excluded because they contain
complete prompts, agent trajectories, tool arguments and outputs,
hidden-verifier logs, response identifiers, internal endpoints, and absolute
local paths. The result JSON files are also excluded because they contain stale
absolute rollout paths and many fields outside this evidence allow-list.

Canonical `rollouts.csv` SHA-256:
`9f9e13f02db5c47ba704ce18046d25194dc2a280f377e78659703bdc06203338`.

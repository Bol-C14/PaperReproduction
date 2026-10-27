# Contextual 24-task baseline outcomes

`outcomes.csv` contains the 24 public task identifiers and binary outcomes in
the paper's matched OSS-runnable baseline table. A value of 1 means that the
single reported attempt passed the final verifier; 0 means it did not. The file
contains no prompts, traces, verifier output, failure notes, or harness data.

The three columns do not have equal provenance:

- `cvdp_pass` is independently recoverable from the preserved run
  `public_oss24_seed_baseline_20260511_211223`. Only the six `per_task` rows in
  each of cid003, cid004, cid005, and cid016 are used. The launcher also
  produced unrelated CID outputs, which are excluded here. The exact result is
  9/24: 4/6, 2/6, 1/6, and 2/6 by CID. The preserved launcher selected an
  unpinned `:latest` verifier image, so the verifier image is not immutably
  reconstructible even for this best-preserved column.
- `codex_pass` is reconstructed from the 24/24-complete summary, driver log,
  and corrected-run launch event retained in an internal authoring-session
  record after the original run directory was lost. It gives 12/24: 4/6, 2/6,
  2/6, and 4/6 by CID, with no recorded runner failures or timeouts. The launch
  invokes the surviving runner on the exact public 24-task manifest with one
  repeat, a 30-turn soft cap, no injected skill, and no model or
  reasoning-effort override. The runner's clean run-scoped configuration
  therefore supplies its defaults: GPT-5.5 and `high` reasoning effort. The
  allow-listed reconstruction is recorded in `codex_launch_provenance.json`.
  The corrected verifier image was also selected through a mutable `:latest`
  tag without a retained digest. The exact Codex CLI build and complete
  per-attempt event streams are not preserved, so these outcomes remain
  contextual rather than fully independently auditable.
- `claude_pass` is reconstructed from a collaborator-supplied 100-task result
  and complete failed-task list, filtered to these 24 identifiers. It gives
  12/24: 5/6, 3/6, 2/6, and 2/6 by CID. No local raw report, traces, exact model
  configuration, or verifier records survive. These outcomes are therefore
  collaborator-reported contextual data, not a fully auditable matched run.

## Exact CVDP sources

| Source | SHA-256 |
|---|---|
| `cid003/result.json` | `b63fe5561c3ca9f92be9c9a5ba1652c0470fd6d323d12b4af884219d30204c39` |
| `cid004/result.json` | `b26fa878be97195bfa5ff29994d3b1880fcc78976a3b7d441e2eb070fdfb895b` |
| `cid005/result.json` | `9822f6a2d70c260e467443f73411f7371852849fc16a4449544465111cf4ab1a` |
| `cid016/result.json` | `bac14f8e9bd36da096d8b06ac405283f4f2b25bd34a1efafa4f4c35bd6c4ea43` |
| `run_metadata.json` | `846b7077a01e1deb4ed5841d3e5a42dc81cc0dca39cacc108cc29aaa18e770d3` |
| `materialized/cid_splits_manifest.json` | `7868a13ff4ff0203d7f72142372160533a0bf77a14bf45b1e85ffd4202080d04` |

The surviving Codex runner has SHA-256
`6cae128d11afd12c334b47e7a6e3d82ba002cac3e17e97f84e8d469b80b19151`.
This hash was computed retrospectively from the separately retained source; it
was not embedded in the original launch manifest.
The retained authoring-session JSONL has SHA-256
`a1dabd543e3a3cb346ce2c2c07eba10611697ab9a50f5db5e5114c0effe90506`.
Raw CVDP rollouts, the private authoring-session contents, and private
benchmark material are deliberately excluded from this release.

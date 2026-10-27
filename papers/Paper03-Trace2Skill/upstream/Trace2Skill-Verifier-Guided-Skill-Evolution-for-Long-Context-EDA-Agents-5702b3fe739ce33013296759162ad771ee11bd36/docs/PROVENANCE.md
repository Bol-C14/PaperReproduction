# Source and experiment provenance

There is no single clean historical commit that represents both paper
conditions. Every original launch recorded a dirty worktree. This public tree
therefore uses the recovered C4 implementation as the portable superset and
disables runtime feedback to express C3.

## C3

- Closest recoverable implementation: commit
  `1d2b582869afc11272e1c894e108527ca8255796`.
- Three primary runs recorded initial clean base
  `d091581d2685448ed46516d64f783f24777ea42a` plus uncommitted changes.
- All eight archived C3 seed-skill hashes match commit `1d2b582` exactly, and
  completed `run_config.json` files provide the parameter ground truth.
- The exact non-skill C3 dirty state was not fully recoverable. C3 is therefore
  a high-confidence reconstruction, not a bit-identical source snapshot.

## C4

- Clean base: `90afe0fcee8e61fc8461992bbe4731674715cf34`.
- The surviving launch worktree supplied a 14-file tracked patch.
- Recovered patch SHA-256:
  `14f6b93338293ef01ac7bebf3882843df35c8db765222175d6cbd2243a2e6623`.

Only the needed, path-portabilized source was moved into this new Git history.
Historical repository history, generated data, model exchanges, and unrelated
experiments were deliberately excluded.

## Dataset and models

- Public CVDP dataset revision:
  `5b807d945f6a99aa645f7e43a64a2115e281b4bf`.
- Recorded rollout alias: `azure/anthropic/claude-opus-4-6`.
- Recorded mutation alias: `azure/anthropic/claude-sonnet-4-5`.
- Recorded oracle alias: `azure/openai/gpt-5`.

The aliases identify the routing names recorded in May 2026, not immutable
model snapshots. The concrete endpoint and credentials are excluded. No
provider-side sampling seed or deployment revision was retained.

The 16 archived C3/C4 task runs were launched and completed between
2026-05-14T06:06:37Z and 2026-05-18T17:38:04Z. The bundled NeMo Gym tree
reports version `0.2.0rc0`. Its exact upstream Git revision was not retained;
the repository therefore distributes the complete recovered source used by
this artifact rather than claiming an unverifiable upstream commit. The
vendored `nemogym/` subtree has Git tree
`e4eaa02a419f669da1566ed398e7ae8e84933a5d`; the nearest recoverable fork
source is commit `1cbd905e9ebaf1ad8914eaac7675439e6521238d` plus local
modifications, and is not claimed as the canonical NVIDIA upstream revision.

## Contextual native-Codex baseline

The public OSS24 evidence includes an allow-listed reconstruction of the
corrected native-Codex launch in
`artifacts/paper-results/evidence/oss24/codex_launch_provenance.json`. A
retained authoring-session launch event ties the exact 24-task manifest to the
surviving runner, one attempt per task, a 30-turn soft cap, no injected skill,
and the runner defaults of GPT-5.5 with `high` reasoning effort. The raw
session, original attempt directory, and complete event streams are excluded;
the exact Codex CLI build is not independently recoverable. The corrected
verifier image used a mutable `:latest` tag without a retained digest, and the
runner hash was computed retrospectively rather than embedded at launch. The
reported 12/24 result is therefore a contextual baseline, not a fully
reproducible run.

## Historical and current prompt trees

The historical C3/C4 manifest records 22 Markdown paths, including
`skills/README.md`. The current public `skills/` tree has the same 22 paths.
Twenty-one files match the historical SHA-256 values exactly;
`analysis/analyzer_skill.md` is a later revision, and its historical text is
not distributed. The manifest documents this distinction explicitly.

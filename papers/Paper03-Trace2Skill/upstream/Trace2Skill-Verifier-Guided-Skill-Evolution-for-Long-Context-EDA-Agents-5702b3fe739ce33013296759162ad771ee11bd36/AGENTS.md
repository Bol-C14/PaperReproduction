# Working agreements

- Keep claims grounded in `artifacts/paper-results/` and distinguish cached
  reproduction from new hosted-model rollouts.
- Never commit credentials, downloaded CVDP bundles, materialized task JSONL,
  raw rollout conversations, hidden-verifier logs, containers, or run outputs.
- Store generated data under `data/` and runs under `runs/`; both are ignored.
- Do not stop unrelated NeMo Gym, Ray, Docker, or optimizer processes.
- Preserve the C3/C4 provenance in `docs/PROVENANCE.md` when changing runtime
  code or paper configurations.
- Run `./scripts/check_public_release.sh` before every release commit.


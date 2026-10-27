# Trace2Skill: Verifier-Guided Skill Evolution for Long-Context EDA Agents

Official code and artifact repository for the MLCAD 2026 paper by Zijian Du
and Nathaniel Pinckney (NVIDIA). The paper is accepted and forthcoming.
The immutable artifact snapshot is identified by
[Zenodo DOI 10.5281/zenodo.21513682](https://doi.org/10.5281/zenodo.21513682).

Trace2Skill evolves natural-language skills for long-context chip-design
agents. A task-local evolutionary algorithm evaluates candidate skills through
real CVDP rollouts, summarizes execution traces, mutates the surviving skill,
and repeats. The C4 condition adds a bounded, sanitized runtime-verifier
feedback tool; C3 uses only the final sparse reward.

## What is included

- The recovered paper implementation of the optimizer and the C4 dense
  verifier path.
- Portable C3-sparse and C4-dense run preparation for the eight paper tasks.
- A pinned downloader for only the public CVDP v1.1.0 no-commercial files
  needed by those tasks.
- Setup, container-build, smoke, launch, reporting, and release-audit scripts.
- Sanitized cached evidence sufficient to recompute the reported C3/C4 results.
- Two real, content-free C3/C4 action traces with provenance commitments and
  allow-listed verifier scalars; see
  [`artifacts/rollout-examples/`](artifacts/rollout-examples/).

The repository intentionally contains no credentials, raw model
conversations, hidden verifier material, benchmark bundles, materialized
repositories, virtual environments, run checkpoints, or container images.

## Reported result

| Condition | Runtime feedback | Passes | Pass rate | Tasks solved | AgentQ |
|---|---:|---:|---:|---:|---:|
| C3 | sparse final reward | 173 / 640 | 27.03% | 3 / 8 | 0.522825 |
| C4 | dense, at most 3 executions/rollout | 215 / 640 | 33.59% | 6 / 8 | 0.565676 |

Recompute these values from the packaged evidence without network access:

```bash
python3 scripts/validate_paper_results.py
```

The validator also reports task, generation, individual, pass rate, SelectQ,
SkillQ, AgentProgressQ, AgentVarianceQ, and AgentAdherenceQ. See
[`docs/RESULTS.md`](docs/RESULTS.md) for definitions and important caveats.

## Public pipeline quick start

Requirements: Linux, Python 3.12, Git, Docker 24+, roughly 25 GB of free space,
and an OpenAI-compatible endpoint serving the configured rollout, mutation,
and oracle models.

```bash
cp .env.example .env
# Edit .env without committing it.
./scripts/setup.sh
./scripts/fetch_cvdp_subset.py
./scripts/build_cvdp_image.sh
./scripts/run_smoke.sh

# Generate the exact eight task-local paper configurations.
envs/unified/bin/python scripts/prepare_mlcad_per_task_oss24_runs.py --condition c3-sparse
envs/unified/bin/python scripts/prepare_mlcad_per_task_oss24_runs.py --condition c4-dense

# Each command runs eight task-local optimizers sequentially.
./scripts/run_mlcad_per_task_oss24_batch.sh c3-sparse
./scripts/run_mlcad_per_task_oss24_batch.sh c4-dense
```

A full condition is 640 long-context rollouts. The original runs consumed
approximately 374 million recorded tokens and 42.11 summed task-hours for C3,
and 520 million tokens and 48.03 task-hours for C4. Start with the offline
smoke and a one-task `g2/p2/r1` run before spending that budget. Detailed steps
are in [`docs/REPRODUCING.md`](docs/REPRODUCING.md).

## Reproducibility boundary

Cached-result validation is deterministic. A new live run is not bit-for-bit
reproducible because the hosted model deployment revisions and provider-side
sampling seed were not retained. The public configurations preserve the
recorded aliases, temperatures, budgets, tasks, and library versions; users
may substitute compatible models to exercise the complete pipeline, but those
results are new experiments rather than replications of the paper's numerical
values. The archived C3/C4 runs were launched and completed between
May 14 and May 18, 2026 (UTC).

## License

Trace2Skill is licensed under the Apache License 2.0; see [`LICENSE`](LICENSE).
The bundled NeMo Gym snapshot retains its upstream Apache License 2.0 terms in
[`nemogym/LICENSE`](nemogym/LICENSE). CVDP data is downloaded separately from
Hugging Face and remains under the upstream terms reproduced in
[`CVDP_DATASET_LICENSE`](CVDP_DATASET_LICENSE) and
[`CVDP_DATASET_NOTICE`](CVDP_DATASET_NOTICE).

Before any release commit or archive:

```bash
./scripts/check_public_release.sh
```

## Citation

Citation metadata is provided in [`CITATION.cff`](CITATION.cff). Proceedings
page numbers and the paper DOI will be added once assigned; the software
artifact DOI is
[10.5281/zenodo.21513682](https://doi.org/10.5281/zenodo.21513682).

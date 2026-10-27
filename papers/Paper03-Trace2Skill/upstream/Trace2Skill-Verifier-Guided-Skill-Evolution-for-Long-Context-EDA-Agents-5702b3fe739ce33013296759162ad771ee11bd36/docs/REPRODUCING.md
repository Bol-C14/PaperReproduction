# Reproducing Trace2Skill

There are two distinct reproduction modes.

## 1. Deterministic paper-result validation

This is the fastest way to verify the claims and requires only Python 3.10+:

```bash
python3 scripts/validate_paper_results.py \
  --json-out runs/cached_validation_report.json
```

It validates 640 rollouts for each condition, task-level pass counts, all five
quality metrics, dense-feedback accounting, model-call counts, retry records,
and the 96-rollout progress audit.

## 2. Live end-to-end rerun

### Prerequisites

- Linux with Python 3.12 and Git.
- Docker 24+ with enough local storage for public CVDP repositories and
  transient verifier containers.
- An OpenAI-compatible endpoint serving a rollout model, mutation model, and
  oracle model.

### Setup

```bash
cp .env.example .env
# Set LLM_BASE_URL, LLM_API_KEY, and model aliases in .env.
./scripts/setup.sh
./scripts/fetch_cvdp_subset.py
./scripts/build_cvdp_image.sh
./scripts/run_smoke.sh
```

Two virtual environments are intentional. The recovered NeMo Gym runtime used
`openai==2.6.1`, while the optimizer client is installed independently. The
NeMo Gym constraints also preserve Python 3.12.3-era `pydantic==2.12.5`,
`ray==2.54.1`, and `PyYAML==6.0.3` records.

### Small live trial

Materialize one public task with two generations, two candidates, and one
repeat:

```bash
envs/unified/bin/python scripts/prepare_mlcad_per_task_oss24_runs.py \
  --condition c4-dense \
  --task schoolMIPS_0012 \
  --generations 2 \
  --population-size 2 \
  --num-repeats 1 \
  --num-parallel 1 \
  --run-root runs/trial

./scripts/launch_optimizer.sh \
  runs/trial/prepared/c4-dense/configs/cid016_schoolMIPS_0012.yml
```

Two generations are needed to exercise mutation. This trial checks the full
EA/control path but is not statistically comparable with the paper.

### Full paper budget

```bash
envs/unified/bin/python scripts/prepare_mlcad_per_task_oss24_runs.py --condition c3-sparse
./scripts/run_mlcad_per_task_oss24_batch.sh c3-sparse

envs/unified/bin/python scripts/prepare_mlcad_per_task_oss24_runs.py --condition c4-dense
./scripts/run_mlcad_per_task_oss24_batch.sh c4-dense
```

Each condition uses 8 tasks × 5 generations × 4 individuals × 4 repeats =
640 rollouts. Task-local optimizers run sequentially; up to two repeats run in
parallel inside a candidate evaluation.

Report a new run in the same field schema:

```bash
python3 scripts/report_runs.py runs/c4-dense > runs/c4-dense/report.csv
```

The CSV includes task, generation, individual, repeat, reward, pass rate,
SelectQ, SkillQ, AgentProgressQ, AgentVarianceQ, and AgentAdherenceQ.

### Resume and process ownership

Pass `--resume` only when the output directory contains `checkpoint.json`.
The launcher refuses to overwrite a nonempty run. It never searches for or
kills unrelated jobs; on exit it terminates only the NeMo Gym process group it
started. Set `SKIP_SERVERS=1` only if a compatible server stack is already
running and owned separately.

## Interpretation of a live rerun

The paper's hosted deployment revisions and sampling seed were not retained,
so exact trajectories cannot be regenerated. With equivalent models, a live
run tests whether the method and direction of effect reproduce. With substitute
models, it tests portability of the pipeline. Only cached validation reproduces
the exact reported numbers.

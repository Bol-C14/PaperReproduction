#!/usr/bin/env bash
# Offline smoke: verify data, materialize one C4 task, and test core EA helpers.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

if [[ ! -x envs/unified/bin/python ]]; then
    echo "Error: run ./scripts/setup.sh first." >&2
    exit 1
fi

PY="envs/unified/bin/python"
"$PY" scripts/fetch_cvdp_subset.py --check-only
"$PY" scripts/prepare_mlcad_per_task_oss24_runs.py \
    --condition c4-dense \
    --task schoolMIPS_0012 \
    --generations 2 \
    --population-size 2 \
    --num-repeats 1 \
    --num-parallel 1 \
    --run-root runs/smoke \
    --force
"$PY" scripts/verify_public_smoke.py runs/smoke/prepared/c4-dense/manifest.json
"$PY" -m pytest -q \
    tests/test_dense_progress_fitness.py \
    tests/test_skill_integration.py \
    tests/test_skill_sanitizer.py \
    tests/test_skill_selector.py \
    tests/test_standard_ea_flow.py

echo "PUBLIC OFFLINE SMOKE PASSED"

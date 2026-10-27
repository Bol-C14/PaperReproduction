#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

python3 scripts/check_public_release.py
git diff --check
bash -n scripts/*.sh
python3 -m compileall -q optimizer eval scripts nemogym/resources_servers/cvdp_agentic_heavy
python3 scripts/validate_paper_results.py >/dev/null
python3 scripts/export_public_rollout_example.py check \
  artifacts/rollout-examples/c3_noobscpu_sparse_example.jsonl \
  artifacts/rollout-examples/c4_noobscpu_dense_example.jsonl >/dev/null

echo "SOURCE, SHELL, AND CACHED-EVIDENCE CHECKS PASSED"

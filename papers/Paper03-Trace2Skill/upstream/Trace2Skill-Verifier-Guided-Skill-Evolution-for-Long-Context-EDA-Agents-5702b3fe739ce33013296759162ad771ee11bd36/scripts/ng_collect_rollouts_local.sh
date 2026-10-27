#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

export PYTHONPATH="$REPO_ROOT/nemogym${PYTHONPATH:+:$PYTHONPATH}"
exec "$REPO_ROOT/envs/nemogym/bin/python" -c \
  'from nemo_gym.rollout_collection import collect_rollouts; collect_rollouts()' "$@"

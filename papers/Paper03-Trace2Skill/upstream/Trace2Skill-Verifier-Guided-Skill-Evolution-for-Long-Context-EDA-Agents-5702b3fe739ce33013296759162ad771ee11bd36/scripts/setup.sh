#!/usr/bin/env bash
# Create separate environments for the optimizer and the pinned NeMo Gym stack.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

PYTHON="${PYTHON:-python3.12}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Error: Python 3.12 is required (override the executable with PYTHON=...)." >&2
    exit 1
fi

version="$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ "$version" != "3.12" ]]; then
    echo "Error: Python 3.12 is required; found $version." >&2
    exit 1
fi

mkdir -p envs

if [[ ! -x envs/unified/bin/python ]]; then
    "$PYTHON" -m venv envs/unified
fi
envs/unified/bin/python -m pip install --upgrade pip setuptools wheel
envs/unified/bin/python -m pip install -e '.[dev]'

if [[ ! -x envs/nemogym/bin/python ]]; then
    "$PYTHON" -m venv envs/nemogym
fi
envs/nemogym/bin/python -m pip install --upgrade pip setuptools wheel
envs/nemogym/bin/python -m pip install -c requirements/nemogym-constraints.txt -e ./nemogym
envs/nemogym/bin/python -m pip install 'pytest>=8.3,<9' 'pytest-asyncio>=0.24,<2'

echo "Trace2Skill environments are ready under envs/."

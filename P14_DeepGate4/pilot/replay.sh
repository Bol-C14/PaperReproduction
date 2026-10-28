#!/usr/bin/env bash
# Local/offline replay. Run setup separately only if the isolated environment is absent.
set -euo pipefail
pilot_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root_dir="$(dirname -- "$pilot_dir")"
python_bin="$root_dir/.venv/bin/python"
if [[ ! -x "$python_bin" ]]; then
  echo 'Missing isolated CPU environment. See README.md for setup; no automatic downloads.' >&2
  exit 2
fi
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
"$python_bin" "$pilot_dir/static_checkpoint.py"
"$python_bin" "$pilot_dir/run_pilot.py"

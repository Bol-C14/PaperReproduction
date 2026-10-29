#!/usr/bin/env bash
set -euo pipefail
ROOT=${TAU2_REPRO_ROOT:?Set TAU2_REPRO_ROOT to the private reproduction workspace}
PAPER=$ROOT/checkouts/tau2/paper
VENV=$ROOT/envs/tau2
RUNTIME=$(dirname "$(dirname "$(readlink -f "$VENV/bin/python")")")
exec timeout 180 taskset -c 0-3 bwrap --unshare-all --die-with-parent --new-session \
  --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /lib64 /lib64 \
  --ro-bind "$RUNTIME" /runtime --ro-bind "$VENV/lib/python3.13/site-packages" /packages \
  --ro-bind "$PAPER" /work --ro-bind "$ROOT/tools/tau2" /scripts \
  --bind "$ROOT/results/tau2" /out --proc /proc --dev /dev --tmpfs /tmp \
  --clearenv --setenv PATH /runtime/bin:/usr/bin --setenv HOME /tmp \
  --setenv PYTHONPATH /work/src:/packages --setenv PYTHONDONTWRITEBYTECODE 1 \
  --setenv PYTEST_DISABLE_PLUGIN_AUTOLOAD 1 --setenv LITELLM_LOCAL_MODEL_COST_MAP True \
  --setenv OMP_NUM_THREADS 4 --setenv OPENBLAS_NUM_THREADS 4 --chdir /work \
  /runtime/bin/python "$@"

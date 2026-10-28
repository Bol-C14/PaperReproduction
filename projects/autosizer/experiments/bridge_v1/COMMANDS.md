# Commands and runtime mapping

All real measurement commands used the isolated experiment Python and native
ngspice, under `taskset -c 24-31` with OMP/OPENBLAS/MKL threads=1. These are portable
forms of the exact argument structure; runtime prefixes are supplied locally and
must not be committed. ROOT must be a **new**, absent directory for preflight.

```sh
# PYTHON, NGSPICE, SELECTOR and ROOT: locally supplied isolated paths.
# Run from the existing repository root; never source credentials or a global env.
STAGE=projects/autosizer/experiments/bridge_v1
taskset -c 24-31 env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  "$PYTHON" "$STAGE/test_bridge.py"
taskset -c 24-31 env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  "$PYTHON" "$STAGE/bridge.py" preflight --root "$ROOT" --binary "$NGSPICE" --selector "$SELECTOR"
# Continue only after preflight_checks.json reports passed=true.
taskset -c 24-31 env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  "$PYTHON" "$STAGE/bridge.py" fixture --root "$ROOT" --binary "$NGSPICE" --selector "$SELECTOR"
# Read-only source-run audit; never launches another circuit.
"$PYTHON" "$STAGE/check.py" "$ROOT"
# Extra offline synthetic boundary tests, added after the frozen run.
"$PYTHON" "$STAGE/test_failures.py"
```

Public package verification requires Python with NumPy/PyYAML; no simulator or API:

```sh
python3 projects/autosizer/experiments/bridge_v1/verify_public.py \
  projects/autosizer/experiments/bridge_v1/evidence/run_01
python3 -m unittest discover -s projects/autosizer/experiments/bridge_v1 -p 'test_*.py'
```

Future file transfers must omit AppleDouble metadata; for example use
`COPYFILE_DISABLE=1 tar --exclude='._*' --exclude='__pycache__' ...`.
No command enables live API execution. The CLI accepts only preflight and fixture.

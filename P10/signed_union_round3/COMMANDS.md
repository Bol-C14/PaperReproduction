# Execution commands
Run from P10/signed_union_round3 in the isolated APRIL checkout. Own paths are rooted at /home/shugu/work/paper-reproduction-april-20261028.
The frozen experiment and audit were executed once; existing outputs must never be overwritten.

    uv venv --python /usr/bin/python3.12 /home/shugu/work/paper-reproduction-april-20261028/envs/rover
    uv pip install --python /home/shugu/work/paper-reproduction-april-20261028/envs/rover/bin/python egglog==14.0.0 z3-solver==4.13.3.0 yowasp-yosys==0.63.0.0.post1107
    /home/shugu/work/paper-reproduction-april-20261028/envs/rover/bin/python -m py_compile *.py
    /home/shugu/work/paper-reproduction-april-20261028/envs/rover/bin/python run.py freeze

For both runtime prewarming and experiments:
    export XDG_CACHE_HOME=/home/shugu/work/paper-reproduction-april-20261028/cache/rover
    export YOWASP_CACHE_DIR=/home/shugu/work/paper-reproduction-april-20261028/cache/rover
    export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
    taskset -c 16-23 /home/shugu/work/paper-reproduction-april-20261028/envs/rover/bin/yowasp-yosys -V
    taskset -c 16-23 /home/shugu/work/paper-reproduction-april-20261028/envs/rover/bin/python run.py
    taskset -c 16-23 /home/shugu/work/paper-reproduction-april-20261028/envs/rover/bin/python audit.py

Actual stdout/stderr are retained in evidence and original owned logs. The parent AGENTS.md DCP/Vivado environment requirements do not apply to this standalone open-tool arithmetic flow; no site .env or license variables were read.

# One frozen execution

The existing APRIL checkout was clean at `96caf97b9ccafca8fe1959ff7a27767d36f67bd4` and fast-forwarded via Git bundle to `52c2c2038c5d8d9020b9deaaa51f33c3a6ba58fc`. No new remote repository, alternate branch, environment or dependency installation was created.

From `/home/shugu/work/paper-reproduction-april-20261028/checkouts/rover/P10/comparison_closure_round5`:

```sh
export XDG_CACHE_HOME=/home/shugu/work/paper-reproduction-april-20261028/cache/rover
export YOWASP_CACHE_DIR=/home/shugu/work/paper-reproduction-april-20261028/cache/rover
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
taskset -c 16-23 /home/shugu/work/paper-reproduction-april-20261028/envs/rover/bin/python run.py freeze
taskset -c 16-23 /home/shugu/work/paper-reproduction-april-20261028/envs/rover/bin/python run.py run > /home/shugu/work/paper-reproduction-april-20261028/logs/rover/comparison_round5_attempt1.log 2>&1
taskset -c 16-23 /home/shugu/work/paper-reproduction-april-20261028/envs/rover/bin/python audit.py > /home/shugu/work/paper-reproduction-april-20261028/logs/rover/comparison_round5_audit1.log 2>&1
```

Results are in `results/rover/comparison_closure_round5_attempt1`; archived copies and both outer logs are in `evidence/attempt1`. Freeze refuses an existing directory, run refuses an existing journal, audit refuses an existing audit file. Do not overwrite. No replay was needed; any future independent replay requires a distinct documented output path before freezing, without using existing results as a selection oracle.

After copying evidence to Mac, the completed standard-library read-only audit from the repository root was:

```sh
python3 P10/comparison_closure_round5/inspect_results.py P10/comparison_closure_round5/evidence/attempt1
```

Its stdout is archived as `evidence/attempt1/independent_checks.json`. The checker imports the earlier independent DAG/netlist recount functions from `nested_combine_round4/inspect_results.py`, not the experiment engine or synthesis measurement implementation. Public-content scans use the existing `P10/PUBLIC_EXPORT/scan_publication.py` with reports outside Git. Raw tool whitespace is retained; authored-file whitespace is checked separately.

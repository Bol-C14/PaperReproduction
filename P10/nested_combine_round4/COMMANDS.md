# Exact bounded execution and review

Reuse the existing APRIL checkout and `envs/rover`; do not reinstall globally. Mac source commits were transferred by Git bundle over the configured strict-verification `april1` SSH alias, then fast-forwarded only after checking the remote worktree clean and the expected prior SHA. No alternate remote repository or branch was created.

Run from `checkouts/rover/P10/nested_combine_round4`, rooted at `/home/shugu/work/paper-reproduction-april-20261028`:

```sh
export XDG_CACHE_HOME=/home/shugu/work/paper-reproduction-april-20261028/cache/rover
export YOWASP_CACHE_DIR=/home/shugu/work/paper-reproduction-april-20261028/cache/rover
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
taskset -c 16-23 /home/shugu/work/paper-reproduction-april-20261028/envs/rover/bin/python run.py freeze
taskset -c 16-23 /home/shugu/work/paper-reproduction-april-20261028/envs/rover/bin/python run.py matrix > /home/shugu/work/paper-reproduction-april-20261028/logs/rover/nested_round4_attempt2.log 2>&1
taskset -c 16-23 /home/shugu/work/paper-reproduction-april-20261028/envs/rover/bin/python audit.py > /home/shugu/work/paper-reproduction-april-20261028/logs/rover/nested_round4_audit2.log 2>&1
```

These commands were executed once for attempt 2 at commit `b1df1fb`; the current runner refuses the existing results path/journal and the audit refuses an existing audit output. Never overwrite either attempt. A future independent replay requires a distinct, documented output path in both runner and audit before freezing. The first three configurations were the pilot slice of the same matrix, without duplicate execution.

Attempt 1 used the same freeze/matrix commands at `115805b`, output path `results/rover/nested_combine_round4_attempt1`, and log `logs/rover/nested_round4_attempt1.log`. It stopped after the recorded optimizer failure; no synthesis audit ran. See both immutable manifests and Git for exact source versions.

After copying original results/logs to Mac, from the repository root, the standard-library independent audit is:

```sh
python3 P10/nested_combine_round4/inspect_results.py P10/nested_combine_round4/evidence/attempt2
```

Its stdout is retained as `evidence/attempt2/independent_checks.json`. It verifies frozen sources using Git objects and recomputes selected DAG costs and netlist metrics without solvers, synthesis, network access or data changes. Publication scanning uses the existing `P10/PUBLIC_EXPORT/scan_publication.py` with a report outside Git; no matched secret values are printed. Raw tool-log whitespace is preserved; authored-file whitespace is checked separately.

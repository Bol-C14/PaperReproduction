# Commands and attempts

Controller: Mac; execution: existing `ssh -o BatchMode=yes -o StrictHostKeyChecking=yes ${EXECUTION_HOST}`. Remote root `R=${REPRO_ROOT}`. No push, external messages, paid provider calls, or model requests.

1. Read `${HOST_HOME}/work/AGENTS.md`, `$R/README.md`, `$R/RESOURCE_PLAN.json`, and upstream Harbor `AGENTS.md`. The execution node instructions about `.env`/Vivado apply to real DCP experiments; none are run here. No environment/credential file was sourced.
2. `git clone --depth 1 https://github.com/harbor-framework/terminal-bench-2.git $R/checkouts/terminal-bench/dataset`
3. `git clone --depth 1 https://github.com/harbor-framework/harbor.git $R/checkouts/terminal-bench/harbor`
4. Run [prepare.sh](../scripts/prepare.sh) via SSH stdin. This fetches registry commit `69671fbaac6d67a7ef0dfec016cc38a64ef7a77c`, freezes selected-file SHA256s/budgets before results, and installs Harbor plus `podman-compose==1.5.0` into `$R/envs/terminal-bench/venv`.
5. Run resource diagnostics in [RESOURCE_PROBE.txt](RESOURCE_PROBE.txt). The original CPU-quota protocol is blocked. Memory/process/security checks succeed.
6. Run [prepare_images.sh](../scripts/prepare_images.sh) via SSH stdin. Online preparation downloads source snapshots, clones v4.0.0 only for protocol review, pulls the three original image tags, resolves their digests, and builds derivative images containing pinned pytest dependencies. No solution executes during this online phase.
7. Initial driver (`$R/tools/terminal-bench/calibrate.py`): all 13 scheduled starts fail on compose `mem_limit` string/int merge; no solutions run. Complete records retained at `$R/results/terminal-bench/*-affinity*` and `summary.json`.
8. v2 driver: duplicate memory field removed. First log no-op completes preflight but parser rejects compose-banner-prefixed JSON; other starts also expose upstream cleanup deleting local images. All 13 failed/incomplete trials retained under `run-v2`. No evaluated reference result inferred.
9. Rebuild the same derivative image recipes. v3 changes JSON parsing and calls `stop(delete=False)` so containers are removed but local images remain. It fails fast on its first no-op verifier upload: podman-compose 1.5.0 has no `cp`, and upstream tar fallback also fails. Records retained under `run-v3`.
10. v4 driver adds native `podman cp` for upload while reusing upstream container lifecycle/downloads, OracleAgent, NopAgent and Verifier. Current source is [calibrate.py](../scripts/calibrate.py). Run:

```sh
export PATH="$R/envs/terminal-bench/venv/bin:$PATH"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
python "$R/tools/terminal-bench/calibrate-v4.py" > "$R/logs/terminal-bench/calibration-v4.log" 2>&1
```

The driver runs one container at a time, aborts on a shared infrastructure failure, retains stdout/stderr and exceptions, checks actual in-container limits and hidden/artifact absence before execution, then collects an artifact and runs upstream plus independent checks. Runtime network is none; dependencies are already installed. Fresh paths refuse overwrite. To repeat, choose a new output directory; never erase old trials.

Raw source, original/final image inspections, all driver revisions, dependency inventories, complete failures, verifier JSON and command transcripts remain in the private evidence bundle. See [RAW_EVIDENCE.md](../RAW_EVIDENCE.md). No original reference files, raw task assets or expected answer files are staged for publication.

11. v4 native-copy trial exposes the upstream image root directory's mode `0555`: with capabilities dropped, creating `/tests` or `/logs` is forbidden. Runtime capabilities are not restored.
12. The first staging-only image build command used `--pull never`, which Podman rejected (`accepts at most 1 arg(s), received 2`). v5 consequently repeats one directory-creation failure; no reference solution result is claimed. Both preparation failures and v5 output are retained.
13. Corrected build uses `podman build --network none --pull=never ...`; it precreates empty `/tests`, `/solution`, `/logs/agent`, `/logs/verifier`, `/logs/artifacts` and verifies their existence in a hardened offline container before execution. v6 gets the first no-op upstream reward 0, then fails parsing expected nonzero independent-check output because compose appends a diagnostic after JSON.
14. v7 uses `JSONDecoder.raw_decode` for the one explicit JSON record and preserves the complete raw output and nonzero return code separately. The final delivered driver points to `run-v7`. Actual invocation:

```sh
export PATH="$R/envs/terminal-bench/venv/bin:$PATH"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
python "$R/tools/terminal-bench/calibrate-v7.py" > "$R/logs/terminal-bench/calibration-v7.log" 2>&1
```

The delivered preparation recipe includes empty staging directories directly; the historical two-stage image recipes used for this run remain in raw evidence. No further online install is needed for rerunning the retained prepared images. Rebuilding mutable apt repositories is a new environment preparation, not byte-identical reconstruction of the retained image IDs.

15. Run [capture_metadata.py](../scripts/capture_metadata.py) and [isolation_inventory.py](../scripts/isolation_inventory.py). They record final image/package identities, source/task hashes, scanned task-accessible files and exact forbidden-content matches. These auditor probes do not count as evaluated task attempts. Run script syntax checks using Python `py_compile` and **Bash** `-n` (the shell scripts use process substitution and are not POSIX sh scripts).

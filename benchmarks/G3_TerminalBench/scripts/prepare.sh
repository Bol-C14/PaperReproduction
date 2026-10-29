#!/usr/bin/env bash
set -eu
R=${REPRO_ROOT:?Set REPRO_ROOT to a dedicated execution root}
T=$R/checkouts/terminal-bench
A=$R/assets/terminal-bench
L=$R/logs/terminal-bench
exec > >(tee "$L/prepare.log") 2>&1
date -u
cd "$T/dataset"
git fetch --depth 1 origin 69671fbaac6d67a7ef0dfec016cc38a64ef7a77c
git checkout --detach FETCH_HEAD
cd "$T"
python3 - <<'PY'
import json,hashlib,pathlib,datetime,subprocess
p=pathlib.Path('dataset'); tasks=['log-summary-date-ranges','regex-log','cancel-async-tasks']
f={str(x.relative_to(p)):hashlib.sha256(x.read_bytes()).hexdigest() for t in tasks for x in sorted((p/t).rglob('*')) if x.is_file()}
r={'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'dataset_version':'2.0','dataset_commit':subprocess.check_output(['git','-C','dataset','rev-parse','HEAD'],text=True).strip(),'tasks':tasks,'selection_reason':'CPU-only; bounded artifacts; logging/date, regex semantics, async cancellation; selected before execution; no outcome-based substitutions','excluded_tasks':{'count':86,'reason':'outside preselected CPU micro-audit; not attempted'},'budget':{'setup_wall_hours':2,'download_bytes_cap':2147483648,'cpu_threads_max':4,'model_calls':0,'paid_usd':0,'settings':[{'cpus':1,'memory_mb':2048},{'cpus':2,'memory_mb':2048}],'max_main_trials':12,'agent_timeout_sec':900,'verifier_timeout_sec':900},'sha256':f}
pathlib.Path('../../assets/terminal-bench/selection.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
PY
for t in log-summary-date-ranges regex-log cancel-async-tasks; do cat "dataset/$t/task.toml"; done
uv venv --python 3.13 "$R/envs/terminal-bench/venv"
UV_CACHE_DIR="$R/cache/terminal-bench/uv" uv pip install --python "$R/envs/terminal-bench/venv/bin/python" -e "$T/harbor" podman-compose==1.5.0
"$R/envs/terminal-bench/venv/bin/harbor" --version
"$R/envs/terminal-bench/venv/bin/python" -m pip freeze || true

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PILOT_DIR="$PWD"
PILOT_IMAGE="p07-verithoughts:yosys041"
mkdir -p logs runs/attempt1
python3 - <<'PY'
import hashlib,json,pathlib
p=pathlib.Path('.')
f=json.loads((p/'freeze.json').read_text())
for name,digest in f['sha256'].items():
    actual=hashlib.sha256((p/name).read_bytes()).hexdigest()
    assert actual==digest,(name,actual,digest)
print('Frozen file digests verified')
PY
if [ -e runs/attempt1/started.json ]; then
  echo 'Experiment attempt1 already exists; refusing overwrite or silent retry.' >&2
  exit 2
fi
docker image inspect "$PILOT_IMAGE" > logs/image_inspect.json
docker run --rm --network=none --user=1000:1000 --read-only \
  --cap-drop=ALL --security-opt=no-new-privileges --pids-limit=128 \
  --cpus=2 --memory=4g --memory-swap=4g --tmpfs /tmp:rw,noexec,nosuid,size=256m \
  --mount "type=bind,src=$PILOT_DIR,dst=/src,readonly" \
  --mount "type=bind,src=$PILOT_DIR/runs/attempt1,dst=/work" \
  "$PILOT_IMAGE" bash -c '
    set -e
    yosys -V
    iverilog -V
    python3 -c "import sys,numpy;print(sys.version);print(numpy.__version__)"
    cp /opt/provenance/dpkg-lock.tsv /work/dpkg-lock.tsv
    cp /opt/provenance/apt-list-bytes.txt /work/apt-list-bytes.txt
    cat /proc/self/status | sed -n "/^Uid:/p;/^NoNewPrivs:/p;/^CapEff:/p"
  ' > logs/preflight.log 2>&1
date -u +%FT%TZ > logs/experiment_started_at.txt
docker run --rm --name p07-contract-pilot --network=none --user=1000:1000 --read-only \
  --cap-drop=ALL --security-opt=no-new-privileges --pids-limit=128 \
  --cpus=2 --memory=4g --memory-swap=4g --tmpfs /tmp:rw,noexec,nosuid,size=256m \
  --mount "type=bind,src=$PILOT_DIR,dst=/src,readonly" \
  --mount "type=bind,src=$PILOT_DIR/runs/attempt1,dst=/work" \
  "$PILOT_IMAGE" bash -c '
    python3 /src/run_pilot.py
    result=$?
    cat /sys/fs/cgroup/memory.peak > /work/container_memory_peak_bytes.txt
    cat /sys/fs/cgroup/cpu.stat > /work/container_cpu.stat
    exit "$result"
  ' > logs/experiment_attempt1.log 2>&1
date -u +%FT%TZ > logs/experiment_finished_at.txt

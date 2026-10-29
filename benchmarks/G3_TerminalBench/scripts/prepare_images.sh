#!/usr/bin/env bash
set -eu
R=${REPRO_ROOT:?Set REPRO_ROOT to a dedicated execution root}
A=$R/assets/terminal-bench
T=$R/checkouts/terminal-bench
L=$R/logs/terminal-bench
export PATH="$R/envs/terminal-bench/venv/bin:$PATH"
exec > >(tee "$L/prepare-images.log") 2>&1
mkdir -p "$A/sources" "$A/ports" "$A/build"
curl -fsSL --max-time 90 https://arxiv.org/html/2601.11868v1 -o "$A/sources/paper-v1.html"
for n in announcement-2-0 terminal-bench-2-1 terminal-bench-3-0 terminal-bench-4-0 continuous-benchmarks leaderboard-integrity-update leaderboard-integrity-and-timeouts; do curl -fsSL --max-time 60 "https://www.tbench.ai/news/$n" -o "$A/sources/$n.html"; done
git clone --depth 1 --branch v4.0.0 https://github.com/harbor-framework/terminal-bench.git "$T/protocol-4"
git -C "$T/protocol-4" rev-parse HEAD
uv pip freeze --python "$R/envs/terminal-bench/venv/bin/python" > "$L/harness-packages.txt"
for t in log-summary-date-ranges regex-log cancel-async-tasks; do
 podman pull "docker.io/alexgshaw/$t:20251031"
 podman image inspect "docker.io/alexgshaw/$t:20251031" > "$L/image-$t.json"
 digest=$(podman image inspect "docker.io/alexgshaw/$t:20251031" --format '{{index .RepoDigests 0}}')
 mkdir -p "$A/build/$t"
 cat > "$A/build/$t/Dockerfile" <<EOF
FROM $digest
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip python3-venv util-linux grep coreutils ca-certificates && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/verifier && /opt/verifier/bin/pip install --no-cache-dir pytest==8.4.1 pytest-json-ctrf==0.3.5
RUN mkdir -p /tests /solution /logs/agent /logs/verifier /logs/artifacts
ENV PATH="/opt/verifier/bin:\$PATH"
EOF
 podman build --jobs 1 -t "localhost/g3-$t:calibration" "$A/build/$t"
 podman image inspect "localhost/g3-$t:calibration" > "$L/prepared-image-$t.json"
done

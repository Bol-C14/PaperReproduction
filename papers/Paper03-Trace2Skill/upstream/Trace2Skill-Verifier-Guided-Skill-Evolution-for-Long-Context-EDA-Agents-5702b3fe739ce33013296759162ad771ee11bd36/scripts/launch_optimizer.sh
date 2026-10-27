#!/usr/bin/env bash
# Start one Trace2Skill run and a run-owned NeMo Gym server process group.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

usage() {
    echo "Usage: $0 <config.yml> [--resume]" >&2
    echo "Set SKIP_SERVERS=1 only when a compatible NeMo Gym stack is already running." >&2
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
    usage
    exit 2
fi

CONFIG="$1"
RESUME_FLAG=""
if [[ "${2:-}" == "--resume" ]]; then
    RESUME_FLAG="--resume"
elif [[ $# -eq 2 ]]; then
    usage
    exit 2
fi

if [[ ! -f "$CONFIG" ]]; then
    echo "Error: config not found: $CONFIG" >&2
    exit 2
fi
if [[ ! -f .env ]]; then
    echo "Error: .env is missing. Copy .env.example to .env and configure the model endpoint." >&2
    exit 2
fi
if [[ ! -x envs/unified/bin/python || ! -x envs/nemogym/bin/ng_run ]]; then
    echo "Error: local environments are missing. Run ./scripts/setup.sh first." >&2
    exit 2
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

if [[ -z "${LLM_BASE_URL:-}" || -z "${ROLLOUT_MODEL:-}" || -z "${MUTATION_MODEL:-}" ]]; then
    echo "Error: LLM_BASE_URL, ROLLOUT_MODEL, and MUTATION_MODEL must be set in .env." >&2
    exit 2
fi

UNIFIED_PY="$REPO_ROOT/envs/unified/bin/python"
NEMOGYM_RUN="$REPO_ROOT/envs/nemogym/bin/ng_run"

mapfile -t CONFIG_META < <("$UNIFIED_PY" - "$CONFIG" <<'PY'
import os
import re
import sys
from pathlib import Path

import yaml

path = Path(sys.argv[1]).resolve()
config = yaml.safe_load(path.read_text(encoding="utf-8"))

def expand(value):
    if not isinstance(value, str):
        return value
    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", lambda m: os.environ.get(m.group(1), m.group(0)), value)

output = Path(expand(config["output_dir"]))
if not output.is_absolute():
    output = (Path.cwd() / output).resolve()
ng_paths = config.get("ng_config_paths") or ["configs/cvdp_lc_30turns.yaml", "nemo_gym_env.yaml"]
feedback = config.get("runtime_verifier_feedback") or {}
artifact = Path(expand(feedback.get("artifact_root") or output / "runtime_verifier_feedback"))
if not artifact.is_absolute():
    artifact = (Path.cwd() / artifact).resolve()
print(output)
print(",".join(map(str, ng_paths)))
print("1" if feedback.get("enabled", False) else "0")
print(int(feedback.get("max_calls", 3)))
print(artifact)
PY
)

if [[ "${#CONFIG_META[@]}" -ne 5 ]]; then
    echo "Error: could not read launcher fields from $CONFIG" >&2
    exit 2
fi

OUTPUT_DIR="${CONFIG_META[0]}"
NG_CONFIG_PATHS="${NG_CONFIG_PATHS:-${CONFIG_META[1]}}"
export CVDP_RUNTIME_VERIFIER_FEEDBACK_ENABLED="${CONFIG_META[2]}"
export CVDP_RUNTIME_VERIFIER_FEEDBACK_MAX_CALLS="${CONFIG_META[3]}"
export CVDP_RUNTIME_VERIFIER_FEEDBACK_ARTIFACT_ROOT="${CONFIG_META[4]}"
export CVDP_TMPDIR="${CVDP_TMPDIR:-$REPO_ROOT/runs/tmp}"
export PYTHONPATH="$REPO_ROOT/nemogym${PYTHONPATH:+:$PYTHONPATH}"
export REPO_ROOT
mkdir -p "$CVDP_TMPDIR"

if [[ -z "$RESUME_FLAG" && -d "$OUTPUT_DIR" && -n "$(find "$OUTPUT_DIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
    echo "Error: output directory is not empty: $OUTPUT_DIR" >&2
    echo "Use a new directory or pass --resume for an existing checkpoint." >&2
    exit 1
fi
if [[ -n "$RESUME_FLAG" && ! -f "$OUTPUT_DIR/checkpoint.json" ]]; then
    echo "Error: --resume requires $OUTPUT_DIR/checkpoint.json" >&2
    exit 1
fi

mkdir -p "$OUTPUT_DIR/system"
NG_LOG="$OUTPUT_DIR/system/ng_run.log"
OPT_LOG="$OUTPUT_DIR/system/optimizer.log"
NG_PID=""

cleanup() {
    status=$?
    trap - EXIT INT TERM
    if [[ -n "$NG_PID" ]] && kill -0 "$NG_PID" 2>/dev/null; then
        echo "Stopping this launcher's NeMo Gym process group (PID $NG_PID)..."
        kill -TERM -- "-$NG_PID" 2>/dev/null || kill -TERM "$NG_PID" 2>/dev/null || true
        for _ in {1..20}; do
            kill -0 "$NG_PID" 2>/dev/null || break
            sleep 0.25
        done
        kill -KILL -- "-$NG_PID" 2>/dev/null || true
    fi
    exit "$status"
}
trap cleanup EXIT INT TERM

if [[ "${SKIP_SERVERS:-0}" != "1" ]]; then
    if ! command -v docker >/dev/null 2>&1; then
        echo "Error: Docker is required for live CVDP verification." >&2
        exit 1
    fi
    if ! command -v setsid >/dev/null 2>&1; then
        echo "Error: setsid is required for run-owned server cleanup." >&2
        exit 1
    fi

    echo "Starting NeMo Gym; log: $NG_LOG"
    (
        cd "$REPO_ROOT/nemogym"
        exec setsid "$NEMOGYM_RUN" \
            "+config_paths=[$NG_CONFIG_PATHS]" \
            "+skip_venv_if_present=true"
    ) >"$NG_LOG" 2>&1 &
    NG_PID=$!

    wait_seconds="${NG_WAIT_SECS:-180}"
    for ((second = 1; second <= wait_seconds; second++)); do
        if grep -Eq "All [0-9]+ / [0-9]+ servers ready" "$NG_LOG" 2>/dev/null; then
            echo "NeMo Gym is ready after ${second}s."
            break
        fi
        if ! kill -0 "$NG_PID" 2>/dev/null; then
            echo "Error: NeMo Gym exited before becoming ready." >&2
            tail -n 30 "$NG_LOG" >&2 || true
            exit 1
        fi
        sleep 1
    done
    if ! grep -Eq "All [0-9]+ / [0-9]+ servers ready" "$NG_LOG" 2>/dev/null; then
        echo "Error: NeMo Gym did not become ready within ${wait_seconds}s." >&2
        tail -n 30 "$NG_LOG" >&2 || true
        exit 1
    fi
fi

echo "Starting optimizer; output: $OUTPUT_DIR"
echo "Optimizer log: $OPT_LOG"
export PYTHONUNBUFFERED=1
set +e
"$UNIFIED_PY" -u optimizer/run_optimizer.py --config "$CONFIG" ${RESUME_FLAG:+"$RESUME_FLAG"} 2>&1 | tee "$OPT_LOG"
OPT_STATUS=${PIPESTATUS[0]}
set -e
exit "$OPT_STATUS"

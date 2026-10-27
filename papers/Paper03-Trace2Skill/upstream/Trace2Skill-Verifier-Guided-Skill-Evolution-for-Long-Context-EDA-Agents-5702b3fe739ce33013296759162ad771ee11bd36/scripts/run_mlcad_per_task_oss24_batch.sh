#!/usr/bin/env bash
# Run the eight task-local paper configurations sequentially.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

CONDITION="${1:-}"
if [[ "$CONDITION" != "c3-sparse" && "$CONDITION" != "c4-dense" ]]; then
    echo "Usage: $0 c3-sparse|c4-dense" >&2
    exit 2
fi

MANIFEST="runs/prepared/$CONDITION/manifest.json"
if [[ ! -f "$MANIFEST" ]]; then
    echo "Error: $MANIFEST is missing." >&2
    echo "Run: ./scripts/prepare_mlcad_per_task_oss24_runs.py --condition $CONDITION" >&2
    exit 2
fi

mapfile -t CONFIGS < <(envs/unified/bin/python - "$MANIFEST" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    manifest = json.load(stream)
for task in manifest["tasks"]:
    print(task["config_path"])
PY
)

if [[ "${#CONFIGS[@]}" -ne 8 && "${ALLOW_PARTIAL_BATCH:-0}" != "1" ]]; then
    echo "Error: expected eight task configs, found ${#CONFIGS[@]}." >&2
    echo "Set ALLOW_PARTIAL_BATCH=1 only for an intentional development subset." >&2
    exit 1
fi

echo "Trace2Skill $CONDITION: ${#CONFIGS[@]} task-local runs, launched sequentially."
for config in "${CONFIGS[@]}"; do
    echo "Launching $config"
    "$SCRIPT_DIR/launch_optimizer.sh" "$config"
done

echo "All $CONDITION runs completed."

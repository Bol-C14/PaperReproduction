#!/usr/bin/env bash
# Build the public OSS Icarus/cocotb verifier image; no image archive is stored.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
IMAGE="${CVDP_OSS_SIM_IMAGE:-trace2skill/cvdp-sim-cocotb-compat:latest}"

docker build \
    --file "$REPO_ROOT/docker/cvdp-sim-cocotb-compat/Dockerfile" \
    --tag "$IMAGE" \
    "$REPO_ROOT/docker/cvdp-sim-cocotb-compat"

echo "Built $IMAGE"

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$( dirname "$SCRIPT_DIR" )"

function check_nvidia() {
  if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "ERROR: nvidia-smi not found. Install NVIDIA drivers and nvidia-container-toolkit first." >&2
    exit 1
  fi
}

check_nvidia

echo "Starting Ollama with GPU support (docker compose override)"
docker compose -f "$ROOT_DIR/docker-compose.yml" -f "$ROOT_DIR/docker-compose.gpu.yml" up -d ollama

echo "Waiting for Ollama to become healthy (120s)"
"$SCRIPT_DIR/check-health.sh" 120 ollama

echo "Pulling curated free models"
"$SCRIPT_DIR/model-pull.sh" all-free

echo "Done. Check local models with: docker compose run --rm ollama ollama list"

#!/usr/bin/env bash
# Pull Ollama models into local cache
# Usage: ./scripts/model-pull.sh [model_name]
# Example: ./scripts/model-pull.sh qwen2.5-coder:7b-q4_0

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

MODEL=${1:-qwen2.5-coder:7b-q4_0}

echo "=== Pulling Model: $MODEL ==="
docker compose -f "$PROJECT_ROOT/docker-compose.yml" run --rm ollama ollama pull "$MODEL"

echo ""
echo "✅ Model $MODEL pulled successfully."
echo ""
echo "Available models:"
docker compose -f "$PROJECT_ROOT/docker-compose.yml" run --rm ollama ollama list

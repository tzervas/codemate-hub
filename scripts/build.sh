#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

# Run preflight checks first
echo "Running preflight checks..."
"$SCRIPT_DIR/preflight-check.sh"

echo ""
echo "=== Building Images ==="
docker compose -f "$PROJECT_ROOT/docker-compose.yml" build app

echo ""
echo "=== Starting Ollama Service ==="
docker compose -f "$PROJECT_ROOT/docker-compose.yml" up -d ollama

echo "Waiting for Ollama to be healthy..."
"$SCRIPT_DIR/check-health.sh" 120 ollama || true

echo ""
echo "=== Pulling Model ==="
docker compose -f "$PROJECT_ROOT/docker-compose.yml" run --rm ollama ollama pull qwen2.5-coder:7b-q4_0

echo ""
echo "=== Initializing Chroma DB ==="
docker compose -f "$PROJECT_ROOT/docker-compose.yml" run --rm app python src/memory_setup.py

echo ""
echo "✅ Build complete!"
echo "Next step: docker-compose up"

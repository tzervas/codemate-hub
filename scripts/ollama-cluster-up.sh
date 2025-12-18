#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )/.."

echo "Starting Ollama small (concurrency) and Ollama large (GPU heavy) instances..."

# Start small instance (CPU-focused) and pull small-models
docker compose -f "$ROOT_DIR/docker-compose.yml" -f "$ROOT_DIR/docker-compose.ollama-small.yml" up -d ollama-small
docker compose -f "$ROOT_DIR/docker-compose.yml" -f "$ROOT_DIR/docker-compose.ollama-small.yml" run --rm ollama-small ollama pull qwen2.5-coder:7b-q4_0 || true
docker compose -f "$ROOT_DIR/docker-compose.yml" -f "$ROOT_DIR/docker-compose.ollama-small.yml" run --rm ollama-small ollama pull mistral:latest || true

# Start large instance with GPU if available
docker compose -f "$ROOT_DIR/docker-compose.yml" -f "$ROOT_DIR/docker-compose.ollama-large.yml" -f "$ROOT_DIR/docker-compose.gpu.yml" up -d ollama-large
docker compose -f "$ROOT_DIR/docker-compose.yml" -f "$ROOT_DIR/docker-compose.ollama-large.yml" -f "$ROOT_DIR/docker-compose.gpu.yml" run --rm ollama-large ollama pull llama2-13b || true

echo "Done. Use docker compose run --rm ollama-small ollama list and ollama-large respectively to validate models." 

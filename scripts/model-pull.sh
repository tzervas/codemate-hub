#!/bin/bash
set -e
MODEL=${1:-qwen2.5-coder:7b-q4_0}
docker compose run --rm ollama ollama pull $MODEL
echo "Model $MODEL pulled."

#!/bin/bash
set -e
docker compose build app
docker compose run --rm ollama ollama pull qwen2.5-coder:7b-q4_0
docker compose run --rm app python src/memory_setup.py
echo "Build complete!"

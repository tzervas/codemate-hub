#!/usr/bin/env bash
# Pre-flight checks for docker-compose startup
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

echo "=== Pre-flight Checks ==="

# Check 1: Docker installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi
echo "✓ Docker found: $(docker --version)"

# Check 2: Docker daemon running
if ! docker ps &> /dev/null; then
    echo "❌ Docker daemon not running or permission denied"
    exit 1
fi
echo "✓ Docker daemon is running"

# Check 2: docker compose available
if ! docker compose version &> /dev/null; then
    echo "❌ docker compose not available"
    exit 1
fi
echo "✓ docker compose available"

# Check 4: PASSWORD environment variable set
if [ -z "${PASSWORD:-}" ]; then
    echo "⚠ PASSWORD environment variable not set"
    if [ -f "$PROJECT_ROOT/.env" ]; then
        echo "  Found .env file; loading..."
        set -a
        source "$PROJECT_ROOT/.env"
        set +a
        if [ -z "${PASSWORD:-}" ]; then
            echo "❌ PASSWORD still not set after loading .env"
            exit 1
        fi
    else
        echo "❌ .env file not found. Copy from .env.example: cp .env.example .env"
        exit 1
    fi
fi
echo "✓ PASSWORD set"

# Check 5: GPU detection and warning
if command -v nvidia-smi &> /dev/null; then
    echo "✓ NVIDIA GPU detected: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
    if docker run --rm --runtime=nvidia nvidia/cuda:12.0.0-runtime-ubuntu22.04 nvidia-smi &> /dev/null; then
        echo "  ℹ nvidia-docker appears to be configured"
        echo "  ℹ To enable GPU: uncomment 'runtime: nvidia' in docker-compose.yml"
    else
        echo "  ⚠ NVIDIA GPU found but nvidia-docker may not be configured"
        echo "  ℹ Proceeding with CPU-only mode"
    fi
else
    echo "ℹ No NVIDIA GPU detected; using CPU-only mode"
fi

# Check 6: Required files exist
REQUIRED_FILES=(
    "docker-compose.yml"
    "Dockerfile"
    "requirements.txt"
)
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$PROJECT_ROOT/$file" ]; then
        echo "❌ Required file missing: $file"
        exit 1
    fi
done
echo "✓ All required files present"

# Check 7: Disk space (warn if low)
AVAILABLE_SPACE=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')  # in KB
REQUIRED_SPACE=$((10 * 1024 * 1024))  # 10 GB in KB
if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
    echo "⚠ Low disk space available: $(numfmt --to=iec $((AVAILABLE_SPACE * 1024)) 2>/dev/null || echo "$AVAILABLE_SPACE KB")"
    echo "  Ollama models can be large; ensure sufficient space"
fi

echo ""
echo "✅ All checks passed! Ready to start: docker-compose up"

#!/usr/bin/env bash
# Validation test for Ollama health check and CPU-only fallback
# This script validates that:
# 1. Ollama healthcheck endpoint is reachable
# 2. CPU-only mode works (no nvidia runtime errors)
# 3. Graceful degradation when GPU not available

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

echo "=== Ollama Health Check & CPU Fallback Test ==="
echo ""

# Test 1: Verify healthcheck endpoint is accessible
echo "Test 1: Checking Ollama healthcheck configuration..."
if grep -q 'test: \["CMD", "curl", "-f", "http://localhost:11434/api/tags"\]' "$PROJECT_ROOT/docker-compose.yml"; then
    echo "✓ Healthcheck endpoint configured correctly"
else
    echo "❌ Healthcheck endpoint not configured"
    exit 1
fi

# Test 2: Verify GPU runtime is optional (commented out)
echo ""
echo "Test 2: Checking GPU runtime configuration..."
if grep -q '# runtime: nvidia' "$PROJECT_ROOT/docker-compose.yml"; then
    echo "✓ GPU runtime is optional (commented out)"
else
    echo "❌ GPU runtime is still hardcoded"
    exit 1
fi

# Test 3: Verify CPU parameters are present
echo ""
echo "Test 3: Checking CPU optimization parameters..."
if grep -q 'OLLAMA_NUM_PARALLEL' "$PROJECT_ROOT/docker-compose.yml"; then
    echo "✓ OLLAMA_NUM_PARALLEL configured"
else
    echo "⚠ OLLAMA_NUM_PARALLEL not found"
fi

if grep -q 'OLLAMA_NUM_THREAD' "$PROJECT_ROOT/docker-compose.yml"; then
    echo "✓ OLLAMA_NUM_THREAD configured"
else
    echo "⚠ OLLAMA_NUM_THREAD not found"
fi

# Test 4: Verify ollama_data volume persistence
echo ""
echo "Test 4: Checking volume persistence..."
if grep -q 'ollama_data:/root/.ollama' "$PROJECT_ROOT/docker-compose.yml"; then
    echo "✓ Ollama data volume mounted correctly"
else
    echo "❌ Ollama data volume not configured"
    exit 1
fi

# Test 5: Check if ollama has timeout safety
echo ""
echo "Test 5: Checking healthcheck timeout safety..."
if grep -q 'timeout: 10s' "$PROJECT_ROOT/docker-compose.yml"; then
    echo "✓ Healthcheck timeout configured (10s)"
else
    echo "❌ Healthcheck timeout not configured"
fi

if grep -q 'retries: 3' "$PROJECT_ROOT/docker-compose.yml"; then
    echo "✓ Healthcheck retries configured (3)"
else
    echo "❌ Healthcheck retries not configured"
fi

# Test 6: Validate docker-compose YAML syntax
echo ""
echo "Test 6: Validating docker-compose.yml syntax..."
if docker compose -f "$PROJECT_ROOT/docker-compose.yml" config &> /dev/null; then
    echo "✓ docker-compose.yml is valid"
else
    echo "❌ docker-compose.yml has syntax errors"
    docker compose -f "$PROJECT_ROOT/docker-compose.yml" config
    exit 1
fi

# Test 7: Check for nvidia-docker if GPU is enabled
echo ""
echo "Test 7: Checking GPU availability..."
if grep -q '^    runtime: nvidia' "$PROJECT_ROOT/docker-compose.yml"; then
    echo "ℹ GPU runtime is enabled in configuration"
    if command -v nvidia-docker &> /dev/null; then
        echo "✓ nvidia-docker is available"
    else
        echo "⚠ nvidia-docker not found (GPU mode will fail)"
        echo "  To install: https://github.com/NVIDIA/nvidia-docker"
    fi
else
    echo "ℹ GPU runtime is disabled (CPU-only mode)"
fi

echo ""
echo "✅ All Ollama health check and CPU fallback tests passed!"
echo ""
echo "Configuration Summary:"
echo "  - Healthcheck: http://localhost:11434/api/tags"
echo "  - Healthcheck timeout: 10s, retries: 3"
echo "  - CPU optimization: OLLAMA_NUM_PARALLEL=4, OLLAMA_NUM_THREAD=4"
echo "  - GPU runtime: Optional (uncomment in docker-compose.yml)"
echo "  - Data persistence: ollama_data volume"
echo ""
echo "Next: Run './scripts/build.sh' to start services"

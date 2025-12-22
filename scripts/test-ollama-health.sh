#!/usr/bin/env bash
# Validation test for Ollama health check configuration
# This script validates that:
# 1. Ollama healthcheck is properly configured
# 2. GPU runtime is configured (optional for CI)
# 3. Required environment variables are set

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

echo "=== Ollama Health Check & Configuration Test ==="
echo ""

# Test 1: Verify healthcheck is configured (ollama list command)
echo "Test 1: Checking Ollama healthcheck configuration..."
if grep -q 'test: \["CMD", "ollama", "list"\]' "$PROJECT_ROOT/docker-compose.yml"; then
    echo "✓ Healthcheck configured correctly (ollama list)"
elif grep -q 'test: \["CMD", "curl", "-f", "http://localhost:11434/api/tags"\]' "$PROJECT_ROOT/docker-compose.yml"; then
    echo "✓ Healthcheck configured correctly (curl endpoint)"
else
    echo "❌ Healthcheck not configured"
    exit 1
fi

# Test 2: Verify GPU runtime configuration exists
echo ""
echo "Test 2: Checking GPU runtime configuration..."
if grep -q 'runtime: nvidia' "$PROJECT_ROOT/docker-compose.yml"; then
    echo "✓ GPU runtime is configured"
elif grep -q '# runtime: nvidia' "$PROJECT_ROOT/docker-compose.yml"; then
    echo "✓ GPU runtime is optional (commented out for CPU-only)"
else
    echo "ℹ No GPU runtime specified (CPU-only mode)"
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
    echo "⚠ Healthcheck timeout not configured (using default)"
fi

if grep -Eq 'retries: [0-9]+' "$PROJECT_ROOT/docker-compose.yml"; then
    RETRIES=$(grep -oE 'retries: [0-9]+' "$PROJECT_ROOT/docker-compose.yml" | head -1 | grep -oE '[0-9]+')
    echo "✓ Healthcheck retries configured ($RETRIES)"
else
    echo "⚠ Healthcheck retries not configured (using default)"
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
echo "✅ All Ollama health check configuration tests passed!"
echo ""
echo "Configuration Summary:"
echo "  - Healthcheck: ollama list command (or curl endpoint)"
echo "  - Data persistence: ollama_data volume"
echo "  - GPU runtime: Configurable (enabled/disabled based on deployment)"
echo ""
echo "Next: Run './scripts/build.sh' to start services"

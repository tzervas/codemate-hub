#!/usr/bin/env bash
# Build and initialize the Codemate-Hub application
# This script is idempotent - safe to run multiple times
# Usage: ./scripts/build.sh

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

# Color output for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function log_info() {
  echo -e "${BLUE}ℹ${NC} $1"
}

function log_success() {
  echo -e "${GREEN}✓${NC} $1"
}

function log_warn() {
  echo -e "${YELLOW}⚠${NC} $1"
}

function log_error() {
  echo -e "${RED}✗${NC} $1" >&2
}

# Run preflight checks first
log_info "Running preflight checks..."
if ! "$SCRIPT_DIR/preflight-check.sh"; then
    log_error "Preflight checks failed"
    exit 1
fi

echo ""
echo "=== Building Images ==="
log_info "Building app image (this may take several minutes on first run)..."
if docker compose -f "$PROJECT_ROOT/docker-compose.yml" build app; then
    log_success "App image built successfully"
else
    log_error "Failed to build app image"
    exit 1
fi

echo ""
echo "=== Starting Ollama Service ==="
# Check if ollama is already running
if docker compose -f "$PROJECT_ROOT/docker-compose.yml" ps ollama | grep -q "Up"; then
    log_info "Ollama service already running"
else
    log_info "Starting Ollama service..."
    docker compose -f "$PROJECT_ROOT/docker-compose.yml" up -d ollama
fi

log_info "Waiting for Ollama to be healthy..."
if ! "$SCRIPT_DIR/check-health.sh" 120 ollama; then
    log_warn "Ollama health check failed; attempting model pull anyway"
fi

echo ""
echo "=== Pulling Model ==="
log_info "Pulling primary model (qwen2.5-coder:7b-q4_0)..."
# ollama pull is idempotent - it will skip if model already exists
if docker compose -f "$PROJECT_ROOT/docker-compose.yml" run --rm ollama ollama pull qwen2.5-coder:7b-q4_0; then
    log_success "Model ready"
else
    log_error "Failed to pull model"
    exit 1
fi

echo ""
echo "=== Initializing Chroma DB ==="
# Check if Chroma DB already exists
if [ -d "$PROJECT_ROOT/chroma_db" ] && [ -n "$(ls -A "$PROJECT_ROOT/chroma_db" 2>/dev/null)" ]; then
    log_info "Chroma DB already initialized, skipping..."
else
    log_info "Initializing Chroma DB with preseeds..."
    if docker compose -f "$PROJECT_ROOT/docker-compose.yml" run --rm app python src/memory_setup.py; then
        log_success "Chroma DB initialized"
    else
        log_error "Failed to initialize Chroma DB"
        exit 1
    fi
fi

echo ""
log_success "Build complete!"
echo ""
echo "Next steps:"
echo "  1. Start all services: ./scripts/deploy.sh"
echo "  2. Or start manually: docker compose up"

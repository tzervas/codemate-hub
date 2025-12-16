#!/usr/bin/env bash
# Pre-flight checks for docker-compose startup
# This script validates the environment before deployment
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

echo "=== Pre-flight Checks ==="

# Check 1: Docker installed
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed"
    echo "  Install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
log_success "Docker found: $(docker --version)"

# Check 2: Docker daemon running
if ! docker ps &> /dev/null; then
    log_error "Docker daemon not running or permission denied"
    echo "  Start Docker daemon or add user to docker group"
    exit 1
fi
log_success "Docker daemon is running"

# Check 3: docker compose available
if ! docker compose version &> /dev/null; then
    log_error "docker compose not available"
    echo "  Requires Docker Compose V2 (included with Docker Desktop)"
    exit 1
fi
log_success "docker compose available: $(docker compose version --short)"

# Check 4: Environment file exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    log_warn ".env file not found"
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        log_info "Creating .env from .env.example..."
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        log_warn "Please edit .env and set required values (especially PASSWORD)"
        log_error "After editing .env, run this script again"
        exit 1
    else
        log_error ".env.example not found. Cannot create .env template."
        exit 1
    fi
fi
log_success ".env file exists"

# Load environment variables from .env
set -a
source "$PROJECT_ROOT/.env"
set +a

# Check 5: Required environment variables
REQUIRED_VARS=(
    "PASSWORD"
    "OLLAMA_BASE_URL"
    "CHROMA_DB_DIR"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    log_error "Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Edit .env and set these variables, then run this script again"
    exit 1
fi
log_success "All required environment variables set"

# Check 6: PASSWORD strength (basic check)
if [ ${#PASSWORD} -lt 8 ]; then
    log_warn "PASSWORD is shorter than 8 characters (current: ${#PASSWORD})"
    log_info "Consider using a stronger password for security"
fi

# Check 7: GPU detection and warning
if command -v nvidia-smi &> /dev/null; then
    log_success "NVIDIA GPU detected: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
    if docker run --rm --runtime=nvidia nvidia/cuda:12.0.0-runtime-ubuntu22.04 nvidia-smi &> /dev/null 2>&1; then
        log_info "nvidia-docker appears to be configured"
        log_info "To enable GPU: uncomment 'runtime: nvidia' in docker-compose.yml"
    else
        log_warn "NVIDIA GPU found but nvidia-docker may not be configured"
        log_info "Proceeding with CPU-only mode"
    fi
else
    log_info "No NVIDIA GPU detected; using CPU-only mode"
fi

# Check 8: Required files exist
REQUIRED_FILES=(
    "docker-compose.yml"
    "Dockerfile"
)
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$PROJECT_ROOT/$file" ]; then
        log_error "Required file missing: $file"
        exit 1
    fi
done
log_success "All required files present"

# Check 9: Disk space (warn if low)
AVAILABLE_SPACE=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')  # in KB
REQUIRED_SPACE=$((10 * 1024 * 1024))  # 10 GB in KB
if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
    SPACE_GB=$((AVAILABLE_SPACE / 1024 / 1024))
    log_warn "Low disk space available: ${SPACE_GB}GB"
    log_info "Ollama models can be large (5-30GB each); ensure sufficient space"
else
    SPACE_GB=$((AVAILABLE_SPACE / 1024 / 1024))
    log_success "Sufficient disk space available: ${SPACE_GB}GB"
fi

echo ""
log_success "All checks passed! Ready to proceed."

#!/usr/bin/env bash
# Complete teardown of containers and volumes
# This script is idempotent - safe to run multiple times
# WARNING: This will delete ALL containers and volumes, including data

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

# Skip confirmation if --force or -f flag is passed
FORCE=false
if [ "${1:-}" = "--force" ] || [ "${1:-}" = "-f" ]; then
    FORCE=true
fi

if [ "$FORCE" = false ]; then
    echo ""
    log_warn "WARNING: This will stop and remove all containers and volumes."
    log_warn "Data in ollama_data and chroma_db volumes will be lost!"
    echo ""
    read -r -p "Continue? (type 'yes' to confirm): " CONFIRM

    if [ "$CONFIRM" != "yes" ]; then
        log_info "Aborted."
        exit 0
    fi
fi

echo ""
echo "=== Stopping Services ==="
# Check if any services are running
if docker compose -f "$PROJECT_ROOT/docker-compose.yml" ps --services --filter "status=running" 2>/dev/null | grep -q .; then
    log_info "Stopping running services..."
    docker compose -f "$PROJECT_ROOT/docker-compose.yml" down -v --remove-orphans
    log_success "Services stopped and removed"
else
    log_info "No running services found, cleaning up resources..."
    # Still run down to clean up any stopped containers/networks
    docker compose -f "$PROJECT_ROOT/docker-compose.yml" down -v --remove-orphans 2>/dev/null || true
fi

echo ""
echo "=== Pruning Unused Resources ==="
log_info "Removing unused Docker resources..."
docker system prune -f
log_success "Unused resources pruned"

echo ""
log_success "Teardown complete."
echo ""
echo "To restart the application:"
echo "  ./scripts/deploy.sh"
echo ""
echo "To rebuild from scratch:"
echo "  ./scripts/build.sh"

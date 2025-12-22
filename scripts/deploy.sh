#!/usr/bin/env bash
# Deploy the dockerized agentic assistant
# This script is idempotent - safe to run multiple times
# Usage: ./scripts/deploy.sh [detached|attached|skip-build]
# Default: detached mode (runs in background)

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"
MODE=${1:-detached}

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

# Run build first unless skip-build is specified
if [ "$MODE" != "skip-build" ]; then
    log_info "Building application..."
    if ! "$SCRIPT_DIR/build.sh"; then
        log_error "Build failed"
        exit 1
    fi
else
    log_info "Skipping build as requested"
    MODE="detached"  # Reset mode to detached after processing skip-build
fi

echo ""
echo "=== Deploying Services ==="

if [ "$MODE" = "detached" ]; then
    log_info "Starting services in background..."
    docker compose -f "$PROJECT_ROOT/docker-compose.yml" up -d
    
    echo ""
    log_info "Services starting. Waiting for health checks..."
    if "$SCRIPT_DIR/check-health.sh" 120; then
        echo ""
        log_success "Deployment successful!"
        echo ""
        echo "Access points (via Nginx Ingress):"
        echo "  - Open-WebUI (Main): http://localhost"
        echo "  - Langflow UI: http://localhost/langflow/"
        echo "  - Code Server: http://localhost/code/"
        echo "  - App API: http://localhost/api/"
        echo ""
        # Try to detect LAN IP for remote access
        LAN_IP=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}')
        if [ -z "$LAN_IP" ]; then
            LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
        fi

        if [ -n "$LAN_IP" ]; then
            echo "LAN access (same network):"
            echo "  - Open-WebUI (Main): http://$LAN_IP"
            echo "  - Langflow UI: http://$LAN_IP/langflow/"
            echo "  - Code Server: http://$LAN_IP/code/"
            echo "  - App API: http://$LAN_IP/api/"
            echo ""
        else
            echo "LAN access: use your host's LAN IP (auto-detection failed)."
            echo ""
        fi

        echo "Direct Access (Internal Ports):"
        echo "  - Ollama API: http://localhost:11434"
        echo "  - Stable Diffusion: http://localhost:7861"
        echo ""
        echo "Useful commands:"
        echo "  - View logs: docker compose logs -f"
        echo "  - Run pipeline: docker exec coding-assistant python src/pipeline.py"
        echo "  - Stop services: docker compose down"
        echo "  - Restart: ./scripts/deploy.sh skip-build  # Skip rebuild"
    else
        log_error "Services failed to become healthy"
        log_info "Displaying service logs..."
        docker compose -f "$PROJECT_ROOT/docker-compose.yml" logs --tail=50
        exit 1
    fi
else
    log_info "Starting services in attached mode (Ctrl+C to stop)..."
    docker compose -f "$PROJECT_ROOT/docker-compose.yml" up
fi

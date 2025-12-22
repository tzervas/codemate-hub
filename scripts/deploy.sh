#!/usr/bin/env bash
# Deploy the dockerized agentic assistant
# Usage: ./scripts/deploy.sh [detached|attached]
# Default: detached mode (runs in background)

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"
MODE=${1:-detached}

# Run build first
echo "Building application..."
"$SCRIPT_DIR/build.sh"

echo ""
echo "=== Deploying Services ==="

if [ "$MODE" = "detached" ]; then
    echo "Starting services in background..."
    docker compose -f "$PROJECT_ROOT/docker-compose.yml" up -d
    
    echo ""
    echo "Services starting. Waiting for health checks..."
    if "$SCRIPT_DIR/check-health.sh" 120; then
        echo ""
        echo "✅ Deployment successful!"
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
    else
        echo "❌ Services failed to become healthy"
        docker compose logs
        exit 1
    fi
else
    echo "Starting services in attached mode..."
    docker compose -f "$PROJECT_ROOT/docker-compose.yml" up
fi

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
        echo "Access points:"
        echo "  - Langflow UI: http://localhost:7860"
        echo "  - Code Server: http://localhost:8080"
        echo "  - Ollama API: http://localhost:11434"
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

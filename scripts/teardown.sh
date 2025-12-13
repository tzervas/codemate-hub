#!/usr/bin/env bash
# Complete teardown of containers and volumes
# WARNING: This will delete ALL containers and volumes, including data

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

echo "⚠️  WARNING: This will stop and remove all containers and volumes."
echo "Data in ollama_data and chroma_db volumes will be lost!"
read -p "Continue? (type 'yes' to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "=== Stopping Services ==="
docker compose -f "$PROJECT_ROOT/docker-compose.yml" down -v --remove-orphans

echo ""
echo "=== Pruning Unused Resources ==="
docker system prune -f

echo ""
echo "✅ Teardown complete."
echo "To restart: ./scripts/deploy.sh"

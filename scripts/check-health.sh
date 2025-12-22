#!/usr/bin/env bash
# Wait for services to become healthy. 
# Usage: 
#   ./scripts/check-health.sh [timeout_seconds] [service_name]
# Examples:
#   ./scripts/check-health.sh 120        # Check all services with 120s timeout
#   ./scripts/check-health.sh 60 ollama  # Check only ollama with 60s timeout

set -euo pipefail

TIMEOUT=${1:-120}
SERVICE=${2:-all}  # 'all', 'ollama', 'langflow', 'app', 'open-webui', 'nginx', 'ingress'
SLEEP=3
END=$((SECONDS + TIMEOUT))

check() {
  local URL=$1
  if curl --silent --fail --max-time 5 "$URL" >/dev/null 2>&1; then
    return 0
  else
    return 1
  fi
}

echo "Waiting up to ${TIMEOUT}s for services (${SERVICE})..."

if [ "$SERVICE" = "ollama" ] || [ "$SERVICE" = "all" ]; then
  while ! check "http://localhost:11434/api/tags"; do
    if [ $SECONDS -ge $END ]; then
      echo "❌ ollama did not become available in time" >&2
      exit 1
    fi
    sleep $SLEEP
  done
  echo "✓ ollama OK"
fi

if [ "$SERVICE" = "langflow" ] || [ "$SERVICE" = "all" ]; then
  while ! check "http://localhost:7860"; do
    if [ $SECONDS -ge $END ]; then
      echo "❌ langflow did not become available in time" >&2
      exit 1
    fi
    sleep $SLEEP
  done
  echo "✓ langflow OK"
fi

if [ "$SERVICE" = "app" ] || [ "$SERVICE" = "all" ]; then
  while ! check "http://localhost:8000"; do
    if [ $SECONDS -ge $END ]; then
      echo "❌ app did not become available in time" >&2
      exit 1
    fi
    sleep $SLEEP
  done
  echo "✓ app OK"
fi

if [ "$SERVICE" = "open-webui" ] || [ "$SERVICE" = "nginx" ] || [ "$SERVICE" = "ingress" ] || [ "$SERVICE" = "all" ]; then
  while ! check "http://localhost"; do
    if [ $SECONDS -ge $END ]; then
      echo "❌ ingress (nginx + open-webui) did not become available in time" >&2
      exit 1
    fi
    sleep $SLEEP
  done
  echo "✓ ingress (nginx + open-webui) OK"
fi

echo "✅ Service checks passed"

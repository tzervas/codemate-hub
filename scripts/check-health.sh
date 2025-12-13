#!/usr/bin/env bash
set -euo pipefail

# Wait for services to become healthy. Usage: ./scripts/check-health.sh [timeout_seconds]
TIMEOUT=${1:-120}
SLEEP=3
END=$((SECONDS + TIMEOUT))

check() {
  URL=$1
  if curl --silent --fail --max-time 5 "$URL" >/dev/null; then
    return 0
  else
    return 1
  fi
}

echo "Waiting up to ${TIMEOUT}s for services..."

until check "http://localhost:11434/api/tags"; do
  if [ $SECONDS -ge $END ]; then
    echo "ollama did not become available in time" >&2
    exit 1
  fi
  sleep $SLEEP
done
echo "ollama OK"

until check "http://localhost:7860"; do
  if [ $SECONDS -ge $END ]; then
    echo "langflow did not become available in time" >&2
    exit 1
  fi
  sleep $SLEEP
done
echo "langflow OK"

until check "http://localhost:8000"; do
  if [ $SECONDS -ge $END ]; then
    echo "app did not become available in time" >&2
    exit 1
  fi
  sleep $SLEEP
done
echo "app OK"

echo "All services healthy"

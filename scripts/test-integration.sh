#!/usr/bin/env bash
# Integration test: Verify docker-compose can start and services become healthy
# This test performs a full smoke test of the deployment

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"
TEST_TIMEOUT=300  # 5 minutes max
TEST_MODE=${1:-dry-run}  # dry-run or full

echo "=== Docker Compose Integration Test (${TEST_MODE} mode) ==="
echo ""

# Preflight checks
echo "Step 1: Running preflight checks..."
if "$SCRIPT_DIR/preflight-check.sh"; then
    echo "✓ Preflight checks passed"
else
    echo "❌ Preflight checks failed"
    exit 1
fi

echo ""
echo "Step 2: Validating Ollama health configuration..."
if "$SCRIPT_DIR/test-ollama-health.sh"; then
    echo "✓ Ollama health configuration valid"
else
    echo "❌ Ollama health configuration invalid"
    exit 1
fi

echo ""
echo "Step 3: Validating docker-compose.yml..."
cd "$PROJECT_ROOT"
if docker compose config > /dev/null 2>&1; then
    echo "✓ docker-compose.yml is valid YAML"
else
    echo "❌ docker-compose.yml has errors"
    exit 1
fi

echo ""
echo "Step 4: Building images..."
if docker compose build --quiet app &> /dev/null; then
    echo "✓ App image built successfully"
else
    echo "❌ App image build failed"
    exit 1
fi

if [ "$TEST_MODE" = "dry-run" ]; then
    echo ""
    echo "✅ Dry-run validation complete!"
    echo "   Run with 'full' mode to start containers:"
    echo "   $0 full"
    exit 0
fi

# Full integration test
echo ""
echo "Step 5: Starting services (full integration test)..."
echo "⏱  This may take 2-5 minutes for Ollama to download and initialize..."

# Start services
docker compose up -d

# Wait for health checks
echo ""
echo "Step 6: Waiting for services to become healthy..."
START_TIME=$(date +%s)

if "$SCRIPT_DIR/check-health.sh" "$TEST_TIMEOUT"; then
    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))
    echo ""
    echo "✅ All services healthy after ${ELAPSED}s!"
    
    echo ""
    echo "Service Status:"
    docker compose ps
    
    echo ""
    echo "Connectivity Tests:"
    
    # Test Ollama
    if curl --silent -f http://localhost:11434/api/tags > /dev/null; then
        echo "✓ Ollama API: http://localhost:11434"
        MODELS=$(curl --silent http://localhost:11434/api/tags | jq -r '.models | length' 2>/dev/null || echo "?")
        echo "  └─ Models available: $MODELS"
    else
        echo "❌ Ollama API not responding"
    fi
    
    # Test Langflow
    if curl --silent -f http://localhost:7860 > /dev/null; then
        echo "✓ Langflow UI: http://localhost:7860"
    else
        echo "⚠ Langflow UI not yet ready"
    fi
    
    # Test App container
    if docker compose exec -T coding-assistant test -f /app/src/pipeline.py; then
        echo "✓ App container: Ready"
    else
        echo "⚠ App container: Not fully initialized"
    fi
    
    echo ""
    echo "✅ Integration test PASSED!"
    echo ""
    echo "Next steps:"
    echo "  1. Access Langflow at http://localhost:7860"
    echo "  2. Access Code Server at http://localhost:8080"
    echo "  3. Run pipeline: docker exec coding-assistant python src/pipeline.py"
    echo "  4. Stop services: docker compose down"
    echo "  5. View logs: docker compose logs -f [service]"
else
    echo ""
    echo "❌ Integration test FAILED: Services did not become healthy"
    echo ""
    echo "Diagnostic Information:"
    docker compose logs --tail=50
    
    echo ""
    echo "Cleanup..."
    docker compose down
    
    exit 1
fi

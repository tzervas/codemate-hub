#!/usr/bin/env bash
# Run integration tests for codemate-hub
# These tests require running Docker services

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

echo "=== Codemate-Hub Integration Test Runner ==="
echo ""

# Check if services are running
echo "Checking service status..."
if ! docker compose ps --format json | grep -q "ollama"; then
    echo "❌ Services not running. Please start them first:"
    echo "   ./scripts/deploy.sh"
    exit 1
fi
echo "✓ Services are running"
echo ""

# Determine test mode
TEST_MODE=${1:-all}

case "$TEST_MODE" in
    "unit")
        echo "Running unit tests only (fast, no services needed)..."
        pytest tests/ -v -m "not integration" --ignore=tests/integration/
        ;;
    "integration")
        echo "Running integration tests only (requires services)..."
        pytest tests/integration/ -v -m integration
        ;;
    "quick")
        echo "Running quick integration tests (excludes slow tests)..."
        pytest tests/integration/ -v -m "integration and not slow"
        ;;
    "slow")
        echo "Running slow integration tests only..."
        pytest tests/integration/ -v -m "integration and slow"
        ;;
    "all")
        echo "Running all tests (unit + integration)..."
        pytest tests/ -v
        ;;
    "coverage")
        echo "Running all tests with coverage report..."
        pytest tests/ -v --cov=src --cov-report=html --cov-report=term
        echo ""
        echo "Coverage report generated at: htmlcov/index.html"
        ;;
    *)
        echo "Usage: $0 [unit|integration|quick|slow|all|coverage]"
        echo ""
        echo "Test modes:"
        echo "  unit        - Run only unit tests (fast, no services needed)"
        echo "  integration - Run only integration tests (requires services)"
        echo "  quick       - Run integration tests, excluding slow tests"
        echo "  slow        - Run only slow integration tests"
        echo "  all         - Run all tests (default)"
        echo "  coverage    - Run all tests with coverage report"
        echo ""
        echo "Examples:"
        echo "  $0 unit              # Quick unit tests"
        echo "  $0 integration       # Full integration test suite"
        echo "  $0 quick             # Quick smoke tests"
        echo "  $0 coverage          # Generate coverage report"
        exit 1
        ;;
esac

echo ""
echo "✅ Test run complete!"

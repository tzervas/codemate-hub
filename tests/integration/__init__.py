"""
Integration tests for codemate-hub services.

These tests require running Docker services and validate:
- Container health and availability
- API endpoints and connectivity
- End-to-end workflows

To run these tests, ensure services are running:
    ./scripts/deploy.sh
    pytest tests/integration/ -v -m integration
"""

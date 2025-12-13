# Test Fixtures

This directory contains JSON fixtures for testing the pipeline in fixture mode (without live Ollama inference).

## Fixture Files

### ollama_success.json
A well-formed Ollama API response simulating a successful code generation request.
- HTTP 200 equivalent
- Contains all required fields: `model`, `response`, `done`, `context`, durations, and counts
- Use for testing the success path

### ollama_http_error.json
Simulates an HTTP error response from Ollama (503 Service Unavailable).
- Non-200 status code
- Contains error message
- Use for testing error handling when Ollama is unavailable

### ollama_malformed.json
A malformed Ollama response missing required fields.
- Missing the `done` field
- Use for testing schema validation failures

### embedding_success.json
A well-formed embedding response.
- Contains a sample embedding vector (15 dimensions for testing)
- Use for testing memory persistence

## Test Matrix

The pipeline tests should cover these scenarios:

1. **Success**: HTTP 200, well-formed body, embeddings persisted, result returned
2. **HTTP Error**: non-200 response, `PipelineError` raised, memory untouched, failure logged
3. **Malformed Schema**: missing/invalid fields, validation failure raised, memory untouched, failure logged

## Usage in Tests

Tests load these fixtures using:
```python
import json
from pathlib import Path

fixture_path = Path(__file__).parent / "fixtures" / "ollama_success.json"
with open(fixture_path) as f:
    fixture_data = json.load(f)
```

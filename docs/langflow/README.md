# Langflow Integration Guide

## Overview

Langflow is a visual workflow orchestration tool integrated into the Codemate-Hub platform. It provides a drag-and-drop interface for creating AI workflows that interact with the Ollama LLM service.

## Architecture

### Container Configuration

The Langflow service is configured in `docker-compose.yml` with the following specifications:

- **Image**: `langflowai/langflow:latest`
- **Container Name**: `langflow`
- **Port**: 7860 (UI accessible at http://localhost:7860)
- **Dependencies**: Requires `ollama` service to be healthy before starting

### Data Persistence

Langflow data is persisted in the `./langflow_data` directory, which is mounted to `/app/langflow/.langflow` in the container.

**Key Files:**
- **Database**: `./langflow_data/langflow.db` - SQLite database storing flow definitions, configurations, and metadata
- **Flows**: Flow exports are stored as JSON files in `./langflow_data/` directory

**Note**: The `langflow_data/` directory is excluded from version control (see `.gitignore`). Flow templates and examples should be documented and versioned separately in `docs/langflow/examples/`.

### Environment Variables

The Langflow container is configured with:

```yaml
environment:
  - LANGFLOW_DATABASE_URL=sqlite:///./langflow_data/langflow.db
  - OLLAMA_BASE_URL=http://ollama:11434
```

- `LANGFLOW_DATABASE_URL`: Path to the SQLite database for persisting flows and configurations
- `OLLAMA_BASE_URL`: Internal Docker network URL for Ollama API access

## Accessing Langflow

### Starting Langflow

1. Ensure all services are running:
   ```bash
   ./scripts/deploy.sh
   ```

2. Wait for services to reach healthy status:
   ```bash
   ./scripts/check-health.sh 120
   ```

3. Access the Langflow UI at: http://localhost:7860

### First-Time Setup

On first access, Langflow will:
1. Initialize the SQLite database at `./langflow_data/langflow.db`
2. Create default configuration files
3. Present the flow creation interface

## Working with Flows

### Creating a Flow

1. Open Langflow UI (http://localhost:7860)
2. Click "New Flow" or select a template
3. Drag components from the sidebar:
   - **LLM**: Use Ollama components configured with `http://ollama:11434`
   - **Prompts**: Template and chain prompts
   - **Chains**: Sequential or conditional workflows
   - **Tools**: Python code execution, API calls, etc.
4. Connect components by dragging between connection points
5. Configure each component's parameters
6. Save the flow with a descriptive name

### Exporting Flows

To export a flow for sharing or backup:

1. In Langflow UI, open the flow you want to export
2. Click the "Export" button (usually in the top toolbar)
3. Choose export format:
   - **JSON**: Full flow definition (recommended)
   - **Python**: Generated Python code
4. Save the exported file to `docs/langflow/examples/` for version control
5. Document the flow purpose and usage in this guide

**Alternative Export Method** (via CLI):
```bash
# Copy from container's database to local examples directory
docker cp langflow:/app/langflow/.langflow/your-flow.json docs/langflow/examples/
```

### Importing Flows

To import a previously exported flow:

1. In Langflow UI, click "Import" or "Upload"
2. Select the JSON file from your local machine or examples directory
3. The flow will be loaded into the editor
4. Verify component connections and configurations
5. Save the imported flow

**Alternative Import Method** (via volume mount):
```bash
# Copy example flow to langflow_data directory
cp docs/langflow/examples/example-flow.json langflow_data/

# The flow will be available in Langflow UI after restart
docker compose restart langflow
```

## Example Flows

Example flows are documented in `docs/langflow/examples/` with:
- Flow JSON files
- README describing each flow's purpose
- Configuration requirements
- Expected inputs/outputs
- Integration points with `src/pipeline.py`

See [examples/README.md](./examples/README.md) for detailed flow documentation.

## Integration with Pipeline

### Langflow ↔ Pipeline Mapping

The Langflow workflows can complement or replace parts of the Python pipeline in `src/pipeline.py`:

| Pipeline Component | Langflow Equivalent | Notes |
|-------------------|---------------------|-------|
| `OllamaClient.generate()` | Ollama LLM component | Both use same Ollama API endpoint |
| Prompt templates | Prompt Template component | Visual prompt engineering |
| Chain logic | Chain components | Sequential processing |
| Memory/Context | Vector Store components | Can integrate with Chroma DB |

### Using Langflow from Python

Langflow provides a REST API for triggering flows programmatically:

```python
import requests

def run_langflow(flow_id: str, inputs: dict) -> dict:
    """Execute a Langflow flow via API."""
    response = requests.post(
        f"http://localhost:7860/api/v1/run/{flow_id}",
        json={"inputs": inputs}
    )
    return response.json()
```

**Note**: Integration with the existing pipeline is optional and depends on use case requirements.

## Troubleshooting

### Langflow UI Not Accessible

```bash
# Check container status
docker compose ps langflow

# View logs
docker compose logs langflow

# Verify health
curl http://localhost:7860/health
```

### Database Locked Errors

If you encounter SQLite database lock errors:

```bash
# Stop all services
docker compose down

# Remove lock files
rm -f langflow_data/*.lock langflow_data/.*.lock

# Restart services
./scripts/deploy.sh
```

### Flow Import Fails

- Verify JSON syntax is valid
- Check that component versions match
- Ensure all required components are available in your Langflow version
- Review Langflow logs for specific error messages

### Ollama Connection Issues

If flows cannot connect to Ollama:

1. Verify Ollama service is healthy:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. Check environment variable in container:
   ```bash
   docker exec langflow env | grep OLLAMA_BASE_URL
   ```

3. Ensure the URL uses container network name: `http://ollama:11434`

## Best Practices

1. **Version Control**: Export flows to `docs/langflow/examples/` and commit JSON files
2. **Documentation**: Document each flow's purpose, inputs, outputs, and dependencies
3. **Naming**: Use descriptive flow names (e.g., `code-review-with-context`, `bug-analysis`)
4. **Testing**: Test flows thoroughly before integrating with production pipelines
5. **Backup**: Regularly backup `langflow_data/langflow.db` before major changes
6. **Resource Usage**: Monitor LLM token usage and response times for complex flows

## Next Steps

1. Create example flows for common coding assistant tasks
2. Document flow patterns and best practices
3. Integrate selected flows with the Python pipeline
4. Set up automated flow testing and validation

## References

- [Langflow Documentation](https://docs.langflow.org/)
- [Ollama API Reference](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Docker Compose Configuration](../../docker-compose.yml)
- [Pipeline Implementation](../../src/pipeline.py)

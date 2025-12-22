# Dockerized Agentic Coding Assistant

A containerized multi-service platform for running an AI-powered coding assistant with Ollama, Langflow, development environment, and comprehensive observability.

## Features

- **Signal-Based Agent Orchestration**: Event-driven task coordination with parallel/sequential execution
- **Local LLM Inference**: Ollama-based model serving with GPU/CPU support
- **Visual Workflows**: Langflow for prompt chain orchestration
- **Integrated Development**: Code-Server for remote VS Code access
- **Vector Memory**: Chroma DB for persistent embeddings

## Services

### Core Services
- **Ollama**: Local LLM inference engine (port 11434)
- **Langflow**: Visual workflow orchestration (port 7860)
- **Code-Server**: Remote VS Code IDE (port 8080)
- **App**: Python coding assistant with pipeline runner and task orchestration (port 8000)
- **Open-WebUI**: Web interface for LLM interactions (port 3000)

### Observability Stack
- **Grafana**: Metrics visualization and dashboards (port 3001)
- **Prometheus**: Metrics collection and alerting (port 9090)
- **Loki**: Log aggregation (port 3100)
- **Tempo**: Distributed tracing (port 3200)
- **OpenTelemetry Collector**: Unified telemetry pipeline
- **Node Exporter**: System metrics (port 9100)
- **cAdvisor**: Container metrics (port 8081)

### MCP Servers (Rust SDK)
- **filesystem**: File operations
- **memory**: Persistent key-value store
- **sqlite**: SQL database operations
- **fetch**: HTTP requests
- **github**: GitHub API (optional)
- **sequential-thinking**: Chain-of-thought reasoning
- **brave-search**: Web search (optional)
- **postgres**: PostgreSQL (optional)

## Quick Start

### 1. Prerequisites

- Docker and Docker Compose
- Linux host (or Windows/Mac with Docker Desktop)
- 10+ GB free disk space (for models)
- Optional: NVIDIA GPU with nvidia-docker for GPU acceleration

### 2. Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and set PASSWORD for code-server
nano .env
```

### 3. Deploy

```bash
# Run preflight checks and build
./scripts/preflight-check.sh

# Build images and pull models
./scripts/build.sh

# Start all services (detached mode)
./scripts/deploy.sh

# Or for attached mode with logs:
./scripts/deploy.sh attached

# (Optional) Deploy observability stack
./scripts/deploy-observability.sh start
```

### 4. Access Services

Once deployment is complete:

**Core Services:**
- **Langflow UI**: http://localhost:7860
- **Code Server**: http://localhost:8080 (password in .env)
- **Ollama API**: http://localhost:11434
- **Open-WebUI**: http://localhost:3000

**Observability (if deployed):**
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100
- **Tempo**: http://localhost:3200

- **Langflow UI**: http://localhost:7860
- **Code Server**: http://localhost:8080 (password in .env)
- **Ollama API**: http://localhost:11434

## Common Commands

### Model Management

#### List Available Models

```bash
./scripts/model-pull.sh list
```

Shows recommended models for download from Ollama Hub.

#### Pull Default Models

```bash
./scripts/model-pull.sh default
```

Pulls the default models:
- `qwen2.5-coder:7b-q4_0` - Qwen 2.5 Coder (primary, optimized for code generation)
- `mistral:latest` - Mistral 7B (fallback, general-purpose)

#### Pull a Specific Model

```bash
./scripts/model-pull.sh neural-chat:latest
```

Any valid Ollama model can be pulled. Visit https://ollama.ai/library for the full list.

#### List Local Models

```bash
docker compose run --rm ollama ollama list
```

Shows all models currently cached locally.

### Memory & Persistence

#### Memory Database Initialization

The Chroma vector database is automatically initialized on first startup. To manually verify initialization:

```bash
python src/memory_setup.py
```

This will:
- Create the Chroma database directory (chroma_db/)
- Initialize OllamaEmbeddings from the local Ollama service
- Load any preseed documents from insights/domain-preseeds/

#### Memory Management

Memory embeddings are persisted in the `chroma_db` volume:
- **Location in container**: `/app/chroma_db`
- **Host mount**: `./chroma_db` (when using docker-compose)
- **Persistence**: Survives container restarts

To reset the memory database:

```bash
# Stop containers and remove all volumes
docker-compose down -v

# Then explicitly remove the chroma_db directory
rm -rf chroma_db/
```

### Observability & Monitoring

#### Deploy Observability Stack

```bash
# Start monitoring services
./scripts/deploy-observability.sh start

# Check status
./scripts/deploy-observability.sh status

# Stop monitoring
./scripts/deploy-observability.sh stop
```

#### Access Monitoring Dashboards

- **Grafana**: http://localhost:3001 (admin/admin)
  - Pre-configured dashboards in "AI Research" folder
  - AI/ML Model Performance
  - Vector Database Metrics
  - Langflow Workflows
  - System Overview

- **Prometheus**: http://localhost:9090
  - Raw metrics and custom queries
  - Alert rules for AI/ML workloads

- **Loki**: http://localhost:3100
  - Structured log aggregation
  - Linked to traces via trace_id

- **Tempo**: http://localhost:3200
  - Distributed tracing
  - Linked to logs and metrics

#### Key Metrics

- **Inference Performance**: Request latency (p50/p95/p99), throughput, tokens/sec
- **GPU Usage**: Utilization %, memory usage, temperature
- **Vector DB**: Query latency, collection sizes, similarity scores, cache hit rate
- **Workflows**: Flow execution time, node performance, success/error rates
- **System**: CPU, memory, disk I/O, network, container metrics

For detailed observability documentation, see [docs/OBSERVABILITY.md](docs/OBSERVABILITY.md).

### Disk Usage & Model Pruning

#### Check Disk Usage

```bash
docker system df
```

Shows total size of Docker images, containers, and volumes.

#### List Prunable Models

```bash
./scripts/model-prune.sh list-unused
```

Shows models that are not in the protected set and can be safely deleted.

#### Preview Pruning (Dry-Run)

```bash
./scripts/model-prune.sh dry-run
```

Shows what would be deleted without making changes.

#### Prune Unused Models

```bash
./scripts/model-prune.sh keep-models
```

**WARNING**: Deletes all non-protected models. Protected models (qwen2.5-coder, mistral) are never removed.

To add additional models to the protected list, edit `scripts/model-prune.sh` and modify the `PROTECTED_MODELS` array.

### Check Service Health

```bash
./scripts/check-health.sh 120
```

### View Logs

```bash
docker-compose logs -f [service]
# Examples:
docker-compose logs -f ollama
docker-compose logs -f langflow
docker-compose logs -f app
```

### Run Pipeline

```bash
docker exec app python src/pipeline.py
```

### Stop Services

```bash
docker-compose down
```

### Complete Cleanup

```bash
./scripts/teardown.sh
```

## GPU Support

If you have an NVIDIA GPU and nvidia-docker installed:

1. Uncomment `runtime: nvidia` in `docker-compose.yml` (ollama service)
2. Uncomment the `NVIDIA_VISIBLE_DEVICES` environment variable
3. Redeploy: `./scripts/deploy.sh`

To verify GPU is working:

```bash
docker exec ollama nvidia-smi
```

## Troubleshooting

### Container won't start

- Run preflight checks: `./scripts/preflight-check.sh`
- Check logs: `docker-compose logs [service]`
- Ensure PASSWORD is set in .env

### Ollama not responding

- Check if ollama is healthy: `curl http://localhost:11434/api/tags`
- Verify disk space: `df -h`
- Check logs: `docker-compose logs ollama`

### Models not downloading

- Verify internet connection
- Check available disk space (models can be 5-30 GB)
- Try manually: `docker exec ollama ollama pull qwen2.5-coder:7b-q4_0`

### Memory/Embeddings issues

- Verify Chroma database exists: `ls -la chroma_db/`
- Check if memory initialization succeeded: `python src/memory_setup.py`
- Review logs: `docker-compose logs app`
- Reset database: `docker-compose down -v chroma_db && docker-compose up`

### High disk usage from models

- List local models: `docker exec ollama ollama list`
- Check model sizes: `du -sh ollama_data/`
- Preview what can be deleted: `./scripts/model-prune.sh dry-run`
- Safely prune unused models: `./scripts/model-prune.sh keep-models`

### GPU not being used

- Verify nvidia-docker is installed: `nvidia-docker --version`
- Check Ollama logs: `docker-compose logs ollama | grep -i cuda`
- Ensure `runtime: nvidia` is uncommented in docker-compose.yml

### Port conflicts

If ports are already in use:

```bash
# Change in docker-compose.yml:
# ports:
#   - "11434:11434"  -> "11435:11434" (for ollama)
#   - "7860:7860"    -> "7861:7860" (for langflow)
#   - "8080:8443"    -> "8081:8443" (for code-server)
#   - "8000:8000"    -> "8001:8000" (for app)
```

## Directory Structure

- `src/`: Python application code
  - `pipeline.py`: Pipeline orchestration
  - `signals.py`: Signal emitter/consumer system
  - `task_manager.py`: Task state management
  - `orchestrator.py`: Task orchestration engine
  - `agents.py`: Agent management
  - `orchestration_examples.py`: Usage examples
- `scripts/`: Deployment and utility scripts
- `zephyr/`: Enclave runtimes and execution environments
- `insights/`: Bootstrap data and domain preseeds
- `langflow_data/`: Langflow workspace and flows (persisted, not in git)
- `docs/langflow/`: Langflow documentation and example flows

## Langflow Workflows

Langflow provides a visual interface for creating AI workflows. See [docs/langflow/README.md](docs/langflow/README.md) for complete documentation.

### Quick Start with Langflow

1. Access Langflow UI at http://localhost:7860 after deployment
2. Import example flows from `docs/langflow/examples/`
3. Configure Ollama connection: `http://ollama:11434`
4. Create and test workflows visually

### Available Example Flows

- **Simple Code Generation**: Generate code from natural language descriptions
- **Code Review with Context**: Review code with specific focus areas
- **Documentation Generator**: Generate comprehensive code documentation

See [docs/langflow/examples/README.md](docs/langflow/examples/README.md) for detailed flow documentation.

### Integration with Pipeline

Langflow workflows can complement or replace parts of the Python pipeline. See [docs/langflow/FLOW_PATTERNS.md](docs/langflow/FLOW_PATTERNS.md) for:
- Flow pattern catalog
- Pipeline-to-Langflow mapping
- Integration strategies
- Best practices
- `langflow_data/`: Langflow workspace and flows (persisted)
- `docs/`: Documentation
  - `ORCHESTRATION.md`: Signal-based orchestration guide
- `tests/`: Test suite
  - `test_signals.py`: Signal system tests
  - `test_orchestrator.py`: Orchestrator tests
  - `test_pipeline.py`: Pipeline tests

## Agent Orchestration

The system includes a signal-based agent orchestration framework for coordinating multiple agent tasks with parallel and sequential execution.

### Quick Example

```python
from src.orchestrator import TaskOrchestrator

orchestrator = TaskOrchestrator(max_parallel_tasks=4)

# Create tasks
task1_id = orchestrator.create_task(name="Task 1", task_func=lambda: "result1")
task2_id = orchestrator.create_task(name="Task 2", task_func=lambda: "result2")

# Execute in parallel
results = orchestrator.execute_tasks_parallel([task1_id, task2_id])
```

### Features

- **Event-driven coordination**: Signal-based pub-sub for task lifecycle events
- **Parallel execution**: Thread pool for concurrent task processing
- **Dependency resolution**: Automatic task ordering based on dependencies
- **Agent management**: Agent pools with role-based assignment
- **Priority scheduling**: Task priority levels (LOW, NORMAL, HIGH, CRITICAL)

### Documentation

See `docs/ORCHESTRATION.md` for complete API reference and examples.

### Running Examples

```bash
# Run all orchestration examples (including next 3 tasks demo)
python -m src.orchestration_examples

# Run orchestration tests
python -m pytest tests/test_signals.py tests/test_orchestrator.py -v
```

## Development

### Adding Dependencies

1. Update `requirements.txt`
2. Rebuild: `docker-compose build app`

### Customizing Pipeline

The pipeline orchestrator (`src/pipeline.py`) coordinates code generation requests and manages memory persistence.

#### Test Pipeline Locally

```bash
# Run in fixture mode (uses test fixtures, no Ollama required)
python src/pipeline.py
```

This executes a test run using pre-recorded fixtures, validating:
- Request/response handling
- Schema validation
- Error handling
- Embedding generation (simulated)

#### Run Pipeline in Container

```bash
docker exec coding-assistant python src/pipeline.py
```

#### Pipeline Testing

The pipeline has comprehensive regression tests operating in fixture mode:

```bash
# Install test dependencies
pip install pytest pydantic

# Run all pipeline tests
pytest tests/test_pipeline.py -v

# Run specific test class
pytest tests/test_pipeline.py::TestPipelineSuccess -v
```

**Test Matrix Coverage:**
- ✅ Success scenario: HTTP 200, well-formed response, embeddings persisted
- ✅ HTTP error scenario: Non-200 response, PipelineError raised, memory untouched
- ✅ Malformed schema: Validation failure, memory untouched, failure logged

All tests run in fixture mode without requiring live Ollama, making them fast and deterministic for CI/CD.

### Accessing Application Container

```bash
docker exec -it coding-assistant bash
```

### Branch Management

#### Updating Subsidiary Branches

When `main` receives new commits, subsidiary feature branches may need to be updated to include the latest changes. An automated script is provided for this purpose:

```bash
# Preview what would be updated (dry-run mode)
./scripts/update-subsidiary-branches.sh --dry-run

# Execute the branch updates
./scripts/update-subsidiary-branches.sh
```

**Features:**
- Automatically fetches and merges `main` into all subsidiary branches
- Detects and reports merge conflicts
- Provides detailed progress reporting
- Supports dry-run mode for safe testing
- Rolls back on push failures

**Documentation:**
- `BRANCH_UPDATE_STRATEGY.md` - Complete update strategy and approach
- `CONFLICT_RESOLUTION_GUIDE.md` - Step-by-step conflict resolution guide
- `BRANCH_UPDATE_EXECUTION_SUMMARY.md` - Execution summary and results

**Common Scenarios:**

1. **Clean merge** - Branch updates automatically and pushes
2. **Conflicts detected** - Merge is aborted, manual resolution required
3. **Already up-to-date** - Branch is skipped

For branches with conflicts, follow the detailed resolution guide in `CONFLICT_RESOLUTION_GUIDE.md`.

## Cleanup

Remove all containers, volumes, and unused images:

```bash
./scripts/teardown.sh
```

This will delete stored data (models, embeddings, database). To preserve data, use:

```bash
docker-compose down
```

## GitHub Actions CI/CD & Secrets

### Setting Up GitHub Secrets

For production deployments and CI/CD pipeline, sensitive values should be stored as GitHub Secrets:

```bash
# Set API keys as secrets (requires gh CLI)
gh secret set CODESERVER_PASSWORD -b "your-secure-password"
gh secret set OPENAI_API_KEY -b "sk-your-openai-key"
gh secret set ANTHROPIC_API_KEY -b "your-anthropic-key"

# View all secrets
gh secret list
```

### CI Environment Files

- `.env.example` - Template for local development (safe to commit)
- `.env.ci` - CI/CD environment (safe to commit, test values only)
- `.env` - Local development (add to .gitignore, create from .env.example)

The CI pipeline automatically uses `.env.ci` for testing. Sensitive values are injected via GitHub Secrets in the workflow.

## For More Information

- See `trackers/` for detailed project planning and milestones
- See `trackers/SPEC.md` for technical specifications
- See `trackers/OVERVIEW.md` for architecture overview
- See `docs/langflow/` for Langflow workflow documentation and examples


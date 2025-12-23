# Dockerized Agentic Coding Assistant

A containerized multi-service platform for running an AI-powered coding assistant with Ollama, Langflow, development environment, and comprehensive observability.

## Features

- **Signal-Based Agent Orchestration**: Event-driven task coordination with parallel/sequential execution
- **Local LLM Inference**: Ollama-based model serving with GPU/CPU support
- **Visual Workflows**: Langflow for prompt chain orchestration
- **Integrated Development**: Code-Server for remote VS Code access
- **Vector Memory**: Chroma DB for persistent embeddings
- **Enclave Execution**: Isolated code execution with resource limits and filesystem restrictions

## Services

### Core Services
- **Ollama**: Local LLM inference engine (port 11434)
- **Langflow**: Visual workflow orchestration (port 7860)
- **Code-Server**: Remote VS Code IDE (port 8080)
- **App**: Python coding assistant with pipeline runner and task orchestration (port 8000)
- **Docs**: Self-hosted documentation and wiki (port 8001)
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

The application requires environment variables for proper operation. A template is provided:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and set required values
nano .env
```

**Required environment variables:**
- `PASSWORD` - Code-server authentication password (minimum 8 characters recommended)
- `OLLAMA_BASE_URL` - Ollama API endpoint (default: `http://ollama:11434`)
- `CHROMA_DB_DIR` - Chroma database directory (default: `/app/chroma_db`)

**Optional variables:**
- `OPENAI_API_KEY` - For GPT models
- `ANTHROPIC_API_KEY` - For Claude models
- `OLLAMA_NUM_PARALLEL` - Parallel request limit (default: 4)
- `OLLAMA_NUM_THREAD` - Thread count for computation (default: 4)

**Tip:** Run `./scripts/preflight-check.sh` to validate your configuration. It will automatically create `.env` from the template if missing.

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

### Enclave Execution

The Zephyr enclave system provides isolated execution environments for code analysis and transformation tasks.

#### Run Enclave Demo

```bash
docker exec -it coding-assistant python zephyr/demo_enclave.py
```

#### Using Enclaves in Code

```python
from src.enclave_tool import EnclaveTool

# Create an enclave with resource limits
tool = EnclaveTool()
enclave_id = tool.create_enclave(
    objective="Analyze code for security",
    max_memory_mb=512,
    max_cpu_percent=50,
    timeout_seconds=30,
    allowed_read_paths=["/app/src"],
    allowed_write_paths=["/tmp/analysis"]
)

# Execute code in the enclave
result = tool.run_in_enclave(
    enclave_id=enclave_id,
    target_function="analyze_code",
    module_path="zephyr.examples.code_analyzer",
    args={"code_file": "/app/src/pipeline.py"}
)

print(f"Analysis: {result.output}")
print(f"Memory used: {result.memory_used_mb:.2f}MB")
print(f"Execution time: {result.execution_time_ms:.2f}ms")

# Cleanup
tool.cleanup_enclave(enclave_id)
```

For more details, see [zephyr/README.md](zephyr/README.md).

### Stop Services

```bash
docker-compose down
```

### Complete Cleanup

```bash
./scripts/teardown.sh

# Or skip confirmation with force flag
./scripts/teardown.sh --force
```

## Automation Scripts

All automation scripts are located in `scripts/` and are designed to be **idempotent** (safe to run multiple times).

### Script Overview

| Script | Purpose | Idempotent |
|--------|---------|------------|
| `preflight-check.sh` | Validates environment before deployment | ✓ |
| `build.sh` | Builds images, pulls models, initializes database | ✓ |
| `deploy.sh` | Deploys all services with health checks | ✓ |
| `model-pull.sh` | Manages Ollama model downloads | ✓ |
| `model-prune.sh` | Cleans up unused models | ✓ |
| `check-health.sh` | Waits for service health checks | ✓ |
| `teardown.sh` | Complete cleanup of containers and volumes | ✓ |

### Preflight Checks

Run before deployment to validate your environment:

```bash
./scripts/preflight-check.sh
```

**What it checks:**
- Docker and Docker Compose installation
- Docker daemon status
- Environment file (`.env`) existence and validity
- Required environment variables (PASSWORD, OLLAMA_BASE_URL, CHROMA_DB_DIR)
- Password strength (warns if < 8 characters)
- GPU detection and nvidia-docker configuration
- Required project files
- Available disk space (warns if < 10GB)

**Auto-fixes:**
- Creates `.env` from `.env.example` if missing
- Provides actionable error messages for all failures

### Build Script

Builds the application and prepares all dependencies:

```bash
./scripts/build.sh
```

**What it does:**
- Runs preflight checks
- Builds Docker images
- Starts Ollama service if not running
- Pulls required models (skips if already present)
- Initializes Chroma DB (skips if already exists)

**Idempotency features:**
- Detects running services before starting
- Skips model pull if model exists
- Skips database initialization if database exists
- Safe to run multiple times

### Deploy Script

Deploys all services with health verification:

```bash
# Default: detached mode (background)
./scripts/deploy.sh

# Attached mode (see logs)
./scripts/deploy.sh attached

# Skip build for faster restarts
./scripts/deploy.sh skip-build
```

**What it does:**
- Runs build script (unless `skip-build` specified)
- Starts all services via docker-compose
- Waits for health checks (120s timeout)
- Displays access URLs and helpful commands

**Advanced usage:**
- Use `skip-build` to restart without rebuilding (much faster)
- Health checks ensure services are ready before completing

### Health Check Script

Waits for services to become healthy:

```bash
# Check all services (120s timeout)
./scripts/check-health.sh 120

# Check specific service (60s timeout)
./scripts/check-health.sh 60 ollama
```

**Supported services:**
- `ollama` - Port 11434
- `langflow` - Port 7860
- `app` - Port 8000
- `all` - All services (default)

### Teardown Script

Complete cleanup with safety confirmation:

```bash
# Interactive (asks for confirmation)
./scripts/teardown.sh

# Force mode (skip confirmation)
./scripts/teardown.sh --force
```

**What it does:**
- Stops all running services
- Removes containers and networks
- Deletes volumes (ollama_data, chroma_db)
- Prunes unused Docker resources

**⚠️ Warning:** This deletes all data including models and embeddings!

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

### Local Development Workflow

This section covers the typical development workflow when working on codemate-hub locally.

#### 1. Initial Setup for Development

```bash
# Clone the repository
git clone https://github.com/tzervas/codemate-hub.git
cd codemate-hub

# Copy and configure environment
cp .env.example .env
nano .env  # Set PASSWORD and other required vars

# Run preflight checks
./scripts/preflight-check.sh

# Build and deploy
./scripts/build.sh
./scripts/deploy.sh
```

#### 2. Working with the Application Code

**Edit code locally** - The `src/` directory is mounted into the container, so changes are reflected immediately:

```bash
# Edit files locally (e.g., with VS Code)
code src/pipeline.py

# Test changes in container without rebuild
docker exec coding-assistant python src/pipeline.py

# Or access code-server
# http://localhost:8080 (password from .env)
```

**Hot reload workflow:**
```bash
# For rapid iteration, keep the logs open
docker-compose logs -f app

# Make changes to src/ files
# Restart only the app service
docker-compose restart app
```

#### 3. Running Tests During Development

```bash
# Run unit tests (fast, no services needed)
pytest tests/test_signals.py tests/test_orchestrator.py -v

# Run pipeline tests in fixture mode
pytest tests/test_pipeline.py -v

# Run enclave tests
pytest tests/test_enclave.py tests/test_enclave_tool.py -v

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

#### 4. Debugging

**Python debugger in container:**
```bash
# Access container shell
docker exec -it coding-assistant bash

# Install debugging tools if needed
pip install ipdb

# Add breakpoint in code: import ipdb; ipdb.set_trace()
# Run the script
python src/pipeline.py
```

**View container logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f ollama

# Last 100 lines
docker-compose logs --tail=100 app
```

#### 5. Testing Model Changes

```bash
# Pull a new model to test
./scripts/model-pull.sh codellama:7b

# Test model availability
curl http://localhost:11434/api/tags

# Update src/memory_setup.py if changing embedding model
# Line 60: embedding_model = "your-new-model:tag"

# Reinitialize embeddings
docker exec coding-assistant python src/memory_setup.py
```

#### 6. Clean Iteration Cycle

```bash
# Quick restart without rebuild (preserves data)
docker-compose restart app

# Full restart with rebuild (when dependencies change)
./scripts/deploy.sh skip-build  # if built already
# or
./scripts/deploy.sh  # full rebuild

# Nuclear option: clean slate
./scripts/teardown.sh --force
./scripts/build.sh
./scripts/deploy.sh
```

### Production Deployment

This section covers deploying codemate-hub in a production environment.

#### Prerequisites for Production

- Linux server (Ubuntu 20.04+ or RHEL 8+ recommended)
- Docker 24.0+ and Docker Compose v2.20+
- Minimum 16GB RAM, 50GB disk space
- Optional: NVIDIA GPU with nvidia-docker for acceleration
- Firewall configured for ports: 11434, 7860, 8080, 8000

#### Production Setup Steps

**1. Server Preparation**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker (if not installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

**2. Configure for Production**

```bash
# Clone repository
git clone https://github.com/tzervas/codemate-hub.git
cd codemate-hub

# Create production environment file
cp .env.example .env

# Set secure production values
nano .env
```

**Production .env requirements:**
```bash
# Strong password (16+ characters)
PASSWORD="your-secure-production-password-here"

# Production URLs (use internal DNS if available)
OLLAMA_BASE_URL="http://ollama:11434"
CHROMA_DB_DIR="/app/chroma_db"

# Optional: External API keys for hybrid deployments
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."

# Performance tuning (adjust based on server specs)
OLLAMA_NUM_PARALLEL=8
OLLAMA_NUM_THREAD=8
```

**3. Security Hardening**

```bash
# Restrict .env file permissions
chmod 600 .env

# Set up firewall rules (example with ufw)
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 8080/tcp   # Code-server (consider VPN instead)
sudo ufw allow 11434/tcp  # Ollama API (internal only)
sudo ufw enable

# For production, consider:
# - Using nginx reverse proxy with SSL
# - Restricting code-server access to VPN
# - Using Docker secrets for sensitive values
```

**4. Deploy with Observability**

```bash
# Run preflight checks
./scripts/preflight-check.sh

# Build images and initialize
./scripts/build.sh

# Deploy core services
./scripts/deploy.sh

# Deploy monitoring stack
./scripts/deploy-observability.sh start

# Verify health
./scripts/check-health.sh 180
```

**5. Production Monitoring**

```bash
# Access Grafana dashboards
# http://your-server:3001 (admin/admin - change on first login)

# Key dashboards:
# - AI/ML Model Performance
# - Vector Database Metrics
# - System Overview

# Check service status
docker-compose ps

# Monitor resource usage
docker stats

# View logs
docker-compose logs -f --tail=100
```

#### Production Maintenance

**Regular tasks:**

```bash
# Weekly: Check disk usage
docker system df
./scripts/model-prune.sh list-unused

# Monthly: Update images
git pull origin main
./scripts/deploy.sh

# As needed: Backup data
tar -czf backup-$(date +%Y%m%d).tar.gz chroma_db/ langflow_data/

# As needed: Rotate logs
docker-compose logs --no-log-prefix > logs-$(date +%Y%m%d).log
```

**Disaster Recovery:**

```bash
# Stop services
docker-compose down

# Restore from backup
tar -xzf backup-20231215.tar.gz

# Restart services
./scripts/deploy.sh skip-build
```

#### Scaling for Production

**Horizontal scaling options:**

1. **Multiple Ollama instances** (load balancing)
   - Deploy ollama on separate nodes
   - Use nginx/HAProxy to distribute requests
   - Update OLLAMA_BASE_URL to point to load balancer

2. **Distributed Chroma** (high availability)
   - Use Chroma client-server mode
   - Deploy Chroma server separately
   - Point app containers to Chroma server

3. **Container orchestration** (Kubernetes, Docker Swarm)
   - Convert docker-compose.yml to K8s manifests
   - Use persistent volume claims for data
   - Deploy with StatefulSets for stateful services

**Performance tuning:**

```yaml
# In docker-compose.yml, adjust resource limits:
services:
  ollama:
    deploy:
      resources:
        limits:
          cpus: '8'
          memory: 16G
        reservations:
          cpus: '4'
          memory: 8G
          
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### Adding Dependencies

**⚠️ IMPORTANT: Use `uv` for dependency management, NOT `pip` directly.**

See [TOOLING.md](TOOLING.md) for complete dependency management guide.

```bash
# Add a new dependency
# 1. Edit pyproject.toml dependencies array
nano pyproject.toml

# 2. Regenerate lock file
uv lock --python 3.12.11

# 3. Sync locally (optional, for local testing)
uv sync --python 3.12.11

# 4. Rebuild container
docker-compose build app

# 5. Deploy
docker-compose up -d app
```

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

### Testing Strategy

The project uses a multi-layered testing approach to ensure reliability at all levels.

#### Test Organization

```
tests/
├── test_signals.py           # Unit: Signal emitter/consumer system
├── test_orchestrator.py      # Unit: Task orchestration engine
├── test_pipeline.py          # Unit: Pipeline with fixtures
├── test_enclave.py           # Unit: Enclave core functionality
├── test_enclave_tool.py      # Integration: Enclave tool API
└── fixtures/                 # Test data and mocks
```

#### Running Tests

**Unit Tests** (fast, no external dependencies):

```bash
# All unit tests
pytest tests/ -v

# Specific test file
pytest tests/test_signals.py -v

# Specific test class
pytest tests/test_orchestrator.py::TestTaskOrchestrator -v

# Specific test function
pytest tests/test_pipeline.py::TestPipelineSuccess::test_successful_generation -v

# With coverage report
pytest tests/ --cov=src --cov-report=html --cov-report=term
open htmlcov/index.html
```

**Integration Tests** (requires running services):

```bash
# Quick validation (docker-compose config + build check)
./scripts/test-integration.sh

# Full integration test (starts services, runs health checks)
./scripts/test-integration.sh full

# Or run integration tests directly
pytest tests/integration/ -v --integration
```

**Smoke Tests** (end-to-end validation):

```bash
# Validate Ollama health configuration
./scripts/test-ollama-health.sh

# Full smoke test (all services)
./scripts/check-health.sh 120

# Test specific endpoints
curl http://localhost:11434/api/tags
curl http://localhost:7860
```

#### Test Categories

1. **Unit Tests** - Test individual components in isolation
   - No external dependencies
   - Fast execution (< 1 second per test)
   - Use fixtures and mocks
   - Examples: test_signals.py, test_orchestrator.py

2. **Integration Tests** - Test component interactions
   - May require services (Ollama, Chroma)
   - Moderate execution time (seconds to minutes)
   - Test real API calls and data flow
   - Examples: test_enclave_tool.py

3. **Smoke Tests** - Validate deployment health
   - Require full service deployment
   - Test critical paths end-to-end
   - Run after deployment
   - Scripts: test-integration.sh, check-health.sh

#### Continuous Integration

The project uses GitHub Actions for CI/CD. Tests run automatically on:

- Pull requests to `main`
- Pushes to `main`
- Scheduled nightly builds

**CI test matrix:**
```yaml
# Unit tests (always)
pytest tests/ --ignore=tests/integration/

# Integration tests (if services healthy)
./scripts/test-integration.sh full

# Smoke tests (deployment validation)
./scripts/check-health.sh 180
```

#### Writing New Tests

**Unit test template:**

```python
# tests/test_my_feature.py
import pytest
from src.my_module import MyClass

class TestMyFeature:
    def setup_method(self):
        """Setup before each test method"""
        self.instance = MyClass()
    
    def test_basic_functionality(self):
        """Test description"""
        result = self.instance.my_method()
        assert result == expected_value
    
    def test_error_handling(self):
        """Test error conditions"""
        with pytest.raises(ValueError):
            self.instance.my_method(invalid_input)
```

**Integration test template:**

```python
# tests/integration/test_my_integration.py
import pytest
import requests

@pytest.mark.integration
class TestMyIntegration:
    def test_api_endpoint(self):
        """Test real API calls"""
        response = requests.get("http://localhost:11434/api/tags")
        assert response.status_code == 200
        assert "models" in response.json()
```

#### Test Configuration

**pytest configuration** (`pyproject.toml`):

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
markers = [
    "integration: Integration tests requiring services",
    "slow: Slow tests that may take minutes",
]
```

**Run tests by marker:**

```bash
# Skip integration tests
pytest tests/ -v -m "not integration"

# Only integration tests
pytest tests/ -v -m integration

# Skip slow tests
pytest tests/ -v -m "not slow"
```

#### Pre-commit Testing

Before committing code, run:

```bash
# Format code
black src/ tests/

# Lint code
ruff src/ tests/

# Run unit tests
pytest tests/ -v --ignore=tests/integration/

# Run integration tests (if services running)
pytest tests/integration/ -v -m integration
```

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


# Dockerized Agentic Coding Assistant

A containerized multi-service platform for running an AI-powered coding assistant with Ollama, Langflow, and a development environment.

## Services

- **Ollama**: Local LLM inference engine (port 11434)
- **Langflow**: Visual workflow orchestration (port 7860)
- **Code-Server**: Remote VS Code IDE (port 8080)
- **App**: Python coding assistant with pipeline runner (port 8000)

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
```

### 4. Access Services

Once deployment is complete:

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

- `src/`: Python application code (pipeline, memory setup, tools)
- `scripts/`: Deployment and utility scripts
- `zephyr/`: Enclave runtimes and execution environments
- `insights/`: Bootstrap data and domain preseeds
- `langflow_data/`: Langflow workspace and flows (persisted)

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
- See `SPEC.md` for technical specifications
- See `OVERVIEW.md` for architecture overview


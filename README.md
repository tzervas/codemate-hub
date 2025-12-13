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
```

### 4. Access Services

Once deployment is complete:

- **Langflow UI**: http://localhost:7860
- **Code Server**: http://localhost:8080 (password in .env)
- **Ollama API**: http://localhost:11434

## Common Commands

### Check Service Health

```bash
./scripts/check-health.sh 120
```

### Pull Additional Models

```bash
./scripts/model-pull.sh mistral:latest
./scripts/model-pull.sh neural-chat:latest
```

### View Logs

```bash
docker-compose logs -f [service]
# Examples:
docker-compose logs -f ollama
docker-compose logs -f langflow
docker-compose logs -f coding-assistant
```

### Run Pipeline

```bash
docker exec coding-assistant python src/pipeline.py
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

Edit `src/pipeline.py` and run:

```bash
docker exec coding-assistant python src/pipeline.py
```

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


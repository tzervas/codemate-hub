# Developer Guide - Codemate Hub

Quick start guide for developers contributing to Codemate Hub.

## Prerequisites

- Docker and Docker Compose v2+
- Git
- Linux/macOS (or Windows with WSL2)
- 10+ GB free disk space
- Optional: NVIDIA GPU with nvidia-docker for GPU acceleration
- Optional: `uv` for local Python development (see [TOOLING.md](TOOLING.md))

## Quick Start

### 1. Initial Setup

```bash
# Clone the repository
git clone https://github.com/tzervas/codemate-hub.git
cd codemate-hub

# Create .env file (required for code-server password)
cp .env.ci .env
# Edit .env and set a secure PASSWORD for code-server
nano .env
```

### 2. Build and Deploy

```bash
# Run preflight checks (validates Docker, disk space, etc.)
./scripts/preflight-check.sh

# Build all images and pull default models
# This will:
# - Build the app Docker image
# - Pull qwen2.5-coder:7b-q4_0 and mistral models
# - Initialize Chroma vector database
./scripts/build.sh

# Deploy all services in detached mode
./scripts/deploy.sh

# Or deploy in attached mode to see logs
./scripts/deploy.sh attached
```

### 3. Access Development Environment

Once deployed, access:

- **Code Server** (VS Code in browser): http://localhost:8080
  - Password: set in `.env` file
  - Workspace auto-opens at `/config/workspace` (mapped to `./src`)
  - Pre-configured with Python linting (ruff, black) and formatting
  - Recommended extensions will be suggested on first open

- **Langflow** (Visual workflows): http://localhost:7860
- **Ollama API**: http://localhost:11434
- **App Container**: `docker exec -it coding-assistant bash`

## Development Workflows

### Python Development

#### Local Development (without containers)

```bash
# Install uv (dependency manager)
curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --version 0.7.18

# Sync dependencies to local virtualenv
uv sync --python 3.12.11

# Activate virtualenv
source .venv/bin/activate

# Run code locally
python src/pipeline.py
```

See [TOOLING.md](TOOLING.md) for complete dependency management guide.

#### Container Development

```bash
# Execute commands in the app container
docker exec -it coding-assistant bash

# Run pipeline
docker exec coding-assistant python src/pipeline.py

# Run memory setup
docker exec coding-assistant python src/memory_setup.py

# Run tests
docker exec coding-assistant pytest tests/
```

### Code Quality

#### Linting

```bash
# Run ruff linter (follows pyproject.toml config)
uv run ruff check src/ tests/

# Auto-fix issues
uv run ruff check --fix src/ tests/
```

#### Formatting

```bash
# Format with black (line-length=100, py312)
uv run black src/ tests/

# Check formatting without changes
uv run black --check src/ tests/
```

#### Testing

```bash
# Run all tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/test_pipeline.py

# Run with coverage
uv run pytest --cov=src tests/

# In container
docker exec coding-assistant pytest tests/
```

### Model Management

```bash
# List available models for download
./scripts/model-pull.sh list

# Pull default models (qwen2.5-coder, mistral)
./scripts/model-pull.sh default

# Pull specific model
./scripts/model-pull.sh deepseek-coder:6.7b

# List locally cached models
docker compose run --rm ollama ollama list

# Remove unused models (dry-run first!)
./scripts/model-prune.sh dry-run
./scripts/model-prune.sh keep-models
```

### Service Management

```bash
# Check service health
./scripts/check-health.sh 120

# View logs
docker compose logs -f [service]
docker compose logs -f app
docker compose logs -f ollama
docker compose logs -f langflow
docker compose logs -f code-server

# Restart a service
docker compose restart app

# Stop all services
docker compose down

# Stop and remove all volumes (WARNING: deletes models and DB)
docker compose down -v

# Complete teardown
./scripts/teardown.sh
```

### Adding Dependencies

**NEVER use pip directly!** Use `uv` for all dependency management.

```bash
# 1. Edit pyproject.toml and add dependency to [project.dependencies]
nano pyproject.toml

# 2. Regenerate lock file
uv lock --python 3.12.11

# 3. Sync local environment
uv sync --python 3.12.11

# 4. Rebuild container
docker compose build app

# 5. Restart service
docker compose restart app
```

See [TOOLING.md](TOOLING.md) for detailed dependency management workflows.

### Working with Git

```bash
# Create feature branch
git checkout -b feature/my-feature

# Commit changes
git add .
git commit -m "feat: description of changes"

# Push to remote
git push origin feature/my-feature
```

### Memory/Vector Database

The Chroma vector database stores embeddings for code context and domain knowledge.

```bash
# Check if database exists
ls -la chroma_db/

# Manually initialize (runs automatically on first build)
docker exec coding-assistant python src/memory_setup.py

# Add custom preseed documents
# Place files in insights/domain-preseeds/
# Then reinitialize:
docker exec coding-assistant python src/memory_setup.py

# Reset database (destructive!)
docker compose down -v
rm -rf chroma_db/
./scripts/build.sh
```

## Project Structure

```
codemate-hub/
├── src/                      # Python application code
│   ├── .vscode/             # VS Code workspace settings (auto-configured)
│   ├── pipeline.py          # Main orchestration pipeline
│   ├── memory_setup.py      # Chroma DB initialization
│   ├── constants.py         # Shared constants
│   └── app.py               # FastAPI application (future)
├── tests/                   # Test suite
│   ├── test_pipeline.py     # Pipeline tests
│   └── fixtures/            # Test fixtures
├── scripts/                 # Automation scripts
│   ├── build.sh            # Build and initialize
│   ├── deploy.sh           # Deploy services
│   ├── model-pull.sh       # Model management
│   ├── model-prune.sh      # Model cleanup
│   ├── check-health.sh     # Health checks
│   └── teardown.sh         # Complete cleanup
├── zephyr/                  # Enclave runtimes (future)
├── insights/                # Bootstrap data and preseeds
├── trackers/                # Project planning docs
│   ├── tasks/              # Task trackers
│   └── PLAN.md             # Master plan
├── docker-compose.yml       # Service definitions
├── Dockerfile              # App container build
├── pyproject.toml          # Python project config
├── uv.lock                 # Dependency lock file
├── README.md               # User documentation
├── TOOLING.md              # Dependency management guide
└── TROUBLESHOOTING.md      # Error resolution guide
```

## Common Development Tasks

### Running Integration Tests

```bash
# Test Ollama health
./scripts/test-ollama-health.sh

# Test full integration
./scripts/test-integration.sh
```

### Debugging

```bash
# Enter app container shell
docker exec -it coding-assistant bash

# Check Python version
docker exec coding-assistant python --version

# Check installed packages
docker exec coding-assistant pip list

# Interactive Python REPL
docker exec -it coding-assistant python

# Check Ollama connectivity from app
docker exec coding-assistant curl http://ollama:11434/api/tags
```

### GPU Development

If you have an NVIDIA GPU:

```bash
# 1. Uncomment in docker-compose.yml:
#    runtime: nvidia (line 14)
#    NVIDIA_VISIBLE_DEVICES=all (line 16)

# 2. Rebuild and redeploy
docker compose build
./scripts/deploy.sh

# 3. Verify GPU is accessible
docker exec ollama nvidia-smi
```

## Troubleshooting

### Common Issues

**Services won't start:**
```bash
./scripts/preflight-check.sh
docker compose logs [service]
```

**Ollama not responding:**
```bash
curl http://localhost:11434/api/tags
docker compose logs ollama
```

**Port conflicts:**
Edit `docker-compose.yml` and change conflicting ports.

**High disk usage:**
```bash
docker system df
./scripts/model-prune.sh dry-run
./scripts/model-prune.sh keep-models
```

**Dependency conflicts:**
See [TOOLING.md](TOOLING.md) for resolution strategies.

For comprehensive troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Code-Server Tips

### Extensions

On first open, VS Code will suggest installing recommended extensions:
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Black Formatter (ms-python.black-formatter)
- Ruff (charliermarsh.ruff)
- Docker (ms-azuretools.vscode-docker)
- YAML (redhat.vscode-yaml)
- GitLens (eamodio.gitlens)

### Settings

Pre-configured settings in `src/.vscode/settings.json`:
- Python interpreter: `/usr/local/bin/python`
- Linting: Ruff (enabled)
- Formatting: Black (enabled, on save)
- Line length: 100
- Tab size: 4 spaces
- Testing: pytest
- File watchers exclude: `chroma_db/`, `ollama_data/`, `__pycache__/`

### Terminal

Integrated terminal in code-server runs in the container context:
```bash
# You're already in /config/workspace (src/)
pwd  # /config/workspace

# Access parent directory
cd /app

# Run Python scripts
python pipeline.py
python memory_setup.py
```

## Getting Help

- **Project Planning**: See `trackers/PLAN.md` and `trackers/tasks/`
- **Architecture**: See `trackers/OVERVIEW.md` and `trackers/SPEC.md`
- **Dependencies**: See [TOOLING.md](TOOLING.md)
- **Errors**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **User Guide**: See [README.md](README.md)

## Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make your changes
3. Run linters and tests: `uv run ruff check src/ && uv run pytest tests/`
4. Commit with descriptive message: `git commit -m "feat: add feature"`
5. Push and create pull request

## Resources

- **Ollama Models**: https://ollama.ai/library
- **Langflow Documentation**: https://docs.langflow.org/
- **CrewAI Documentation**: https://docs.crewai.com/
- **LangGraph Documentation**: https://python.langchain.com/docs/langgraph
- **uv Documentation**: https://docs.astral.sh/uv/

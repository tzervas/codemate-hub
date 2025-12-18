# Copilot Instructions for Codemate-Hub

## Quick Navigation to Authoritative Docs

**Start here for comprehensive info:**
- **[README.md](../README.md)** - Complete guide: setup, deployment, commands, troubleshooting
- **[TOOLING.md](../TOOLING.md)** - Python dependency management with `uv`, version resolution
- **[TROUBLESHOOTING.md](../TROUBLESHOOTING.md)** - Detailed error resolution (649 lines)
- **[trackers/](../trackers/)** - Project planning, milestones, specifications

**This file provides AI-specific quick reference. When in doubt, consult the docs above.**

---

## Architecture Overview

**Containerized multi-service AI coding assistant** with four services (see [README.md#Services](../README.md#Services)):
- **ollama** (port 11434): Local LLM inference, serves `qwen2.5-coder:7b-q4_0` as primary model
- **langflow** (port 7860): Visual workflow orchestration, configured to use Ollama API
- **code-server** (port 8080): Remote VS Code IDE
- **app** (port 8000): Python coding assistant with CrewAI + LangGraph pipeline

**Key Data Flows:**
- `app` → `ollama` for model inference via `http://ollama:11434` (container network)
- `app` → `chroma_db` volume for persistent vector embeddings
- `langflow` → `ollama` for workflow-based LLM interactions
- All services coordinate via `docker-compose.yml` with health checks

**Full details:** [trackers/OVERVIEW.md](../trackers/OVERVIEW.md), [trackers/SPEC.md](../trackers/SPEC.md)

## Critical Developer Workflows

**Full deployment guide:** [README.md#Quick-Start](../README.md)

### Build & Deploy
```bash
./scripts/build.sh          # Builds images, pulls models, initializes Chroma DB
./scripts/deploy.sh         # Full deployment (detached mode by default)
./scripts/deploy.sh attached   # Deploy with live logs
```

### Model Management

**Full commands:** [README.md#Model-Management](../README.md)

```bash
./scripts/model-pull.sh default     # Pull qwen2.5-coder:7b-q4_0 + mistral
./scripts/model-pull.sh list        # Show available models
./scripts/model-prune.sh list-unused # Check prunable models
docker compose run --rm ollama ollama list # List locally cached models
```

**⚠️ Default Model:** `qwen2.5-coder:7b-q4_0` is hardcoded in `src/memory_setup.py` (line 60). Change there if switching embeddings model.

### Memory/Vector DB

**Full documentation:** [README.md#Memory-&-Persistence](../README.md#Memory-&-Persistence)

- **Chroma DB** persists in `chroma_db/` volume (mapped to `/app/chroma_db` in container)
- Initialize manually when needed: `docker compose run --rm app python src/memory_setup.py` is the same command run during `build.sh` and `Dockerfile` bootstrapping.

## Python Environment & Dependencies

**⚠️ READ FIRST:** [TOOLING.md](../TOOLING.md) - Complete dependency management guide

**Tool:** `uv` (v0.7.18) for all dependency management—**never use pip directly**

**Python Version:** 3.12.11 (pinned in `pyproject.toml`)

### Adding Dependencies

**Full workflow:** [TOOLING.md#Adding-Dependencies](../TOOLING.md)

```bash
# Edit pyproject.toml dependencies array
uv lock --python 3.12.11              # Regenerate uv.lock
uv sync --python 3.12.11              # Install locally
docker compose build app              # Rebuild container
```

**⚠️ Known Conflict:** `aider-chat` removed due to `regex` version conflict with `crewai`. Details: [TOOLING.md#Dependency-Conflicts-Resolved](../TOOLING.md)

### Container Python Usage
Dependencies install via `uv` in `Dockerfile` builder stage (line 20). Runtime uses Python 3.12-slim without uv.
## Project-Specific Conventions

### File Locations
- **Application code:** `src/` (mounted into containers)
- **Agent personas:** `personas.yaml` (role presets for CrewAI agents)
- **Enclave code:** `zephyr/` (secure/isolated execution, in development)
- **Preseeds/context:** `insights/` (bootstraps for vector DB)
- **Operations scripts:** `scripts/` (all executable, use these over manual docker commands)

### Environment Variables
Critical vars in containers (see `docker-compose.yml`):
- `OLLAMA_BASE_URL`: `http://ollama:11434` (inter-container) or `http://localhost:11434` (local dev)
- `CHROMA_DB_DIR`: `/app/chroma_db` (container path)
- `PASSWORD`: code-server auth (set in `.env` file, not committed)

### Script Conventions
All scripts in `scripts/` follow this pattern:
- Use absolute paths via `SCRIPT_DIR` and `PROJECT_ROOT` variables
- Run preflight checks before critical operations
- Output color-coded logs (🔵 info, ✅ success, ⚠️ warn, ❌ error)
- Exit with `set -euo pipefail` for fail-fast behavior

## Integration Points

### Ollama API
- Healthcheck endpoint: `http://localhost:11434/api/tags`
- Model pull: `POST /api/pull` with `{"name": "model:tag"}`
- Used by: `app` (embeddings), `langflow` (workflows)

### CrewAI Personas
`personas.yaml` defines agent roles (manager, reviewer, python_worker, rust_worker). Each has:
- `role`: Agent identity
- `goal`: Primary objective
- `backstory`: Context for LLM
- `preseed_query`: Vector DB lookup key for domain knowledge

Load in code via `yaml.safe_load(open('personas.yaml'))`.

## Testing & Validation

**Health Check:** `./scripts/check-health.sh 120` (waits up to 120s for services)

**Integration Test:** `./scripts/test-integration.sh` (validates full pipeline)

**Ollama Test:** `./scripts/test-ollama-health.sh` (checks model availability)

**Manual Pipeline Run:**
```bash
docker exec coding-assistant python src/pipeline.py
```

## Common Gotchas

**Full troubleshooting:** [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) (649 lines covering all errors)

1. **Container vs Local URLs:** Use `http://ollama:11434` in containers, `http://localhost:11434` on host
2. **Model-Embedding Mismatch:** `memory_setup.py` uses `qwen2.5-coder:7b-q4_0` for embeddings—must match pulled model
3. **Volume Persistence:** `docker compose down -v` **deletes** all data (models + embeddings)
4. **GPU Support:** Requires uncommenting `runtime: nvidia` in `docker-compose.yml` and NVIDIA Docker toolkit. See [README.md#GPU-Support](../README.md)
5. **Build Order:** Always run `build.sh` before `deploy.sh` to ensure model pulls and DB init complete
6. **Port Conflicts:** See [TROUBLESHOOTING.md#Port-Already-in-Use](../TROUBLESHOOTING.md)
7. **Disk Space:** Models can be 5-30GB each. Check with `docker system df`. See [README.md#Disk-Usage-&-Model-Pruning](../README.md)

## Quick Reference

**All commands:** [README.md#Common-Commands](../README.md)

**View Logs:** `docker compose logs -f [service_name]`  
**Shell into App:** `docker exec -it coding-assistant bash`  
**Restart Service:** `docker compose restart [service_name]`  
**Full Teardown:** `./scripts/teardown.sh` (stops and removes all containers/volumes)  
**Disk Usage:** `docker system df` (check model storage consumption)

## When Things Break

1. **Start here:** [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) - indexed by error type
2. **Common errors:** Port conflicts, disk space, GPU issues, health checks
3. **Still stuck?** Check service logs: `docker compose logs [service]`

---

## Enabling Copilot 'Raptor mini' in this repository

If you're experimenting with GitHub Copilot's experimental Raptor mini model and want repository members to use it when working on `codemate-hub`, add the following workspace setting to `.vscode/settings.json` (this repository already recommends it):

```json
{
	"github.copilot": {
		"enable": true,
		"experimental": {
			"enableRaptorMini": true
		}
	}
}
```

Note: workspace settings are applied on a per-client basis and may prompt the user to accept the workspace settings the first time they open the repository. Enabling the setting at the organization level requires admin access (see `.devcontainer/README.md` for recommended org-level steps).

--
IMPORTANT: This repo is set up so Raptor mini is requested at the workspace level, but the org-level policy should limit usage to the `vector-weight` organization and the `tzervas` personal account only; follow `docs/ENABLE_RAPTOR_MINI.md` for the admin UI steps and verification.

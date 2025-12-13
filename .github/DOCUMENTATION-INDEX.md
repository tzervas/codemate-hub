# Documentation Index - Where to Find Answers

**Purpose:** Quick lookup to find the right documentation for any task. Links to authoritative sources only.

## For AI Agents

**Primary:** [copilot-instructions.md](copilot-instructions.md) - AI-specific quick reference with links to detailed docs

## Getting Started

| Task | Documentation | Key Sections |
|------|--------------|--------------|
| First-time setup | [README.md](../README.md) | Quick Start, Prerequisites, Configuration |
| Deploy the platform | [README.md](../README.md#Deploy) | Step 3: Deploy |
| Access services | [README.md](../README.md#Access-Services) | Service URLs and ports |

## Development

| Task | Documentation | Key Sections |
|------|--------------|--------------|
| Add Python dependencies | [TOOLING.md](../TOOLING.md) | Adding Dependencies |
| Fix dependency conflicts | [TOOLING.md](../TOOLING.md) | Dependency Conflicts Resolved |
| Understand project architecture | [trackers/OVERVIEW.md](../trackers/OVERVIEW.md) | Purpose, Key runtime concerns |
| Review technical specs | [trackers/SPEC.md](../trackers/SPEC.md) | Architecture, Interfaces |
| Check project roadmap | [trackers/PLAN.md](../trackers/PLAN.md) | Milestones, Timeline |

## Operations

| Task | Documentation | Key Sections |
|------|--------------|--------------|
| Pull Ollama models | [README.md](../README.md#Model-Management) | Pull Default Models, Pull Specific Model |
| Manage disk space | [README.md](../README.md#Disk-Usage-&-Model-Pruning) | Check Disk Usage, Prune Models |
| Initialize vector DB | [README.md](../README.md#Memory-&-Persistence) | Memory Database Initialization |
| Check service health | [README.md](../README.md#Check-Service-Health) | Health check scripts |
| View logs | [README.md](../README.md#View-Logs) | Log commands per service |
| Enable GPU | [README.md](../README.md#GPU-Support) | GPU configuration |
| Run the pipeline | [README.md](../README.md#Run-Pipeline) | Manual execution |
| Full cleanup | [README.md](../README.md#Cleanup) | Teardown procedures |

## Troubleshooting

| Problem | Documentation | Key Sections |
|---------|--------------|--------------|
| Docker not working | [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Pre-Deployment Issues |
| Build failures | [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Build Issues |
| Services won't start | [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Service Startup Issues |
| Health checks failing | [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Health Check Issues |
| GPU not detected | [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | GPU Issues |
| Port conflicts | [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Port Already in Use |
| Out of disk space | [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Out of Disk Space |
| Models not downloading | [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Model Download Issues |
| Memory/embeddings issues | [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Memory/Embeddings Issues |

## Configuration

| Item | Location | Notes |
|------|----------|-------|
| Environment variables | `.env` (create from `.env.example`) | Required: PASSWORD |
| Service ports | `docker-compose.yml` | Modify if conflicts exist |
| Python dependencies | `pyproject.toml` | Use `uv` to manage |
| Agent personas | `personas.yaml` | CrewAI role definitions |
| Model selection | `src/memory_setup.py` (line 60) | Hardcoded embedding model |
| Protected models | `scripts/model-prune.sh` | PROTECTED_MODELS array |

## Key Files & Directories

| Path | Purpose | Documentation |
|------|---------|--------------|
| `src/` | Application code | [trackers/OVERVIEW.md](../trackers/OVERVIEW.md) |
| `scripts/` | Operational scripts | [README.md](../README.md) - all use these |
| `zephyr/` | Enclave/isolated execution | [trackers/OVERVIEW.md](../trackers/OVERVIEW.md) |
| `insights/` | Vector DB preseeds | [README.md](../README.md#Memory-&-Persistence) |
| `langflow_data/` | Langflow workspace | [README.md](../README.md#Directory-Structure) |
| `chroma_db/` | Vector database | [README.md](../README.md#Memory-&-Persistence) |
| `trackers/` | Project planning | [trackers/README.md](../trackers/README.md) |

## Scripts Reference

| Script | Purpose | Documentation |
|--------|---------|--------------|
| `scripts/build.sh` | Build images, pull models, init DB | [README.md](../README.md#Deploy) |
| `scripts/deploy.sh` | Full deployment | [README.md](../README.md#Deploy) |
| `scripts/preflight-check.sh` | Validate environment | [README.md](../README.md#Deploy) |
| `scripts/check-health.sh` | Wait for services | [README.md](../README.md#Check-Service-Health) |
| `scripts/model-pull.sh` | Download Ollama models | [README.md](../README.md#Model-Management) |
| `scripts/model-prune.sh` | Clean up unused models | [README.md](../README.md#Disk-Usage-&-Model-Pruning) |
| `scripts/teardown.sh` | Full cleanup | [README.md](../README.md#Cleanup) |
| `scripts/test-integration.sh` | Validate pipeline | [README.md](../README.md) |
| `scripts/test-ollama-health.sh` | Test Ollama | [README.md](../README.md) |

## Documentation Maintenance

**When adding new docs:** Update this index to maintain single source of truth

**Documentation principles:**
- README.md = comprehensive user guide (setup, commands, troubleshooting)
- TOOLING.md = Python/dependency specifics
- TROUBLESHOOTING.md = error-indexed problem solving
- trackers/ = project planning and architecture
- .github/ = AI agent guidance and this index

**Avoiding duplication:** Link to authoritative docs rather than copying content

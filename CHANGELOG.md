# Changelog

_Last updated: 2025-12-13_

## Completed Tasks

### Infrastructure Tracker
- Status: ✅ COMPLETE
- Completion Date: 2024-12-13

Highlights:
- Subtask 1.1: Validate docker-compose (no GPU)
- Removed hardcoded `runtime: nvidia` from ollama service
- Made GPU runtime optional via comments
- Added CPU optimization parameters (OLLAMA_NUM_PARALLEL=4, OLLAMA_NUM_THREAD=4)
- Created `.env.example` template with documentation
- Implemented `scripts/preflight-check.sh` for comprehensive system validation
- Subtask 1.2: Validate Ollama healthcheck & CPU fallback
- Created `scripts/test-ollama-health.sh` (validates health configuration)
- Enhanced `scripts/check-health.sh` with service filtering capability
- Updated all scripts to docker compose v2 syntax (docker compose instead of docker-compose)
- Created `scripts/test-integration.sh` for full smoke testing
- All 7 health validation tests passed successfully
- Subtask 1.3: Document troubleshooting guide
- Created comprehensive `TROUBLESHOOTING.md` (~13KB, 30+ solutions)
- Enhanced `README.md` with complete quick-start guide (60+ lines)
- Documented GPU/CPU setup instructions
- Created advanced debugging and recovery sections
- Covers pre-deployment, configuration, build, startup, GPU, network, volume issues
- Subtask 1.4: Add CI smoke test
- Enhanced `.github/workflows/ci.yml` with 9 validation jobs
- Implemented: Python checks, preflight validation, YAML/Dockerfile linting
- Added: Docker image build test, smoke test (dry-run), documentation checks
- Triggers on push/PR to relevant branches with comprehensive reporting

### Models & Data Tracker
- Status: ✅ COMPLETE
- Completion Date: 2024-12-13

Highlights:
- Subtask 2.1: Ollama Service Configuration
- Enhanced docker-compose.yml with OLLAMA_HOST binding
- Added CPU optimization parameters (OLLAMA_NUM_PARALLEL=4, OLLAMA_NUM_THREAD=4)
- Configured resource limits (2 CPU/4GB memory)
- Implemented proper healthcheck (curl /api/tags every 30s)
- Created ollama_data volume for model persistence
- Subtask 2.2: Model Management Script
- Created `scripts/model-pull.sh` with 114 lines
- Three modes: list (hub models), default (pull defaults), custom (specific models)
- Default models: qwen2.5-coder:7b-q4_0 (primary), mistral:latest (fallback)
- Color-coded logging (info/success/warn/error)
- Comprehensive help documentation
- Subtask 2.3: Memory Initialization
- Implemented `src/memory_setup.py` with 171 lines
- initialize_memory(): Creates Chroma vector store with OllamaEmbeddings
- load_preseeds(): Loads domain preseed documents from insights/domain-preseeds
- Full error handling for missing dependencies and directories
- Environment variables: CHROMA_DB_DIR=/app/chroma_db, OLLAMA_BASE_URL=http://ollama:11434
- Subtask 2.4: Data Retention & Pruning
- Created `scripts/model-prune.sh` with 224 lines
- Protected models (never deleted): qwen2.5-coder:7b-q4_0, mistral:latest
- Four modes: list-unused, dry-run (preview), keep-models (execute), help
- Model size estimation and disk usage management
- Safe deletion with comprehensive logging

Progress Log:
- 2025-12-13: Finalized uv installation flow in CI (`ci: pin uv installer invocation`).

## Active Tasks

### Application & Pipeline Tracker
- Status: IN PROGRESS
- Start Date: 2025-12-13
- Branch: feature/task-03-application

Progress Log:
- 2025-12-13: Created feature branch `feature/task-03-application` to begin Task 03 subtasks.

## Pending Tasks

### Langflow Tracker
- Status: NOT STARTED

### Enclaves (Zephyr) Tracker
- Status: NOT STARTED

### Developer UX Tracker
- Status: NOT STARTED

### Automation & Scripts Tracker
- Status: NOT STARTED

### Docs & QA Tracker
- Status: NOT STARTED

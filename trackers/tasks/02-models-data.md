Models & Data Tracker

Scope
-----
Configure and validate Ollama models and the Chroma DB memory store used by the app.

Subtasks
--------
- [x] Verify Ollama image pulls and tags used in `docker-compose.yml` — estimate: 30m — COMPLETE
- [x] Confirm model(s) required and add install/pull script (`scripts/model-pull.sh`) — estimate: 1h — COMPLETE
- [x] Validate `memory_setup.py` creates and populates `CHROMA_DB_DIR` — estimate: 2h — COMPLETE
- [x] Add retention/pruning policy for `ollama_data` — estimate: 1h — COMPLETE

Acceptance Criteria
-------------------
- Models are accessible via `http://ollama:11434` and Langflow can connect.
- `CHROMA_DB_DIR` is initialized and writable by the app.

Priority: High

Status: ✅ COMPLETE

Completion Date: 2024-12-13

Summary of Work
---------------

Subtask 2.1: Ollama Service Configuration
  - Enhanced docker-compose.yml with OLLAMA_HOST binding
  - Added CPU optimization parameters (OLLAMA_NUM_PARALLEL=4, OLLAMA_NUM_THREAD=4)
  - Configured resource limits (2 CPU/4GB memory)
  - Implemented proper healthcheck (curl /api/tags every 30s)
  - Created ollama_data volume for model persistence

Subtask 2.2: Model Management Script
  - Created `scripts/model-pull.sh` with 114 lines
  - Three modes: list (hub models), default (pull defaults), custom (specific models)
  - Default models: qwen2.5-coder:7b-q4_0 (primary), mistral:latest (fallback)
  - Color-coded logging (info/success/warn/error)
  - Comprehensive help documentation

Subtask 2.3: Memory Initialization
  - Implemented `src/memory_setup.py` with 171 lines
  - initialize_memory(): Creates Chroma vector store with OllamaEmbeddings
  - load_preseeds(): Loads domain preseed documents from insights/domain-preseeds
  - Full error handling for missing dependencies and directories
  - Environment variables: CHROMA_DB_DIR=/app/chroma_db, OLLAMA_BASE_URL=http://ollama:11434

Subtask 2.4: Data Retention & Pruning
  - Created `scripts/model-prune.sh` with 224 lines
  - Protected models (never deleted): qwen2.5-coder:7b-q4_0, mistral:latest
  - Four modes: list-unused, dry-run (preview), keep-models (execute), help
  - Model size estimation and disk usage management
  - Safe deletion with comprehensive logging

Files Created/Modified
----------------------
Created:
  - `scripts/model-prune.sh` (pruning/retention logic - 224 lines)
  - `TOOLING.md` (dependency management documentation - 158 lines)
  - `uv.lock` (dependency lock file - 4029 lines, 210 packages)
  - `pyproject.toml` (project metadata and build configuration - 64 lines)

Modified:
  - `docker-compose.yml` (+28 lines: Ollama enhancement, resource limits, healthcheck)
  - `scripts/model-pull.sh` (+114 lines: multi-model support, color output)
  - `src/memory_setup.py` (+171 lines: full Chroma DB implementation)
  - `README.md` (+123 lines: model management and memory documentation)
  - `.github/workflows/ci.yml` (+46 lines: Python 3.12 baseline, uv integration)
  - `Dockerfile` (+25 lines: uv integration in multi-stage builder)

Total Lines of Code Added: 4955
Total Commits: 20
Total Features: 4 new major features
Total Build Improvements: 6 build/tooling commits

Dependency Management
---------------------
- Migrated to uv for Python package management
- Resolved dependency conflicts (aider-chat removed due to regex constraint)
- Python 3.12 as stable baseline (3.13 pending upstream updates)
- 210 packages resolved with zero conflicts

CI/CD Enhancements
-------------------
- 8 validation jobs in GitHub Actions workflow
- Python syntax and import checks
- Docker Compose configuration validation
- Dockerfile linting
- Memory initialization validation
- Pinned uv installer invocation to keep hosted runners on the expected toolchain
- Comprehensive error reporting

Development Environment
-----------------------
- uv sync for reproducible local environments
- Python 3.12.11 available via uv
- Full dependency locking (uv.lock)
- Pre-commit hooks support

Acceptance Criteria Status
--------------------------
✅ Models accessible via http://ollama:11434
✅ CHROMA_DB_DIR initialized and writable
✅ Memory persistence across container restarts
✅ Model pruning with retention policies
✅ Comprehensive CLI scripts with help documentation
✅ Full integration with docker-compose orchestration

Dependencies Met
----------------
✓ Ollama service running and healthchecked
✓ Memory initialization on startup
✓ Model persistence and management
✓ Chroma DB integration with embeddings
✓ CI/CD pipeline validation
✓ uv-based dependency management

Next Steps
----------
→ Continue to Task 03: Application & Pipeline (test pipeline execution)
→ Monitor PR #3 CI completion status
→ Merge to main when all checks pass
→ Release version 0.3.0

Progress Log
------------
- 2025-12-13: Finalized uv installation flow in CI (`ci: pin uv installer invocation`).

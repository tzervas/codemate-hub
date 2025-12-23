# Changelog

_Last updated: 2025-12-23_


## Snapshot 2025-12-23

### Completed Tasks

#### Infrastructure Tracker
_(unchanged since 2025-12-13)_

#### Models & Data Tracker
_(unchanged since 2025-12-13)_

#### Application & Pipeline Tracker
_(unchanged since 2025-12-13)_

#### Langflow Tracker
_(unchanged since 2025-12-13)_

#### Enclaves (Zephyr) Tracker
_(unchanged since 2025-12-13)_

#### Developer UX Tracker
_(unchanged since 2025-12-22)_

#### Automation & Scripts Tracker
_(unchanged since 2025-12-22)_


### Pending Tasks

#### Docs & QA Tracker
_(unchanged since 2025-12-13)_

## Snapshot 2025-12-22

### Completed Tasks

#### Infrastructure Tracker
_(unchanged since 2025-12-13)_

#### Models & Data Tracker
_(unchanged since 2025-12-13)_

#### Application & Pipeline Tracker
_(unchanged since 2025-12-13)_

#### Langflow Tracker
_(unchanged since 2025-12-13)_

#### Enclaves (Zephyr) Tracker
_(unchanged since 2025-12-13)_

#### Developer UX Tracker <!-- hash:9d35d885 -->
- Status: COMPLETED

#### Automation & Scripts Tracker <!-- hash:c6a0d2a1 -->
- Status: ✅ COMPLETE
- Completion Date: 2025-12-16

Highlights:
- Subtask 7.1: Script Idempotency Review
- Enhanced `build.sh` with idempotency checks
- * Detects if Ollama is already running before starting
- * Skips Chroma DB initialization if already exists
- * Added color-coded logging for better UX
- * Improved error handling with exit codes
- Enhanced `deploy.sh` with skip-build option
- * Added `skip-build` mode for faster restarts
- * Improved error messages with service log display
- * Added color-coded logging
- * Better health check integration
- Enhanced `teardown.sh` with safety improvements
- * Added --force/-f flag to skip confirmation
- * Detects if services are running before attempting teardown
- * Idempotent - safe to run multiple times
- * Added color-coded logging
- `model-pull.sh` already idempotent (ollama pull checks for existing models)
- `check-health.sh` already idempotent (created in Task 01)
- Subtask 7.2: Environment Variable Safety Checks
- Enhanced `preflight-check.sh` with comprehensive env var validation
- * Automatically creates .env from .env.example if missing
- * Validates required env vars: PASSWORD, OLLAMA_BASE_URL, CHROMA_DB_DIR
- * Added PASSWORD strength check (warns if < 8 chars)
- * Improved error messages with actionable guidance
- * Color-coded output for better readability
- Created `.env.example` template file
- * Comprehensive documentation for all env vars
- * Security notes and best practices
- * Examples for optional API keys (OpenAI, Anthropic)
- * Clear separation of required vs optional vars
- Subtask 7.3: Health Check Script
- `check-health.sh` already existed (created in Task 01)
- Provides service-specific health checks
- Supports timeout configuration
- Can check individual services or all services
- Integrated into build.sh and deploy.sh


### Pending Tasks

#### Docs & QA Tracker
_(unchanged since 2025-12-13)_


### 👤 Human Changes

**Fixes**
- 233e169 fix(deps): update opentelemetry versions to match crewai requirements

**Other**
- 18b8c61 Merge pull request #14 from tzervas/feature/ci-tooling (#14)

### 🤖 AI/Agent Changes

**Other**
- a430dd7 Task 06: Developer UX - workspace configuration and onboarding guide (#23) (#23)
- 46061ed Add self-hosted documentation infrastructure with MkDocs and automation (#25) (#25)
- 71fe8f1 Implement Zephyr enclave system for isolated code execution (#22) (#22)
- a643e82 Add Langflow integration documentation and example workflow templates (#21) (#21)
- 8bd7530 Implement signal-based agent orchestration with parallel task execution (#19) (#19)
- 7fc5521 Add branch update automation and documentation (#31) (#31)

### ⚙️ Bot Changes

**Other**
- 8dbd3bd Merge origin/devel - integrate Tasks 04-08 changes
- ede6d3d Merge origin/main into copilot/merge-feature-branches-for-task-07
- 8ab33cb Fix shellcheck warning: add -r flag to read command in teardown.sh
- 5a56f0c Add .env.example template file for environment configuration
- 50d2ffc Complete Task 07: Enhance automation scripts with idempotency and env validation
- 0ed2ce4 Initial plan

### Contributors

**👤 Human**
- Tyler Zervas (2 commits)

**🤖 AI/Agent**
- Copilot (6 commits)

**⚙️ Bot**
- copilot-swe-agent[bot] (6 commits)

### Areas Touched

- Application
- Configuration
- Documentation
- Other
- Scripts
- Tests

## Snapshot 2025-12-13

### Completed Tasks

#### Infrastructure Tracker <!-- hash:4c1576d0 -->
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

#### Models & Data Tracker <!-- hash:a586f024 -->
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

#### Application & Pipeline Tracker <!-- hash:a402ba9d -->
- Status: ✅ COMPLETE
- Completion Date: 2025-12-13
- Branch: feature/task-03-application

Highlights:
- Subtask 3.1: Pipeline Orchestration Implementation
- Created `src/pipeline.py` with ~330 lines of production code
- Implemented structured result types: `PipelineResult` dataclass
- Implemented exception hierarchy: `PipelineError`, `HTTPError`, `SchemaValidationError`
- Created injectable client abstraction via `OllamaClient` protocol
- Implemented three fixture clients: `FixtureClient`, `HTTPErrorFixtureClient`, `MalformedFixtureClient`
- Added Pydantic models for schema validation: `OllamaResponse`, `EmbeddingResponse`
- Comprehensive structured logging with timestamps and log levels
- Standalone execution mode for manual testing and validation
- Subtask 3.2: Test Infrastructure & Fixtures
- Created `tests/` directory structure with pytest configuration
- Created `tests/fixtures/` with comprehensive JSON test fixtures
- Four fixture files covering all test matrix scenarios:
- * `ollama_success.json` - Well-formed Ollama response (HTTP 200 equivalent)
- * `ollama_http_error.json` - HTTP error response (503 Service Unavailable)
- * `ollama_malformed.json` - Malformed response missing required fields
- * `embedding_success.json` - Well-formed embedding response
- Created `tests/fixtures/README.md` documenting fixture schemas and usage
- Subtask 3.3: Regression Test Suite
- Created `tests/test_pipeline.py` with 19 comprehensive test cases
- Test coverage breakdown:
- * TestPipelineSuccess: 3 tests (basic success, embeddings, response content)
- * TestPipelineHTTPError: 3 tests (failure result, no embeddings, duration tracking)
- * TestPipelineMalformedSchema: 3 tests (validation failure, no embeddings, error logging)
- * TestPipelineFixtures: 4 tests (verify fixture structure and integrity)
- * TestPipelineDefaultBehavior: 3 tests (default client, embeddings off, model selection)
- * TestPipelineResult: 3 tests (result structure and field validation)
- All 19 tests pass with 100% success rate
- Execution time: ~0.14s for full suite (fast enough for CI)
- All tests operate in fixture mode (no live Ollama dependency)
- Subtask 3.4: CI/CD Integration
- Added `pipeline-tests` job to `.github/workflows/ci.yml`
- Configured with Python toolchain setup via custom action
- Installs minimal dependencies (pydantic, pytest) via uv
- Runs pytest with verbose output and short traceback
- Integrated into test-results summary job
- Proper dependency ordering (needs: python-checks)
- Subtask 3.5: Documentation Updates
- Updated `README.md` with comprehensive pipeline testing section
- Added local testing instructions (both in/out of container)
- Documented test matrix coverage with checkmarks
- Explained fixture mode vs live mode operation
- Updated `CHANGELOG.md` with detailed Task 03 completion entry
- Documented all files created/modified with line counts

Progress Log:
- 2025-12-13: Created feature branch `feature/task-03-application` to begin Task 03 subtasks.
- 2025-12-13: Implemented complete fixture-based pipeline orchestration with dependency injection.
- 2025-12-13: Created comprehensive test suite with 19 tests covering all matrix scenarios.
- 2025-12-13: Integrated pipeline tests into CI/CD workflow.
- 2025-12-13: ✅ Task 03 completed - all acceptance criteria met.

#### Langflow Tracker <!-- hash:9d35d885 -->
- Status: COMPLETED

#### Enclaves (Zephyr) Tracker <!-- hash:32c78c91 -->
- Status: ✅ COMPLETE
- Completion Date: 2025-12-16


### Pending Tasks

#### Developer UX Tracker <!-- hash:e1efca75 -->
- Status: NOT STARTED

#### Automation & Scripts Tracker <!-- hash:e1efca75 -->
- Status: NOT STARTED

#### Docs & QA Tracker <!-- hash:e1efca75 -->
- Status: NOT STARTED

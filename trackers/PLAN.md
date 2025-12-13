Project Plan & Milestones

Milestones
----------
1. Discovery & baseline (this checkpoint): repo review, trackers created, decomposition finished. ✅ (Done)
2. Infrastructure: make `docker-compose` robust, healthchecks, and GPU compatibility checks. ✅ (Done)
3. Models & Data: configure Ollama models, Chroma persistence, and memory initialization. ✅ (Done)
4. Application & Pipeline: test `src/pipeline.py`, add CI for pipeline runs. ✅ (Done)
5. Langflow flows: create reproducible flows for common tasks and store in `langflow_data`. 🔄 (In Progress - `feature/task-04-langflow`)
6. Enclaves: test `zephyr` enclaves and integrate with `app`. 🔄 (In Progress - `feature/task-05-enclaves-zephyr`)
7. Automation Scripts: enhance scripts for reliability and idempotency. 🔄 (In Progress - `feature/task-07-automation-scripts`)
8. Dev UX: polish `code-server` workspace and developer onboarding. 🔄 (In Progress - `feature/task-06-dev-ux`)
9. Docs & QA: comprehensive documentation and smoke tests. 🔄 (In Progress - `feature/task-08-docs-qa`)

Timeline (updated)
------------------
- Week 0: Discovery, create trackers, plan ✅ (Complete)
- Week 1: Infrastructure + Models & Data ✅ (Complete)
- Week 2: Application + Pipeline ✅ (Complete)
- Week 3: Feature branches created with comprehensive documentation ✅ (Complete)
- Week 4+: Implementation of remaining tasks in parallel on feature branches 🔄 (In Progress)

Deliverables
------------
- `docker-compose` validated on target host
- Working pipeline example that queries Ollama and persists to Chroma
- Langflow flows exported under `langflow_data`
- Enclave execution example under `zephyr/`

Acceptance criteria
-------------------
- All containers start and reach healthy status via `docker-compose up`.
- End-to-end sample pipeline runs successfully and stores embeddings.
- Documentation updated for running locally and in CI.

Dependencies & assumptions
--------------------------
- Host has Docker and (optional) NVIDIA drivers for GPU support.
- Ollama image able to pull and run in the environment.

Feature Branches
----------------
All remaining work has been organized into focused feature branches with comprehensive documentation:

| Branch | Task | Priority | Documentation |
|--------|------|----------|---------------|
| `feature/task-04-langflow` | Langflow Integration | Medium | `TASK-04-README.md` |
| `feature/task-05-enclaves-zephyr` | Enclaves/Zephyr | Medium | `TASK-05-README.md` |
| `feature/task-06-dev-ux` | Developer UX | Low | `TASK-06-README.md` |
| `feature/task-07-automation-scripts` | Automation Scripts | Medium | `TASK-07-README.md` |
| `feature/task-08-docs-qa` | Documentation & QA | Medium | `TASK-08-README.md` |

Each feature branch includes:
- Comprehensive README with scope, subtasks, and acceptance criteria
- Getting started guide for implementation
- Related documentation links
- Best practices and implementation notes

See `FEATURE-BRANCHES.md` for complete workflow documentation.

Next steps
----------
- Work can now proceed in parallel on any of the feature branches:
  - `feature/task-04-langflow` - Langflow flows and integration
  - `feature/task-05-enclaves-zephyr` - Enclave isolation and security
  - `feature/task-06-dev-ux` - Developer experience improvements
  - `feature/task-07-automation-scripts` - Script enhancements
  - `feature/task-08-docs-qa` - Documentation and testing
- Each branch contains a TASK-XX-README.md with comprehensive implementation guidance
- See `FEATURE-BRANCHES.md` for complete overview and workflow instructions
- Suggested priority order: Task 07 → Task 04 → Task 05 → Task 08 → Task 06

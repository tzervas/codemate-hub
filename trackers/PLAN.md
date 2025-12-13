Project Plan & Milestones

Milestones
----------
1. Discovery & baseline (this checkpoint): repo review, trackers created, decomposition finished. (Done)
2. Infrastructure: make `docker-compose` robust, healthchecks, and GPU compatibility checks. (1-2 days)
3. Models & Data: configure Ollama models, Chroma persistence, and memory initialization. (2-3 days, Done)
4. Application & Pipeline: test `src/pipeline.py`, add CI for pipeline runs. (2-3 days, In Progress)
5. Langflow flows: create reproducible flows for common tasks and store in `langflow_data`. (2 days)
6. Enclaves: test `zephyr` enclaves and integrate with `app`. (2-4 days)
7. Dev UX & automation: polish `code-server` workspace, docs, scripts, deployment automation. (1-2 days)

Timeline (example)
------------------
- Week 0: Discovery, create trackers, plan (current)
- Week 1: Infrastructure + Models & Data
- Week 2: Application + Langflow flows
- Week 3: Enclaves + Automation + QA

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

Next steps
----------
- Run the acceptance smoke tests and iterate on any failing items.
- Execute Task 03 work on branch `feature/task-03-application` and update trackers after each subtask.

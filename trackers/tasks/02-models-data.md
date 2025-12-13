Models & Data Tracker

Scope
-----
Configure and validate Ollama models and the Chroma DB memory store used by the app.

Subtasks
--------
- [ ] Verify Ollama image pulls and tags used in `docker-compose.yml` — estimate: 30m
- [ ] Confirm model(s) required and add install/pull script (`scripts/model-pull.sh`) — estimate: 1h
- [ ] Validate `memory_setup.py` creates and populates `CHROMA_DB_DIR` — estimate: 2h
- [ ] Add retention/pruning policy for `ollama_data` — estimate: 1h

Acceptance Criteria
-------------------
- Models are accessible via `http://ollama:11434` and Langflow can connect.
- `CHROMA_DB_DIR` is initialized and writable by the app.

Priority: High

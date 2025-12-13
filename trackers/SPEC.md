Technical Specification

Scope
-----
This spec documents architecture, interfaces, runtime requirements, and acceptance criteria for the Dockerized Agentic Coding Assistant.

Architecture
------------
- `docker-compose.yml` coordinates four primary containers: `ollama`, `langflow`, `code-server`, and `app` (coding assistant).
- `app` runs `src/pipeline.py` and depends on `ollama` + `langflow` to be available.
- `langflow` stores its workspace in `./langflow_data` and is configured to talk to `ollama` via `OLLAMA_BASE_URL`.

Runtime configuration
---------------------
- Required ports: `11434` (ollama), `7860` (langflow UI), `8080` (code-server), `8000` (app internal port mapping).
- Required environment variables: `PASSWORD` for code-server, `OLLAMA_BASE_URL` and `CHROMA_DB_DIR` for the app.
- GPU support: `ollama` configured with `runtime: nvidia` and `NVIDIA_VISIBLE_DEVICES=all`.

Data persistence
----------------
- `ollama_data` volume stores model artifacts.
- `chroma_db` is mounted into the app to persist memory embeddings (Chroma).

Interfaces and contracts
------------------------
- `app` expects a local Ollama HTTP API at `http://ollama:11434` (see `Dockerfile` and `docker-compose.yml`).
- Langflow is expected to connect to `OLLAMA_BASE_URL` for model interactions.

Testing & Acceptance
--------------------
- Acceptance: `docker-compose up` brings all services to healthy state and `app` can call `http://ollama:11434/api/tags`.
- Integration test: a sample pipeline run in `src/pipeline.py` should connect to Ollama and write to `CHROMA_DB_DIR`.

Security & Secrets
------------------
- `PASSWORD` is stored in environment for `code-server`. Recommend using a `.env` or secrets manager in prod.

Risks
-----
- GPU runtime may not be available on all hosts; fallback plans should be documented.
- Model sizes and disk usage in `ollama_data` may grow; implement pruning or quotas.

Project Overview

Purpose
-------
This repository hosts a Dockerized Agentic Coding Assistant. It composes multiple services via `docker-compose.yml`:

- `ollama`: model server (OLLAMA) exposing a local API
- `langflow`: Langflow UI and flows for orchestrating prompt/chain workflows
- `code-server`: remote VS Code instance for developer access
- `app` (coding-assistant): local Python app containing `pipeline.py`, `memory_setup.py`, and other helpers

Key runtime concerns
--------------------
- Containerized deployment with GPU support for `ollama` (uses `runtime: nvidia` and `NVIDIA_VISIBLE_DEVICES=all`).
- Persistent volumes: `ollama_data`, `chroma_db`.
- Local dev workspace exposed into `code-server` and `app` containers via `./src` and `./zephyr` mounts.

Primary repo areas
------------------
- `src/`: application code (`pipeline.py`, `app.py`, `enclave_tool.py`, `memory_setup.py`)
- `zephyr/`: enclave code and runtime
- `insights/`: bootstraps and preseeds
- `scripts/`: build and deployment helpers
- `personas.yaml`: role presets for agent personas

High-level intent
------------------
Provide a reproducible, containerized environment to run an agentic assistant that integrates language model hosting, Langflow orchestration, and a development environment (code-server). The code includes memory setup (Chroma DB), a pipeline runner, and enclave tooling for secure or isolated execution.

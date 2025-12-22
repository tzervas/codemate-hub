Chained agent pipelines with specialized local models
===================================================

This document describes an approach for executing workflows composed of multiple specialized model steps.

Key element: run multiple small specialized models to keep latency low and to dynamically allocate compute depending on the workload. This is better for concurrency and cheaper than a single giant model for many workflows.

Example pipeline (manager / worker / reviewer)
- Manager: decomposes a broad objective into steps (small powerful model like qwen2.5-coder or neural-chat)
- Worker: executes the step (e.g., code generation by a coder-specialized model — qwen2.5-coder)
- Reviewer: critiques and offers edits/refinements (a small general model like mistral or neural-chat tuned for review)

Example usage & code snippet
----------------------------
The repository includes an `orchestrator` module with a minimal `ChainOrchestrator` demonstrating this pattern.

Usage example (Python):

```python
from src.orchestrator import ChainOrchestrator
from src.pipeline import FixtureClient

# Create fixture client for testing without a live Ollama, or provide an OllamaClient
client = FixtureClient(fixtures_dir=Path('tests/fixtures'))
orch = ChainOrchestrator(client=client, manager_model='neural-chat:latest', worker_model='qwen2.5-coder:7b-q4_0', reviewer_model='mistral:latest')
result = orch.run_chain('Create a function that reverses a string and tests it')
print(result)
```

Deployment & routing patterns
----------------------------
1. Single Ollama instance with multiple models loaded: simple and easy to manage; route at app-level by model name.
2. Ollama small + Ollama large instances: spin up separate instances for small (multi-agent) conj to handle concurrent small steps and a GPU-backed large instance for heavy single tasks.
3. Dynamic start/stop for heavy instance: use `docker compose` with GPU override to bring up `ollama-large` only when required.

Orchestration & scaling considerations
-------------------------------------
- Keep steps atomic: short tasks benefit from lower latency with smaller models.
- Use quantized models where possible to lower VRAM usage and improve concurrency.
- Add retries, watchdogs, and logging for robust in-production behavior; add custom gateways or an API router for scheduling.

Next steps you may want
----------------------
- Add logging/observability across model calls in the orchestrator (A/B tests, latency, success rate).
- Add a `chain` definition language to define agent pipelines declaratively and a simple runner.
- Add per-agent timeout and concurrency controls to avoid resource contention.

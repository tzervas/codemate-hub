Model matrix (approx. numbers for quantized variants)
---------------------------------------------------

| Model | Typical Size | Quantization | Approx VRAM (q4) | Use case | Notes |
|---|---:|---:|---:|---|---|
| qwen2.5-coder:7b-q4_0 | 7B | q4_0 | ~3-6GB | Multi-agent (2-4), low-latency codegen | Optimized for code; low resource footprint |
| mistral:latest | 7B | q4_0 | ~4-8GB | Multi-agent + general tasks | High quality general-purpose model |
| neural-chat:latest | 7B | q4_0 | ~4-8GB | Chat and assistant tasks | Instruction tuned; great for assistant flows |
| Llama 2 (13B) | 13B | q4_0 | ~12-16GB | Heavy single pipeline (high-quality) | Great for longer reasoning and codegen (check license) |
| Mixed 7B+13B | mixed | q4_0 | varies | Hybrid workflows | Use 7Bs for fast concurrency and 13B for deep work |

Notes:
- These are approximate VRAM numbers — actual usage depends on batch sizes, context window, quantization, and GPU driver.
- For concurrency (2-4 agents), use quantized 7B models to keep latency low and avoid GPU memory contention.

Deployment patterns & dynamic allocation
--------------------------------------
1) Shared Ollama for convenience: a single Ollama instance hosts multiple models and receives model requests by name; set `OLLAMA_NUM_PARALLEL` to tune CPU work.
2) Dedicated small/large Ollama instances: dedicate a `ollama-small` container for 7B models and a `ollama-large` container with the 13B model on GPU. Route requests via the `app` based on task complexity.
3) Dynamic scaling: bring up the `ollama-large` instance only on-demand for heavy jobs via `docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d ollama-large` and `down` when not needed.

Suggested selection heuristics (x = heuristics for the `app` routing policy)
-------------------------------------------------------------------
- If pipeline contains >1 high-importance stage (e.g., multi-step code generation + test), route to `llama2-13b` (heavy). x
- If parallel agents (e.g., 2-4 concurrent code-lint or small gen tasks) route to `qwen2.5-coder:7b-q4_0` or `mistral` (small). x
- If a one-off deep analysis request, prefer 13B.

Next steps I can implement
-------------------------
- Add a small routing function to `src/pipeline.py` to choose model per pipeline type – optional autoscaling/bring-up script (`ollama-gpu-up.sh`) already created.
- Add a `docker-compose.ollama-small.yml` and `docker-compose.ollama-large.yml` to run dedicated Ollama services for small/large models and route requests at the application level.
- Add a small agent-level configuration file to pick model depending on task type.

Model Selection for Vector-Weight-Technologies
=============================================

Goal
----
Provide recommendations for which local (self-hosted) models to use for two usage patterns:

1. Concurrent multi-agent usage (2-4 agents working simultaneously)
2. Heavy single-pipeline usage (one intensive pipeline, e.g. large codegen + tests)

Constraints and hardware
------------------------
- Local GPU: RTX 5080 (assumed 48GB VRAM) — good for running models up to ~13B-30B with quantization.
- Quantized models (q4/q8) drastically reduce VRAM usage; prioritise q4 models for concurrency.
- Monitor model licensing: some models are allowed for local self-hosting; verify each model license before using in production.

Key candidate models (safe starting set)
--------------------------------------
- qwen2.5-coder:7b-q4_0 — small, quantized coder model; low-latency, great for concurrent agents.
- mistral:latest (7B) — versatile 7B model; good balance of speed and quality.
- neural-chat:latest — instruction/coding friendly; used for chat-style agents.
- lliama 2 / 3 (13B) — heavier; recommended for large single-pipeline tasks; verify license.

Recommendations
---------------
1) Multi-agent workflows (2-4 concurrent agents)
   - Use a pool of small, quantized models (7B q4/x4) for fast parallel inference.
   - Example deployment: central `ollama` service with the set of quantized models loaded and ready. Each agent chooses a model per request.
   - Why: Lower VRAM requirement allows multiple agents to run simultaneously with acceptable latency.
     - qwen2.5-coder:7b-q4_0: Good for code generation & synthesis steps in pipelining
     - mistral:latest: General-purpose fallback for non-coding generative tasks

2) Heavy single pipeline (one high throughput, high-memory request)
   - Use larger 13B quantized models with more VRAM (e.g., Llama 2 13B, a quantized variant), or a larger 30B model if VRAM is sufficient and you'd like higher quality.
   - Example deployment: reserve a separate `ollama` instance for the heavy model, run on the RTX 5080 with GPU enabled.
   - Why: Larger models produce improved quality at the expense of VRAM and sometimes latency — good for single, complex orchestration (like code generation + multi-step compilation & testing).

Deployment patterns
-------------------
1) Single Ollama service hosting all models
   - Pros: Simple, single entrypoint, can route by model name via the app's client layer
   - Cons: Shared resources; heavy model usage can cause latency for concurrent small-model agents

2) Multi-instance Ollama deployment (preferred for mixed workloads)
   - Ollama-small: 7B quantized models (qwen, mistral) for concurrency
   - Ollama-large: 13B quantized model for heavy single-pipeline jobs
   - Use an app-side router to choose which Ollama endpoint to call based on the task
   - Start via `docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d` for the `ollama-large` service

3) Dynamic allocation (advanced)
   - Start `ollama-small` by default, and `ollama-large` on-demand when heavy pipelines are scheduled
   - For local scaling, use a shell script or `docker compose` with the GPU override to bring up the heavy image when needed

GPU sizing & concurrency guidance
--------------------------------
- With a 48GB GPU, you can host a 13B quantized model for single-pipeline use and still host a few 7B quantized models in CPU-based or secondary GPU memory with efficient quantization.
- Keep 7B models for quick parallel agents where you need low-latency.
- Set OLLAMA_NUM_PARALLEL/THREAD variables exposed in `docker-compose.yml` to tune CPU resources when GPU doesn't handle a given model.

Example Docker Compose Options
------------------------------
Use the existing `docker-compose.gpu.yml` to run with GPUs:

```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d ollama
```

For scaled deployment (small + large Ollama instances), use an overlay compose file with explicit service names and dedicated model directory/volume(s) for each instance.

Next steps
----------
1. Confirm models you'd like to use for 'all-free' pulling (I used qwen2.5 + mistral + neural-chat by default).
2. If you want, I can add a `docker-compose.ollama-small.yml` and `docker-compose.ollama-large.yml` that start separate Ollama instances and example routing configuration in the app.
3. For production-grade behavior, we can add health probes and a tiny router layer or service selection logic in `app` based on required model.

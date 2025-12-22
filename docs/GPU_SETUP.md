GPU Setup & Running Ollama on an RTX 5080
======================================

This short guide explains how to prepare and run the local Ollama model server using an NVIDIA GPU (e.g., RTX 5080) for local/self-hosted inference.

Prerequisites
-------------
- Host OS with NVIDIA drivers installed and verified (`nvidia-smi`).
- Docker Engine and Docker Compose v2 installed (Docker Desktop on Windows or Docker on Linux).
- `nvidia-container-toolkit` installed for GPU access inside containers.

NVIDIA Docker / Toolkit Installation (Ubuntu example)
---------------------------------------------------
```bash
# Add NVIDIA docker repo and install the toolkit (Ubuntu/Debian example)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Verify GPU available
docker run --rm --gpus all nvidia/cuda:12.2.0-runtime-ubuntu22.04 nvidia-smi
```

Docker Compose GPU settings
---------------------------
Add (or uncomment) the following `device_requests` block in the `ollama` service in `docker-compose.yml` (recommended for Docker Compose v2):

```yaml
services:
  ollama:
    ...
    # Optional: enable GPU device requests (requires nvidia-container-toolkit)
    # device_requests:
    #   - driver: nvidia
    #     count: all
    #     capabilities: ["gpu"]
```

or you can use the `--gpus all` flag when running the container directly:

```bash
docker compose up -d
docker compose run --rm --gpus all ollama ollama pull qwen2.5-coder:7b-q4_0
```

Model selection
---------------
Use the `scripts/model-pull.sh` helper to pull the curated list of models for local inference:

```bash
# Pull default models
./scripts/model-pull.sh default

# Pull curated set of free/self-hostable models
./scripts/model-pull.sh all-free
```

Ollama tuning for GPU (environment variables and resource guidelines)
-------------------------------------------------------------------
- Use `OLLAMA_NUM_PARALLEL` and `OLLAMA_NUM_THREAD` to tune CPU usage when you run models on CPU; when using GPU, GPU usage is key
- You can pass these as environment variables to the service in `docker-compose.yml` as you prefer

Example: After enabling GPU and pulling models, start services
-------------------------------------------------------------
```bash
# Start services with GPU support enabled in docker-compose.yml (device_requests/gpus)
docker compose up -d ollama

# Wait until Ollama is healthy and list local models
./scripts/test-ollama-health.sh 120
docker compose run --rm ollama ollama list
```

Safety & license notes
----------------------
- Confirm model licenses before running them locally — some local models have restricted, commercial, or non-commercial licenses.
- Monitor GPU memory/temperature when running inference on large models; the `rtx5080` has significant memory but ensure available system resources.

If you'd like, I can:
 - Update `docker-compose.yml` with a safe, commented GPU config (done), and a `docker-compose.gpu.yml` file you can enable via `-f docker-compose.gpu.yml`.
 - Prepare a step-by-step local checklist for you to run on the desktop (Ubuntu/WSL2/Windows Docker Desktop) to set up the NVIDIA toolkit and GPU-enabled compose run.

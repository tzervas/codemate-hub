# Quick Start Guide

Get Codemate Hub running in minutes with this streamlined guide.

## Prerequisites

Ensure you have the following installed:

- [Docker](https://docs.docker.com/get-docker/) (20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (2.0+)
- 10+ GB free disk space
- (Optional) NVIDIA GPU with [nvidia-docker](https://github.com/NVIDIA/nvidia-docker)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/tzervas/codemate-hub.git
cd codemate-hub
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit and set CODE_SERVER password
nano .env
```

Set at minimum:
```ini
PASSWORD=your-secure-password-here
```

### 3. Run Preflight Checks

```bash
./scripts/preflight-check.sh
```

This validates:
- Docker and Docker Compose installation
- System resources
- Network connectivity

### 4. Build and Deploy

```bash
# Build images and pull AI models
./scripts/build.sh

# Deploy all services
./scripts/deploy.sh
```

!!! tip "Deployment Modes"
    - **Detached** (default): `./scripts/deploy.sh`
    - **Attached** (with logs): `./scripts/deploy.sh attached`

## Accessing Services

Once deployment completes, access:

| Service | URL | Description |
|---------|-----|-------------|
| **Langflow** | [http://localhost:7860](http://localhost:7860) | Visual workflow designer |
| **Code Server** | [http://localhost:8080](http://localhost:8080) | Remote VS Code IDE |
| **Ollama API** | [http://localhost:11434](http://localhost:11434) | LLM inference API |
| **Documentation** | [http://localhost:8001](http://localhost:8001) | This documentation site |

!!! note "Code Server Authentication"
    Use the password set in your `.env` file to access Code Server.

## Verify Installation

Run health checks to ensure all services are operational:

```bash
./scripts/check-health.sh 120
```

This waits up to 120 seconds for all services to become healthy.

## Next Steps

- 📖 Read the [Architecture Overview](../architecture/overview.md)
- 🔧 Learn about [Model Management](../guides/model-management.md)
- 🎯 Explore [Configuration Options](configuration.md)
- 🚀 Try the [First Steps Tutorial](first-steps.md)

## Common Issues

### Port Already in Use

If deployment fails with port conflicts:

```bash
# Check which service is using the port
sudo lsof -i :11434  # or :7860, :8080, :8001

# Kill the process or change port in docker-compose.yml
```

### Insufficient Disk Space

Models can be large (5-30 GB each). Check space:

```bash
docker system df
```

Prune unused models:

```bash
./scripts/model-prune.sh list-unused
./scripts/model-prune.sh prune-unused
```

### Slow Model Downloads

Model downloads can take 10-30 minutes depending on network speed. Monitor progress:

```bash
docker compose logs -f ollama
```

For more troubleshooting, see the [Troubleshooting Guide](../guides/troubleshooting.md).

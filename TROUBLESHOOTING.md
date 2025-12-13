# Troubleshooting Guide

This guide covers common issues and solutions when running the Dockerized Agentic Coding Assistant.

## Pre-Deployment Issues

### Docker Not Installed

**Error**: `command not found: docker`

**Solution**:
1. Install Docker: https://docs.docker.com/get-docker/
2. Verify installation: `docker --version`
3. Ensure Docker daemon is running

**Linux Only**: Add your user to docker group (optional):
```bash
sudo usermod -aG docker $USER
# Log out and log back in
```

### Docker Daemon Not Running

**Error**: `Cannot connect to Docker daemon` or `permission denied`

**Solution**:
1. Start Docker daemon:
   ```bash
   sudo systemctl start docker  # Linux
   ```
2. Or start Docker Desktop (Mac/Windows)

### Docker Compose Not Found

**Error**: `command not found: docker compose` or `docker-compose`

**Solution**:
1. Ensure Docker Compose v2 is installed: `docker compose version`
2. If using older `docker-compose` v1:
   - Update to Docker Desktop with Compose v2 built-in
   - Or install: https://docs.docker.com/compose/install/

### Insufficient Permissions

**Error**: `permission denied while trying to connect to Docker daemon`

**Solution**:
```bash
# Option 1: Use sudo
sudo docker compose up

# Option 2: Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker
```

## Configuration Issues

### PASSWORD Not Set

**Error**: `error: missing required argument PASSWORD`

**Solution**:
```bash
# Copy example environment file
cp .env.example .env

# Edit and set a strong password
nano .env
# Or: export PASSWORD=your_password

# Then run:
docker compose up
```

### Missing .env File

**Error**: `failed to load .env`

**Solution**:
```bash
cp .env.example .env
# The .env.example file is provided as a template
```

### Port Already in Use

**Error**: `bind: address already in use` or `ports conflict`

**Solution**:

1. **Find which service uses the port**:
   ```bash
   lsof -i :11434  # Ollama
   lsof -i :7860   # Langflow
   lsof -i :8080   # Code Server
   lsof -i :8000   # App
   ```

2. **Option A: Stop conflicting service**:
   ```bash
   docker compose down
   # Kill the conflicting process if needed:
   kill -9 <PID>
   ```

3. **Option B: Change ports in docker-compose.yml**:
   ```yaml
   ollama:
     ports:
       - "11435:11434"  # Changed from 11434
   ```

4. **Option C: Use different docker compose file**:
   ```bash
   docker compose -f docker-compose.alt.yml up
   ```

## Build Issues

### Image Build Fails

**Error**: `ERROR: failed to solve` or `build context error`

**Solution**:
1. Check internet connection (building pulls base images)
2. Clear Docker cache:
   ```bash
   docker system prune -a --volumes
   ```
3. Rebuild with verbose output:
   ```bash
   docker compose build --progress=plain app
   ```

### Dockerfile Syntax Error

**Error**: `failed to parse dockerfile`

**Solution**:
1. Validate Dockerfile:
   ```bash
   docker build -f Dockerfile .
   ```
2. Check for tab characters (use spaces instead)
3. Ensure all commands are valid

### Out of Disk Space

**Error**: `no space left on device`

**Solution**:
1. Check disk usage:
   ```bash
   df -h
   du -sh ~/Docker*
   ```
2. Clean up Docker:
   ```bash
   docker system prune -a --volumes  # WARNING: Removes all images
   docker image prune -a              # Remove unused images
   docker volume prune                # Remove unused volumes
   ```
3. Free up disk space and retry

## Service Startup Issues

### Services Don't Start

**Error**: Containers exit immediately or fail to start

**Solution**:
1. Check logs:
   ```bash
   docker compose logs app
   docker compose logs ollama
   ```
2. Validate docker-compose.yml:
   ```bash
   docker compose config
   ```
3. Check available system resources:
   ```bash
   docker system df
   free -h
   ```

### Ollama Fails to Start

**Error**: `ollama: exec: "ollama": executable file not found`

**Solution**:
1. Verify the ollama image is correct:
   ```bash
   docker pull ollama/ollama:latest
   ```
2. Check logs:
   ```bash
   docker compose logs ollama
   ```
3. Try removing and rebuilding:
   ```bash
   docker compose down -v
   docker compose up ollama
   ```

### Ollama Takes Too Long to Start

**Note**: Ollama can take 1-2 minutes to initialize on first run.

**Solution**:
1. Increase health check timeout in docker-compose.yml:
   ```yaml
   ollama:
     healthcheck:
       timeout: 30s  # Increase from 10s
       retries: 5    # Increase from 3
   ```
2. Monitor startup:
   ```bash
   docker compose logs -f ollama
   ```
3. Check system resources (CPU, memory):
   ```bash
   docker stats
   ```

### Langflow Fails to Start

**Error**: `Langflow exited with code 1`

**Solution**:
1. Check logs:
   ```bash
   docker compose logs langflow
   ```
2. Verify database directory exists:
   ```bash
   mkdir -p ./langflow_data
   chmod 755 ./langflow_data
   ```
3. Clear Langflow database:
   ```bash
   docker compose down -v  # Removes all volumes
   docker compose up langflow
   ```

### Code Server Authentication Fails

**Error**: `Unauthorized` when accessing port 8080

**Solution**:
1. Verify PASSWORD is set:
   ```bash
   echo $PASSWORD
   cat .env | grep PASSWORD
   ```
2. Restart code-server:
   ```bash
   docker compose restart code-server
   ```
3. Check code-server logs:
   ```bash
   docker compose logs code-server
   ```

## Health Check Issues

### Services Not Becoming Healthy

**Error**: `check-health.sh: Services did not become healthy`

**Solution**:
1. Run manual health checks:
   ```bash
   ./scripts/check-health.sh 60  # 60 second timeout
   ```
2. Test individual services:
   ```bash
   ./scripts/check-health.sh 120 ollama
   ./scripts/check-health.sh 120 langflow
   ./scripts/check-health.sh 120 app
   ```
3. Check curl is installed in containers:
   ```bash
   docker compose exec ollama which curl
   ```

### Ollama Healthcheck Fails

**Error**: `curl: (7) Failed to connect` or `curl: command not found`

**Solution**:
1. Test manually:
   ```bash
   curl -f http://localhost:11434/api/tags
   ```
2. If curl not found in container, the base image needs curl:
   ```dockerfile
   # In Dockerfile or docker-compose.yml environment
   RUN apt-get update && apt-get install -y curl
   ```
3. Check if Ollama is listening:
   ```bash
   docker compose exec ollama netstat -tlnp | grep 11434
   ```

### App Container Not Ready

**Error**: `coding-assistant did not become available`

**Solution**:
1. Check if app depends on ollama health:
   ```yaml
   app:
     depends_on:
       ollama:
         condition: service_healthy
   ```
2. Verify ollama is healthy first:
   ```bash
   docker compose logs ollama | grep healthy
   ```

## GPU Issues

### NVIDIA GPU Not Detected

**Error**: `GPU not available` or `CUDA not found`

**Solution**:
1. Check GPU availability:
   ```bash
   nvidia-smi
   ```
2. If no output, NVIDIA drivers not installed:
   - Install NVIDIA drivers: https://developer.nvidia.com/cuda-downloads
   - Verify: `nvidia-smi`

### nvidia-docker Not Configured

**Error**: `runtime: nvidia: not found` or `unknown runtime error`

**Solution**:
1. Install nvidia-docker:
   ```bash
   # Ubuntu/Debian
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
     sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update && sudo apt-get install -y nvidia-docker2
   sudo systemctl restart docker
   ```
2. Verify:
   ```bash
   nvidia-docker --version
   ```
3. Uncomment in docker-compose.yml:
   ```yaml
   ollama:
     runtime: nvidia
   ```

### GPU Memory Issues

**Error**: `CUDA out of memory` or `GPU memory exhausted`

**Solution**:
1. Check GPU memory:
   ```bash
   nvidia-smi
   ```
2. Reduce model size (pull a smaller model):
   ```bash
   ./scripts/model-pull.sh mistral:7b-q4_0  # Smaller than 13B
   ```
3. Close other GPU-using applications
4. Reduce OLLAMA_NUM_PARALLEL:
   ```yaml
   environment:
     - OLLAMA_NUM_PARALLEL=1  # Default is 4
   ```

## Network Issues

### Cannot Access Services

**Error**: `Connection refused` when accessing localhost:7860, etc.

**Solution**:
1. Verify services are running:
   ```bash
   docker compose ps
   ```
2. Check if ports are bound:
   ```bash
   docker compose port langflow 7860
   docker compose port ollama 11434
   ```
3. Try accessing from inside container:
   ```bash
   docker exec langflow curl -f http://localhost:7860
   ```
4. Check firewall (if on remote server):
   ```bash
   sudo ufw allow 7860/tcp
   sudo ufw allow 11434/tcp
   ```

### Container Cannot Reach Other Container

**Error**: `Connection refused` from one container to another

**Solution**:
1. Verify service names in docker-compose.yml
2. Use container name (not localhost) in URLs:
   ```yaml
   environment:
     - OLLAMA_BASE_URL=http://ollama:11434  # Correct
     # NOT: http://localhost:11434
   ```
3. Check container networking:
   ```bash
   docker network ls
   docker network inspect giggitty-cluster-cluster-a_default
   ```
4. Restart services:
   ```bash
   docker compose restart
   ```

## Volume Mount Issues

### Volume Permission Denied

**Error**: `permission denied` when accessing mounted volumes

**Solution**:
1. Check volume permissions:
   ```bash
   ls -la ./src
   ls -la ./langflow_data
   ls -la ./zephyr
   ```
2. Fix permissions:
   ```bash
   chmod -R 755 ./src
   chmod -R 755 ./langflow_data
   chmod -R 755 ./zephyr
   ```
3. Or run Docker with same user (Linux):
   ```bash
   export PUID=$(id -u)
   export PGID=$(id -g)
   docker compose up
   ```

### Volume Not Persisting

**Error**: Data lost after container restart

**Solution**:
1. Verify volumes in docker-compose.yml:
   ```yaml
   volumes:
     ollama_data:
     chroma_db:
   ```
2. Check volume exists:
   ```bash
   docker volume ls | grep giggitty
   ```
3. Inspect volume:
   ```bash
   docker volume inspect giggitty-cluster-cluster-a_ollama_data
   ```
4. Mount to local directory instead:
   ```yaml
   volumes:
     ollama_data: ./ollama_data  # Local directory
   ```

## Memory and Performance

### Containers Using Too Much Memory

**Error**: `Killed` or `OOMKilled` error

**Solution**:
1. Check memory usage:
   ```bash
   docker stats
   free -h
   ```
2. Set memory limits:
   ```yaml
   services:
     ollama:
       mem_limit: 4g  # Limit to 4GB
   ```
3. Stop other services
4. Add swap (Linux):
   ```bash
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

### Slow Performance

**Symptoms**: Services slow to respond, high CPU usage

**Solution**:
1. Monitor resource usage:
   ```bash
   docker stats
   top
   ```
2. Check available CPU cores:
   ```bash
   nproc
   ```
3. Adjust parallel settings:
   ```yaml
   environment:
     - OLLAMA_NUM_PARALLEL=2  # Reduce from 4
     - OLLAMA_NUM_THREAD=2
   ```
4. Disable GPU if CPU-only performs better:
   ```yaml
   # Comment out runtime: nvidia
   # ollama:
   #   runtime: nvidia
   ```

## Log Analysis

### Where to Find Logs

```bash
# View logs for all services
docker compose logs

# View logs for specific service
docker compose logs ollama
docker compose logs langflow
docker compose logs coding-assistant

# Follow logs in real-time
docker compose logs -f

# Show last N lines
docker compose logs --tail=50

# Show logs since specific time
docker compose logs --since 2024-01-01
```

### Common Error Patterns

**Pattern**: `OOMKilled`
- Solution: Increase available memory or reduce parallel workers

**Pattern**: `Connection refused`
- Solution: Verify service is running and port is correct

**Pattern**: `Health check failed`
- Solution: Increase timeout or check service logs

**Pattern**: `File not found`
- Solution: Verify volume mounts and file paths

## Getting Help

1. **Check logs first**:
   ```bash
   docker compose logs --tail=100
   ```

2. **Run diagnostics**:
   ```bash
   ./scripts/preflight-check.sh
   ./scripts/test-ollama-health.sh
   ```

3. **Test with minimal setup**:
   ```bash
   docker compose up ollama  # Test just Ollama
   ```

4. **Review configuration**:
   ```bash
   docker compose config
   cat .env
   ```

5. **Check system resources**:
   ```bash
   df -h
   free -h
   docker system df
   ```

## Advanced Debugging

### Exec into Container

```bash
# Access app container shell
docker exec -it coding-assistant /bin/bash

# Access ollama container
docker exec -it ollama /bin/bash
```

### Test Connectivity

```bash
# From host to container
curl http://localhost:11434/api/tags

# From container to container
docker exec coding-assistant curl http://ollama:11434/api/tags
```

### Rebuild from Scratch

```bash
# Remove everything
docker compose down -v
docker system prune -a --volumes

# Rebuild
docker compose build --no-cache --progress=plain
docker compose up
```

### Enable Debug Logging

```bash
# Docker daemon debug logs
sudo journalctl -u docker -f

# Container environment debugging
docker compose exec ollama env
```

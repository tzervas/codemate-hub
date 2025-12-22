# Preseed: Docker and DevOps Best Practices

## Docker Compose Patterns

### Service Dependencies
Always use health checks with proper conditions:
```yaml
services:
  app:
    depends_on:
      database:
        condition: service_healthy
      redis:
        condition: service_started
```

### Health Checks
Include proper health checks with realistic timeouts:
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s  # Allow time for startup
```

### GPU Configuration
For NVIDIA GPU support:
```yaml
services:
  ml-service:
    runtime: nvidia
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
```

### Volume Management
Use named volumes for persistence:
```yaml
volumes:
  db_data:
    driver: local
  cache_data:
    driver: local
    driver_opts:
      type: tmpfs
      device: tmpfs
```

## Dockerfile Best Practices

### Multi-Stage Builds
```dockerfile
# Build stage
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev

# Runtime stage
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/ ./src/
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "src.main"]
```

### Layer Optimization
- Order instructions from least to most frequently changing
- Combine RUN commands to reduce layers
- Use .dockerignore to exclude unnecessary files

## Nginx Reverse Proxy

### WebSocket Support
```nginx
location /ws {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400;
}
```

### Security Headers
```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### Rate Limiting
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://backend:8000;
}
```

## CI/CD with GitHub Actions

### Workflow Structure
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, devel]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync
      - run: uv run pytest

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: docker/build-push-action@v5
```

### Caching
```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/uv
    key: ${{ runner.os }}-uv-${{ hashFiles('**/uv.lock') }}
```

## Monitoring and Observability

### Container Metrics
```yaml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
```

### Log Aggregation
```yaml
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

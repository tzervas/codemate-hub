# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder

# Install build dependencies and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock requirements.txt ./

# Install dependencies using uv (faster and more reliable than pip)
RUN uv pip install --python /usr/local/bin/python -r requirements.txt

FROM python:3.12-slim AS runtime
WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY personas.yaml ./

# Initialize memory/embeddings
RUN python src/memory_setup.py

EXPOSE 8000
CMD ["python", "src/pipeline.py"]

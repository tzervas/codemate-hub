# Observability Stack Setup Guide

## Overview

The observability stack provides comprehensive monitoring, logging, and tracing for the AI R&D platform.

### Stack Components

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- **Loki**: Log aggregation
- **Promtail**: Log shipping
- **Tempo**: Distributed tracing
- **OpenTelemetry Collector**: Unified telemetry pipeline
- **Node Exporter**: System metrics
- **cAdvisor**: Container metrics

## Quick Start

### 1. Deploy Monitoring Stack

```bash
# Create monitoring network
docker network create ai-monitoring

# Start observability stack
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d

# Verify all services are healthy
docker compose -f docker-compose.observability.yml ps
```

### 2. Access Dashboards

- **Grafana**: http://localhost:3001
  - Username: `admin`
  - Password: `admin` (change on first login)

- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100
- **Tempo**: http://localhost:3200

### 3. Pre-configured Dashboards

Navigate to Grafana → Dashboards → AI Research folder:

1. **AI/ML Model Performance** - Inference metrics, latency, tokens, GPU usage
2. **Vector Database Metrics** - ChromaDB query performance, embeddings
3. **Langflow Workflows** - Flow execution, node timing, success rates
4. **System Overview** - CPU, memory, disk, network (auto-configured)

## Configuration Details

### Prometheus Scrape Targets

All services expose metrics on `/metrics` endpoints:

| Service | Port | Metrics Path | Scrape Interval |
|---------|------|--------------|-----------------|
| Ollama | 11434 | `/metrics` | 10s |
| App | 8001 | `/metrics` | 10s |
| Langflow | 7860 | `/metrics` | 30s |
| Node Exporter | 9100 | `/metrics` | 15s |
| cAdvisor | 8081 | `/metrics` | 15s |

### Log Labels

Loki automatically adds labels to container logs:

- `container`: Container name
- `compose_service`: Docker Compose service name
- `stream`: stdout/stderr
- `level`: Log level (if JSON structured)
- `trace_id`: Trace ID (if present, links to Tempo)

### Trace Context

OpenTelemetry traces include:

- `service.name`: Service identifier
- `ai.model.name`: Model used for inference
- `ai.tokens.input/output`: Token counts
- `ai.latency_ms`: Operation latency
- `trace_id`: Links logs→traces→metrics

## Instrumentation

### Python Services

Services use the `observability.py` module:

```python
from observability import setup_tracing, track_ollama_request, track_chroma_query

# Initialize tracing
tracer = setup_tracing("my-service")

# Track Ollama requests
@track_ollama_request(model="qwen2.5-coder:7b-q4_0")
def call_ollama(prompt):
    # Your code here
    pass

# Track ChromaDB queries
@track_chroma_query(collection="documents", operation="query")
def search_vectors(query):
    # Your code here
    pass
```

### Metrics Endpoint

Each service exposes Prometheus metrics:

```python
from fastapi import FastAPI
from observability import get_metrics

app = FastAPI()

@app.get("/metrics")
def metrics():
    data, content_type = get_metrics()
    return Response(content=data, media_type=content_type)
```

## Alerts

Pre-configured alerts in Prometheus:

1. **HighInferenceLatency**: p95 > 10s for 5 minutes
2. **HighGPUMemoryUsage**: >90% for 5 minutes
3. **HighErrorRate**: >5% error rate for 5 minutes
4. **ContainerDown**: Service down for 2 minutes
5. **DiskSpaceLow**: <10% disk remaining
6. **HighVectorDBLatency**: ChromaDB p95 > 2s

## Data Retention

- **Prometheus**: 30 days
- **Loki**: 7 days (168 hours)
- **Tempo**: 7 days (168 hours)

Adjust in respective config files:
- `config/observability/prometheus/prometheus.yml`: `--storage.tsdb.retention.time`
- `config/observability/loki/loki-config.yml`: `retention_period`
- `config/observability/tempo/tempo-config.yml`: `block_retention`

## Advanced Usage

### Query Examples

**PromQL (Prometheus)**:
```promql
# Average inference latency by model
avg(rate(ollama_request_duration_seconds_sum[5m]) / rate(ollama_request_duration_seconds_count[5m])) by (model)

# GPU utilization
nvidia_gpu_utilization_percent

# Error rate
rate(ollama_requests_total{status="error"}[5m])
```

**LogQL (Loki)**:
```logql
# All errors from Ollama
{compose_service="ollama"} |= "error"

# Traces with high latency
{compose_service="app"} | json | latency_ms > 5000

# Search by trace ID
{trace_id="abc123"}
```

**TraceQL (Tempo)**:
```traceql
# Spans with high duration
{ duration > 5s }

# AI model traces
{ resource.service.name = "ollama" }
```

### Custom Dashboards

Create custom dashboards in Grafana:

1. Go to Dashboards → New → New Dashboard
2. Add panels using Prometheus/Loki/Tempo datasources
3. Save to AI Research folder
4. Export JSON and save to `config/observability/grafana/dashboards/`

### Scaling

For production deployments:

1. **Prometheus HA**: Deploy multiple Prometheus replicas with Thanos
2. **Loki Scalability**: Use S3 storage backend and distributed mode
3. **Tempo Scalability**: Use object storage (S3, GCS) for traces
4. **Grafana HA**: Deploy multiple Grafana instances behind load balancer

## Troubleshooting

### Services Not Scraping

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check if metrics endpoint is accessible
curl http://app:8001/metrics
```

### No Logs in Loki

```bash
# Check Promtail is running
docker compose -f docker-compose.observability.yml logs promtail

# Verify Loki is receiving logs
curl http://localhost:3100/loki/api/v1/label
```

### Missing Traces

```bash
# Verify OTEL collector is running
curl http://localhost:13133

# Check if services are sending traces
docker compose -f docker-compose.observability.yml logs otel-collector
```

### High Resource Usage

Reduce retention periods or disable unused components:

```bash
# Stop unused exporters
docker compose -f docker-compose.observability.yml stop node-exporter cadvisor

# Reduce scrape intervals in prometheus.yml
```

## MCP Servers (Rust SDK)

### Installation

MCP servers are installed via Rust/Cargo in the application container:

```dockerfile
RUN cargo install --git https://github.com/modelcontextprotocol/servers \
    mcp-server-filesystem \
    mcp-server-memory \
    mcp-server-sqlite \
    mcp-server-fetch
```

### Configuration

MCP servers are configured in `config/mcp/servers.json`:

- **filesystem**: File operations on `/app/src`, `/app/config`, `/app/insights`
- **memory**: Persistent key-value store at `/app/chroma_db/mcp_memory.db`
- **sqlite**: SQL database at `/app/data/mcp.sqlite`
- **fetch**: HTTP operations with custom user agent
- **github**: GitHub API (requires `GITHUB_TOKEN`)
- **sequential-thinking**: Chain-of-thought reasoning
- **brave-search**: Web search (requires `BRAVE_API_KEY`)
- **postgres**: PostgreSQL (requires `DATABASE_URL`)

### Enabling Optional Servers

Set required environment variables in `.env`:

```bash
GITHUB_TOKEN=ghp_your_token_here
BRAVE_API_KEY=your_brave_api_key
DATABASE_URL=postgresql://user:pass@host:5432/db
```

Then update `config/mcp/servers.json` to set `"enabled": true`.

### Health Monitoring

MCP servers report health via:
- Prometheus metrics on `/metrics`
- OpenTelemetry traces to Tempo
- Structured logs to Loki

Monitor in Grafana under **MCP Servers** dashboard (auto-created on first run).

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/)
- [Tempo Documentation](https://grafana.com/docs/tempo/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Model Context Protocol](https://github.com/modelcontextprotocol)

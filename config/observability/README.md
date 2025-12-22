# Observability Configuration

This directory contains all configuration files for the comprehensive observability stack.

## Directory Structure

```
config/observability/
├── prometheus/
│   ├── prometheus.yml          # Prometheus configuration with scrape targets
│   └── rules/
│       └── ai_alerts.yml       # AI/ML specific alerting rules
├── loki/
│   └── loki-config.yml         # Loki log aggregation configuration
├── promtail/
│   └── promtail-config.yml     # Log shipping and processing
├── tempo/
│   └── tempo-config.yml        # Distributed tracing configuration
├── otel/
│   └── otel-collector-config.yml # OpenTelemetry collector pipeline
└── grafana/
    ├── provisioning/
    │   ├── datasources/
    │   │   └── datasources.yml # Auto-provisioned datasources
    │   └── dashboards/
    │       └── dashboards.yml  # Dashboard provider config
    └── dashboards/
        ├── ai-ml-performance.json    # LLM inference metrics
        ├── vector-db-metrics.json    # ChromaDB performance
        ├── langflow-workflows.json   # Workflow execution
        └── system-overview.json      # System/container metrics
```

## Quick Start

1. **Deploy the stack**:
   ```bash
   ./scripts/deploy-observability.sh start
   ```

2. **Access Grafana**:
   - URL: http://localhost:3001
   - Username: `admin`
   - Password: `admin` (change on first login)

3. **View dashboards**:
   - Navigate to Dashboards → AI Research folder
   - Pre-configured dashboards will auto-load

## Configuration Files

### Prometheus (`prometheus/prometheus.yml`)

Configures metric scraping from all services:
- Scrape interval: 15s (10s for Ollama/App)
- Retention: 30 days
- Targets: All application services + system exporters

**Key scrape targets**:
- `ollama`: LLM inference metrics
- `app`: Application/agent metrics
- `langflow`: Workflow metrics
- `node-exporter`: System metrics
- `cadvisor`: Container metrics

### Loki (`loki/loki-config.yml`)

Log aggregation and storage:
- Storage: Local filesystem (TSDB)
- Retention: 7 days
- Ingestion rate: 10MB/s (burst: 20MB/s)
- Compaction: Every 10 minutes

### Promtail (`promtail/promtail-config.yml`)

Ships logs from Docker containers:
- Auto-discovers containers via Docker socket
- Adds metadata labels (container, service, stream)
- Parses JSON logs
- Extracts AI-specific fields (model, tokens, latency)
- Links logs to traces via `trace_id`

### Tempo (`tempo/tempo-config.yml`)

Distributed tracing backend:
- Ingestion: OTLP (gRPC/HTTP), Jaeger, Zipkin
- Storage: Local filesystem
- Retention: 7 days
- Generates span metrics for Prometheus
- Links traces to logs/metrics

### OpenTelemetry Collector (`otel/otel-collector-config.yml`)

Unified telemetry pipeline:
- Receives: OTLP traces/metrics/logs
- Processes: Batching, resource attribution, AI-specific enrichment
- Exports: Tempo (traces), Prometheus (metrics), Loki (logs)
- Generates span metrics from traces

### Grafana (`grafana/provisioning/`)

Auto-provisions datasources and dashboards:
- **Datasources**: Prometheus, Loki, Tempo (linked for correlation)
- **Dashboards**: 4 pre-configured dashboards in AI Research folder
- **Plugins**: Automatically installs piechart, worldmap panels

## Alert Rules

Located in `prometheus/rules/ai_alerts.yml`:

1. **HighInferenceLatency**: p95 > 10s for 5m
2. **HighGPUMemoryUsage**: >90% for 5m
3. **HighErrorRate**: >5% for 5m
4. **ContainerDown**: Service unhealthy for 2m
5. **DiskSpaceLow**: <10% remaining
6. **HighVectorDBLatency**: ChromaDB p95 > 2s

## Customization

### Adding New Scrape Targets

Edit `prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'my-service'
    static_configs:
      - targets: ['my-service:9090']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### Creating Custom Dashboards

1. Create dashboard in Grafana UI
2. Export as JSON
3. Save to `grafana/dashboards/my-dashboard.json`
4. Restart Grafana to auto-load

### Modifying Retention

**Prometheus** (in `prometheus.yml` command args):
```yaml
command:
  - '--storage.tsdb.retention.time=60d'  # Change from 30d
```

**Loki** (in `loki-config.yml`):
```yaml
limits_config:
  retention_period: 336h  # 14 days (from 168h/7 days)
```

**Tempo** (in `tempo-config.yml`):
```yaml
compactor:
  compaction:
    block_retention: 336h  # 14 days
```

### Adding Custom Log Parsing

Edit `promtail/promtail-config.yml` under `scrape_configs` → `pipeline_stages`:

```yaml
- match:
    selector: '{compose_service="my-service"}'
    stages:
      - json:
          expressions:
            my_field: my_field
      - labels:
          my_field:
```

## Data Volumes

All observability data is persisted in Docker volumes:

- `prometheus_data`: Prometheus time-series database
- `loki_data`: Loki log chunks and indexes
- `tempo_data`: Tempo trace blocks
- `grafana_data`: Grafana dashboards, users, settings

**Backup**:
```bash
docker compose -f docker-compose.observability.yml down
tar czf observability-backup.tar.gz \
  $(docker volume inspect --format '{{.Mountpoint}}' prometheus_data) \
  $(docker volume inspect --format '{{.Mountpoint}}' loki_data) \
  $(docker volume inspect --format '{{.Mountpoint}}' tempo_data) \
  $(docker volume inspect --format '{{.Mountpoint}}' grafana_data)
```

## Troubleshooting

### Prometheus Not Scraping

```bash
# Check targets
curl http://localhost:9090/api/v1/targets

# Verify metrics endpoint
curl http://app:8001/metrics
```

### No Logs in Loki

```bash
# Check Promtail
docker compose -f docker-compose.observability.yml logs promtail

# Verify Loki labels
curl http://localhost:3100/loki/api/v1/label
```

### Missing Traces

```bash
# Check OTEL Collector
curl http://localhost:13133

# Verify service is sending traces
docker compose -f docker-compose.observability.yml logs otel-collector | grep "ExportTraceServiceRequest"
```

## References

- [Prometheus Configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)
- [Loki Configuration](https://grafana.com/docs/loki/latest/configuration/)
- [Tempo Configuration](https://grafana.com/docs/tempo/latest/configuration/)
- [OTEL Collector](https://opentelemetry.io/docs/collector/configuration/)
- [Grafana Provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)

# GPU Resource Manager

A Go-based service for managing GPU allocation, monitoring, and optimization in the Codemate-Hub platform.

## Overview

This service provides intelligent GPU resource management for the Codemate-Hub AI coding assistant, including:
- Automatic GPU detection and capability assessment
- Dynamic resource allocation based on workload
- Real-time monitoring and metrics
- Optimization strategies to minimize fragmentation

## Status

**Current Version:** v2.0 (Scaffolding - GPU-001)

### Implemented
- ✅ Basic service structure with graceful shutdown
- ✅ Configuration framework (see `../../config/gpu-resource-strategy.yaml`)
- ✅ Signal handling and context management
- ✅ Dependency declarations for NVML, Prometheus, and YAML parsing

### Pending
- ⏳ GPU-002: Allocator package (`pkg/allocator`) - NVML detector and capability detection
- ⏳ GPU-010: Monitor package (`pkg/monitor`) - Prometheus metrics server on port 9090

## Building

```bash
go build -o gpu-resource-manager .
```

## Running

```bash
./gpu-resource-manager --config /path/to/strategy.yaml
```

Default config path: `/config/strategy.yaml`

## Dependencies

- **go-nvml** (v0.12.0-1): NVIDIA GPU management via NVML library
- **prometheus/client_golang** (v1.17.0): Metrics exposure
- **yaml.v3** (v3.0.1): Configuration parsing

## Configuration

See `../../config/gpu-resource-strategy.yaml` for the allocation strategy configuration including:
- Auto-discovery settings
- Minimum allocation thresholds (2048 MB VRAM, 25% compute)
- Expansion triggers
- Optimization strategies

## Next Steps

1. Implement `pkg/allocator` package (GPU-002)
   - NVML detector initialization
   - GPU capability detection
   - Resource allocation logic

2. Implement `pkg/monitor` package (GPU-010)
   - Prometheus metrics server
   - Real-time GPU monitoring
   - Performance tracking

## Architecture

```
gpu-resource-manager/
├── main.go              # Entry point with signal handling
├── go.mod               # Go module definition
├── pkg/
│   ├── allocator/      # (TODO: GPU-002) Resource allocation
│   └── monitor/        # (TODO: GPU-010) Metrics and monitoring
└── README.md           # This file
```

## Integration

This service will integrate with the Ollama container's GPU runtime to:
- Detect available GPU resources
- Allocate resources based on model requirements
- Monitor usage and adjust allocations dynamically
- Provide metrics for observability

---

**Tasks:** GPU-001 (Complete), GPU-002 (Pending), GPU-010 (Pending)

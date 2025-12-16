# Pipeline API Reference

!!! info "Auto-Generated Documentation"
    This page uses automated API documentation extraction from Python docstrings.

## Pipeline Module

::: src.pipeline
    options:
      show_source: true
      heading_level: 3

## Overview

The pipeline module orchestrates the main execution flow for the coding assistant, coordinating between agents, tasks, and the LLM inference layer.

## Key Components

### CodingPipeline Class

The main orchestrator for coding tasks, managing:

- Task execution flow
- Agent coordination
- Memory system integration
- Error handling and recovery

### Ollama Integration

Interfaces with the Ollama service for:

- Model inference
- Embedding generation
- Response streaming

## Usage Examples

```python
from src.pipeline import CodingPipeline

# Initialize pipeline
pipeline = CodingPipeline()

# Execute a coding task
result = pipeline.run_task("Implement a binary search function in Python")
```

!!! note "TODO: Expand Examples"
    Additional usage examples will be added covering:
    - Custom agent configuration
    - Memory context injection
    - Error handling patterns
    - Performance tuning

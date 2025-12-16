# Orchestrator API Reference

!!! info "Auto-Generated Documentation"
    This page uses automated API documentation extraction from Python docstrings.

## Orchestrator Module

::: src.orchestrator
    options:
      show_source: true
      heading_level: 3

## Overview

The orchestrator module manages task scheduling, execution, and coordination across multiple agents using a signal-based architecture.

## Key Components

### TaskOrchestrator Class

Central coordinator for:

- Task scheduling and prioritization
- Dependency resolution
- Parallel execution management
- Signal-based event handling

## Usage Examples

```python
from src.orchestrator import TaskOrchestrator

# Initialize orchestrator
orchestrator = TaskOrchestrator()

# Schedule tasks
task_id = orchestrator.schedule_task(
    name="code_review",
    dependencies=["build", "test"]
)
```

!!! note "TODO: Expand Examples"
    Additional examples will cover:
    - Parallel task execution
    - Custom task dependencies
    - Error recovery strategies
    - Progress monitoring

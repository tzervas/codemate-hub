# Agents API Reference

!!! info "Auto-Generated Documentation"
    This page uses automated API documentation extraction from Python docstrings.

## Agents Module

::: src.agents
    options:
      show_source: true
      heading_level: 3

## Overview

The agents module provides the agent abstraction layer, managing agent creation, lifecycle, and persona-based configuration.

## Key Components

### AgentPool Class

Manages multiple agents with:

- Role-based selection
- Agent lifecycle management
- Resource allocation
- Load balancing

### Agent Creation

```python
from src.agents import create_agent_from_persona

# Create agent from persona configuration
agent = create_agent_from_persona("python_worker")
```

## Persona Configuration

Agents are configured via `personas.yaml`:

```yaml
python_worker:
  role: "Python Developer"
  goal: "Write high-quality Python code"
  backstory: "Expert Python developer..."
  preseed_query: "Python best practices"
```

!!! note "TODO: Expand Documentation"
    Additional documentation will include:
    - Custom persona creation guide
    - Agent communication patterns
    - State management
    - Performance optimization

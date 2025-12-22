# Agents API Reference

!!! info "TODO"
    This page will contain auto-generated API documentation once the agents module is implemented.

## Overview

The agents module will provide the agent abstraction layer, managing agent creation, lifecycle, and persona-based configuration.

## Planned Implementation

Based on the project architecture, the agents module will include:

- **AgentPool Class** - Managing multiple agents with role-based selection
- **Agent Creation** - Factory methods for creating agents from personas
- **Persona Integration** - Loading agent configuration from `personas.yaml`

## Persona Configuration

Agents will be configured via `personas.yaml`:

```yaml
python_worker:
  role: "Python Developer"
  goal: "Write high-quality Python code"
  backstory: "Expert Python developer..."
  preseed_query: "Python best practices"

rust_worker:
  role: "Rust Developer"
  goal: "Write safe, efficient Rust code"
  backstory: "Systems programming expert..."
  preseed_query: "Rust best practices"
```

See [personas.yaml](https://github.com/tzervas/codemate-hub/blob/main/personas.yaml) for the current persona definitions.

## Temporary Reference

The persona system is documented in the main [README.md](https://github.com/tzervas/codemate-hub/blob/main/README.md).

## Usage Examples

!!! note "TODO"
    Once implemented, this page will include examples for:
    - Creating agents from personas
    - Custom persona creation
    - Agent communication patterns
    - State management
    - Performance optimization

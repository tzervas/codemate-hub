# API Reference

Complete API documentation for all Codemate Hub modules.

## Core Modules

| Module | Description |
|--------|-------------|
| [Pipeline](pipeline.md) | Main execution pipeline and orchestration |
| [Orchestrator](orchestrator.md) | Task scheduling and coordination |
| [Agents](agents.md) | Agent management and persona system |
| [Task Manager](task-manager.md) | Task lifecycle and state management |

## Additional Modules

!!! info "TODO"
    Additional modules will be documented as development progresses:
    
    - **Signals** - Event-driven signal system
    - **Memory Setup** - ChromaDB initialization and management
    - **Constants** - Shared constants and configuration

## Quick Links

- [Architecture Overview](../architecture/overview.md)
- [Development Setup](../development/setup.md)
- [Getting Started](../getting-started/quick-start.md)

## Auto-Generated Documentation

All API documentation is automatically generated from Python docstrings using 
MkDocs Material and mkdocstrings. To regenerate:

```bash
./scripts/docs-generate.sh
```

## Documentation Standards

### Docstring Style

We use Google-style docstrings for all Python code:

```python
def example_function(param: str, count: int = 0) -> dict[str, Any]:
    """Brief description of the function.

    Longer description explaining the purpose and behavior in detail.

    Args:
        param: Description of the param parameter.
        count: Description of count parameter. Defaults to 0.

    Returns:
        Dictionary containing the results.

    Raises:
        ValueError: If param is empty.

    Examples:
        >>> example_function("test", 5)
        {'param': 'test', 'count': 5}
    """
    if not param:
        raise ValueError("param cannot be empty")
    return {"param": param, "count": count}
```

### Type Hints

All public APIs must include type hints:

```python
from typing import Optional, List, Dict, Any

def process_items(
    items: List[str],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, List[str]]:
    """Process a list of items with optional configuration."""
    # Implementation
    pass
```

### Usage Examples

Include usage examples in docstrings when appropriate:

```python
def create_agent(role: str, goal: str) -> Agent:
    """Create a new agent with specified role and goal.

    Examples:
        Create a Python developer agent:
        
        >>> agent = create_agent(
        ...     role="Python Developer",
        ...     goal="Write clean, tested code"
        ... )
        >>> agent.role
        'Python Developer'
    """
    # Implementation
    pass
```

## Contributing to API Docs

When adding or modifying Python modules:

1. **Write clear docstrings** for all public functions, classes, and methods
2. **Include type hints** for all parameters and return values
3. **Provide examples** in docstrings for complex functions
4. **Run documentation generation** to verify formatting:
   ```bash
   ./scripts/docs-generate.sh
   ./scripts/docs-build.sh validate
   ```
5. **Review the output** at http://localhost:8001

See the [Contributing Guide](../development/contributing.md) for complete documentation guidelines.

## API Stability

!!! warning "Alpha Status"
    Codemate Hub is currently in **alpha** (v0.4.0). APIs may change between versions.
    
    We follow semantic versioning:
    - **Major** (x.0.0): Breaking changes
    - **Minor** (0.x.0): New features, backward compatible
    - **Patch** (0.0.x): Bug fixes, backward compatible

## Need Help?

- 📖 Check the [Architecture Overview](../architecture/overview.md) for system design
- 🧪 See [Testing Guide](../development/testing.md) for testing APIs
- 🐛 Visit [Troubleshooting](../guides/troubleshooting.md) for common issues
- 💬 Open an [issue](https://github.com/tzervas/codemate-hub/issues) or [discussion](https://github.com/tzervas/codemate-hub/discussions)

# Zephyr Enclave System

## Overview

Zephyr provides a lightweight enclave system for isolated execution of code analysis and transformation tasks. Enclaves provide:

- **Filesystem Isolation**: Restricted read/write access to specified directories
- **Resource Limits**: CPU, memory, and execution time constraints
- **Process Isolation**: Restricted system capabilities and network access
- **Security**: Sandboxed execution environment for untrusted operations

## Architecture

### Core Components

- **`zephyr/core/`**: Core enclave abstractions and configuration
  - `enclave.py`: Base enclave class and protocols
  - `config.py`: Configuration management for enclaves
  - `limits.py`: Resource limit enforcement

- **`zephyr/exec/`**: Execution engine for running code in enclaves
  - `runner.py`: Enclave execution runner
  - `isolation.py`: Filesystem and process isolation mechanisms

- **`zephyr/examples/`**: Example enclave implementations
  - `code_analyzer.py`: Simple code analysis enclave
  - `pipeline_step.py`: Example pipeline step in an enclave

## Usage

### Basic Enclave Execution

```python
from zephyr.core.enclave import EnclaveConfig
from zephyr.exec.runner import EnclaveRunner

# Configure enclave
config = EnclaveConfig(
    name="code-analyzer",
    max_memory_mb=512,
    max_cpu_percent=50,
    timeout_seconds=30,
    allowed_read_paths=["/app/src"],
    allowed_write_paths=["/tmp/enclave-output"]
)

# Create and run enclave
runner = EnclaveRunner(config)
result = runner.execute(
    target_function="analyze_code",
    module_path="zephyr.examples.code_analyzer",
    args={"code_file": "/app/src/pipeline.py"}
)
```

### Integration with Pipeline

```python
from src.enclave_tool import EnclaveTool

# Use enclave tool for isolated execution
tool = EnclaveTool()
enclave_id = tool.create_enclave(objective="Analyze code for security issues")
result = tool.run_in_enclave(enclave_id, task="analyze", file_path="/app/src/app.py")
```

## Security Considerations

1. **Filesystem Access**: Enclaves have explicit read/write path allowlists
2. **Network Access**: Network operations are disabled by default
3. **Resource Limits**: Memory, CPU, and time limits prevent resource exhaustion
4. **Process Isolation**: Subprocess execution is restricted
5. **Input Validation**: All inputs are validated before execution

## Limitations

- Enclaves are process-based, not container-based (lighter weight but less isolation than Docker)
- Filesystem isolation uses Python's working directory and path restrictions (not kernel namespaces)
- Resource limits are advisory and enforced at the application level
- For stronger isolation, consider using Docker containers or actual OS-level sandboxing

## Examples

See `zephyr/examples/` for working examples of enclave usage.

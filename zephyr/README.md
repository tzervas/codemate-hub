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

1. **Filesystem Access**: Enclaves have explicit read/write path allowlists with symlink validation
2. **Network Access**: Network operations are not actively blocked (advisory restriction only)
3. **Resource Limits**: Memory, CPU, and time limits are monitored but not strictly enforced at OS level
4. **Process Isolation**: Subprocess execution is not actively restricted (advisory restriction only)
5. **Input Validation**: Basic path and numeric validation is performed; additional validation should be done by callers

**Important**: The current implementation provides application-level isolation and monitoring, not OS-level sandboxing. Enclave code can still:
- Use network operations (sockets, HTTP requests, etc.)
- Spawn subprocesses
- Access system resources not explicitly blocked

For production use with untrusted code, consider additional hardening:
- OS-level network isolation (network namespaces, firewall rules)
- Subprocess restrictions (seccomp filters, AppArmor/SELinux policies)
- Container-based isolation (Docker, Podman)
- Comprehensive input sanitization and validation

## Limitations

- Enclaves are process-based, not container-based (lighter weight but less isolation than Docker)
- Filesystem isolation uses Python path validation with symlink checks (not kernel namespaces)
- Resource limits are advisory and monitored at the application level (not enforced by OS)
- Network and subprocess restrictions are not actively enforced
- For stronger isolation, use Docker containers or actual OS-level sandboxing (cgroups, namespaces, seccomp)

## Examples

See `zephyr/examples/` for working examples of enclave usage.

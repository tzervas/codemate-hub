"""
Core enclave abstractions and configuration.

Defines the base enclave interfaces, configuration, and result types.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol


@dataclass
class EnclaveConfig:
    """Configuration for an enclave execution environment.
    
    Attributes:
        name: Unique identifier for the enclave
        max_memory_mb: Maximum memory usage in megabytes (0 = unlimited)
        max_cpu_percent: Maximum CPU usage percentage (0-100, 0 = unlimited)
        timeout_seconds: Maximum execution time in seconds (0 = unlimited)
        allowed_read_paths: List of paths the enclave can read from
        allowed_write_paths: List of paths the enclave can write to
        working_directory: Working directory for enclave execution
        env_vars: Environment variables to set for the enclave
        network_enabled: Whether network access is allowed (default: False)
    """
    
    name: str
    max_memory_mb: int = 512
    max_cpu_percent: int = 50
    timeout_seconds: int = 30
    allowed_read_paths: List[str] = field(default_factory=list)
    allowed_write_paths: List[str] = field(default_factory=list)
    working_directory: str = "/tmp/enclave"
    env_vars: Dict[str, str] = field(default_factory=dict)
    network_enabled: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.max_memory_mb < 0:
            raise ValueError("max_memory_mb must be non-negative")
        if not 0 <= self.max_cpu_percent <= 100:
            raise ValueError("max_cpu_percent must be between 0 and 100")
        if self.timeout_seconds < 0:
            raise ValueError("timeout_seconds must be non-negative")
        
        # Ensure paths are absolute
        self.allowed_read_paths = [str(Path(p).resolve()) for p in self.allowed_read_paths]
        self.allowed_write_paths = [str(Path(p).resolve()) for p in self.allowed_write_paths]
        self.working_directory = str(Path(self.working_directory).resolve())


@dataclass
class EnclaveResult:
    """Result from an enclave execution.
    
    Attributes:
        success: Whether the execution completed successfully
        output: The output/return value from the execution
        error: Error message if execution failed
        execution_time_ms: Time taken to execute in milliseconds
        memory_used_mb: Peak memory usage in megabytes
        cpu_percent: Average CPU usage percentage
        isolated: Whether isolation constraints were enforced
    """
    
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    memory_used_mb: float = 0.0
    cpu_percent: float = 0.0
    isolated: bool = True
    
    def __str__(self) -> str:
        """Human-readable representation of the result."""
        status = "SUCCESS" if self.success else "FAILED"
        lines = [
            f"EnclaveResult: {status}",
            f"  Execution Time: {self.execution_time_ms:.2f}ms",
            f"  Memory Used: {self.memory_used_mb:.2f}MB",
            f"  CPU Usage: {self.cpu_percent:.1f}%",
            f"  Isolated: {self.isolated}",
        ]
        if self.error:
            lines.append(f"  Error: {self.error}")
        if self.output is not None:
            output_str = str(self.output)
            if len(output_str) > 100:
                output_str = output_str[:100] + "..."
            lines.append(f"  Output: {output_str}")
        return "\n".join(lines)


class Enclave(Protocol):
    """Protocol defining the enclave interface.
    
    An enclave provides isolated execution of code with resource limits
    and filesystem restrictions.
    """
    
    @property
    def config(self) -> EnclaveConfig:
        """Get the enclave configuration."""
        ...
    
    def execute(
        self,
        target_function: str,
        module_path: str,
        args: Optional[Dict[str, Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> EnclaveResult:
        """Execute a function in the enclave.
        
        Args:
            target_function: Name of the function to execute
            module_path: Python module path containing the function
            args: Positional arguments to pass to the function
            kwargs: Keyword arguments to pass to the function
            
        Returns:
            EnclaveResult containing execution outcome and metrics
        """
        ...
    
    def validate_path_access(self, path: str, write: bool = False) -> bool:
        """Validate if a path is accessible within the enclave.
        
        Args:
            path: Path to validate
            write: Whether write access is required
            
        Returns:
            True if access is allowed, False otherwise
        """
        ...
    
    def cleanup(self) -> None:
        """Clean up enclave resources."""
        ...

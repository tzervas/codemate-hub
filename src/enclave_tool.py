"""
Enclave management tool.

Provides high-level interface for creating and managing enclaves
for isolated code execution.
"""

import logging
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from zephyr.core.enclave import EnclaveConfig, EnclaveResult
from zephyr.exec.runner import EnclaveRunner


logger = logging.getLogger(__name__)


class EnclaveTool:
    """High-level tool for managing enclaves.
    
    Provides a simple interface for creating and executing code
    in isolated enclave environments.
    """
    
    def __init__(self):
        """Initialize the enclave tool."""
        self.enclaves: Dict[str, EnclaveRunner] = {}
        self.configs: Dict[str, EnclaveConfig] = {}
    
    def create_enclave(
        self,
        objective: str,
        name: Optional[str] = None,
        max_memory_mb: int = 512,
        max_cpu_percent: int = 50,
        timeout_seconds: int = 30,
        allowed_read_paths: Optional[list] = None,
        allowed_write_paths: Optional[list] = None,
    ) -> str:
        """Create a new enclave for isolated execution.
        
        Args:
            objective: Description of the enclave's purpose
            name: Optional name for the enclave (auto-generated if not provided)
            max_memory_mb: Maximum memory limit in MB
            max_cpu_percent: Maximum CPU usage percentage
            timeout_seconds: Maximum execution time in seconds
            allowed_read_paths: Paths the enclave can read from
            allowed_write_paths: Paths the enclave can write to
            
        Returns:
            Enclave ID for future operations
        """
        enclave_id = name or f"enclave-{uuid.uuid4().hex[:8]}"
        
        logger.info(f"Creating enclave '{enclave_id}' for: {objective}")
        
        # Set default paths if not provided
        if allowed_read_paths is None:
            allowed_read_paths = ["/app/src", "/app/insights"]
        if allowed_write_paths is None:
            allowed_write_paths = [f"/tmp/{enclave_id}"]
        
        # Create configuration
        config = EnclaveConfig(
            name=enclave_id,
            max_memory_mb=max_memory_mb,
            max_cpu_percent=max_cpu_percent,
            timeout_seconds=timeout_seconds,
            allowed_read_paths=allowed_read_paths,
            allowed_write_paths=allowed_write_paths,
            working_directory=f"/tmp/{enclave_id}",
        )
        
        # Create runner
        runner = EnclaveRunner(config)
        
        # Store enclave
        self.enclaves[enclave_id] = runner
        self.configs[enclave_id] = config
        
        logger.info(
            f"Enclave '{enclave_id}' created: "
            f"memory={max_memory_mb}MB, "
            f"cpu={max_cpu_percent}%, "
            f"timeout={timeout_seconds}s"
        )
        
        return enclave_id
    
    def run_in_enclave(
        self,
        enclave_id: str,
        target_function: str,
        module_path: str,
        args: Optional[Dict[str, Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> EnclaveResult:
        """Execute a function in an enclave.
        
        Args:
            enclave_id: ID of the enclave to use
            target_function: Name of the function to execute
            module_path: Python module path containing the function
            args: Positional arguments to pass
            kwargs: Keyword arguments to pass
            
        Returns:
            EnclaveResult containing execution outcome
            
        Raises:
            KeyError: If enclave_id doesn't exist
        """
        if enclave_id not in self.enclaves:
            raise KeyError(f"Enclave '{enclave_id}' not found")
        
        runner = self.enclaves[enclave_id]
        return runner.execute(target_function, module_path, args, kwargs)
    
    def cleanup_enclave(self, enclave_id: str) -> None:
        """Clean up an enclave and its resources.
        
        Args:
            enclave_id: ID of the enclave to clean up
        """
        if enclave_id in self.enclaves:
            runner = self.enclaves[enclave_id]
            runner.cleanup()
            del self.enclaves[enclave_id]
            del self.configs[enclave_id]
            logger.info(f"Enclave '{enclave_id}' cleaned up")
    
    def list_enclaves(self) -> Dict[str, EnclaveConfig]:
        """List all active enclaves.
        
        Returns:
            Dictionary mapping enclave IDs to their configurations
        """
        return self.configs.copy()

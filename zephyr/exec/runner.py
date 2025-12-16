"""
Enclave execution runner.

Provides the main execution engine for running code in isolated enclaves
with resource limits and filesystem restrictions.
"""

import importlib
import logging
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

from zephyr.core.enclave import EnclaveConfig, EnclaveResult
from zephyr.core.limits import ResourceLimits, ResourceMonitor
from zephyr.exec.isolation import FilesystemIsolation, ProcessIsolation


logger = logging.getLogger(__name__)


class EnclaveRunner:
    """Execute code in an isolated enclave environment.
    
    The runner enforces resource limits, filesystem restrictions,
    and process isolation for secure execution of untrusted code.
    """
    
    def __init__(self, config: EnclaveConfig):
        """Initialize the enclave runner.
        
        Args:
            config: Configuration for the enclave
        """
        self.config = config
        self.filesystem = FilesystemIsolation(
            allowed_read_paths=config.allowed_read_paths,
            allowed_write_paths=config.allowed_write_paths,
        )
        self.resource_limits = ResourceLimits(
            max_memory_mb=config.max_memory_mb,
            max_cpu_percent=config.max_cpu_percent,
            timeout_seconds=config.timeout_seconds,
        )
        self._monitor: Optional[ResourceMonitor] = None
    
    @property
    def config(self) -> EnclaveConfig:
        """Get the enclave configuration."""
        return self._config
    
    @config.setter
    def config(self, value: EnclaveConfig):
        """Set the enclave configuration."""
        self._config = value
    
    def validate_path_access(self, path: str, write: bool = False) -> bool:
        """Validate if a path is accessible within the enclave.
        
        Args:
            path: Path to validate
            write: Whether write access is required
            
        Returns:
            True if access is allowed, False otherwise
        """
        return self.filesystem.validate_path_access(path, write=write)
    
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
            args: Positional arguments (as dict for now, can be list)
            kwargs: Keyword arguments to pass to the function
            
        Returns:
            EnclaveResult containing execution outcome and metrics
        """
        logger.info(
            f"[{self.config.name}] Executing {module_path}.{target_function}"
        )
        
        # Initialize resource monitor
        self._monitor = ResourceMonitor(self.resource_limits)
        start_time = time.time()
        
        # Apply process isolation
        if not self.config.network_enabled:
            ProcessIsolation.disable_network()
        ProcessIsolation.restrict_subprocess()
        
        # Set up environment
        old_env = self._setup_environment()
        old_cwd = os.getcwd()
        
        try:
            # Change to working directory
            working_dir = Path(self.config.working_directory)
            if not working_dir.exists():
                working_dir.mkdir(parents=True, exist_ok=True)
            os.chdir(working_dir)
            
            # Import the module and get the function
            try:
                module = importlib.import_module(module_path)
                func = getattr(module, target_function)
            except (ImportError, AttributeError) as e:
                logger.error(f"Failed to load {module_path}.{target_function}: {e}")
                raise
            
            # Check resource limits before execution
            within_limits, error_msg = self._monitor.check_limits()
            if not within_limits:
                raise RuntimeError(f"Resource limit check failed: {error_msg}")
            
            # Execute the function
            actual_args = args or {}
            actual_kwargs = kwargs or {}
            
            # If args is a dict and looks like kwargs, use as kwargs
            if isinstance(actual_args, dict) and not actual_kwargs:
                result = func(**actual_args)
            else:
                result = func(*actual_args.values() if isinstance(actual_args, dict) else actual_args, **actual_kwargs)
            
            # Check resource limits after execution
            within_limits, error_msg = self._monitor.check_limits()
            if not within_limits:
                logger.warning(f"Resource limit exceeded: {error_msg}")
            
            # Get final metrics
            metrics = self._monitor.get_metrics()
            
            logger.info(
                f"[{self.config.name}] Execution completed successfully "
                f"in {metrics['execution_time_ms']:.2f}ms"
            )
            
            return EnclaveResult(
                success=True,
                output=result,
                execution_time_ms=metrics["execution_time_ms"],
                memory_used_mb=metrics["memory_used_mb"],
                cpu_percent=metrics["cpu_percent"],
                isolated=True,
            )
            
        except Exception as e:
            logger.error(
                f"[{self.config.name}] Execution failed: {e}\n"
                f"{traceback.format_exc()}"
            )
            
            # Get metrics even on failure
            metrics = self._monitor.get_metrics() if self._monitor else {
                "execution_time_ms": (time.time() - start_time) * 1000,
                "memory_used_mb": 0.0,
                "cpu_percent": 0.0,
            }
            
            return EnclaveResult(
                success=False,
                error=str(e),
                execution_time_ms=metrics["execution_time_ms"],
                memory_used_mb=metrics["memory_used_mb"],
                cpu_percent=metrics["cpu_percent"],
                isolated=True,
            )
            
        finally:
            # Restore environment
            os.chdir(old_cwd)
            self._restore_environment(old_env)
            self._monitor = None
    
    def _setup_environment(self) -> Dict[str, str]:
        """Set up enclave environment variables.
        
        Returns:
            Dictionary of old environment values for restoration
        """
        old_env = {}
        for key, value in self.config.env_vars.items():
            old_env[key] = os.environ.get(key)
            os.environ[key] = value
        return old_env
    
    def _restore_environment(self, old_env: Dict[str, str]) -> None:
        """Restore original environment variables.
        
        Args:
            old_env: Dictionary of old environment values
        """
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    
    def cleanup(self) -> None:
        """Clean up enclave resources."""
        # Clean up working directory if needed
        working_dir = Path(self.config.working_directory)
        if working_dir.exists() and working_dir.name.startswith("enclave-"):
            # Only clean up auto-generated enclave directories
            try:
                import shutil
                shutil.rmtree(working_dir)
                logger.debug(f"Cleaned up enclave directory: {working_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up {working_dir}: {e}")

"""
Filesystem and process isolation mechanisms.

Provides utilities for enforcing filesystem access restrictions
and process isolation within enclaves.
"""

import os
from pathlib import Path
from typing import List


class FilesystemIsolation:
    """Enforce filesystem access restrictions for enclaves.
    
    This class validates file access against configured allowlists
    for read and write operations.
    """
    
    def __init__(
        self,
        allowed_read_paths: List[str],
        allowed_write_paths: List[str],
    ):
        """Initialize filesystem isolation.
        
        Args:
            allowed_read_paths: Paths that can be read
            allowed_write_paths: Paths that can be written
        """
        self.allowed_read_paths = [Path(p).resolve() for p in allowed_read_paths]
        self.allowed_write_paths = [Path(p).resolve() for p in allowed_write_paths]
    
    def validate_read_access(self, path: str) -> bool:
        """Check if a path can be read.
        
        Args:
            path: Path to validate
            
        Returns:
            True if read access is allowed
        """
        try:
            target_path = Path(path).resolve()
        except (ValueError, OSError):
            return False
        
        # Check if path is under any allowed read path
        for allowed_path in self.allowed_read_paths:
            try:
                target_path.relative_to(allowed_path)
                return True
            except ValueError:
                continue
        
        return False
    
    def validate_write_access(self, path: str) -> bool:
        """Check if a path can be written.
        
        Args:
            path: Path to validate
            
        Returns:
            True if write access is allowed
        """
        try:
            target_path = Path(path).resolve()
        except (ValueError, OSError):
            return False
        
        # Check if path is under any allowed write path
        for allowed_path in self.allowed_write_paths:
            try:
                target_path.relative_to(allowed_path)
                return True
            except ValueError:
                continue
        
        return False
    
    def validate_path_access(self, path: str, write: bool = False) -> bool:
        """Validate if a path is accessible.
        
        Args:
            path: Path to validate
            write: Whether write access is required
            
        Returns:
            True if access is allowed
        """
        if write:
            return self.validate_write_access(path)
        else:
            return self.validate_read_access(path)
    
    def safe_open(self, path: str, mode: str = "r"):
        """Open a file with access validation.
        
        Args:
            path: Path to open
            mode: File mode ('r', 'w', 'a', etc.)
            
        Returns:
            File handle
            
        Raises:
            PermissionError: If access is not allowed
        """
        write_mode = any(m in mode for m in ['w', 'a', '+'])
        
        if not self.validate_path_access(path, write=write_mode):
            raise PermissionError(
                f"Access denied: {path} "
                f"({'write' if write_mode else 'read'} not allowed in enclave)"
            )
        
        return open(path, mode)


class ProcessIsolation:
    """Process isolation utilities for enclaves.
    
    Provides utilities to restrict process capabilities like
    network access and subprocess execution.
    """
    
    @staticmethod
    def disable_network():
        """Disable network access for the process.
        
        Note: This is a best-effort implementation. True network
        isolation requires OS-level sandboxing (e.g., network namespaces).
        """
        # This is a placeholder - true network isolation requires
        # OS-level features like network namespaces or firewall rules
        # For now, we just document the restriction
        pass
    
    @staticmethod
    def restrict_subprocess():
        """Restrict subprocess execution.
        
        Note: This is advisory. True subprocess restriction requires
        OS-level sandboxing (e.g., seccomp filters).
        """
        # This is a placeholder - true subprocess restriction requires
        # OS-level features like seccomp or AppArmor
        pass

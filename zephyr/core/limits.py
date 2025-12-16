"""
Resource limit tracking and enforcement.

Provides utilities for monitoring and enforcing resource limits during enclave execution.
"""

import os
import psutil
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class ResourceLimits:
    """Resource limits for an enclave.
    
    Attributes:
        max_memory_mb: Maximum memory in megabytes (0 = unlimited)
        max_cpu_percent: Maximum CPU percentage (0-100, 0 = unlimited)
        timeout_seconds: Maximum execution time in seconds (0 = unlimited)
    """
    
    max_memory_mb: int = 0
    max_cpu_percent: int = 0
    timeout_seconds: int = 0


class ResourceMonitor:
    """Monitor and enforce resource limits for a process.
    
    This class tracks CPU, memory, and execution time for a process
    and can enforce configured limits.
    """
    
    def __init__(self, limits: ResourceLimits, pid: Optional[int] = None):
        """Initialize the resource monitor.
        
        Args:
            limits: Resource limits to enforce
            pid: Process ID to monitor (default: current process)
        """
        self.limits = limits
        self.pid = pid or os.getpid()
        self.start_time = time.time()
        self.peak_memory_mb = 0.0
        self.avg_cpu_percent = 0.0
        
        try:
            self.process = psutil.Process(self.pid)
        except psutil.NoSuchProcess:
            self.process = None
    
    def check_limits(self) -> tuple[bool, Optional[str]]:
        """Check if resource limits are being exceeded.
        
        Returns:
            Tuple of (within_limits, error_message)
            If within_limits is False, error_message contains the violation reason
        """
        if not self.process:
            return True, None
        
        # Check timeout
        if self.limits.timeout_seconds > 0:
            elapsed = time.time() - self.start_time
            if elapsed > self.limits.timeout_seconds:
                return False, f"Timeout exceeded: {elapsed:.2f}s > {self.limits.timeout_seconds}s"
        
        # Check memory
        if self.limits.max_memory_mb > 0:
            try:
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)
                self.peak_memory_mb = max(self.peak_memory_mb, memory_mb)
                
                if memory_mb > self.limits.max_memory_mb:
                    return False, f"Memory limit exceeded: {memory_mb:.2f}MB > {self.limits.max_memory_mb}MB"
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Check CPU (this is informational, hard to enforce in Python)
        if self.limits.max_cpu_percent > 0:
            try:
                cpu_percent = self.process.cpu_percent(interval=0.1)
                self.avg_cpu_percent = (self.avg_cpu_percent + cpu_percent) / 2
                
                # CPU limit is advisory - we log but don't fail
                if cpu_percent > self.limits.max_cpu_percent:
                    # Note: We don't fail on CPU limit, just track it
                    pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return True, None
    
    def get_metrics(self) -> dict:
        """Get current resource usage metrics.
        
        Returns:
            Dictionary with execution_time_ms, memory_used_mb, cpu_percent
        """
        elapsed_ms = (time.time() - self.start_time) * 1000
        
        return {
            "execution_time_ms": elapsed_ms,
            "memory_used_mb": self.peak_memory_mb,
            "cpu_percent": self.avg_cpu_percent,
        }


def check_memory_available(required_mb: int) -> bool:
    """Check if sufficient memory is available.
    
    Args:
        required_mb: Required memory in megabytes
        
    Returns:
        True if sufficient memory is available
    """
    try:
        mem = psutil.virtual_memory()
        available_mb = mem.available / (1024 * 1024)
        return available_mb >= required_mb
    except Exception:
        # If we can't check, assume it's available
        return True

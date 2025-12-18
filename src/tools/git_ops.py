"""
Git Operations Tool

Git repository operations for version control integration.
Provides safe operations with configurable restrictions.
"""

import asyncio
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class GitResult:
    """Result of a git operation."""
    success: bool
    output: str
    error: str
    command: str


class GitOperationsTool:
    """
    Git operations tool with safety restrictions.
    
    Supports common git operations with configurable
    restrictions to prevent destructive actions.
    """
    
    name = "git_operations"
    description = "Git repository operations"
    
    # Operations that are always safe (read-only)
    SAFE_OPERATIONS = {
        "status", "diff", "log", "show", "branch", "remote",
        "tag", "stash list", "describe", "rev-parse", "ls-files",
        "blame", "shortlog", "reflog",
    }
    
    # Operations that modify state (require explicit enable)
    WRITE_OPERATIONS = {
        "add", "commit", "push", "pull", "fetch", "checkout",
        "merge", "rebase", "reset", "stash", "cherry-pick",
    }
    
    # Operations that are never allowed
    DANGEROUS_OPERATIONS = {
        "push --force", "reset --hard", "clean -fd", "gc --prune",
        "filter-branch", "rebase -i", "push --delete",
    }
    
    def __init__(
        self,
        repo_path: Optional[str] = None,
        allowed_operations: Optional[list[str]] = None,
        allow_writes: bool = False,
        max_output_lines: int = 500,
    ):
        """
        Initialize git operations tool.
        
        Args:
            repo_path: Path to git repository (default: current directory)
            allowed_operations: Explicit list of allowed operations
            allow_writes: Enable write operations (add, commit, push, etc.)
            max_output_lines: Maximum output lines before truncation
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.allow_writes = allow_writes
        self.max_output_lines = max_output_lines
        
        # Build allowed operations set
        self.allowed_operations = set(allowed_operations) if allowed_operations else set()
        if not self.allowed_operations:
            self.allowed_operations = self.SAFE_OPERATIONS.copy()
            if self.allow_writes:
                self.allowed_operations.update(self.WRITE_OPERATIONS)
    
    async def execute(
        self,
        operation: str,
        args: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Execute a git operation.
        
        Args:
            operation: Git operation (e.g., "status", "log", "diff")
            args: Additional arguments for the operation
            
        Returns:
            Dictionary with operation results
        """
        args = args or []
        
        # Validate operation
        validation = self._validate_operation(operation, args)
        if not validation["allowed"]:
            return {
                "success": False,
                "error": validation["reason"],
                "operation": operation,
            }
        
        # Build command
        command = ["git", operation] + args
        command_str = " ".join(command)
        
        try:
            result = await self._run_git_command(command)
            return {
                "success": result.success,
                "output": result.output,
                "error": result.error,
                "command": command_str,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command_str,
            }
    
    def _validate_operation(
        self,
        operation: str,
        args: list[str],
    ) -> dict[str, Any]:
        """Validate if operation is allowed."""
        full_operation = f"{operation} {' '.join(args)}".strip()
        
        # Check dangerous operations first
        for dangerous in self.DANGEROUS_OPERATIONS:
            if dangerous in full_operation:
                return {
                    "allowed": False,
                    "reason": f"Dangerous operation not allowed: {dangerous}",
                }
        
        # Check if operation is in allowed set
        if operation not in self.allowed_operations:
            return {
                "allowed": False,
                "reason": f"Operation not allowed: {operation}. Allowed: {sorted(self.allowed_operations)}",
            }
        
        return {"allowed": True}
    
    async def _run_git_command(self, command: list[str]) -> GitResult:
        """Run git command and capture output."""
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.repo_path),
        )
        
        stdout, stderr = await process.communicate()
        
        output = stdout.decode('utf-8', errors='replace')
        error = stderr.decode('utf-8', errors='replace')
        
        # Truncate output if needed
        lines = output.split('\n')
        if len(lines) > self.max_output_lines:
            output = '\n'.join(lines[:self.max_output_lines])
            output += f"\n... [{len(lines) - self.max_output_lines} more lines truncated]"
        
        return GitResult(
            success=process.returncode == 0,
            output=output,
            error=error,
            command=' '.join(command),
        )
    
    # Convenience methods for common operations
    
    async def status(self, short: bool = False) -> dict[str, Any]:
        """Get repository status."""
        args = ["-s"] if short else []
        return await self.execute("status", args)
    
    async def diff(
        self,
        staged: bool = False,
        path: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get diff of changes."""
        args = []
        if staged:
            args.append("--staged")
        if path:
            args.extend(["--", path])
        return await self.execute("diff", args)
    
    async def log(
        self,
        count: int = 10,
        oneline: bool = True,
        path: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get commit log."""
        args = [f"-{count}"]
        if oneline:
            args.append("--oneline")
        if path:
            args.extend(["--", path])
        return await self.execute("log", args)
    
    async def branch(self, all: bool = False) -> dict[str, Any]:
        """List branches."""
        args = ["-a"] if all else []
        return await self.execute("branch", args)
    
    async def show(self, ref: str = "HEAD") -> dict[str, Any]:
        """Show commit details."""
        return await self.execute("show", [ref])
    
    async def add(self, path: str = ".") -> dict[str, Any]:
        """Stage changes."""
        if not self.allow_writes:
            return {
                "success": False,
                "error": "Write operations not enabled",
            }
        return await self.execute("add", [path])
    
    async def commit(self, message: str) -> dict[str, Any]:
        """Create commit."""
        if not self.allow_writes:
            return {
                "success": False,
                "error": "Write operations not enabled",
            }
        return await self.execute("commit", ["-m", message])
    
    async def get_repo_info(self) -> dict[str, Any]:
        """Get repository information."""
        info = {}
        
        # Get current branch
        result = await self.execute("rev-parse", ["--abbrev-ref", "HEAD"])
        if result["success"]:
            info["current_branch"] = result["output"].strip()
        
        # Get remote URL
        result = await self.execute("remote", ["get-url", "origin"])
        if result["success"]:
            info["remote_url"] = result["output"].strip()
        
        # Get latest commit
        result = await self.execute("log", ["-1", "--oneline"])
        if result["success"]:
            info["latest_commit"] = result["output"].strip()
        
        # Get status summary
        result = await self.status(short=True)
        if result["success"]:
            lines = [l for l in result["output"].split('\n') if l.strip()]
            info["changes_count"] = len(lines)
            info["has_changes"] = len(lines) > 0
        
        return {
            "success": True,
            "repo_path": str(self.repo_path),
            **info,
        }


if __name__ == "__main__":
    async def main():
        # Initialize with read-only access
        tool = GitOperationsTool(allow_writes=False)
        
        print("Repository Info:")
        info = await tool.get_repo_info()
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        print("\nRecent commits:")
        result = await tool.log(count=5)
        if result["success"]:
            print(result["output"])
        
        print("\nCurrent status:")
        result = await tool.status()
        if result["success"]:
            print(result["output"] or "  No changes")
    
    asyncio.run(main())

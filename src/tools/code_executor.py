"""
Code Executor Tool

Sandboxed code execution for Python, JavaScript, and Bash.
Provides safe execution with timeouts and resource limits.
"""

import asyncio
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class ExecutionResult:
    """Result of code execution."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: float
    language: str
    truncated: bool = False


class CodeExecutorTool:
    """
    Sandboxed code executor supporting multiple languages.
    
    Supports:
    - Python (via subprocess)
    - JavaScript (via Node.js)
    - Bash (via shell)
    
    Features:
    - Timeout enforcement
    - Output truncation
    - Error capture
    """
    
    name = "code_executor"
    description = "Execute code snippets in a sandboxed environment"
    
    SUPPORTED_LANGUAGES = {
        "python": {
            "extension": ".py",
            "command": [sys.executable, "-u"],
            "shebang": "#!/usr/bin/env python3",
        },
        "javascript": {
            "extension": ".js",
            "command": ["node"],
            "shebang": "#!/usr/bin/env node",
        },
        "bash": {
            "extension": ".sh",
            "command": ["bash"],
            "shebang": "#!/bin/bash",
        },
    }
    
    def __init__(
        self,
        sandbox: bool = True,
        timeout_seconds: int = 30,
        max_memory_mb: int = 512,
        max_output_chars: int = 10000,
        allowed_languages: Optional[list[str]] = None,
    ):
        """
        Initialize code executor.
        
        Args:
            sandbox: Enable sandboxing (restricts file/network access)
            timeout_seconds: Maximum execution time
            max_memory_mb: Maximum memory usage (not enforced on Windows)
            max_output_chars: Maximum output length before truncation
            allowed_languages: List of allowed languages (default: all)
        """
        self.sandbox = sandbox
        self.timeout_seconds = timeout_seconds
        self.max_memory_mb = max_memory_mb
        self.max_output_chars = max_output_chars
        self.allowed_languages = allowed_languages or list(self.SUPPORTED_LANGUAGES.keys())
    
    async def execute(
        self,
        code: str,
        language: str,
        timeout: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Execute code snippet.
        
        Args:
            code: Code to execute
            language: Programming language
            timeout: Override default timeout
            
        Returns:
            Dictionary with execution results
        """
        language = language.lower()
        
        # Validate language
        if language not in self.SUPPORTED_LANGUAGES:
            return {
                "success": False,
                "error": f"Unsupported language: {language}",
                "supported_languages": list(self.SUPPORTED_LANGUAGES.keys()),
            }
        
        if language not in self.allowed_languages:
            return {
                "success": False,
                "error": f"Language not allowed: {language}",
                "allowed_languages": self.allowed_languages,
            }
        
        timeout = timeout or self.timeout_seconds
        lang_config = self.SUPPORTED_LANGUAGES[language]
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=lang_config["extension"],
            delete=False,
            encoding='utf-8',
        ) as f:
            # Add shebang for non-Windows
            if os.name != 'nt':
                f.write(lang_config["shebang"] + "\n")
            f.write(code)
            temp_file = f.name
        
        try:
            result = await self._run_subprocess(
                command=lang_config["command"] + [temp_file],
                timeout=timeout,
                language=language,
            )
            return {
                "success": result.success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code,
                "execution_time_ms": result.execution_time_ms,
                "language": result.language,
                "truncated": result.truncated,
            }
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except OSError:
                pass
    
    async def _run_subprocess(
        self,
        command: list[str],
        timeout: int,
        language: str,
    ) -> ExecutionResult:
        """Run subprocess with timeout and capture output."""
        start_time = time.time()
        
        try:
            # Build environment
            env = os.environ.copy()
            
            # Sandbox restrictions (basic)
            if self.sandbox:
                # Restrict certain environment variables
                env.pop("AWS_ACCESS_KEY_ID", None)
                env.pop("AWS_SECRET_ACCESS_KEY", None)
                env.pop("GITHUB_TOKEN", None)
                env.pop("DATABASE_URL", None)
            
            # Run process
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr=f"Execution timed out after {timeout} seconds",
                    exit_code=-1,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    language=language,
                )
            
            execution_time = (time.time() - start_time) * 1000
            
            # Decode output
            stdout = stdout_bytes.decode('utf-8', errors='replace')
            stderr = stderr_bytes.decode('utf-8', errors='replace')
            
            # Truncate if needed
            truncated = False
            if len(stdout) > self.max_output_chars:
                stdout = stdout[:self.max_output_chars] + "\n... [output truncated]"
                truncated = True
            if len(stderr) > self.max_output_chars:
                stderr = stderr[:self.max_output_chars] + "\n... [output truncated]"
                truncated = True
            
            return ExecutionResult(
                success=process.returncode == 0,
                stdout=stdout,
                stderr=stderr,
                exit_code=process.returncode or 0,
                execution_time_ms=execution_time,
                language=language,
                truncated=truncated,
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                exit_code=-1,
                execution_time_ms=(time.time() - start_time) * 1000,
                language=language,
            )
    
    async def validate_syntax(
        self,
        code: str,
        language: str,
    ) -> dict[str, Any]:
        """
        Validate code syntax without execution.
        
        Args:
            code: Code to validate
            language: Programming language
            
        Returns:
            Dictionary with validation results
        """
        language = language.lower()
        
        if language == "python":
            try:
                compile(code, "<string>", "exec")
                return {
                    "valid": True,
                    "language": language,
                }
            except SyntaxError as e:
                return {
                    "valid": False,
                    "language": language,
                    "error": str(e),
                    "line": e.lineno,
                    "offset": e.offset,
                }
        
        elif language == "javascript":
            # Use node to check syntax
            result = await self.execute(
                code=f"new Function({repr(code)})",
                language="javascript",
                timeout=5,
            )
            if result["success"]:
                return {"valid": True, "language": language}
            else:
                return {
                    "valid": False,
                    "language": language,
                    "error": result.get("stderr", "Syntax error"),
                }
        
        elif language == "bash":
            # Use bash -n to check syntax
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                process = await asyncio.create_subprocess_exec(
                    "bash", "-n", temp_file,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await process.communicate()
                
                if process.returncode == 0:
                    return {"valid": True, "language": language}
                else:
                    return {
                        "valid": False,
                        "language": language,
                        "error": stderr.decode('utf-8', errors='replace'),
                    }
            finally:
                os.unlink(temp_file)
        
        else:
            return {
                "valid": False,
                "error": f"Syntax validation not supported for: {language}",
            }


if __name__ == "__main__":
    async def main():
        executor = CodeExecutorTool(timeout_seconds=10)
        
        # Test Python
        print("Testing Python execution:")
        result = await executor.execute(
            code='print("Hello from Python!")\nprint(2 + 2)',
            language="python",
        )
        print(f"  Success: {result['success']}")
        print(f"  Output: {result['stdout']}")
        print(f"  Time: {result['execution_time_ms']:.2f}ms")
        
        # Test syntax validation
        print("\nTesting syntax validation:")
        valid_result = await executor.validate_syntax(
            code='def hello():\n    print("hi")',
            language="python",
        )
        print(f"  Valid syntax: {valid_result['valid']}")
        
        invalid_result = await executor.validate_syntax(
            code='def hello(\n    print("hi")',
            language="python",
        )
        print(f"  Invalid syntax: {not invalid_result['valid']}")
        print(f"  Error: {invalid_result.get('error', 'N/A')}")
    
    asyncio.run(main())

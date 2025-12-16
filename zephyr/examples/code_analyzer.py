"""
Simple code analyzer example for enclave execution.

This demonstrates a simple code analysis task that can run in an enclave
with filesystem isolation and resource limits.
"""

import ast
import logging
from pathlib import Path
from typing import Dict, Any


logger = logging.getLogger(__name__)


def analyze_code(code_file: str) -> Dict[str, Any]:
    """Analyze a Python code file and extract metrics.
    
    This is a simple example that demonstrates enclave execution.
    It counts lines, functions, classes, and imports in a Python file.
    
    Args:
        code_file: Path to the Python file to analyze
        
    Returns:
        Dictionary containing code metrics
    """
    logger.info(f"Analyzing code file: {code_file}")
    
    # Read the file
    try:
        with open(code_file, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        logger.error(f"Failed to read {code_file}: {e}")
        raise
    
    # Parse the code
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        logger.error(f"Syntax error in {code_file}: {e}")
        raise
    
    # Extract metrics
    metrics = {
        "file": code_file,
        "lines": len(code.splitlines()),
        "functions": 0,
        "classes": 0,
        "imports": 0,
        "async_functions": 0,
    }
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            metrics["functions"] += 1
        elif isinstance(node, ast.AsyncFunctionDef):
            metrics["async_functions"] += 1
        elif isinstance(node, ast.ClassDef):
            metrics["classes"] += 1
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            metrics["imports"] += 1
    
    logger.info(
        f"Code analysis complete: "
        f"{metrics['lines']} lines, "
        f"{metrics['functions']} functions, "
        f"{metrics['classes']} classes"
    )
    
    return metrics


def analyze_code_string(code: str, filename: str = "<string>") -> Dict[str, Any]:
    """Analyze Python code from a string.
    
    Args:
        code: Python code to analyze
        filename: Name to use for the code (for error messages)
        
    Returns:
        Dictionary containing code metrics
    """
    logger.info(f"Analyzing code string: {filename}")
    
    # Parse the code
    try:
        tree = ast.parse(code, filename=filename)
    except SyntaxError as e:
        logger.error(f"Syntax error in {filename}: {e}")
        raise
    
    # Extract metrics
    metrics = {
        "file": filename,
        "lines": len(code.splitlines()),
        "functions": 0,
        "classes": 0,
        "imports": 0,
        "async_functions": 0,
    }
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            metrics["functions"] += 1
        elif isinstance(node, ast.AsyncFunctionDef):
            metrics["async_functions"] += 1
        elif isinstance(node, ast.ClassDef):
            metrics["classes"] += 1
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            metrics["imports"] += 1
    
    logger.info(
        f"Code analysis complete: "
        f"{metrics['lines']} lines, "
        f"{metrics['functions']} functions, "
        f"{metrics['classes']} classes"
    )
    
    return metrics

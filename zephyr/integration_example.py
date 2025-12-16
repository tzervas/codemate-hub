"""
Example integration of Zephyr enclaves with the pipeline.

This demonstrates how to use enclaves for secure code analysis
within the coding assistant pipeline.
"""

import logging
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.enclave_tool import EnclaveTool


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def analyze_codebase_in_enclave():
    """Analyze multiple files in the codebase using enclaves."""
    logger.info("Analyzing codebase with Zephyr enclaves")
    
    tool = EnclaveTool()
    
    # Create a dedicated enclave for code analysis
    enclave_id = tool.create_enclave(
        objective="Analyze Python codebase for metrics",
        name="codebase-analyzer",
        max_memory_mb=512,
        max_cpu_percent=75,
        timeout_seconds=60,
        allowed_read_paths=["/home/runner/work/codemate-hub/codemate-hub/src"],
    )
    
    # Files to analyze
    files_to_analyze = [
        "/home/runner/work/codemate-hub/codemate-hub/src/pipeline.py",
        "/home/runner/work/codemate-hub/codemate-hub/src/enclave_tool.py",
        "/home/runner/work/codemate-hub/codemate-hub/src/memory_setup.py",
    ]
    
    results = []
    for file_path in files_to_analyze:
        logger.info(f"Analyzing {Path(file_path).name}...")
        
        result = tool.run_in_enclave(
            enclave_id=enclave_id,
            target_function="analyze_code",
            module_path="zephyr.examples.code_analyzer",
            args={"code_file": file_path},
        )
        
        if result.success:
            results.append(result.output)
            logger.info(
                f"  ✓ {result.output['lines']} lines, "
                f"{result.output['functions']} functions, "
                f"{result.output['classes']} classes "
                f"({result.execution_time_ms:.0f}ms)"
            )
        else:
            logger.error(f"  ✗ Failed: {result.error}")
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("Analysis Summary")
    logger.info("=" * 60)
    
    total_lines = sum(r["lines"] for r in results)
    total_functions = sum(r["functions"] for r in results)
    total_classes = sum(r["classes"] for r in results)
    total_imports = sum(r["imports"] for r in results)
    
    logger.info(f"Files analyzed: {len(results)}")
    logger.info(f"Total lines: {total_lines}")
    logger.info(f"Total functions: {total_functions}")
    logger.info(f"Total classes: {total_classes}")
    logger.info(f"Total imports: {total_imports}")
    
    # Cleanup
    tool.cleanup_enclave(enclave_id)
    logger.info("\nEnclave cleaned up")


def secure_code_transformation():
    """Transform code securely in an enclave."""
    logger.info("\n" + "=" * 60)
    logger.info("Secure Code Transformation")
    logger.info("=" * 60)
    
    tool = EnclaveTool()
    
    # Create enclave for transformation
    enclave_id = tool.create_enclave(
        objective="Transform code snippets",
        name="code-transformer",
        max_memory_mb=256,
        timeout_seconds=10,
    )
    
    # Sample code snippets to transform
    snippets = [
        "def hello(): pass",
        "class MyClass: pass",
        "import sys; import os",
    ]
    
    # Transform to uppercase (simple example)
    result = tool.run_in_enclave(
        enclave_id=enclave_id,
        target_function="simple_transform",
        module_path="zephyr.examples.pipeline_step",
        args={"data": snippets, "operation": "upper"},
    )
    
    if result.success:
        logger.info("Transformation successful:")
        for original, transformed in zip(snippets, result.output["data"]):
            logger.info(f"  {original[:30]:30} → {transformed[:30]}")
    
    tool.cleanup_enclave(enclave_id)
    logger.info("Enclave cleaned up")


def main():
    """Run integration examples."""
    logger.info("Zephyr Enclave Integration Examples")
    logger.info("=" * 60)
    
    try:
        analyze_codebase_in_enclave()
        secure_code_transformation()
        
        logger.info("\n" + "=" * 60)
        logger.info("Integration examples completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Integration example failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

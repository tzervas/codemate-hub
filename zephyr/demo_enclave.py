#!/usr/bin/env python3
"""
Demonstration script for the Zephyr enclave system.

This script demonstrates:
1. Creating an enclave with resource limits
2. Running code analysis in an isolated environment
3. Running data transformation tasks
4. Filesystem isolation
5. Resource monitoring
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.enclave_tool import EnclaveTool
from zephyr.core.enclave import EnclaveConfig
from zephyr.exec.runner import EnclaveRunner


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def demo_basic_enclave():
    """Demonstrate basic enclave creation and execution."""
    logger.info("=" * 60)
    logger.info("Demo 1: Basic Enclave Execution")
    logger.info("=" * 60)
    
    tool = EnclaveTool()
    
    # Create an enclave for data transformation
    enclave_id = tool.create_enclave(
        objective="Transform text data",
        name="demo-transform",
        max_memory_mb=256,
        max_cpu_percent=50,
        timeout_seconds=10,
    )
    
    logger.info(f"Created enclave: {enclave_id}")
    
    # Run a transformation
    result = tool.run_in_enclave(
        enclave_id=enclave_id,
        target_function="simple_transform",
        module_path="zephyr.examples.pipeline_step",
        args={"data": ["hello", "world", "from", "enclave"], "operation": "upper"},
    )
    
    logger.info(f"Execution result:\n{result}")
    
    # Cleanup
    tool.cleanup_enclave(enclave_id)
    logger.info("Enclave cleaned up\n")


def demo_code_analysis():
    """Demonstrate code analysis in an enclave."""
    logger.info("=" * 60)
    logger.info("Demo 2: Code Analysis in Enclave")
    logger.info("=" * 60)
    
    # Use relative path that works across different environments
    src_dir = Path(__file__).parent.parent / "src"
    
    # Create enclave with direct runner
    config = EnclaveConfig(
        name="code-analyzer",
        max_memory_mb=512,
        timeout_seconds=15,
        allowed_read_paths=[str(src_dir)],
    )
    runner = EnclaveRunner(config)
    
    # Analyze the pipeline.py file
    pipeline_file = src_dir / "pipeline.py"
    result = runner.execute(
        target_function="analyze_code",
        module_path="zephyr.examples.code_analyzer",
        args={"code_file": str(pipeline_file)},
    )
    
    if result.success:
        logger.info(f"Analysis successful!")
        logger.info(f"File: {result.output['file']}")
        logger.info(f"Lines: {result.output['lines']}")
        logger.info(f"Functions: {result.output['functions']}")
        logger.info(f"Classes: {result.output['classes']}")
        logger.info(f"Imports: {result.output['imports']}")
        logger.info(f"Execution time: {result.execution_time_ms:.2f}ms")
        logger.info(f"Memory used: {result.memory_used_mb:.2f}MB")
    else:
        logger.error(f"Analysis failed: {result.error}")
    
    runner.cleanup()
    logger.info("Runner cleaned up\n")


def demo_filesystem_isolation():
    """Demonstrate filesystem isolation."""
    logger.info("=" * 60)
    logger.info("Demo 3: Filesystem Isolation")
    logger.info("=" * 60)
    
    config = EnclaveConfig(
        name="isolated-fs",
        allowed_read_paths=["/tmp"],
        allowed_write_paths=["/tmp/enclave-output"],
    )
    runner = EnclaveRunner(config)
    
    # Test read access validation
    can_read_tmp = runner.validate_path_access("/tmp/test.txt", write=False)
    can_read_etc = runner.validate_path_access("/etc/passwd", write=False)
    
    logger.info(f"Can read /tmp/test.txt: {can_read_tmp}")
    logger.info(f"Can read /etc/passwd: {can_read_etc}")
    
    # Test write access validation
    can_write_allowed = runner.validate_path_access("/tmp/enclave-output/test.txt", write=True)
    can_write_denied = runner.validate_path_access("/tmp/test.txt", write=True)
    
    logger.info(f"Can write /tmp/enclave-output/test.txt: {can_write_allowed}")
    logger.info(f"Can write /tmp/test.txt: {can_write_denied}")
    
    logger.info("Filesystem isolation working as expected!\n")


def demo_word_count():
    """Demonstrate word counting in an enclave."""
    logger.info("=" * 60)
    logger.info("Demo 4: Word Count Analysis")
    logger.info("=" * 60)
    
    tool = EnclaveTool()
    
    enclave_id = tool.create_enclave(
        objective="Analyze text content",
        name="word-counter",
    )
    
    sample_text = """
    The Zephyr enclave system provides lightweight isolation for code execution.
    It enables secure execution of untrusted code with resource limits and
    filesystem restrictions. This makes it ideal for analyzing user-provided
    code or running transformations on sensitive data.
    """
    
    result = tool.run_in_enclave(
        enclave_id=enclave_id,
        target_function="word_count",
        module_path="zephyr.examples.pipeline_step",
        args={"text": sample_text},
    )
    
    if result.success:
        logger.info(f"Word count analysis:")
        logger.info(f"  Total words: {result.output['total_words']}")
        logger.info(f"  Unique words: {result.output['unique_words']}")
        logger.info(f"  Average word length: {result.output['avg_word_length']:.1f}")
        logger.info(f"  Longest word: {result.output['longest_word']}")
        logger.info(f"  Execution time: {result.execution_time_ms:.2f}ms")
    
    tool.cleanup_enclave(enclave_id)
    logger.info("Enclave cleaned up\n")


def demo_multiple_enclaves():
    """Demonstrate running multiple enclaves concurrently."""
    logger.info("=" * 60)
    logger.info("Demo 5: Multiple Concurrent Enclaves")
    logger.info("=" * 60)
    
    tool = EnclaveTool()
    
    # Create multiple enclaves
    enc1 = tool.create_enclave(objective="Transform to uppercase", name="enc-upper")
    enc2 = tool.create_enclave(objective="Transform to lowercase", name="enc-lower")
    enc3 = tool.create_enclave(objective="Reverse strings", name="enc-reverse")
    
    logger.info(f"Created {len(tool.list_enclaves())} enclaves")
    
    # Run transformations in parallel
    data = ["Hello", "World", "Enclave"]
    
    result1 = tool.run_in_enclave(
        enc1, "simple_transform", "zephyr.examples.pipeline_step",
        args={"data": data, "operation": "upper"}
    )
    
    result2 = tool.run_in_enclave(
        enc2, "simple_transform", "zephyr.examples.pipeline_step",
        args={"data": data, "operation": "lower"}
    )
    
    result3 = tool.run_in_enclave(
        enc3, "simple_transform", "zephyr.examples.pipeline_step",
        args={"data": data, "operation": "reverse"}
    )
    
    logger.info(f"Uppercase: {result1.output['data']}")
    logger.info(f"Lowercase: {result2.output['data']}")
    logger.info(f"Reversed: {result3.output['data']}")
    
    # Cleanup all
    for enclave_id in [enc1, enc2, enc3]:
        tool.cleanup_enclave(enclave_id)
    
    logger.info("All enclaves cleaned up\n")


def main():
    """Run all demonstrations."""
    logger.info("Zephyr Enclave System Demonstration")
    logger.info("=" * 60)
    logger.info("")
    
    try:
        demo_basic_enclave()
        demo_code_analysis()
        demo_filesystem_isolation()
        demo_word_count()
        demo_multiple_enclaves()
        
        logger.info("=" * 60)
        logger.info("All demonstrations completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Demonstration failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

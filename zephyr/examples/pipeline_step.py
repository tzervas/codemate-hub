"""
Simple pipeline step example for enclave execution.

This demonstrates a simple data transformation task that can run
in an enclave with resource limits.
"""

import logging
from typing import Any, Dict, List


logger = logging.getLogger(__name__)


def simple_transform(data: List[str], operation: str = "upper") -> Dict[str, Any]:
    """Perform a simple transformation on a list of strings.
    
    This is a simple example that demonstrates enclave execution
    for data transformation tasks.
    
    Args:
        data: List of strings to transform
        operation: Transformation to apply ('upper', 'lower', 'reverse')
        
    Returns:
        Dictionary containing transformed data and metadata
    """
    logger.info(f"Transforming {len(data)} items with operation: {operation}")
    
    if operation == "upper":
        transformed = [s.upper() for s in data]
    elif operation == "lower":
        transformed = [s.lower() for s in data]
    elif operation == "reverse":
        transformed = [s[::-1] for s in data]
    else:
        raise ValueError(f"Unknown operation: {operation}")
    
    result = {
        "input_count": len(data),
        "output_count": len(transformed),
        "operation": operation,
        "data": transformed,
    }
    
    logger.info(f"Transformation complete: {len(transformed)} items")
    
    return result


def word_count(text: str) -> Dict[str, Any]:
    """Count words in a text string.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary containing word count statistics
    """
    logger.info("Counting words in text")
    
    words = text.split()
    unique_words = set(words)
    
    result = {
        "total_words": len(words),
        "unique_words": len(unique_words),
        "avg_word_length": sum(len(w) for w in words) / len(words) if words else 0,
        "longest_word": max(words, key=len) if words else "",
    }
    
    logger.info(
        f"Word count complete: "
        f"{result['total_words']} total, "
        f"{result['unique_words']} unique"
    )
    
    return result

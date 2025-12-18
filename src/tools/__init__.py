"""
Codemate Hub Tools Package

Custom tools for the coding assistant platform.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .code_executor import CodeExecutorTool
    from .document_processor import DocumentProcessor, DocumentProcessorTool
    from .git_ops import GitOperationsTool
    from .vector_search import VectorSearchTool

__all__ = [
    "CodeExecutorTool",
    "DocumentProcessor",
    "DocumentProcessorTool",
    "GitOperationsTool",
    "VectorSearchTool",
]


def load_tool(tool_name: str, config: dict | None = None):
    """
    Load a tool by name with optional configuration.
    
    Args:
        tool_name: Name of the tool to load
        config: Optional configuration dictionary
        
    Returns:
        Initialized tool instance
        
    Raises:
        ValueError: If tool name is not recognized
    """
    config = config or {}
    
    if tool_name == "code_executor":
        from .code_executor import CodeExecutorTool
        return CodeExecutorTool(**config)
    
    elif tool_name == "document_processor":
        from .document_processor import DocumentProcessorTool
        return DocumentProcessorTool(config)
    
    elif tool_name == "git_operations":
        from .git_ops import GitOperationsTool
        return GitOperationsTool(**config)
    
    elif tool_name == "vector_search":
        from .vector_search import VectorSearchTool
        return VectorSearchTool(**config)
    
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def list_available_tools() -> list[dict]:
    """
    List all available tools with their descriptions.
    
    Returns:
        List of tool information dictionaries
    """
    return [
        {
            "name": "code_executor",
            "description": "Execute code snippets in sandboxed environment",
            "languages": ["python", "javascript", "bash"],
        },
        {
            "name": "document_processor",
            "description": "Process and chunk documents for RAG",
            "formats": ["pdf", "docx", "txt", "md", "html", "csv", "json"],
        },
        {
            "name": "git_operations",
            "description": "Git repository operations",
            "operations": ["status", "diff", "log", "branch", "commit", "push"],
        },
        {
            "name": "vector_search",
            "description": "Semantic search in ChromaDB",
            "capabilities": ["search", "add", "delete", "info"],
        },
    ]

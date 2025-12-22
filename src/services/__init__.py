"""
Codemate Hub Services Package

High-level services for the coding assistant platform.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .embedding_service import EmbeddingService
    from .ingestion_service import DocumentIngestionService
    from .rag_pipeline import RAGPipeline

__all__ = [
    "EmbeddingService",
    "DocumentIngestionService",
    "RAGPipeline",
]

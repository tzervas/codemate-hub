"""
Embedding Service

High-level embedding service for document and query embedding operations.
Provides batch processing and caching capabilities.
"""

import hashlib
import os
import time
from dataclasses import dataclass
from typing import Any, Optional

from langchain_community.embeddings import OllamaEmbeddings


@dataclass
class EmbeddingResult:
    """Result of embedding operation."""
    text: str
    embedding: list[float]
    model: str
    dimensions: int
    processing_time_ms: float


class EmbeddingService:
    """
    Embedding service for generating vector representations.
    
    Features:
    - Multiple embedding models
    - Batch processing
    - Simple in-memory caching
    - Dimension tracking
    """
    
    def __init__(
        self,
        model: str = "nomic-embed-text",
        ollama_base_url: Optional[str] = None,
        cache_enabled: bool = True,
        cache_max_size: int = 1000,
    ):
        """
        Initialize embedding service.
        
        Args:
            model: Embedding model name
            ollama_base_url: Ollama API URL
            cache_enabled: Enable embedding cache
            cache_max_size: Maximum cache entries
        """
        self.model = model
        self.ollama_base_url = ollama_base_url or os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        self.cache_enabled = cache_enabled
        self.cache_max_size = cache_max_size
        
        self._cache: dict[str, list[float]] = {}
        self._embeddings: Optional[OllamaEmbeddings] = None
        self._dimensions: Optional[int] = None
    
    @property
    def embeddings(self) -> OllamaEmbeddings:
        """Lazy-load embeddings model."""
        if self._embeddings is None:
            self._embeddings = OllamaEmbeddings(
                base_url=self.ollama_base_url,
                model=self.model,
            )
        return self._embeddings
    
    def _cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(f"{self.model}:{text}".encode()).hexdigest()
    
    def _get_from_cache(self, text: str) -> Optional[list[float]]:
        """Get embedding from cache if available."""
        if not self.cache_enabled:
            return None
        return self._cache.get(self._cache_key(text))
    
    def _add_to_cache(self, text: str, embedding: list[float]) -> None:
        """Add embedding to cache."""
        if not self.cache_enabled:
            return
        
        # Simple LRU-like eviction
        if len(self._cache) >= self.cache_max_size:
            # Remove oldest entry (first key)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        self._cache[self._cache_key(text)] = embedding
    
    async def embed_text(self, text: str) -> EmbeddingResult:
        """
        Embed a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            EmbeddingResult with vector and metadata
        """
        start_time = time.time()
        
        # Check cache
        cached = self._get_from_cache(text)
        if cached:
            return EmbeddingResult(
                text=text,
                embedding=cached,
                model=self.model,
                dimensions=len(cached),
                processing_time_ms=0.0,
            )
        
        # Generate embedding
        embedding = self.embeddings.embed_query(text)
        
        # Update dimensions if not set
        if self._dimensions is None:
            self._dimensions = len(embedding)
        
        # Cache result
        self._add_to_cache(text, embedding)
        
        processing_time = (time.time() - start_time) * 1000
        
        return EmbeddingResult(
            text=text,
            embedding=embedding,
            model=self.model,
            dimensions=len(embedding),
            processing_time_ms=processing_time,
        )
    
    async def embed_batch(
        self,
        texts: list[str],
        show_progress: bool = False,
    ) -> list[EmbeddingResult]:
        """
        Embed multiple texts.
        
        Args:
            texts: List of texts to embed
            show_progress: Print progress updates
            
        Returns:
            List of EmbeddingResult objects
        """
        results = []
        total = len(texts)
        
        for i, text in enumerate(texts):
            result = await self.embed_text(text)
            results.append(result)
            
            if show_progress and (i + 1) % 10 == 0:
                print(f"[embedding] Processed {i + 1}/{total} texts")
        
        return results
    
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Embed documents (wrapper for LangChain compatibility).
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        results = await self.embed_batch(texts)
        return [r.embedding for r in results]
    
    async def embed_query(self, text: str) -> list[float]:
        """
        Embed a query (wrapper for LangChain compatibility).
        
        Args:
            text: Query text
            
        Returns:
            Embedding vector
        """
        result = await self.embed_text(text)
        return result.embedding
    
    def get_dimensions(self) -> int:
        """Get embedding dimensions (generates sample if needed)."""
        if self._dimensions is None:
            # Generate sample embedding to get dimensions
            sample = self.embeddings.embed_query("sample text")
            self._dimensions = len(sample)
        return self._dimensions
    
    def clear_cache(self) -> int:
        """Clear the embedding cache. Returns number of entries cleared."""
        count = len(self._cache)
        self._cache.clear()
        return count
    
    def get_stats(self) -> dict[str, Any]:
        """Get service statistics."""
        return {
            "model": self.model,
            "ollama_url": self.ollama_base_url,
            "dimensions": self._dimensions,
            "cache_enabled": self.cache_enabled,
            "cache_size": len(self._cache),
            "cache_max_size": self.cache_max_size,
        }


# Convenience function
async def embed(text: str, model: str = "nomic-embed-text") -> list[float]:
    """Quick embedding function."""
    service = EmbeddingService(model=model)
    result = await service.embed_text(text)
    return result.embedding


if __name__ == "__main__":
    import asyncio
    
    async def main():
        service = EmbeddingService(
            model="nomic-embed-text",
            ollama_base_url="http://localhost:11434",
        )
        
        # Single embedding
        result = await service.embed_text("Hello, world!")
        print(f"Embedding dimensions: {result.dimensions}")
        print(f"Processing time: {result.processing_time_ms:.2f}ms")
        
        # Batch embedding
        texts = [
            "Python is a programming language",
            "Docker containers are portable",
            "Machine learning is transforming software",
        ]
        results = await service.embed_batch(texts)
        print(f"\nBatch processed {len(results)} texts")
        
        # Stats
        print(f"\nService stats: {service.get_stats()}")
    
    asyncio.run(main())

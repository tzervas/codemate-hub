"""
Vector Search Tool

Semantic search in ChromaDB for RAG pipelines.
Provides similarity search with relevance filtering.
"""

import os
from dataclasses import dataclass
from typing import Any, Optional

from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings


@dataclass
class SearchResult:
    """Represents a search result from vector store."""

    content: str
    metadata: dict
    score: float
    chunk_id: str


class VectorSearchTool:
    """
    Semantic search tool for ChromaDB integration.

    Provides similarity search with configurable parameters
    and relevance threshold filtering.
    """

    name = "vector_search"
    description = "Semantic search in ChromaDB vector store"

    def __init__(
        self,
        collection_name: str = "documents",
        persist_directory: Optional[str] = None,
        ollama_base_url: Optional[str] = None,
        embedding_model: str = "nomic-embed-text",
        top_k: int = 5,
        relevance_threshold: float = 0.7,
    ):
        """
        Initialize vector search tool.

        Args:
            collection_name: ChromaDB collection name
            persist_directory: Path to ChromaDB persistence directory
            ollama_base_url: Ollama API base URL
            embedding_model: Model to use for embeddings
            top_k: Default number of results to return
            relevance_threshold: Minimum relevance score (0-1)
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or os.getenv("CHROMA_DB_DIR", "./chroma_db")
        self.ollama_base_url = ollama_base_url or os.getenv(
            "OLLAMA_BASE_URL", "http://ollama:11434"
        )
        self.embedding_model = embedding_model
        self.top_k = top_k
        self.relevance_threshold = relevance_threshold

        self._vectorstore: Optional[Chroma] = None
        self._embeddings: Optional[OllamaEmbeddings] = None

    @property
    def embeddings(self) -> OllamaEmbeddings:
        """Lazy-load embeddings model."""
        if self._embeddings is None:
            self._embeddings = OllamaEmbeddings(
                base_url=self.ollama_base_url,
                model=self.embedding_model,
            )
        return self._embeddings

    @property
    def vectorstore(self) -> Chroma:
        """Lazy-load vector store."""
        if self._vectorstore is None:
            self._vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory,
            )
        return self._vectorstore

    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[dict] = None,
        relevance_threshold: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        Perform semantic search.

        Args:
            query: Search query text
            top_k: Number of results to return
            filter_metadata: Metadata filter for results
            relevance_threshold: Minimum relevance score

        Returns:
            Dictionary with search results and metadata
        """
        top_k = top_k or self.top_k
        relevance_threshold = relevance_threshold or self.relevance_threshold

        try:
            # Perform similarity search with scores
            results_with_scores = self.vectorstore.similarity_search_with_relevance_scores(
                query=query,
                k=top_k,
                filter=filter_metadata,
            )

            # Filter by relevance threshold and format results
            filtered_results = []
            for doc, score in results_with_scores:
                # ChromaDB returns distance (lower is better), convert to similarity
                # If using cosine distance, similarity = 1 - distance
                similarity = 1 - score if score <= 1 else score

                if similarity >= relevance_threshold:
                    filtered_results.append(
                        SearchResult(
                            content=doc.page_content,
                            metadata=doc.metadata,
                            score=similarity,
                            chunk_id=doc.metadata.get("chunk_id", ""),
                        )
                    )

            return {
                "success": True,
                "query": query,
                "total_results": len(filtered_results),
                "top_k": top_k,
                "relevance_threshold": relevance_threshold,
                "results": [
                    {
                        "content": r.content,
                        "metadata": r.metadata,
                        "score": r.score,
                        "chunk_id": r.chunk_id,
                    }
                    for r in filtered_results
                ],
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "query": query,
            }

    async def add_documents(
        self,
        documents: list[dict],
    ) -> dict[str, Any]:
        """
        Add documents to the vector store.

        Args:
            documents: List of dicts with 'content' and optional 'metadata'

        Returns:
            Dictionary with operation results
        """
        try:
            texts = []
            metadatas = []
            ids = []

            for i, doc in enumerate(documents):
                texts.append(doc.get("content", ""))
                metadata = doc.get("metadata", {})
                metadatas.append(metadata)

                # Generate ID if not provided
                doc_id = doc.get("id") or metadata.get("chunk_id") or f"doc_{i}"
                ids.append(doc_id)

            self.vectorstore.add_texts(
                texts=texts,
                metadatas=metadatas,
                ids=ids,
            )

            return {
                "success": True,
                "documents_added": len(texts),
                "ids": ids,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    async def delete_documents(
        self,
        ids: Optional[list[str]] = None,
        filter_metadata: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Delete documents from the vector store.

        Args:
            ids: List of document IDs to delete
            filter_metadata: Metadata filter for deletion

        Returns:
            Dictionary with operation results
        """
        try:
            if ids:
                self.vectorstore._collection.delete(ids=ids)
                return {
                    "success": True,
                    "deleted_ids": ids,
                }
            elif filter_metadata:
                self.vectorstore._collection.delete(where=filter_metadata)
                return {
                    "success": True,
                    "deleted_filter": filter_metadata,
                }
            else:
                return {
                    "success": False,
                    "error": "Must provide either ids or filter_metadata",
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    async def get_collection_info(self) -> dict[str, Any]:
        """
        Get information about the collection.

        Returns:
            Dictionary with collection statistics
        """
        try:
            collection = self.vectorstore._collection
            count = collection.count()

            return {
                "success": True,
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory,
                "embedding_model": self.embedding_model,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }


# Convenience function for quick searches
async def quick_search(
    query: str,
    top_k: int = 5,
    collection_name: str = "documents",
) -> list[dict]:
    """
    Convenience function for quick semantic search.

    Args:
        query: Search query
        top_k: Number of results
        collection_name: Collection to search

    Returns:
        List of search results
    """
    tool = VectorSearchTool(collection_name=collection_name, top_k=top_k)
    result = await tool.search(query)

    if result.get("success"):
        return result.get("results", [])
    else:
        raise RuntimeError(result.get("error", "Search failed"))


if __name__ == "__main__":
    import asyncio

    async def main():
        tool = VectorSearchTool(
            collection_name="documents",
            persist_directory="./chroma_db",
            ollama_base_url="http://localhost:11434",
        )

        # Get collection info
        info = await tool.get_collection_info()
        print(f"Collection info: {info}")

        # Example search (requires populated database)
        result = await tool.search("python best practices", top_k=3)
        print(f"Search results: {result}")

    asyncio.run(main())

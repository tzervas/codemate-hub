"""
RAG Pipeline Service

Complete RAG (Retrieval-Augmented Generation) pipeline for document-based Q&A.
Integrates document processing, vector storage, and LLM response generation.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama

from src.tools.document_processor import DocumentProcessor
from src.tools.vector_search import VectorSearchTool


@dataclass
class RAGConfig:
    """Configuration for RAG pipeline."""

    # Ollama settings
    ollama_base_url: str = "http://ollama:11434"
    llm_model: str = "qwen2.5-coder:7b-q4_0"
    embedding_model: str = "nomic-embed-text"

    # ChromaDB settings
    collection_name: str = "documents"
    persist_directory: str = "./chroma_db"

    # Retrieval settings
    top_k: int = 5
    relevance_threshold: float = 0.7

    # LLM settings
    temperature: float = 0.2
    max_tokens: int = 2048

    # Chunking settings
    chunk_size: int = 1000
    chunk_overlap: int = 200


class RAGPipeline:
    """
    Complete RAG pipeline for document-based question answering.

    Provides:
    - Document ingestion with chunking
    - Vector storage in ChromaDB
    - Semantic retrieval
    - LLM-powered response generation
    """

    DEFAULT_PROMPT = """You are a helpful assistant. Use the following context to answer the question.
If the answer is not in the context, say "I don't have enough information to answer that question."

Context:
{context}

Question: {question}

Answer:"""

    def __init__(self, config: Optional[RAGConfig] = None):
        """
        Initialize RAG pipeline.

        Args:
            config: Optional configuration, uses defaults if not provided
        """
        self.config = config or RAGConfig(
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
            persist_directory=os.getenv("CHROMA_DB_DIR", "./chroma_db"),
        )

        self._embeddings: Optional[OllamaEmbeddings] = None
        self._vectorstore: Optional[Chroma] = None
        self._llm: Optional[Ollama] = None
        self._qa_chain: Optional[RetrievalQA] = None

        # Initialize document processor
        self.doc_processor = DocumentProcessor(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )

    @property
    def embeddings(self) -> OllamaEmbeddings:
        """Lazy-load embeddings model."""
        if self._embeddings is None:
            self._embeddings = OllamaEmbeddings(
                base_url=self.config.ollama_base_url,
                model=self.config.embedding_model,
            )
        return self._embeddings

    @property
    def vectorstore(self) -> Chroma:
        """Lazy-load vector store."""
        if self._vectorstore is None:
            self._vectorstore = Chroma(
                collection_name=self.config.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.config.persist_directory,
            )
        return self._vectorstore

    @property
    def llm(self) -> Ollama:
        """Lazy-load LLM."""
        if self._llm is None:
            self._llm = Ollama(
                base_url=self.config.ollama_base_url,
                model=self.config.llm_model,
                temperature=self.config.temperature,
                num_predict=self.config.max_tokens,
            )
        return self._llm

    @property
    def qa_chain(self) -> RetrievalQA:
        """Lazy-load QA chain."""
        if self._qa_chain is None:
            prompt = PromptTemplate(
                template=self.DEFAULT_PROMPT,
                input_variables=["context", "question"],
            )

            self._qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(search_kwargs={"k": self.config.top_k}),
                chain_type_kwargs={"prompt": prompt},
                return_source_documents=True,
            )
        return self._qa_chain

    async def ingest_file(self, file_path: str | Path) -> dict[str, Any]:
        """
        Ingest a document file into the vector store.

        Args:
            file_path: Path to the document

        Returns:
            Dictionary with ingestion results
        """
        try:
            # Process document
            result = self.doc_processor.process_file(file_path)

            # Add chunks to vector store
            texts = [chunk.content for chunk in result.chunks]
            metadatas = [chunk.metadata for chunk in result.chunks]
            ids = [chunk.chunk_id for chunk in result.chunks]

            self.vectorstore.add_texts(
                texts=texts,
                metadatas=metadatas,
                ids=ids,
            )

            return {
                "success": True,
                "source": result.source,
                "chunks_added": len(result.chunks),
                "total_chars": len(result.content),
                "processing_time_ms": result.processing_time_ms,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    async def ingest_directory(
        self,
        directory: str | Path,
        recursive: bool = True,
        extensions: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Ingest all documents from a directory.

        Args:
            directory: Path to directory
            recursive: Whether to process subdirectories
            extensions: File extensions to process (default: all supported)

        Returns:
            Dictionary with batch ingestion results
        """
        directory = Path(directory)
        extensions = extensions or list(self.doc_processor.SUPPORTED_FORMATS.keys())

        results = []
        total_chunks = 0

        # Build file list
        pattern = "**/*" if recursive else "*"
        files = []
        for ext in extensions:
            files.extend(directory.glob(f"{pattern}{ext}"))

        for file_path in files:
            result = await self.ingest_file(file_path)
            results.append(
                {
                    "file": str(file_path),
                    "success": result.get("success", False),
                    "chunks": result.get("chunks_added", 0),
                }
            )
            if result.get("success"):
                total_chunks += result.get("chunks_added", 0)

        successful = sum(1 for r in results if r["success"])

        return {
            "success": True,
            "files_processed": len(results),
            "files_successful": successful,
            "files_failed": len(results) - successful,
            "total_chunks": total_chunks,
            "details": results,
        }

    async def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        include_sources: bool = True,
    ) -> dict[str, Any]:
        """
        Query the RAG pipeline.

        Args:
            question: Question to answer
            top_k: Number of documents to retrieve
            include_sources: Whether to include source documents

        Returns:
            Dictionary with answer and sources
        """
        try:
            # Override top_k if specified
            if top_k and top_k != self.config.top_k:
                self._qa_chain = None  # Force rebuild
                self.config.top_k = top_k

            # Run QA chain
            result = self.qa_chain.invoke({"query": question})

            response = {
                "success": True,
                "question": question,
                "answer": result.get("result", ""),
            }

            if include_sources:
                sources = []
                for doc in result.get("source_documents", []):
                    sources.append(
                        {
                            "content": (
                                doc.page_content[:500] + "..."
                                if len(doc.page_content) > 500
                                else doc.page_content
                            ),
                            "metadata": doc.metadata,
                        }
                    )
                response["sources"] = sources

            return response

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "question": question,
            }

    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Perform semantic search without LLM generation.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            Dictionary with search results
        """
        tool = VectorSearchTool(
            collection_name=self.config.collection_name,
            persist_directory=self.config.persist_directory,
            ollama_base_url=self.config.ollama_base_url,
            embedding_model=self.config.embedding_model,
            top_k=top_k or self.config.top_k,
            relevance_threshold=self.config.relevance_threshold,
        )

        return await tool.search(query)

    def get_collection_stats(self) -> dict[str, Any]:
        """Get statistics about the document collection."""
        try:
            collection = self.vectorstore._collection
            count = collection.count()

            return {
                "success": True,
                "collection_name": self.config.collection_name,
                "document_count": count,
                "embedding_model": self.config.embedding_model,
                "llm_model": self.config.llm_model,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


# Convenience functions


async def quick_ingest(file_path: str, config: Optional[RAGConfig] = None) -> dict:
    """Quick document ingestion."""
    pipeline = RAGPipeline(config)
    return await pipeline.ingest_file(file_path)


async def quick_query(question: str, config: Optional[RAGConfig] = None) -> str:
    """Quick RAG query returning just the answer."""
    pipeline = RAGPipeline(config)
    result = await pipeline.query(question)
    if result.get("success"):
        return result.get("answer", "")
    raise RuntimeError(result.get("error", "Query failed"))


if __name__ == "__main__":
    import asyncio

    async def main():
        # Initialize pipeline
        config = RAGConfig(
            ollama_base_url="http://localhost:11434",
            persist_directory="./chroma_db",
        )
        pipeline = RAGPipeline(config)

        # Get collection stats
        stats = pipeline.get_collection_stats()
        print(f"Collection stats: {stats}")

        # Example query
        if stats.get("document_count", 0) > 0:
            result = await pipeline.query("What are the best practices for Python development?")
            print(f"Answer: {result.get('answer', 'No answer')}")

    asyncio.run(main())

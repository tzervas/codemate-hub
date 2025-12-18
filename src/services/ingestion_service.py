"""
Document Ingestion Service

Orchestrates document ingestion workflows with multiple processing stages:
1. Document detection and validation
2. Content extraction
3. Chunking and metadata enrichment
4. Embedding generation
5. Vector storage
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from langchain_chroma import Chroma

from src.services.embedding_service import EmbeddingService
from src.tools.document_processor import DocumentProcessor


@dataclass
class IngestionJob:
    """Represents a document ingestion job."""
    job_id: str
    source: str
    status: str = "pending"  # pending, processing, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    chunks_created: int = 0
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class IngestionConfig:
    """Configuration for document ingestion."""
    # Storage
    chroma_persist_dir: str = "./chroma_db"
    collection_name: str = "documents"
    
    # Processing
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Embeddings
    embedding_model: str = "nomic-embed-text"
    ollama_base_url: str = "http://ollama:11434"
    
    # Behavior
    skip_duplicates: bool = True
    batch_size: int = 50
    
    # Supported formats
    supported_extensions: list = field(default_factory=lambda: [
        ".pdf", ".docx", ".txt", ".md", ".html", ".htm", ".csv", ".json"
    ])


class DocumentIngestionService:
    """
    Document ingestion service for RAG pipelines.
    
    Provides:
    - File and directory ingestion
    - Duplicate detection
    - Batch processing
    - Progress tracking
    """
    
    def __init__(self, config: Optional[IngestionConfig] = None):
        """
        Initialize ingestion service.
        
        Args:
            config: Optional configuration
        """
        self.config = config or IngestionConfig(
            chroma_persist_dir=os.getenv("CHROMA_DB_DIR", "./chroma_db"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
        )
        
        self._jobs: dict[str, IngestionJob] = {}
        self._processor: Optional[DocumentProcessor] = None
        self._embedding_service: Optional[EmbeddingService] = None
        self._vectorstore: Optional[Chroma] = None
    
    @property
    def processor(self) -> DocumentProcessor:
        """Lazy-load document processor."""
        if self._processor is None:
            self._processor = DocumentProcessor(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
            )
        return self._processor
    
    @property
    def embedding_service(self) -> EmbeddingService:
        """Lazy-load embedding service."""
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService(
                model=self.config.embedding_model,
                ollama_base_url=self.config.ollama_base_url,
            )
        return self._embedding_service
    
    @property
    def vectorstore(self) -> Chroma:
        """Lazy-load vector store."""
        if self._vectorstore is None:
            from langchain_community.embeddings import OllamaEmbeddings
            
            embeddings = OllamaEmbeddings(
                base_url=self.config.ollama_base_url,
                model=self.config.embedding_model,
            )
            
            self._vectorstore = Chroma(
                collection_name=self.config.collection_name,
                embedding_function=embeddings,
                persist_directory=self.config.chroma_persist_dir,
            )
        return self._vectorstore
    
    def _generate_job_id(self) -> str:
        """Generate unique job ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _check_duplicate(self, source_path: str) -> bool:
        """Check if document already exists in collection."""
        if not self.config.skip_duplicates:
            return False
        
        try:
            results = self.vectorstore._collection.get(
                where={"source_path": str(source_path)},
                limit=1,
            )
            return len(results.get("ids", [])) > 0
        except Exception:
            return False
    
    async def ingest_file(
        self,
        file_path: str | Path,
        metadata: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Ingest a single file.
        
        Args:
            file_path: Path to file
            metadata: Additional metadata to attach
            
        Returns:
            Dictionary with ingestion results
        """
        path = Path(file_path)
        job_id = self._generate_job_id()
        
        job = IngestionJob(
            job_id=job_id,
            source=str(path),
            started_at=datetime.now(),
        )
        self._jobs[job_id] = job
        
        try:
            # Validate file
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            
            if path.suffix.lower() not in self.config.supported_extensions:
                raise ValueError(f"Unsupported format: {path.suffix}")
            
            # Check for duplicates
            if self._check_duplicate(str(path.absolute())):
                job.status = "skipped"
                job.metadata["reason"] = "duplicate"
                return {
                    "success": True,
                    "job_id": job_id,
                    "status": "skipped",
                    "reason": "Document already exists in collection",
                }
            
            job.status = "processing"
            
            # Process document
            doc_result = self.processor.process_file(path)
            
            # Prepare for storage
            texts = []
            metadatas = []
            ids = []
            
            base_metadata = metadata or {}
            base_metadata["source_path"] = str(path.absolute())
            base_metadata["ingested_at"] = datetime.now().isoformat()
            
            for chunk in doc_result.chunks:
                texts.append(chunk.content)
                
                chunk_meta = {**base_metadata, **chunk.metadata}
                metadatas.append(chunk_meta)
                ids.append(chunk.chunk_id)
            
            # Add to vector store
            self.vectorstore.add_texts(
                texts=texts,
                metadatas=metadatas,
                ids=ids,
            )
            
            job.status = "completed"
            job.chunks_created = len(texts)
            job.completed_at = datetime.now()
            
            return {
                "success": True,
                "job_id": job_id,
                "status": "completed",
                "source": str(path),
                "chunks_created": len(texts),
                "processing_time_ms": doc_result.processing_time_ms,
            }
            
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.now()
            
            return {
                "success": False,
                "job_id": job_id,
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
            }
    
    async def ingest_directory(
        self,
        directory: str | Path,
        recursive: bool = True,
        extensions: Optional[list[str]] = None,
        metadata: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Ingest all documents from a directory.
        
        Args:
            directory: Path to directory
            recursive: Include subdirectories
            extensions: File extensions to process
            metadata: Metadata to attach to all documents
            
        Returns:
            Dictionary with batch results
        """
        directory = Path(directory)
        extensions = extensions or self.config.supported_extensions
        
        if not directory.exists():
            return {
                "success": False,
                "error": f"Directory not found: {directory}",
            }
        
        # Collect files
        files = []
        pattern = "**/*" if recursive else "*"
        for ext in extensions:
            files.extend(directory.glob(f"{pattern}{ext}"))
        
        # Process files
        results = []
        total_chunks = 0
        successful = 0
        skipped = 0
        failed = 0
        
        for file_path in files:
            result = await self.ingest_file(file_path, metadata)
            results.append({
                "file": str(file_path.relative_to(directory)),
                "status": result.get("status"),
                "chunks": result.get("chunks_created", 0),
            })
            
            if result.get("status") == "completed":
                successful += 1
                total_chunks += result.get("chunks_created", 0)
            elif result.get("status") == "skipped":
                skipped += 1
            else:
                failed += 1
        
        return {
            "success": True,
            "directory": str(directory),
            "files_found": len(files),
            "files_successful": successful,
            "files_skipped": skipped,
            "files_failed": failed,
            "total_chunks": total_chunks,
            "details": results,
        }
    
    async def ingest_text(
        self,
        text: str,
        source: str = "direct_input",
        metadata: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Ingest raw text content.
        
        Args:
            text: Text content
            source: Source identifier
            metadata: Additional metadata
            
        Returns:
            Dictionary with ingestion results
        """
        job_id = self._generate_job_id()
        
        try:
            # Process text
            doc_result = self.processor.process_text(text, source, metadata)
            
            # Prepare for storage
            texts = [chunk.content for chunk in doc_result.chunks]
            metadatas = [chunk.metadata for chunk in doc_result.chunks]
            ids = [chunk.chunk_id for chunk in doc_result.chunks]
            
            # Add timestamp
            for meta in metadatas:
                meta["ingested_at"] = datetime.now().isoformat()
            
            # Add to vector store
            self.vectorstore.add_texts(
                texts=texts,
                metadatas=metadatas,
                ids=ids,
            )
            
            return {
                "success": True,
                "job_id": job_id,
                "source": source,
                "chunks_created": len(texts),
                "processing_time_ms": doc_result.processing_time_ms,
            }
            
        except Exception as e:
            return {
                "success": False,
                "job_id": job_id,
                "error": str(e),
                "error_type": type(e).__name__,
            }
    
    def get_job_status(self, job_id: str) -> Optional[dict]:
        """Get status of an ingestion job."""
        job = self._jobs.get(job_id)
        if not job:
            return None
        
        return {
            "job_id": job.job_id,
            "source": job.source,
            "status": job.status,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "chunks_created": job.chunks_created,
            "error": job.error,
        }
    
    def get_collection_stats(self) -> dict[str, Any]:
        """Get collection statistics."""
        try:
            collection = self.vectorstore._collection
            count = collection.count()
            
            return {
                "success": True,
                "collection_name": self.config.collection_name,
                "document_count": count,
                "persist_directory": self.config.chroma_persist_dir,
                "embedding_model": self.config.embedding_model,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


if __name__ == "__main__":
    import asyncio
    
    async def main():
        service = DocumentIngestionService()
        
        # Get stats
        stats = service.get_collection_stats()
        print(f"Collection stats: {stats}")
        
        # Example: Ingest a directory
        # result = await service.ingest_directory("./docs")
        # print(f"Ingestion result: {result}")
    
    asyncio.run(main())

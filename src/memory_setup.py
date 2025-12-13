"""
ChromaDB Memory Initialization

Initializes a persistent vector database for embedding storage
and retrieval in the coding assistant pipeline.

Environment Variables:
  CHROMA_DB_DIR: Path to persistent Chroma database (default: ./chroma_db)
  OLLAMA_BASE_URL: Ollama API endpoint for embeddings (default: http://localhost:11434)
"""

import os
import sys
from pathlib import Path
from typing import Optional

from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings


def initialize_memory(
    db_path: Optional[str] = None,
    ollama_base_url: Optional[str] = None,
    verbose: bool = True,
) -> Chroma:
    """
    Initialize and return a Chroma vector database instance.
    
    Args:
        db_path: Path to persistent database directory
        ollama_base_url: Ollama API base URL for embeddings
        verbose: Enable detailed initialization logging
        
    Returns:
        Initialized Chroma database instance
        
    Raises:
        RuntimeError: If database initialization fails
    """
    # Load from environment with sensible defaults
    # Note: In Docker, use http://ollama:11434; locally use http://localhost:11434
    db_path = db_path or os.getenv("CHROMA_DB_DIR", "./chroma_db")
    ollama_base_url = ollama_base_url or os.getenv(
        "OLLAMA_BASE_URL", "http://ollama:11434"
    )
    
    if verbose:
        print(f"[memory] Initializing Chroma database at: {db_path}")
        print(f"[memory] Using Ollama embeddings from: {ollama_base_url}")
    
    try:
        # Create database directory if it doesn't exist
        db_dir = Path(db_path)
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings from Ollama
        embeddings = OllamaEmbeddings(
            base_url=ollama_base_url,
            model="qwen2.5-coder:7b-q4_0",  # Must match default pulled model
        )
        
        # Initialize Chroma with persistent storage
        # collection_name defaults to 'documents' for general purpose
        vector_db = Chroma(
            embedding_function=embeddings,
            persist_directory=str(db_path),
            collection_name="documents",
        )
        
        if verbose:
            print(f"[memory] ✓ Chroma database initialized successfully")
            # Try to get collection count
            try:
                collection = vector_db.get_collection()
                count = collection.count()
                print(f"[memory] Collection has {count} documents")
            except Exception as e:
                print(f"[memory] Could not query collection count: {e}")
        
        return vector_db
        
    except Exception as e:
        error_msg = f"Failed to initialize Chroma database: {e}"
        print(f"[memory] ✗ {error_msg}", file=sys.stderr)
        raise RuntimeError(error_msg) from e


def load_preseeds(
    vector_db: Chroma,
    preseeds_dir: str = "./insights/domain-preseeds",
    verbose: bool = True,
) -> int:
    """
    Load preseed documents from a directory into the vector database.
    
    Args:
        vector_db: Initialized Chroma database instance
        preseeds_dir: Directory containing preseed documents
        verbose: Enable detailed logging
        
    Returns:
        Number of documents loaded
    """
    preseeds_path = Path(preseeds_dir)
    
    if not preseeds_path.exists():
        if verbose:
            print(f"[memory] Preseeds directory not found: {preseeds_dir} (skipping)")
        return 0
    
    # Look for markdown files to load as documents
    preseed_files = list(preseeds_path.glob("*.md"))
    
    if not preseed_files and verbose:
        print(f"[memory] No preseed files found in: {preseeds_dir}")
        return 0
    
    loaded_count = 0
    for filepath in preseed_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Add to vector database with metadata
            metadata = {
                "source": filepath.name,
                "type": "preseed",
            }
            
            vector_db.add_texts(
                texts=[content],
                metadatas=[metadata],
                ids=[filepath.stem],  # Use filename stem as unique ID
            )
            
            loaded_count += 1
            if verbose:
                print(f"[memory] Loaded preseed: {filepath.name}")
                
        except Exception as e:
            print(
                f"[memory] Warning: Failed to load preseed {filepath.name}: {e}",
                file=sys.stderr,
            )
    
    if verbose and loaded_count > 0:
        print(f"[memory] ✓ Loaded {loaded_count} preseed documents")
    
    return loaded_count


if __name__ == "__main__":
    """
    Standalone initialization for testing or manual setup.
    Usage: python src/memory_setup.py
    """
    try:
        # Initialize memory with defaults
        db = initialize_memory(verbose=True)
        
        # Load preseeds if available
        loaded = load_preseeds(db, verbose=True)
        
        print(f"\n[memory] ✓ Memory system initialized successfully")
        print(f"[memory] - Database: persistent storage enabled")
        print(f"[memory] - Preseeds: {loaded} documents loaded")
        
    except Exception as e:
        print(f"\n[memory] ✗ Initialization failed: {e}", file=sys.stderr)
        sys.exit(1)

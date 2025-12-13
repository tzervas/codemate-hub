"""
Pipeline Orchestration for Coding Assistant

This module provides the core pipeline orchestration for the coding assistant,
including fixture-based testing support for CI/CD validation without live Ollama inference.

The pipeline operates in two modes:
1. Fixture mode (testing): Uses pre-recorded JSON responses for deterministic tests
2. Live mode (production): Makes real API calls to Ollama

Environment Variables (for future live mode):
  OLLAMA_BASE_URL: Ollama API endpoint (default: http://ollama:11434)
  CHROMA_DB_DIR: Path to persistent Chroma database (default: ./chroma_db)
"""

import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Protocol

from pydantic import BaseModel, Field, ValidationError


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# Exception classes
class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass


class HTTPError(PipelineError):
    """Raised when HTTP request fails."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


class SchemaValidationError(PipelineError):
    """Raised when response schema validation fails."""
    pass


# Response models
class OllamaResponse(BaseModel):
    """Pydantic model for Ollama API response."""
    model: str
    response: str
    done: bool
    context: Optional[list] = Field(default=None)
    total_duration: Optional[int] = Field(default=None)
    load_duration: Optional[int] = Field(default=None)
    prompt_eval_count: Optional[int] = Field(default=None)
    prompt_eval_duration: Optional[int] = Field(default=None)
    eval_count: Optional[int] = Field(default=None)
    eval_duration: Optional[int] = Field(default=None)


class EmbeddingResponse(BaseModel):
    """Pydantic model for embedding response."""
    embedding: list[float]


@dataclass
class PipelineResult:
    """Structured result from pipeline execution."""
    success: bool
    response: Optional[str] = None
    model: Optional[str] = None
    error: Optional[str] = None
    embeddings_stored: bool = False
    duration_ms: Optional[float] = None


# Client abstraction for testability
class OllamaClient(Protocol):
    """Protocol for Ollama client interface."""
    
    def generate(self, prompt: str, model: str) -> Dict[str, Any]:
        """Generate response from model."""
        ...
    
    def embed(self, text: str, model: str) -> Dict[str, Any]:
        """Generate embeddings for text."""
        ...


class FixtureClient:
    """
    Fixture-based client for testing without live Ollama.
    
    Loads pre-recorded JSON responses from fixture files.
    """
    
    def __init__(self, fixtures_dir: Path):
        self.fixtures_dir = fixtures_dir
    
    def generate(self, prompt: str, model: str) -> Dict[str, Any]:
        """Load generate fixture."""
        fixture_file = self.fixtures_dir / "ollama_success.json"
        if not fixture_file.exists():
            raise HTTPError(503, "Fixture not found")
        
        with open(fixture_file) as f:
            return json.load(f)
    
    def embed(self, text: str, model: str) -> Dict[str, Any]:
        """Load embedding fixture."""
        fixture_file = self.fixtures_dir / "embedding_success.json"
        if not fixture_file.exists():
            raise HTTPError(503, "Fixture not found")
        
        with open(fixture_file) as f:
            return json.load(f)


class HTTPErrorFixtureClient(FixtureClient):
    """Fixture client that simulates HTTP errors."""
    
    def generate(self, prompt: str, model: str) -> Dict[str, Any]:
        """Simulate HTTP error."""
        fixture_file = self.fixtures_dir / "ollama_http_error.json"
        with open(fixture_file) as f:
            data = json.load(f)
        raise HTTPError(data.get("status_code", 503), data.get("error", "Unknown error"))
    
    def embed(self, text: str, model: str) -> Dict[str, Any]:
        """Simulate HTTP error."""
        raise HTTPError(503, "Service unavailable")


class MalformedFixtureClient(FixtureClient):
    """Fixture client that returns malformed responses."""
    
    def generate(self, prompt: str, model: str) -> Dict[str, Any]:
        """Return malformed response."""
        fixture_file = self.fixtures_dir / "ollama_malformed.json"
        with open(fixture_file) as f:
            return json.load(f)


def run_pipeline(
    prompt: str,
    model: str = "qwen2.5-coder:7b-q4_0",
    client: Optional[OllamaClient] = None,
    persist_embeddings: bool = False,
) -> PipelineResult:
    """
    Run the coding assistant pipeline.
    
    Args:
        prompt: Input prompt for code generation
        model: Model name to use
        client: Optional client for dependency injection (defaults to fixture client)
        persist_embeddings: Whether to persist embeddings to Chroma
        
    Returns:
        PipelineResult capturing success or failure details
    """
    import time
    start_time = time.time()
    
    # Default to fixture client for testing
    if client is None:
        fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures"
        client = FixtureClient(fixtures_dir)
        logger.info("Using fixture client (testing mode)")
    
    logger.info(f"Starting pipeline with model: {model}")
    logger.info(f"Prompt: {prompt[:100]}..." if len(prompt) > 100 else f"Prompt: {prompt}")
    
    try:
        # Step 1: Generate response from Ollama
        logger.info("Requesting generation from Ollama...")
        raw_response = client.generate(prompt, model)
        
        # Step 2: Validate response schema
        logger.info("Validating response schema...")
        try:
            validated_response = OllamaResponse(**raw_response)
        except ValidationError as e:
            logger.error(f"Schema validation failed: {e}")
            raise SchemaValidationError(f"Invalid response schema: {e}") from e
        
        logger.info(f"✓ Generated response ({len(validated_response.response)} chars)")
        
        # Step 3: Optionally persist embeddings
        embeddings_stored = False
        if persist_embeddings:
            try:
                logger.info("Generating embeddings...")
                embedding_data = client.embed(validated_response.response, model)
                embedding_response = EmbeddingResponse(**embedding_data)
                
                # In fixture mode, we simulate persistence without real Chroma writes
                # In production mode, this would call memory_setup.initialize_memory()
                logger.info(f"✓ Generated embeddings ({len(embedding_response.embedding)} dims)")
                embeddings_stored = True
                
            except HTTPError as e:
                logger.warning(f"Failed to persist embeddings: {e}")
                # Don't fail the pipeline if embeddings fail
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        result = PipelineResult(
            success=True,
            response=validated_response.response,
            model=validated_response.model,
            embeddings_stored=embeddings_stored,
            duration_ms=duration_ms,
        )
        
        logger.info(f"✓ Pipeline completed successfully in {duration_ms:.2f}ms")
        return result
        
    except HTTPError as e:
        # HTTP errors are logged and re-raised
        logger.error(f"HTTP error: {e}")
        duration_ms = (time.time() - start_time) * 1000
        return PipelineResult(
            success=False,
            error=str(e),
            duration_ms=duration_ms,
        )
        
    except SchemaValidationError as e:
        # Schema validation errors are logged and re-raised
        logger.error(f"Schema validation error: {e}")
        duration_ms = (time.time() - start_time) * 1000
        return PipelineResult(
            success=False,
            error=str(e),
            duration_ms=duration_ms,
        )
        
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected pipeline error: {e}", exc_info=True)
        duration_ms = (time.time() - start_time) * 1000
        return PipelineResult(
            success=False,
            error=f"Unexpected error: {e}",
            duration_ms=duration_ms,
        )


if __name__ == "__main__":
    """
    Standalone execution for testing.
    Usage: python src/pipeline.py
    """
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    print("=" * 60)
    print("Pipeline Test Run (Fixture Mode)")
    print("=" * 60)
    
    # Test prompt
    test_prompt = "Write a Python function to calculate fibonacci numbers"
    
    # Run pipeline in fixture mode
    result = run_pipeline(test_prompt, persist_embeddings=True)
    
    print(f"\nResult:")
    print(f"  Success: {result.success}")
    print(f"  Model: {result.model}")
    print(f"  Duration: {result.duration_ms:.2f}ms")
    print(f"  Embeddings stored: {result.embeddings_stored}")
    
    if result.response:
        print(f"\nGenerated code:")
        print("-" * 60)
        print(result.response)
        print("-" * 60)
    
    if result.error:
        print(f"\nError: {result.error}")
        sys.exit(1)
    
    print("\n✓ Pipeline test completed successfully")

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

import hashlib
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Protocol

from pydantic import BaseModel, Field, ValidationError

from src.constants import (
    DEFAULT_MODEL,
    HTTP_SERVICE_UNAVAILABLE,
    MS_PER_SECOND,
    PROMPT_PREVIEW_LENGTH,
)
from services.review_orchestrator.security.prompt_sanitizer import PromptSanitizer


# Module logger - configuration should be done by the application, not the library
logger = logging.getLogger(__name__)

# Module-level sanitizer singleton for efficient pattern reuse
_sanitizer = PromptSanitizer()


def _configure_logging() -> None:
    """Configure logging for standalone execution.

    This should only be called from the CLI/entrypoint, not when imported as a library.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# Exception classes
class PipelineError(Exception):
    """Base exception for pipeline errors."""


class HTTPError(PipelineError):
    """Raised when HTTP request fails."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


class SchemaValidationError(PipelineError):
    """Raised when response schema validation fails."""


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
            raise HTTPError(HTTP_SERVICE_UNAVAILABLE, "Fixture not found")

        with open(fixture_file) as f:
            return json.load(f)

    def embed(self, text: str, model: str) -> Dict[str, Any]:
        """Load embedding fixture."""
        fixture_file = self.fixtures_dir / "embedding_success.json"
        if not fixture_file.exists():
            raise HTTPError(HTTP_SERVICE_UNAVAILABLE, "Fixture not found")

        with open(fixture_file) as f:
            return json.load(f)


class HTTPErrorFixtureClient(FixtureClient):
    """Fixture client that simulates HTTP errors."""

    def generate(self, prompt: str, model: str) -> Dict[str, Any]:
        """Simulate HTTP error."""
        fixture_file = self.fixtures_dir / "ollama_http_error.json"
        with open(fixture_file) as f:
            data = json.load(f)
        status_code = data.get("status_code", HTTP_SERVICE_UNAVAILABLE)
        error_message = data.get("error", "Unknown error")
        raise HTTPError(status_code, error_message)

    def embed(self, text: str, model: str) -> Dict[str, Any]:
        """Simulate HTTP error."""
        raise HTTPError(HTTP_SERVICE_UNAVAILABLE, "Service unavailable")


class MalformedFixtureClient(FixtureClient):
    """Fixture client that returns malformed responses."""

    def generate(self, prompt: str, model: str) -> Dict[str, Any]:
        """Return malformed response."""
        fixture_file = self.fixtures_dir / "ollama_malformed.json"
        with open(fixture_file) as f:
            return json.load(f)


def _calculate_duration_ms(start_time: float) -> float:
    """Calculate duration in milliseconds from start time."""
    return (time.time() - start_time) * MS_PER_SECOND


def run_pipeline(
    prompt: str,
    model: str = DEFAULT_MODEL,
    client: Optional[OllamaClient] = None,
    persist_embeddings: bool = False,
    fixtures_dir: Optional[Path] = None,
) -> PipelineResult:
    """
    Run the coding assistant pipeline.

    Args:
        prompt: Input prompt for code generation
        model: Model name to use
        client: Optional client for dependency injection (defaults to fixture client)
        persist_embeddings: Whether to persist embeddings to Chroma
        fixtures_dir: Directory containing test fixtures (for fixture client fallback)

    Returns:
        PipelineResult with success status and details

    Raises:
        PipelineError: For any pipeline execution failures
    """
    start_time = time.time()

    # Step 0: Sanitize user input to prevent prompt injection attacks
    # Use module-level singleton for efficient pattern reuse
    try:
        original_prompt = prompt
        prompt = _sanitizer.sanitize(prompt)
        # Only log if sanitization actually changed the prompt
        if prompt != original_prompt:
            logger.warning("Dangerous patterns detected and removed from input")
        else:
            logger.debug("Input sanitization completed (no changes)")
    except ValueError as e:
        logger.error(f"Input validation failed: {e}")
        duration_ms = _calculate_duration_ms(start_time)
        return PipelineResult(
            success=False,
            error=f"Input validation error: {e}",
            duration_ms=duration_ms,
        )

    # Default to fixture client for testing
    if client is None:
        if fixtures_dir is None:
            fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures"
        client = FixtureClient(fixtures_dir)
        logger.info("Using fixture client (testing mode)")

    logger.info(f"Starting pipeline with model: {model}")

    # Log only prompt metadata at info level to avoid leaking sensitive content
    prompt_length = len(prompt)
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
    logger.info(f"Prompt metadata - length: {prompt_length}, sha256: {prompt_hash}...")

    # Optionally log a short preview of the prompt only when explicitly enabled
    log_prompt_content = os.getenv("LOG_PROMPT_CONTENT", "").lower() in ("1", "true", "yes")
    if log_prompt_content or logger.isEnabledFor(logging.DEBUG):
        preview_len = min(PROMPT_PREVIEW_LENGTH, prompt_length)
        prompt_preview = (
            f"{prompt[:preview_len]}..." if prompt_length > preview_len else prompt
        )
        logger.debug(f"Prompt preview: {prompt_preview}")

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

            except Exception as e:
                logger.warning(f"Failed to persist embeddings: {e}")
                # Don't fail the pipeline if embeddings fail

        # Calculate duration
        duration_ms = _calculate_duration_ms(start_time)

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
        duration_ms = _calculate_duration_ms(start_time)
        return PipelineResult(
            success=False,
            error=str(e),
            duration_ms=duration_ms,
        )

    except SchemaValidationError as e:
        # Schema validation errors are logged and re-raised
        logger.error(f"Schema validation error: {e}")
        duration_ms = _calculate_duration_ms(start_time)
        return PipelineResult(
            success=False,
            error=str(e),
            duration_ms=duration_ms,
        )

    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected pipeline error: {e}", exc_info=True)
        duration_ms = _calculate_duration_ms(start_time)
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
    # Configure logging only for CLI execution
    _configure_logging()

    print("=" * 60)
    print("Pipeline Test Run (Fixture Mode)")
    print("=" * 60)

    # Test prompt
    test_prompt = "Write a Python function to calculate fibonacci numbers"

    # Run pipeline in fixture mode
    result = run_pipeline(test_prompt, persist_embeddings=True)

    print("\nResult:")
    print(f"  Success: {result.success}")
    print(f"  Model: {result.model}")
    print(f"  Duration: {result.duration_ms:.2f}ms")
    print(f"  Embeddings stored: {result.embeddings_stored}")

    if result.response:
        print("\nGenerated code:")
        print("-" * 60)
        print(result.response)
        print("-" * 60)

    if result.error:
        print(f"\nError: {result.error}")
        sys.exit(1)

    print("\n✓ Pipeline test completed successfully")

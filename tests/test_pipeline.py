"""
Test suite for pipeline orchestration.

Tests the pipeline in fixture mode with three scenarios:
1. Success: HTTP 200, well-formed body, embeddings persisted
2. HTTP Error: non-200 response, PipelineError raised, memory untouched
3. Malformed Schema: missing/invalid fields, validation failure
"""

import json
import pytest
from pathlib import Path

from src.pipeline import (
    run_pipeline,
    PipelineResult,
    PipelineError,
    HTTPError,
    SchemaValidationError,
    FixtureClient,
    HTTPErrorFixtureClient,
    MalformedFixtureClient,
)


@pytest.fixture
def fixtures_dir():
    """Return path to fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_client(fixtures_dir):
    """Create a fixture client for testing."""
    return FixtureClient(fixtures_dir)


@pytest.fixture
def http_error_client(fixtures_dir):
    """Create an HTTP error fixture client."""
    return HTTPErrorFixtureClient(fixtures_dir)


@pytest.fixture
def malformed_client(fixtures_dir):
    """Create a malformed response fixture client."""
    return MalformedFixtureClient(fixtures_dir)


class TestPipelineSuccess:
    """Test successful pipeline execution."""
    
    def test_basic_success(self, fixture_client):
        """Test basic successful pipeline run."""
        result = run_pipeline(
            "Write a hello world function",
            client=fixture_client,
            persist_embeddings=False,
        )
        
        assert result.success is True
        assert result.response is not None
        assert result.model == "qwen2.5-coder:7b-q4_0"
        assert result.error is None
        assert result.duration_ms is not None
        assert result.duration_ms > 0
    
    def test_success_with_embeddings(self, fixture_client):
        """Test successful pipeline with embedding persistence."""
        result = run_pipeline(
            "Write a hello world function",
            client=fixture_client,
            persist_embeddings=True,
        )
        
        assert result.success is True
        assert result.response is not None
        assert result.embeddings_stored is True
        assert result.error is None
    
    def test_response_content(self, fixture_client):
        """Test that response contains expected code."""
        result = run_pipeline(
            "Write a hello world function",
            client=fixture_client,
        )
        
        assert result.success is True
        assert "def hello_world():" in result.response
        assert "print('Hello, World!')" in result.response


class TestPipelineHTTPError:
    """Test pipeline handling of HTTP errors."""
    
    def test_http_error_returns_failure(self, http_error_client):
        """Test that HTTP errors result in failure result."""
        result = run_pipeline(
            "Write a function",
            client=http_error_client,
        )
        
        assert result.success is False
        assert result.response is None
        assert result.error is not None
        assert "503" in result.error or "HTTP" in result.error
    
    def test_http_error_no_embeddings(self, http_error_client):
        """Test that HTTP errors don't store embeddings."""
        result = run_pipeline(
            "Write a function",
            client=http_error_client,
            persist_embeddings=True,
        )
        
        assert result.success is False
        assert result.embeddings_stored is False
    
    def test_http_error_duration_tracked(self, http_error_client):
        """Test that duration is tracked even on error."""
        result = run_pipeline(
            "Write a function",
            client=http_error_client,
        )
        
        assert result.duration_ms is not None
        assert result.duration_ms > 0


class TestPipelineMalformedSchema:
    """Test pipeline handling of malformed responses."""
    
    def test_malformed_response_returns_failure(self, malformed_client):
        """Test that malformed responses result in failure."""
        result = run_pipeline(
            "Write a function",
            client=malformed_client,
        )
        
        assert result.success is False
        assert result.response is None
        assert result.error is not None
        assert "schema" in result.error.lower() or "validation" in result.error.lower()
    
    def test_malformed_no_embeddings(self, malformed_client):
        """Test that malformed responses don't store embeddings."""
        result = run_pipeline(
            "Write a function",
            client=malformed_client,
            persist_embeddings=True,
        )
        
        assert result.success is False
        assert result.embeddings_stored is False
    
    def test_malformed_error_logged(self, malformed_client):
        """Test that validation errors are captured."""
        result = run_pipeline(
            "Write a function",
            client=malformed_client,
        )
        
        assert result.error is not None
        assert len(result.error) > 0


class TestPipelineFixtures:
    """Test that fixtures are correctly structured."""
    
    def test_success_fixture_structure(self, fixtures_dir):
        """Test that success fixture has required fields."""
        fixture_path = fixtures_dir / "ollama_success.json"
        assert fixture_path.exists()
        
        with open(fixture_path) as f:
            data = json.load(f)
        
        # Verify required fields
        assert "model" in data
        assert "response" in data
        assert "done" in data
        assert data["done"] is True
    
    def test_error_fixture_structure(self, fixtures_dir):
        """Test that error fixture has error info."""
        fixture_path = fixtures_dir / "ollama_http_error.json"
        assert fixture_path.exists()
        
        with open(fixture_path) as f:
            data = json.load(f)
        
        assert "error" in data
        assert "status_code" in data
    
    def test_malformed_fixture_structure(self, fixtures_dir):
        """Test that malformed fixture is missing required field."""
        fixture_path = fixtures_dir / "ollama_malformed.json"
        assert fixture_path.exists()
        
        with open(fixture_path) as f:
            data = json.load(f)
        
        # Should have model and response but NOT done
        assert "model" in data
        assert "response" in data
        assert "done" not in data  # This is the malformation
    
    def test_embedding_fixture_structure(self, fixtures_dir):
        """Test that embedding fixture has valid structure."""
        fixture_path = fixtures_dir / "embedding_success.json"
        assert fixture_path.exists()
        
        with open(fixture_path) as f:
            data = json.load(f)
        
        assert "embedding" in data
        assert isinstance(data["embedding"], list)
        assert len(data["embedding"]) > 0
        assert all(isinstance(x, (int, float)) for x in data["embedding"])


class TestPipelineDefaultBehavior:
    """Test pipeline default behaviors."""
    
    def test_default_client_is_fixture(self):
        """Test that pipeline defaults to fixture client."""
        # Without passing a client, should use fixture client
        result = run_pipeline("Write a function")
        
        # Should succeed with fixture data
        assert result.success is True
        assert result.model is not None
    
    def test_default_no_embeddings(self, fixture_client):
        """Test that embeddings are off by default."""
        result = run_pipeline(
            "Write a function",
            client=fixture_client,
        )
        
        assert result.embeddings_stored is False
    
    def test_default_model(self, fixture_client):
        """Test that default model is used."""
        result = run_pipeline(
            "Write a function",
            client=fixture_client,
        )
        
        assert result.model == "qwen2.5-coder:7b-q4_0"


class TestPipelineResult:
    """Test PipelineResult structure."""
    
    def test_result_has_all_fields(self, fixture_client):
        """Test that result has all expected fields."""
        result = run_pipeline("Write a function", client=fixture_client)
        
        assert hasattr(result, "success")
        assert hasattr(result, "response")
        assert hasattr(result, "model")
        assert hasattr(result, "error")
        assert hasattr(result, "embeddings_stored")
        assert hasattr(result, "duration_ms")
    
    def test_success_result_fields(self, fixture_client):
        """Test success result field values."""
        result = run_pipeline("Write a function", client=fixture_client)
        
        assert result.success is True
        assert result.response is not None
        assert result.model is not None
        assert result.error is None
    
    def test_error_result_fields(self, http_error_client):
        """Test error result field values."""
        result = run_pipeline("Write a function", client=http_error_client)
        
        assert result.success is False
        assert result.response is None
        assert result.error is not None

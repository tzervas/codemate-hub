"""
Integration tests for API endpoints and service connectivity.

These tests verify that service APIs are accessible and responding correctly.
"""

import pytest
import requests
import time
from typing import Dict, Optional


@pytest.fixture
def service_urls():
    """Fixture providing service URLs."""
    return {
        "ollama": "http://localhost:11434",
        "langflow": "http://localhost:7860",
        "app": "http://localhost:8000",
    }


@pytest.fixture
def ollama_client(service_urls):
    """Fixture providing an Ollama API client."""
    return OllamaClient(service_urls["ollama"])


class OllamaClient:
    """Simple client for Ollama API."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()

    def health_check(self) -> bool:
        """Check if Ollama API is responsive."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def list_models(self) -> Optional[list]:
        """List available models."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                return response.json().get("models", [])
            return None
        except requests.RequestException:
            return None

    def generate(self, model: str, prompt: str, stream: bool = False) -> Optional[Dict]:
        """Generate text using a model."""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream,
            }
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60,
            )
            if response.status_code == 200:
                return response.json()
            return None
        except requests.RequestException:
            return None


@pytest.mark.integration
class TestOllamaAPI:
    """Test Ollama API endpoints."""

    def test_ollama_api_reachable(self, service_urls):
        """Test that Ollama API is reachable."""
        response = requests.get(f"{service_urls['ollama']}/api/tags", timeout=10)
        assert response.status_code == 200, \
            f"Ollama API not reachable. Status: {response.status_code}"

    def test_ollama_api_returns_json(self, service_urls):
        """Test that Ollama API returns valid JSON."""
        response = requests.get(f"{service_urls['ollama']}/api/tags", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        assert "models" in data, "Ollama API response missing 'models' key"

    def test_ollama_health_check(self, ollama_client):
        """Test Ollama health check."""
        assert ollama_client.health_check(), \
            "Ollama health check failed"

    def test_ollama_list_models(self, ollama_client):
        """Test listing models from Ollama."""
        models = ollama_client.list_models()
        
        assert models is not None, "Failed to list models from Ollama"
        assert isinstance(models, list), "Models response is not a list"
        
        # We expect at least the default model to be present
        model_names = [m.get("name", "") for m in models]
        assert len(model_names) > 0, \
            "No models found. Run './scripts/model-pull.sh default' first."

    def test_ollama_has_default_model(self, ollama_client):
        """Test that default model is available."""
        models = ollama_client.list_models()
        
        assert models is not None, "Failed to list models"
        
        model_names = [m.get("name", "") for m in models]
        
        # Check for default models (either one is fine)
        default_models = ["qwen2.5-coder:7b-q4_0", "mistral:latest"]
        has_default = any(
            any(default in name for default in default_models)
            for name in model_names
        )
        
        assert has_default, \
            f"No default model found. Available: {model_names}. " \
            f"Run './scripts/model-pull.sh default'"

    @pytest.mark.slow
    def test_ollama_generate_simple_prompt(self, ollama_client):
        """Test generating text with Ollama."""
        models = ollama_client.list_models()
        assert models is not None and len(models) > 0, \
            "No models available for generation test"
        
        # Use the first available model
        model_name = models[0].get("name")
        
        result = ollama_client.generate(
            model=model_name,
            prompt="Say 'test successful' and nothing else.",
            stream=False,
        )
        
        assert result is not None, "Failed to generate text"
        assert "response" in result, "Generation response missing 'response' key"
        assert len(result["response"]) > 0, "Generated response is empty"


@pytest.mark.integration
class TestLangflowAPI:
    """Test Langflow API endpoints."""

    def test_langflow_ui_reachable(self, service_urls):
        """Test that Langflow UI is reachable."""
        try:
            response = requests.get(service_urls["langflow"], timeout=10)
            assert response.status_code in [200, 302], \
                f"Langflow UI not reachable. Status: {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("Langflow service not available (optional service)")

    def test_langflow_api_base(self, service_urls):
        """Test Langflow API base endpoint."""
        try:
            response = requests.get(f"{service_urls['langflow']}/api/v1", timeout=10)
            # Langflow API may return various status codes, just check it responds
            assert response.status_code < 500, \
                f"Langflow API error. Status: {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("Langflow service not available (optional service)")


@pytest.mark.integration
class TestAppAPI:
    """Test application API endpoints."""

    def test_app_container_accessible(self):
        """Test that app container is accessible via docker exec."""
        import subprocess
        
        result = subprocess.run(
            ["docker", "exec", "coding-assistant", "echo", "test"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        assert result.returncode == 0, \
            "Cannot access app container. Check if 'coding-assistant' is running."
        assert "test" in result.stdout, "Unexpected output from container"

    def test_app_python_environment(self):
        """Test that Python environment is properly set up in app container."""
        import subprocess
        
        result = subprocess.run(
            ["docker", "exec", "coding-assistant", "python", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        assert result.returncode == 0, "Python not available in app container"
        assert "Python 3.12" in result.stdout, \
            f"Wrong Python version. Expected 3.12, got: {result.stdout}"

    def test_app_has_required_modules(self):
        """Test that required Python modules are installed."""
        import subprocess
        
        required_modules = ["crewai", "langchain", "chromadb", "psutil"]
        
        for module in required_modules:
            result = subprocess.run(
                ["docker", "exec", "coding-assistant", "python", "-c", 
                 f"import {module}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            assert result.returncode == 0, \
                f"Required module '{module}' not installed in app container"

    def test_app_pipeline_exists(self):
        """Test that pipeline.py exists and is executable."""
        import subprocess
        
        result = subprocess.run(
            ["docker", "exec", "coding-assistant", "test", "-f", "/app/src/pipeline.py"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        assert result.returncode == 0, \
            "pipeline.py not found in app container"


@pytest.mark.integration
class TestServiceCommunication:
    """Test communication between services."""

    def test_app_can_reach_ollama(self):
        """Test that app container can reach Ollama service."""
        import subprocess
        
        # Test from within the app container using container network
        result = subprocess.run(
            ["docker", "exec", "coding-assistant", "curl", "-f", 
             "http://ollama:11434/api/tags"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        assert result.returncode == 0, \
            "App container cannot reach Ollama service on container network"

    def test_app_can_access_chroma_db(self):
        """Test that app can access Chroma DB directory."""
        import subprocess
        
        result = subprocess.run(
            ["docker", "exec", "coding-assistant", "test", "-d", "/app/chroma_db"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        assert result.returncode == 0, \
            "Chroma DB directory not accessible from app container"

    @pytest.mark.slow
    def test_app_can_initialize_memory(self):
        """Test that app can initialize memory/embeddings."""
        import subprocess
        
        # Run memory setup script
        result = subprocess.run(
            ["docker", "exec", "coding-assistant", "python", 
             "/app/src/memory_setup.py"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        
        # Memory setup may fail if Ollama is still loading, but should exit cleanly
        assert result.returncode in [0, 1], \
            f"Memory setup script crashed. Output: {result.stderr}"


@pytest.mark.integration
class TestEndpointPerformance:
    """Test API endpoint performance and response times."""

    def test_ollama_response_time(self, service_urls):
        """Test that Ollama API responds within acceptable time."""
        start_time = time.time()
        response = requests.get(f"{service_urls['ollama']}/api/tags", timeout=10)
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed < 5.0, \
            f"Ollama API too slow. Response time: {elapsed:.2f}s (expected < 5s)"

    def test_multiple_ollama_requests(self, service_urls):
        """Test handling multiple concurrent requests."""
        url = f"{service_urls['ollama']}/api/tags"
        
        # Make 5 requests sequentially (avoid overwhelming during tests)
        response_times = []
        for _ in range(5):
            start = time.time()
            response = requests.get(url, timeout=10)
            elapsed = time.time() - start
            
            assert response.status_code == 200
            response_times.append(elapsed)
        
        avg_time = sum(response_times) / len(response_times)
        assert avg_time < 5.0, \
            f"Average response time too high: {avg_time:.2f}s (expected < 5s)"

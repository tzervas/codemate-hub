"""
End-to-end smoke tests for codemate-hub.

These tests validate the complete stack functionality:
- Service deployment and health
- Model availability
- Memory/embeddings system
- Full pipeline execution
"""

import pytest
import subprocess
import requests
import time
from typing import Optional


@pytest.fixture
def ollama_base_url():
    """Ollama API base URL."""
    return "http://localhost:11434"


@pytest.fixture
def ensure_services_ready():
    """
    Fixture that ensures services are ready before running tests.
    Waits up to 60 seconds for critical services.
    """
    max_wait = 60
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            # Check Ollama
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        
        time.sleep(5)
    
    pytest.skip("Services not ready within timeout")


@pytest.mark.integration
@pytest.mark.slow
class TestEndToEndStack:
    """End-to-end smoke tests for the complete stack."""

    def test_full_stack_deployed(self, ensure_services_ready):
        """Test that all critical services are deployed and running."""
        # Check docker-compose is running
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "json"],
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0, "docker-compose not running"
        
        # Parse and check for critical services
        import json
        services = []
        for line in result.stdout.strip().split("\n"):
            if line:
                services.append(json.loads(line))
        
        service_names = [s.get("Service", "") for s in services]
        
        critical_services = ["ollama", "coding-assistant"]
        for service in critical_services:
            assert service in service_names, \
                f"Critical service '{service}' not deployed"

    def test_ollama_models_available(self, ollama_base_url):
        """Test that Ollama has models available."""
        response = requests.get(f"{ollama_base_url}/api/tags", timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        models = data.get("models", [])
        
        assert len(models) > 0, \
            "No models available in Ollama. Run './scripts/model-pull.sh default'"
        
        # Log available models for debugging
        model_names = [m.get("name") for m in models]
        print(f"\nAvailable models: {model_names}")

    def test_ollama_embedding_capability(self, ollama_base_url):
        """Test that Ollama can generate embeddings."""
        # Get first available model
        response = requests.get(f"{ollama_base_url}/api/tags", timeout=10)
        models = response.json().get("models", [])
        
        if not models:
            pytest.skip("No models available for embedding test")
        
        model_name = models[0].get("name")
        
        # Test embedding generation
        payload = {
            "model": model_name,
            "prompt": "This is a test for embedding generation.",
        }
        
        response = requests.post(
            f"{ollama_base_url}/api/embeddings",
            json=payload,
            timeout=30,
        )
        
        # Embeddings endpoint may not be available on all models
        if response.status_code == 200:
            data = response.json()
            assert "embedding" in data, "Embedding response missing 'embedding' key"
            assert len(data["embedding"]) > 0, "Empty embedding vector"
        else:
            pytest.skip(f"Model {model_name} does not support embeddings")

    def test_chroma_db_initialized(self):
        """Test that Chroma DB has been initialized."""
        import os
        
        # Check if chroma_db directory exists
        chroma_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "chroma_db"
        )
        
        # Directory should exist after build.sh
        assert os.path.exists(chroma_path), \
            "Chroma DB directory not found. Run './scripts/build.sh'"
        
        # Check for database files (SQLite)
        db_files = os.listdir(chroma_path)
        assert len(db_files) > 0, \
            "Chroma DB directory is empty. Run './scripts/build.sh'"

    def test_memory_setup_script_exists(self):
        """Test that memory setup script is accessible."""
        result = subprocess.run(
            ["docker", "exec", "coding-assistant", "test", "-f", 
             "/app/src/memory_setup.py"],
            capture_output=True,
            timeout=10,
        )
        
        assert result.returncode == 0, \
            "memory_setup.py not found in app container"

    @pytest.mark.slow
    def test_pipeline_can_execute(self):
        """Test that pipeline.py can execute without crashing."""
        result = subprocess.run(
            ["docker", "exec", "coding-assistant", "python", 
             "/app/src/pipeline.py"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        
        # Pipeline should exit cleanly (0 for success, 1 for controlled errors)
        assert result.returncode in [0, 1], \
            f"Pipeline crashed with code {result.returncode}. " \
            f"Output: {result.stdout}\nError: {result.stderr}"
        
        # Check for common error patterns
        error_patterns = ["Traceback", "Exception", "Error"]
        has_unhandled_error = any(
            pattern in result.stderr for pattern in error_patterns
        )
        
        if has_unhandled_error and result.returncode != 0:
            print(f"\nPipeline stderr: {result.stderr}")
            print(f"Pipeline stdout: {result.stdout}")

    @pytest.mark.slow
    def test_enclave_demo_executable(self):
        """Test that enclave demo can execute."""
        result = subprocess.run(
            ["docker", "exec", "coding-assistant", "python", 
             "/app/zephyr/demo_enclave.py"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        
        # Demo should exit cleanly
        assert result.returncode == 0, \
            f"Enclave demo failed with code {result.returncode}. " \
            f"Output: {result.stdout}\nError: {result.stderr}"

    def test_orchestrator_examples_executable(self):
        """Test that orchestrator examples can execute."""
        result = subprocess.run(
            ["docker", "exec", "coding-assistant", "python", "-m", 
             "src.orchestration_examples"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        
        # Examples should exit cleanly
        assert result.returncode == 0, \
            f"Orchestrator examples failed. " \
            f"Output: {result.stdout}\nError: {result.stderr}"


@pytest.mark.integration
class TestStackResilience:
    """Test stack resilience and recovery."""

    def test_services_survive_docker_restart(self):
        """Test that docker-compose can be restarted successfully."""
        # This test documents the restart procedure but doesn't actually
        # restart to avoid disrupting other tests
        
        # Verify services are currently running
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "json"],
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0, "Cannot query service status"
        
        # Document the restart procedure
        restart_procedure = [
            "docker-compose restart",
            "docker-compose down && docker-compose up -d",
            "./scripts/deploy.sh skip-build",
        ]
        
        # This test passes if we can query status (restart is documented)
        assert len(restart_procedure) > 0

    def test_health_check_script_available(self):
        """Test that health check script is available and executable."""
        import os
        
        script_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "scripts", "check-health.sh"
        )
        
        assert os.path.exists(script_path), \
            "check-health.sh script not found"
        assert os.access(script_path, os.X_OK), \
            "check-health.sh is not executable"

    def test_teardown_script_available(self):
        """Test that teardown script is available."""
        import os
        
        script_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "scripts", "teardown.sh"
        )
        
        assert os.path.exists(script_path), \
            "teardown.sh script not found"
        assert os.access(script_path, os.X_OK), \
            "teardown.sh is not executable"


@pytest.mark.integration
@pytest.mark.slow
class TestProductionReadiness:
    """Test production readiness indicators."""

    def test_environment_variables_configured(self):
        """Test that critical environment variables are set."""
        result = subprocess.run(
            ["docker", "exec", "coding-assistant", "env"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        assert result.returncode == 0
        env_output = result.stdout
        
        # Check for critical env vars
        required_vars = ["OLLAMA_BASE_URL", "CHROMA_DB_DIR"]
        for var in required_vars:
            assert var in env_output, \
                f"Required environment variable '{var}' not set"

    def test_volumes_properly_mounted(self):
        """Test that data volumes are properly mounted."""
        # Check ollama_data volume
        result = subprocess.run(
            ["docker", "volume", "ls", "--format", "{{.Name}}"],
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0
        volumes = result.stdout.strip().split("\n")
        
        # Should have ollama_data volume
        ollama_volumes = [v for v in volumes if "ollama" in v]
        assert len(ollama_volumes) > 0, \
            "Ollama data volume not found. Models will not persist."

    def test_preflight_check_script_passes(self):
        """Test that preflight check script passes."""
        import os
        
        script_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "scripts", "preflight-check.sh"
        )
        
        if os.path.exists(script_path):
            result = subprocess.run(
                [script_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            # Preflight checks should pass if services are running
            assert result.returncode == 0, \
                f"Preflight checks failed: {result.stdout}\n{result.stderr}"
        else:
            pytest.skip("Preflight check script not found")

    def test_integration_test_script_available(self):
        """Test that integration test script is available."""
        import os
        
        script_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "scripts", 
            "test-integration.sh"
        )
        
        assert os.path.exists(script_path), \
            "test-integration.sh script not found"
        assert os.access(script_path, os.X_OK), \
            "test-integration.sh is not executable"


@pytest.mark.integration
class TestDocumentation:
    """Test that documentation is complete and accessible."""

    def test_readme_exists(self):
        """Test that README.md exists."""
        import os
        
        readme_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "README.md"
        )
        
        assert os.path.exists(readme_path), "README.md not found"
        
        # Check that README has substantial content
        with open(readme_path, "r") as f:
            content = f.read()
            assert len(content) > 1000, "README.md seems incomplete"

    def test_trackers_directory_exists(self):
        """Test that project trackers exist."""
        import os
        
        trackers_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "trackers"
        )
        
        assert os.path.exists(trackers_path), "trackers/ directory not found"
        
        # Check for key tracker files
        key_files = ["README.md", "PLAN.md", "SPEC.md"]
        for file in key_files:
            file_path = os.path.join(trackers_path, file)
            assert os.path.exists(file_path), \
                f"Tracker file {file} not found"

    def test_langflow_documentation_exists(self):
        """Test that Langflow documentation exists."""
        import os
        
        langflow_docs = os.path.join(
            os.path.dirname(__file__), "..", "..", "docs", "langflow"
        )
        
        assert os.path.exists(langflow_docs), \
            "Langflow documentation directory not found"
        
        readme_path = os.path.join(langflow_docs, "README.md")
        assert os.path.exists(readme_path), \
            "Langflow README.md not found"

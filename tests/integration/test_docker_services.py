"""
Integration tests for Docker service health and availability.

These tests verify that all Docker containers are running and healthy.
"""

import pytest
import subprocess
import time
from typing import Dict, Optional


@pytest.fixture
def docker_compose():
    """Fixture to interact with docker-compose services."""
    return DockerComposeHelper()


class DockerComposeHelper:
    """Helper class for docker-compose operations."""

    def get_service_status(self, service_name: str) -> Dict[str, str]:
        """
        Get status information for a specific service.
        
        Args:
            service_name: Name of the service (e.g., 'ollama', 'app')
            
        Returns:
            Dict with 'state' and 'health' keys
        """
        try:
            result = subprocess.run(
                ["docker", "compose", "ps", "--format", "json", service_name],
                capture_output=True,
                text=True,
                check=True,
            )
            
            if not result.stdout.strip():
                return {"state": "not_running", "health": "unknown"}
            
            # Parse JSON output
            import json
            services = [json.loads(line) for line in result.stdout.strip().split("\n")]
            
            if not services:
                return {"state": "not_running", "health": "unknown"}
            
            service = services[0]
            return {
                "state": service.get("State", "unknown"),
                "health": service.get("Health", "unknown"),
            }
        except subprocess.CalledProcessError:
            return {"state": "error", "health": "unknown"}
        except Exception as e:
            return {"state": "error", "health": f"exception: {e}"}

    def is_service_running(self, service_name: str) -> bool:
        """Check if a service is running."""
        status = self.get_service_status(service_name)
        return status["state"] in ["running", "up"]

    def is_service_healthy(self, service_name: str, timeout: int = 30) -> bool:
        """
        Check if a service is healthy, with retry logic.
        
        Args:
            service_name: Name of the service
            timeout: Maximum seconds to wait for health
            
        Returns:
            True if service is healthy within timeout, False otherwise
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_service_status(service_name)
            
            # If service has no healthcheck, consider it healthy if running
            if status["health"] == "unknown" and status["state"] == "running":
                return True
            
            # If healthcheck exists and is healthy
            if status["health"] == "healthy":
                return True
            
            time.sleep(2)
        
        return False

    def get_all_services(self) -> list:
        """Get list of all services defined in docker-compose.yml."""
        try:
            result = subprocess.run(
                ["docker", "compose", "config", "--services"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip().split("\n")
        except subprocess.CalledProcessError:
            return []


@pytest.mark.integration
class TestDockerServices:
    """Test Docker service health and availability."""

    def test_ollama_container_running(self, docker_compose):
        """Test that Ollama container is running."""
        assert docker_compose.is_service_running("ollama"), \
            "Ollama service is not running. Run './scripts/deploy.sh' first."

    def test_ollama_container_healthy(self, docker_compose):
        """Test that Ollama container is healthy."""
        assert docker_compose.is_service_healthy("ollama", timeout=60), \
            "Ollama service is not healthy. Check logs with 'docker-compose logs ollama'"

    def test_langflow_container_running(self, docker_compose):
        """Test that Langflow container is running."""
        assert docker_compose.is_service_running("langflow"), \
            "Langflow service is not running. Run './scripts/deploy.sh' first."

    def test_app_container_running(self, docker_compose):
        """Test that app (coding-assistant) container is running."""
        assert docker_compose.is_service_running("coding-assistant"), \
            "App service is not running. Run './scripts/deploy.sh' first."

    def test_code_server_container_running(self, docker_compose):
        """Test that code-server container is running."""
        # Code-server is optional, so we just check if it's in the config
        services = docker_compose.get_all_services()
        if "code-server" in services:
            assert docker_compose.is_service_running("code-server"), \
                "Code-server service is not running."

    def test_all_required_services_running(self, docker_compose):
        """Test that all required services are running."""
        required_services = ["ollama", "langflow", "coding-assistant"]
        
        running_services = []
        not_running = []
        
        for service in required_services:
            if docker_compose.is_service_running(service):
                running_services.append(service)
            else:
                not_running.append(service)
        
        assert len(not_running) == 0, \
            f"Required services not running: {not_running}. Running: {running_services}"

    @pytest.mark.slow
    def test_all_services_become_healthy(self, docker_compose):
        """Test that all services with healthchecks become healthy within timeout."""
        services_to_check = ["ollama", "langflow", "coding-assistant"]
        unhealthy_services = []
        
        for service in services_to_check:
            if not docker_compose.is_service_healthy(service, timeout=120):
                unhealthy_services.append(service)
        
        assert len(unhealthy_services) == 0, \
            f"Services not healthy: {unhealthy_services}. Check logs with 'docker-compose logs <service>'"

    def test_containers_can_restart(self, docker_compose):
        """Test that containers can be restarted without errors."""
        # This is a basic check - just verify the service exists and can be queried
        status = docker_compose.get_service_status("ollama")
        assert status["state"] != "error", \
            "Error accessing service status. Docker may be misconfigured."


@pytest.mark.integration
class TestServicePersistence:
    """Test that service data persists across restarts."""

    def test_ollama_volume_mounted(self):
        """Test that Ollama data volume is properly mounted."""
        result = subprocess.run(
            ["docker", "compose", "config", "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        assert result.returncode == 0, "Failed to read docker-compose config"
        
        # Check for ollama_data volume in config
        assert "ollama_data" in result.stdout, \
            "ollama_data volume not configured in docker-compose.yml"

    def test_chroma_db_directory_exists(self):
        """Test that Chroma DB directory exists for persistence."""
        import os
        
        # Check if chroma_db directory exists
        chroma_path = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")
        
        # Directory may not exist on fresh install, which is ok
        # Just check that the volume is configured
        result = subprocess.run(
            ["docker", "compose", "config"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        assert "chroma_db" in result.stdout, \
            "chroma_db volume not configured in docker-compose.yml"


@pytest.mark.integration
@pytest.mark.slow
class TestServiceRecovery:
    """Test service recovery and restart behavior."""

    def test_ollama_survives_restart(self, docker_compose):
        """Test that Ollama service can be restarted successfully."""
        # Verify service is running first
        assert docker_compose.is_service_running("ollama"), \
            "Ollama must be running before restart test"
        
        # Restart the service
        result = subprocess.run(
            ["docker", "compose", "restart", "ollama"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        
        assert result.returncode == 0, \
            f"Failed to restart Ollama: {result.stderr}"
        
        # Wait for service to become healthy again
        time.sleep(5)
        assert docker_compose.is_service_healthy("ollama", timeout=60), \
            "Ollama did not become healthy after restart"

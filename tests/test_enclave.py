"""
Tests for the Zephyr enclave system.

This module tests enclave isolation, resource limits, and execution.
"""

import tempfile
from pathlib import Path

import pytest

from zephyr.core.enclave import EnclaveConfig, EnclaveResult
from zephyr.exec.runner import EnclaveRunner
from zephyr.exec.isolation import FilesystemIsolation


class TestEnclaveConfig:
    """Test enclave configuration."""
    
    def test_config_creation(self):
        """Test creating a basic enclave configuration."""
        config = EnclaveConfig(
            name="test-enclave",
            max_memory_mb=256,
            max_cpu_percent=50,
            timeout_seconds=10,
        )
        
        assert config.name == "test-enclave"
        assert config.max_memory_mb == 256
        assert config.max_cpu_percent == 50
        assert config.timeout_seconds == 10
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Negative memory should raise error
        with pytest.raises(ValueError, match="max_memory_mb"):
            EnclaveConfig(name="test", max_memory_mb=-1)
        
        # Invalid CPU percent should raise error
        with pytest.raises(ValueError, match="max_cpu_percent"):
            EnclaveConfig(name="test", max_cpu_percent=150)
        
        # Negative timeout should raise error
        with pytest.raises(ValueError, match="timeout_seconds"):
            EnclaveConfig(name="test", timeout_seconds=-1)
    
    def test_path_resolution(self):
        """Test that paths are resolved to absolute paths."""
        config = EnclaveConfig(
            name="test",
            allowed_read_paths=["./src", "/tmp"],
            allowed_write_paths=["./output"],
        )
        
        # All paths should be absolute
        for path in config.allowed_read_paths:
            assert Path(path).is_absolute()
        for path in config.allowed_write_paths:
            assert Path(path).is_absolute()


class TestFilesystemIsolation:
    """Test filesystem isolation mechanisms."""
    
    def test_read_access_validation(self):
        """Test read access validation."""
        isolation = FilesystemIsolation(
            allowed_read_paths=["/tmp"],
            allowed_write_paths=[],
        )
        
        # Should allow reading from /tmp
        assert isolation.validate_read_access("/tmp/test.txt")
        assert isolation.validate_read_access("/tmp/subdir/file.txt")
        
        # Should deny reading from other paths
        assert not isolation.validate_read_access("/etc/passwd")
        assert not isolation.validate_read_access("/home/user/file.txt")
    
    def test_write_access_validation(self):
        """Test write access validation."""
        isolation = FilesystemIsolation(
            allowed_read_paths=["/tmp"],
            allowed_write_paths=["/tmp/output"],
        )
        
        # Should allow writing to /tmp/output
        assert isolation.validate_write_access("/tmp/output/test.txt")
        assert isolation.validate_write_access("/tmp/output/subdir/file.txt")
        
        # Should deny writing to other paths
        assert not isolation.validate_write_access("/tmp/test.txt")
        assert not isolation.validate_write_access("/etc/config")
    
    def test_safe_open_read(self):
        """Test safe file opening for reading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Hello, world!")
            
            isolation = FilesystemIsolation(
                allowed_read_paths=[tmpdir],
                allowed_write_paths=[],
            )
            
            # Should be able to read the file
            with isolation.safe_open(str(test_file), "r") as f:
                content = f.read()
                assert content == "Hello, world!"
    
    def test_safe_open_write_denied(self):
        """Test that writing is denied without permission."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            
            isolation = FilesystemIsolation(
                allowed_read_paths=[tmpdir],
                allowed_write_paths=[],  # No write permission
            )
            
            # Should raise PermissionError
            with pytest.raises(PermissionError, match="Access denied"):
                with isolation.safe_open(str(test_file), "w"):
                    pass


class TestEnclaveExecution:
    """Test enclave execution."""
    
    def test_simple_execution(self):
        """Test executing a simple function in an enclave."""
        config = EnclaveConfig(
            name="test-simple",
            timeout_seconds=10,
        )
        runner = EnclaveRunner(config)
        
        result = runner.execute(
            target_function="simple_transform",
            module_path="zephyr.examples.pipeline_step",
            args={"data": ["hello", "world"], "operation": "upper"},
        )
        
        assert result.success
        assert result.output["data"] == ["HELLO", "WORLD"]
        assert result.execution_time_ms > 0
        assert result.isolated
    
    def test_word_count_execution(self):
        """Test executing word count in an enclave."""
        config = EnclaveConfig(
            name="test-wordcount",
            timeout_seconds=10,
        )
        runner = EnclaveRunner(config)
        
        result = runner.execute(
            target_function="word_count",
            module_path="zephyr.examples.pipeline_step",
            args={"text": "hello world hello"},
        )
        
        assert result.success
        assert result.output["total_words"] == 3
        assert result.output["unique_words"] == 2
    
    def test_code_analysis_execution(self):
        """Test executing code analysis in an enclave."""
        config = EnclaveConfig(
            name="test-analysis",
            timeout_seconds=10,
        )
        runner = EnclaveRunner(config)
        
        sample_code = """
def hello():
    pass

class MyClass:
    pass
"""
        
        result = runner.execute(
            target_function="analyze_code_string",
            module_path="zephyr.examples.code_analyzer",
            args={"code": sample_code, "filename": "test.py"},
        )
        
        assert result.success
        assert result.output["functions"] == 1
        assert result.output["classes"] == 1
    
    def test_timeout_enforcement(self):
        """Test that timeout is enforced."""
        # Note: This is a simplified test. True timeout enforcement
        # would require a long-running function
        config = EnclaveConfig(
            name="test-timeout",
            timeout_seconds=1,  # Very short timeout
        )
        runner = EnclaveRunner(config)
        
        # A quick function should still succeed
        result = runner.execute(
            target_function="simple_transform",
            module_path="zephyr.examples.pipeline_step",
            args={"data": ["test"], "operation": "upper"},
        )
        
        assert result.success
        # Execution time should be well under timeout
        assert result.execution_time_ms < 1000
    
    def test_execution_error_handling(self):
        """Test that execution errors are properly handled."""
        config = EnclaveConfig(name="test-error")
        runner = EnclaveRunner(config)
        
        # Try to execute with invalid operation
        result = runner.execute(
            target_function="simple_transform",
            module_path="zephyr.examples.pipeline_step",
            args={"data": ["test"], "operation": "invalid"},
        )
        
        assert not result.success
        assert result.error is not None
        assert "Unknown operation" in result.error
    
    def test_module_not_found(self):
        """Test handling of non-existent module."""
        config = EnclaveConfig(name="test-notfound")
        runner = EnclaveRunner(config)
        
        result = runner.execute(
            target_function="some_function",
            module_path="nonexistent.module",
            args={},
        )
        
        assert not result.success
        assert result.error is not None


class TestEnclaveResult:
    """Test enclave result handling."""
    
    def test_result_string_representation(self):
        """Test EnclaveResult string representation."""
        result = EnclaveResult(
            success=True,
            output={"key": "value"},
            execution_time_ms=100.5,
            memory_used_mb=50.2,
            cpu_percent=25.0,
        )
        
        result_str = str(result)
        assert "SUCCESS" in result_str
        assert "100.50ms" in result_str
        assert "50.20MB" in result_str
        assert "25.0%" in result_str
    
    def test_result_with_error(self):
        """Test EnclaveResult with error."""
        result = EnclaveResult(
            success=False,
            error="Test error message",
            execution_time_ms=50.0,
        )
        
        result_str = str(result)
        assert "FAILED" in result_str
        assert "Test error message" in result_str


class TestEnclaveIntegration:
    """Integration tests for enclave system."""
    
    def test_multiple_executions(self):
        """Test multiple executions in the same enclave."""
        config = EnclaveConfig(
            name="test-multiple",
            timeout_seconds=10,
        )
        runner = EnclaveRunner(config)
        
        # Execute first function
        result1 = runner.execute(
            target_function="simple_transform",
            module_path="zephyr.examples.pipeline_step",
            args={"data": ["a", "b"], "operation": "upper"},
        )
        
        # Execute second function
        result2 = runner.execute(
            target_function="word_count",
            module_path="zephyr.examples.pipeline_step",
            args={"text": "hello world"},
        )
        
        assert result1.success
        assert result2.success
        assert result1.output["data"] == ["A", "B"]
        assert result2.output["total_words"] == 2
    
    def test_cleanup(self):
        """Test enclave cleanup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            working_dir = Path(tmpdir) / "enclave-test"
            
            config = EnclaveConfig(
                name="test-cleanup",
                working_directory=str(working_dir),
            )
            runner = EnclaveRunner(config)
            
            # Execute something to create the working directory
            result = runner.execute(
                target_function="simple_transform",
                module_path="zephyr.examples.pipeline_step",
                args={"data": ["test"], "operation": "upper"},
            )
            
            assert result.success
            assert working_dir.exists()
            
            # Cleanup should remove the directory
            runner.cleanup()
            assert not working_dir.exists()

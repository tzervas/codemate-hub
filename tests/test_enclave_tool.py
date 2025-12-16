"""
Tests for the enclave tool integration.

This module tests the high-level EnclaveTool interface.
"""

import pytest

from src.enclave_tool import EnclaveTool


class TestEnclaveTool:
    """Test the EnclaveTool high-level interface."""
    
    def test_create_enclave(self):
        """Test creating an enclave."""
        tool = EnclaveTool()
        
        enclave_id = tool.create_enclave(
            objective="Test enclave",
            name="test-enclave-1",
        )
        
        assert enclave_id == "test-enclave-1"
        assert enclave_id in tool.enclaves
        assert enclave_id in tool.configs
    
    def test_create_enclave_auto_id(self):
        """Test creating an enclave with auto-generated ID."""
        tool = EnclaveTool()
        
        enclave_id = tool.create_enclave(objective="Test enclave")
        
        assert enclave_id.startswith("enclave-")
        assert enclave_id in tool.enclaves
    
    def test_run_in_enclave(self):
        """Test running code in an enclave."""
        tool = EnclaveTool()
        
        enclave_id = tool.create_enclave(
            objective="Run simple transform",
            timeout_seconds=10,
        )
        
        result = tool.run_in_enclave(
            enclave_id=enclave_id,
            target_function="simple_transform",
            module_path="zephyr.examples.pipeline_step",
            args={"data": ["hello", "world"], "operation": "upper"},
        )
        
        assert result.success
        assert result.output["data"] == ["HELLO", "WORLD"]
    
    def test_run_in_nonexistent_enclave(self):
        """Test running in a non-existent enclave raises error."""
        tool = EnclaveTool()
        
        with pytest.raises(KeyError, match="not found"):
            tool.run_in_enclave(
                enclave_id="nonexistent",
                target_function="some_func",
                module_path="some.module",
            )
    
    def test_cleanup_enclave(self):
        """Test cleaning up an enclave."""
        tool = EnclaveTool()
        
        enclave_id = tool.create_enclave(objective="Test cleanup")
        
        assert enclave_id in tool.enclaves
        
        tool.cleanup_enclave(enclave_id)
        
        assert enclave_id not in tool.enclaves
        assert enclave_id not in tool.configs
    
    def test_list_enclaves(self):
        """Test listing active enclaves."""
        tool = EnclaveTool()
        
        # Create multiple enclaves
        id1 = tool.create_enclave(objective="Test 1", name="enclave-1")
        id2 = tool.create_enclave(objective="Test 2", name="enclave-2")
        
        enclaves = tool.list_enclaves()
        
        assert len(enclaves) == 2
        assert id1 in enclaves
        assert id2 in enclaves
        assert enclaves[id1].name == "enclave-1"
        assert enclaves[id2].name == "enclave-2"
    
    def test_custom_resource_limits(self):
        """Test creating enclave with custom resource limits."""
        tool = EnclaveTool()
        
        enclave_id = tool.create_enclave(
            objective="Test limits",
            max_memory_mb=1024,
            max_cpu_percent=75,
            timeout_seconds=60,
        )
        
        config = tool.configs[enclave_id]
        assert config.max_memory_mb == 1024
        assert config.max_cpu_percent == 75
        assert config.timeout_seconds == 60
    
    def test_custom_filesystem_paths(self):
        """Test creating enclave with custom filesystem paths."""
        tool = EnclaveTool()
        
        enclave_id = tool.create_enclave(
            objective="Test paths",
            allowed_read_paths=["/tmp/read"],
            allowed_write_paths=["/tmp/write"],
        )
        
        config = tool.configs[enclave_id]
        # Paths should be resolved to absolute
        assert any("/tmp/read" in p for p in config.allowed_read_paths)
        assert any("/tmp/write" in p for p in config.allowed_write_paths)
    
    def test_multiple_operations_same_enclave(self):
        """Test running multiple operations in the same enclave."""
        tool = EnclaveTool()
        
        enclave_id = tool.create_enclave(objective="Test multiple ops")
        
        # Run first operation
        result1 = tool.run_in_enclave(
            enclave_id=enclave_id,
            target_function="simple_transform",
            module_path="zephyr.examples.pipeline_step",
            args={"data": ["a", "b"], "operation": "upper"},
        )
        
        # Run second operation
        result2 = tool.run_in_enclave(
            enclave_id=enclave_id,
            target_function="word_count",
            module_path="zephyr.examples.pipeline_step",
            args={"text": "hello world"},
        )
        
        assert result1.success
        assert result2.success
        assert result1.output["data"] == ["A", "B"]
        assert result2.output["total_words"] == 2

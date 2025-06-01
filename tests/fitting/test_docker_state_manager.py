"""
Test DockerStateManager functionality
"""
import pytest
import json
import tempfile
import os
from unittest.mock import MagicMock, patch

from src.env_integration.fitting.docker_state_manager import (
    DockerStateManager, DockerStateInfo
)
from src.context.execution_context import ExecutionContext


class TestDockerStateInfo:
    """Test DockerStateInfo class"""
    
    def test_from_context_with_dockerfile_resolver(self):
        """Test creating DockerStateInfo from context with dockerfile resolver"""
        # Mock context
        mock_context = MagicMock(spec=ExecutionContext)
        mock_context.language = "python"
        mock_context.get_docker_names.return_value = {
            "image_name": "python_abc123",
            "container_name": "cph_python",
            "oj_image_name": "ojtools_def456",
            "oj_container_name": "cph_ojtools"
        }
        
        # Mock dockerfile resolver
        mock_resolver = MagicMock()
        mock_resolver.dockerfile = "FROM python:3.9\nRUN pip install requests"
        mock_resolver.oj_dockerfile = "FROM python:3.9\nRUN pip install online-judge-tools"
        mock_context.dockerfile_resolver = mock_resolver
        
        # Create DockerStateInfo
        state_info = DockerStateInfo.from_context(mock_context)
        
        assert state_info.language == "python"
        assert state_info.dockerfile_hash is not None
        assert len(state_info.dockerfile_hash) == 12
        assert state_info.oj_dockerfile_hash is not None
        assert len(state_info.oj_dockerfile_hash) == 12
        assert state_info.image_name == "python_abc123"
        assert state_info.oj_image_name == "ojtools_def456"
        assert state_info.container_name == "cph_python"
        assert state_info.oj_container_name == "cph_ojtools"
        assert state_info.last_updated is not None
    
    def test_from_context_without_dockerfile_resolver(self):
        """Test creating DockerStateInfo from context without dockerfile resolver"""
        # Mock context
        mock_context = MagicMock(spec=ExecutionContext)
        mock_context.language = "rust"
        mock_context.get_docker_names.return_value = {
            "image_name": "rust",
            "container_name": "cph_rust",
            "oj_image_name": "ojtools",
            "oj_container_name": "cph_ojtools"
        }
        mock_context.dockerfile_resolver = None
        
        # Create DockerStateInfo
        state_info = DockerStateInfo.from_context(mock_context)
        
        assert state_info.language == "rust"
        assert state_info.dockerfile_hash is None
        assert state_info.oj_dockerfile_hash is None
        assert state_info.image_name == "rust"
        assert state_info.oj_image_name == "ojtools"
        assert state_info.container_name == "cph_rust"
        assert state_info.oj_container_name == "cph_ojtools"
    
    def test_from_context_with_empty_dockerfiles(self):
        """Test creating DockerStateInfo with empty dockerfile content"""
        # Mock context
        mock_context = MagicMock(spec=ExecutionContext)
        mock_context.language = "python"
        mock_context.get_docker_names.return_value = {
            "image_name": "python",
            "container_name": "cph_python",
            "oj_image_name": "ojtools",
            "oj_container_name": "cph_ojtools"
        }
        
        # Mock dockerfile resolver with empty content
        mock_resolver = MagicMock()
        mock_resolver.dockerfile = ""
        mock_resolver.oj_dockerfile = None
        mock_context.dockerfile_resolver = mock_resolver
        
        # Create DockerStateInfo
        state_info = DockerStateInfo.from_context(mock_context)
        
        assert state_info.dockerfile_hash is None
        assert state_info.oj_dockerfile_hash is None


class TestDockerStateManager:
    """Test DockerStateManager class"""
    
    def setup_method(self):
        """Setup test environment"""
        # Create temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.temp_file_path = self.temp_file.name
    
    def teardown_method(self):
        """Cleanup test environment"""
        if os.path.exists(self.temp_file_path):
            os.unlink(self.temp_file_path)
    
    def test_init_default(self):
        """Test default initialization"""
        manager = DockerStateManager()
        assert manager.state_file_path == "docker_state.json"
        assert manager._state_cache is None
    
    def test_init_with_file_path(self):
        """Test initialization with custom file path"""
        manager = DockerStateManager(state_file_path="/custom/path.json")
        assert manager.state_file_path == "/custom/path.json"
        assert manager._state_cache is None
    
    def test_init_with_initial_state(self):
        """Test initialization with initial state (for testing)"""
        initial_state = {"python_docker": {"language": "python"}}
        manager = DockerStateManager(initial_state=initial_state)
        assert manager._state_cache == initial_state
    
    def test_from_filepath_nonexistent_file(self):
        """Test from_filepath with non-existent file"""
        manager = DockerStateManager.from_filepath("/nonexistent/file.json")
        assert manager.state_file_path == "/nonexistent/file.json"
        assert manager._state_cache == {}
    
    def test_from_filepath_existing_file(self):
        """Test from_filepath with existing file"""
        # Write test data to file
        test_data = {
            "python_docker": {
                "language": "python",
                "dockerfile_hash": "abc123456789",
                "image_name": "python_abc123"
            }
        }
        with open(self.temp_file_path, 'w') as f:
            json.dump(test_data, f)
        
        # Load from file
        manager = DockerStateManager.from_filepath(self.temp_file_path)
        assert manager.state_file_path == self.temp_file_path
        assert manager._state_cache == test_data
    
    def test_load_state_no_file(self):
        """Test loading state when file doesn't exist"""
        manager = DockerStateManager(state_file_path="/nonexistent/file.json")
        state = manager._load_state()
        assert state == {}
        assert manager._state_cache == {}
    
    def test_load_state_existing_file(self):
        """Test loading state from existing file"""
        # Write test data to file
        test_data = {"test": "data"}
        with open(self.temp_file_path, 'w') as f:
            json.dump(test_data, f)
        
        manager = DockerStateManager(state_file_path=self.temp_file_path)
        state = manager._load_state()
        assert state == test_data
        assert manager._state_cache == test_data
    
    def test_load_state_invalid_json(self):
        """Test loading state from file with invalid JSON"""
        # Write invalid JSON to file
        with open(self.temp_file_path, 'w') as f:
            f.write("invalid json content")
        
        manager = DockerStateManager(state_file_path=self.temp_file_path)
        state = manager._load_state()
        assert state == {}
        assert manager._state_cache == {}
    
    def test_save_state(self):
        """Test saving state to file"""
        manager = DockerStateManager(state_file_path=self.temp_file_path)
        test_data = {"python_docker": {"language": "python"}}
        
        manager._save_state(test_data)
        
        # Verify file was written
        with open(self.temp_file_path, 'r') as f:
            saved_data = json.load(f)
        assert saved_data == test_data
        assert manager._state_cache == test_data
    
    def test_get_state_key(self):
        """Test state key generation"""
        manager = DockerStateManager()
        key = manager.get_state_key("python", "docker")
        assert key == "python_docker"
    
    def test_check_rebuild_needed_no_previous_state(self):
        """Test rebuild check with no previous state"""
        manager = DockerStateManager(initial_state={})
        
        # Mock context
        mock_context = MagicMock(spec=ExecutionContext)
        mock_context.language = "python"
        mock_context.env_type = "docker"
        mock_context.get_docker_names.return_value = {
            "image_name": "python",
            "container_name": "cph_python",
            "oj_image_name": "ojtools",
            "oj_container_name": "cph_ojtools"
        }
        mock_context.dockerfile_resolver = None
        
        # Check rebuild needs
        result = manager.check_rebuild_needed(mock_context)
        image_rebuild, oj_rebuild, container_recreate, oj_container_recreate = result
        
        # Everything should need rebuilding/recreation
        assert image_rebuild is True
        assert oj_rebuild is True
        assert container_recreate is True
        assert oj_container_recreate is True
    
    def test_check_rebuild_needed_no_changes(self):
        """Test rebuild check with no changes needed"""
        # Setup previous state
        previous_state = {
            "python_docker": {
                "language": "python",
                "dockerfile_hash": "abc123456789",
                "oj_dockerfile_hash": None,
                "image_name": "python",
                "container_name": "cph_python",
                "oj_image_name": "ojtools",
                "oj_container_name": "cph_ojtools"
            }
        }
        manager = DockerStateManager(initial_state=previous_state)
        
        # Mock context with same values
        mock_context = MagicMock(spec=ExecutionContext)
        mock_context.language = "python"
        mock_context.env_type = "docker"
        mock_context.get_docker_names.return_value = {
            "image_name": "python",
            "container_name": "cph_python",
            "oj_image_name": "ojtools",
            "oj_container_name": "cph_ojtools"
        }
        
        # Mock dockerfile resolver that produces same hash
        mock_resolver = MagicMock()
        mock_resolver.dockerfile = "FROM python:3.9"  # Will produce specific hash
        mock_resolver.oj_dockerfile = None
        mock_context.dockerfile_resolver = mock_resolver
        
        # Patch the hash calculation in the DockerStateInfo module to return consistent value
        with patch('src.env_integration.fitting.docker_state_manager.hashlib.sha256') as mock_sha256:
            mock_sha256.return_value.hexdigest.return_value = "abc123456789abcdef"
            
            result = manager.check_rebuild_needed(mock_context)
            image_rebuild, oj_rebuild, container_recreate, oj_container_recreate = result
            
            # Hash should match, so no rebuild needed
            assert image_rebuild is False  # Hash matches stored value
            assert oj_rebuild is False  # No OJ dockerfile
            assert container_recreate is False  # No image rebuild needed
            assert oj_container_recreate is False  # No OJ changes
    
    def test_check_rebuild_needed_dockerfile_changed(self):
        """Test rebuild check when dockerfile content changed"""
        # Setup previous state
        previous_state = {
            "python_docker": {
                "dockerfile_hash": "old_hash",
                "oj_dockerfile_hash": None,
                "image_name": "python",
                "container_name": "cph_python",
                "oj_image_name": "ojtools",
                "oj_container_name": "cph_ojtools"
            }
        }
        manager = DockerStateManager(initial_state=previous_state)
        
        # Mock context
        mock_context = MagicMock(spec=ExecutionContext)
        mock_context.language = "python"
        mock_context.env_type = "docker"
        mock_context.get_docker_names.return_value = {
            "image_name": "python",
            "container_name": "cph_python",
            "oj_image_name": "ojtools",
            "oj_container_name": "cph_ojtools"
        }
        
        # Mock dockerfile resolver with new content
        mock_resolver = MagicMock()
        mock_resolver.dockerfile = "FROM python:3.10\nRUN pip install new-package"
        mock_resolver.oj_dockerfile = None
        mock_context.dockerfile_resolver = mock_resolver
        
        result = manager.check_rebuild_needed(mock_context)
        image_rebuild, oj_rebuild, container_recreate, oj_container_recreate = result
        
        # Image should need rebuilding, container should need recreation
        assert image_rebuild is True
        assert oj_rebuild is False
        assert container_recreate is True
        assert oj_container_recreate is False
    
    def test_update_state(self):
        """Test updating stored state"""
        manager = DockerStateManager(state_file_path=self.temp_file_path)
        
        # Mock context
        mock_context = MagicMock(spec=ExecutionContext)
        mock_context.language = "python"
        mock_context.env_type = "docker"
        mock_context.get_docker_names.return_value = {
            "image_name": "python_abc123",
            "container_name": "cph_python",
            "oj_image_name": "ojtools",
            "oj_container_name": "cph_ojtools"
        }
        mock_context.dockerfile_resolver = None
        
        # Update state
        manager.update_state(mock_context)
        
        # Verify state was saved
        with open(self.temp_file_path, 'r') as f:
            saved_data = json.load(f)
        
        assert "python_docker" in saved_data
        state_data = saved_data["python_docker"]
        assert state_data["language"] == "python"
        assert state_data["image_name"] == "python_abc123"
        assert state_data["container_name"] == "cph_python"
    
    def test_get_expected_image_name(self):
        """Test getting expected image name"""
        manager = DockerStateManager()
        
        # Mock context
        mock_context = MagicMock(spec=ExecutionContext)
        mock_context.language = "python"
        mock_context.get_docker_names.return_value = {
            "image_name": "python_abc123",
            "container_name": "cph_python",
            "oj_image_name": "ojtools_def456",
            "oj_container_name": "cph_ojtools"
        }
        mock_context.dockerfile_resolver = None
        
        # Test regular image
        image_name = manager.get_expected_image_name(mock_context, is_oj=False)
        assert image_name == "python_abc123"
        
        # Test OJ image
        oj_image_name = manager.get_expected_image_name(mock_context, is_oj=True)
        assert oj_image_name == "ojtools_def456"
    
    def test_clear_state_specific(self):
        """Test clearing specific state entry"""
        manager = DockerStateManager(state_file_path=self.temp_file_path)
        
        # Setup initial state
        initial_state = {
            "python_docker": {"language": "python"},
            "rust_docker": {"language": "rust"}
        }
        manager._save_state(initial_state)
        
        # Clear specific entry
        manager.clear_state("python", "docker")
        
        # Verify only python_docker was removed
        state = manager._load_state()
        assert "python_docker" not in state
        assert "rust_docker" in state
    
    def test_clear_state_all(self):
        """Test clearing all state"""
        manager = DockerStateManager(state_file_path=self.temp_file_path)
        
        # Setup initial state
        initial_state = {
            "python_docker": {"language": "python"},
            "rust_docker": {"language": "rust"}
        }
        manager._save_state(initial_state)
        
        # Clear all state
        manager.clear_state()
        
        # Verify all state was cleared
        state = manager._load_state()
        assert state == {}
    
    def test_inspect_container_compatibility_nonexistent(self):
        """Test container compatibility check for non-existent container"""
        manager = DockerStateManager()
        
        # Mock operations
        mock_operations = MagicMock()
        mock_docker_driver = MagicMock()
        mock_docker_driver.ps.return_value = []  # No containers
        mock_operations.resolve.return_value = mock_docker_driver
        
        # Check compatibility
        result = manager.inspect_container_compatibility(
            mock_operations, "nonexistent_container", "expected_image"
        )
        assert result is False
    
    def test_inspect_container_compatibility_compatible(self):
        """Test container compatibility check for compatible container"""
        manager = DockerStateManager()
        
        # Mock operations
        mock_operations = MagicMock()
        mock_docker_driver = MagicMock()
        mock_docker_driver.ps.return_value = ["test_container"]
        
        # Mock inspect result
        mock_inspect_result = MagicMock()
        mock_inspect_result.success = True
        mock_inspect_result.stdout = json.dumps([{
            "Config": {"Image": "expected_image:latest"}
        }])
        mock_docker_driver.inspect.return_value = mock_inspect_result
        mock_operations.resolve.return_value = mock_docker_driver
        
        # Check compatibility
        result = manager.inspect_container_compatibility(
            mock_operations, "test_container", "expected_image"
        )
        assert result is True
    
    def test_inspect_container_compatibility_incompatible(self):
        """Test container compatibility check for incompatible container"""
        manager = DockerStateManager()
        
        # Mock operations
        mock_operations = MagicMock()
        mock_docker_driver = MagicMock()
        mock_docker_driver.ps.return_value = ["test_container"]
        
        # Mock inspect result with different image
        mock_inspect_result = MagicMock()
        mock_inspect_result.success = True
        mock_inspect_result.stdout = json.dumps([{
            "Config": {"Image": "different_image:latest"}
        }])
        mock_docker_driver.inspect.return_value = mock_inspect_result
        mock_operations.resolve.return_value = mock_docker_driver
        
        # Check compatibility
        result = manager.inspect_container_compatibility(
            mock_operations, "test_container", "expected_image"
        )
        assert result is False
    
    def test_inspect_container_compatibility_inspect_fails(self):
        """Test container compatibility check when inspect fails"""
        manager = DockerStateManager()
        
        # Mock operations
        mock_operations = MagicMock()
        mock_docker_driver = MagicMock()
        mock_docker_driver.ps.return_value = ["test_container"]
        
        # Mock failed inspect
        mock_inspect_result = MagicMock()
        mock_inspect_result.success = False
        mock_docker_driver.inspect.return_value = mock_inspect_result
        mock_operations.resolve.return_value = mock_docker_driver
        
        # Check compatibility
        result = manager.inspect_container_compatibility(
            mock_operations, "test_container", "expected_image"
        )
        assert result is False
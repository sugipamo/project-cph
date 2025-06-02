"""
Tests for ExecutionContext
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.context.execution_context import ExecutionContext
from src.context.execution_data import ExecutionData
from src.context.dockerfile_resolver import DockerfileResolver


class TestExecutionContext:
    
    def test_init(self):
        """Test ExecutionContext initialization"""
        env_json = {"python": {"commands": {}}}
        resolver = Mock()
        
        context = ExecutionContext(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json=env_json,
            resolver=resolver
        )
        
        # Verify data storage
        assert context.command_type == "build"
        assert context.language == "python"
        assert context.contest_name == "abc123"
        assert context.problem_name == "a"
        assert context.env_type == "docker"
        assert context.env_json == env_json
        assert context.resolver == resolver
    
    def test_property_setters(self):
        """Test property setters"""
        context = ExecutionContext(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        # Test setters
        context.command_type = "test"
        assert context.command_type == "test"
        
        context.language = "rust"
        assert context.language == "rust"
        
        context.contest_name = "abc456"
        assert context.contest_name == "abc456"
        
        context.problem_name = "b"
        assert context.problem_name == "b"
        
        context.env_type = "local"
        assert context.env_type == "local"
        
        new_env_json = {"rust": {}}
        context.env_json = new_env_json
        assert context.env_json == new_env_json
    
    def test_resolver_setter_updates_config_resolver(self):
        """Test that setting resolver updates ConfigResolverProxy"""
        with patch('src.context.execution_context.ConfigResolverProxy') as mock_proxy_class:
            context = ExecutionContext(
                command_type="build",
                language="python",
                contest_name="abc123",
                problem_name="a",
                env_type="docker",
                env_json={}
            )
            
            new_resolver = Mock()
            context.resolver = new_resolver
            
            # Should create new ConfigResolverProxy with updated data
            assert mock_proxy_class.call_count >= 2  # Once in init, once in setter
    
    def test_dockerfile_resolver_property(self):
        """Test dockerfile resolver getter and setter"""
        context = ExecutionContext(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        # Initially None
        assert context.dockerfile_resolver is None
        
        # Set resolver
        mock_resolver = Mock(spec=DockerfileResolver)
        context.dockerfile_resolver = mock_resolver
        assert context.dockerfile_resolver == mock_resolver
    
    def test_dockerfile_property_with_resolver(self):
        """Test dockerfile property with resolver"""
        context = ExecutionContext(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        # Setup dockerfile resolver
        mock_resolver = Mock(spec=DockerfileResolver)
        mock_resolver.dockerfile = "FROM python:3.9"
        context.dockerfile_resolver = mock_resolver
        
        # Access dockerfile
        assert context.dockerfile == "FROM python:3.9"
    
    def test_dockerfile_property_without_resolver(self):
        """Test dockerfile property without resolver"""
        context = ExecutionContext(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        # No resolver set
        assert context.dockerfile is None
    
    def test_oj_dockerfile_property(self):
        """Test oj_dockerfile property"""
        context = ExecutionContext(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        # Setup dockerfile resolver
        mock_resolver = Mock(spec=DockerfileResolver)
        mock_resolver.oj_dockerfile = "FROM ojtools:latest"
        context.dockerfile_resolver = mock_resolver
        
        # Access oj_dockerfile
        assert context.oj_dockerfile == "FROM ojtools:latest"
    
    def test_old_execution_context_property(self):
        """Test old_execution_context property"""
        context = ExecutionContext(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        # Initially None
        assert context.old_execution_context is None
        
        # Set value
        old_context = {"old": "context"}
        context.old_execution_context = old_context
        assert context.old_execution_context == old_context
    
    @patch('src.context.execution_context.ContextValidator')
    def test_validate(self, mock_validator_class):
        """Test validate method"""
        # Setup
        mock_validator = Mock()
        mock_validator.validate.return_value = (True, None)
        mock_validator_class.return_value = mock_validator
        
        context = ExecutionContext(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        # Execute
        is_valid, error = context.validate()
        
        # Verify
        assert is_valid is True
        assert error is None
        mock_validator.validate.assert_called_once()
    
    def test_resolve(self):
        """Test resolve method"""
        context = ExecutionContext(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        # Mock config resolver
        mock_result = Mock()
        context._config_resolver.resolve = Mock(return_value=mock_result)
        
        # Execute
        path = ["python", "commands", "build"]
        result = context.resolve(path)
        
        # Verify
        assert result == mock_result
        context._config_resolver.resolve.assert_called_once_with(path)
    
    def test_to_format_dict(self):
        """Test to_format_dict method"""
        context = ExecutionContext(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={
                "python": {
                    "contest_current_path": "/current",
                    "workspace_path": "/workspace",
                    "language_id": "python3",
                    "source_file_name": "main.py"
                }
            }
        )
        
        # Execute
        format_dict = context.to_format_dict()
        
        # Verify basic keys
        assert format_dict["command_type"] == "build"
        assert format_dict["language"] == "python"
        assert format_dict["contest_name"] == "abc123"
        assert format_dict["problem_name"] == "a"
        assert format_dict["env_type"] == "docker"
    
    def test_get_docker_names(self):
        """Test get_docker_names method"""
        context = ExecutionContext(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        # Execute
        docker_names = context.get_docker_names()
        
        # Verify structure
        assert isinstance(docker_names, dict)
        assert "image_name" in docker_names
        assert "container_name" in docker_names
        assert "oj_image_name" in docker_names
        assert "oj_container_name" in docker_names
    
    def test_format_string(self):
        """Test format_string method"""
        context = ExecutionContext(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        # Test formatting
        template = "Contest: {contest_name}, Problem: {problem_name}"
        result = context.format_string(template)
        
        assert result == "Contest: abc123, Problem: a"
    
    @patch('src.context.execution_context.format_with_missing_keys')
    def test_format_string_with_missing_keys(self, mock_format):
        """Test format_string with missing keys"""
        context = ExecutionContext(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        mock_format.return_value = ("formatted", ["missing_key"])
        
        # Test formatting with missing key
        template = "Contest: {contest_name}, Missing: {missing_key}"
        result = context.format_string(template)
        
        # Should call format_with_missing_keys
        mock_format.assert_called_once()
    
    def test_dockerfile_setter_backward_compatibility(self):
        """Test dockerfile setter for backward compatibility"""
        context = ExecutionContext(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        # Setting dockerfile should not raise error (no-op for now)
        context.dockerfile = "FROM python:3.9"
        # No assertion needed - just ensure no error
    
    def test_oj_dockerfile_setter_backward_compatibility(self):
        """Test oj_dockerfile setter for backward compatibility"""
        context = ExecutionContext(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        # Setting oj_dockerfile should not raise error (no-op for now)
        context.oj_dockerfile = "FROM ojtools:latest"
        # No assertion needed - just ensure no error
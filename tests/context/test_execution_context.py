"""
Comprehensive tests for context.execution_context module
This is a critical untested module (280 LOC) that manages execution context as a facade
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from src.context.execution_context import ExecutionContext
from src.context.execution_data import ExecutionData
from src.context.dockerfile_resolver import DockerfileResolver
from src.pure_functions.execution_context_formatter_pure import ExecutionFormatData


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
    
    def test_validate(self):
        """Test validate method"""
        # Valid context
        context = ExecutionContext(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={"python": {}}
        )
        
        # Execute
        is_valid, error = context.validate()
        
        # Verify
        assert is_valid is True
        assert error is None
        
        # Invalid context - missing command_type
        context2 = ExecutionContext(
            command_type="",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        is_valid2, error2 = context2.validate()
        assert is_valid2 is False
        assert error2 == "command_type is required"
    
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
    
    def test_format_string_with_missing_keys(self):
        """Test format_string with missing keys"""
        context = ExecutionContext(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        # Test formatting with missing key
        template = "Contest: {contest_name}, Missing: {missing_key}"
        result = context.format_string(template)
        
        # Should handle missing keys gracefully
        assert "abc123" in result
        assert "{missing_key}" in result
    
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


class TestExecutionContextAdvanced:
    """Advanced ExecutionContext tests for comprehensive coverage"""
    
    def test_config_resolver_properties(self):
        """Test config resolver proxy properties"""
        context = ExecutionContext("build", "python", "abc", "a", "local", {})
        
        # Mock config resolver properties using PropertyMock
        with patch.object(type(context._config_resolver), 'workspace_path', new_callable=PropertyMock) as mock_workspace, \
             patch.object(type(context._config_resolver), 'contest_current_path', new_callable=PropertyMock) as mock_current, \
             patch.object(type(context._config_resolver), 'contest_template_path', new_callable=PropertyMock) as mock_template, \
             patch.object(type(context._config_resolver), 'contest_temp_path', new_callable=PropertyMock) as mock_temp, \
             patch.object(type(context._config_resolver), 'source_file_name', new_callable=PropertyMock) as mock_source:
            
            mock_workspace.return_value = "/test/workspace"
            mock_current.return_value = "/test/current"
            mock_template.return_value = "/test/template"
            mock_temp.return_value = "/test/temp"
            mock_source.return_value = "main.py"
            
            assert context.workspace_path == "/test/workspace"
            assert context.contest_current_path == "/test/current"
            assert context.contest_template_path == "/test/template"
            assert context.contest_temp_path == "/test/temp"
            assert context.source_file_name == "main.py"
    
    def test_contest_stock_path_with_node(self):
        """Test contest_stock_path with valid node"""
        context = ExecutionContext("build", "python", "abc", "a", "local", {})
        
        mock_node = Mock()
        mock_node.value = "/test/stock/path"
        
        with patch.object(context, 'resolve') as mock_resolve:
            mock_resolve.return_value = mock_node
            
            result = context.contest_stock_path
            
            assert result == "/test/stock/path"
            mock_resolve.assert_called_once_with(["python", "contest_stock_path"])
    
    def test_contest_stock_path_without_node(self):
        """Test contest_stock_path with no node"""
        context = ExecutionContext("build", "python", "abc", "a", "local", {})
        
        with patch.object(context, 'resolve') as mock_resolve:
            mock_resolve.return_value = None
            
            result = context.contest_stock_path
            
            assert result is None
    
    def test_language_id_with_node(self):
        """Test language_id with valid node"""
        context = ExecutionContext("build", "python", "abc", "a", "local", {})
        
        mock_node = Mock()
        mock_node.value = "python3.9"
        
        with patch.object(context, 'resolve') as mock_resolve:
            mock_resolve.return_value = mock_node
            
            result = context.language_id
            
            assert result == "python3.9"
            mock_resolve.assert_called_once_with(["python", "language_id"])
    
    def test_language_id_without_node(self):
        """Test language_id with no node"""
        context = ExecutionContext("build", "python", "abc", "a", "local", {})
        
        with patch.object(context, 'resolve') as mock_resolve:
            mock_resolve.return_value = None
            
            result = context.language_id
            
            assert result is None
    
    def test_get_steps(self):
        """Test get_steps method"""
        context = ExecutionContext("build", "python", "abc", "a", "local", {})
        
        expected_steps = [Mock(), Mock(), Mock()]
        context._config_resolver.get_steps = Mock(return_value=expected_steps)
        
        result = context.get_steps()
        
        assert result == expected_steps
        context._config_resolver.get_steps.assert_called_once()
    
    @patch('src.utils.path_operations.DockerPathOperations.get_docker_mount_path_from_config')
    def test_get_docker_mount_path(self, mock_get_mount_path):
        """Test get_docker_mount_path method"""
        context = ExecutionContext("build", "python", "abc", "a", "local", {"docker": {"mount": "/test"}})
        
        mock_get_mount_path.return_value = "/docker/mount/path"
        
        result = context.get_docker_mount_path()
        
        assert result == "/docker/mount/path"
        mock_get_mount_path.assert_called_once_with(
            {"docker": {"mount": "/test"}},
            "python",
            '/workspace'
        )
    
    @patch('src.context.execution_context.get_docker_naming_from_data')
    def test_get_docker_names_with_dockerfile_resolver(self, mock_get_naming):
        """Test get_docker_names with dockerfile resolver"""
        context = ExecutionContext("build", "python", "abc", "a", "docker", {})
        
        # Setup dockerfile resolver
        mock_resolver = Mock(spec=DockerfileResolver)
        mock_resolver.dockerfile = "FROM python:3.9"
        mock_resolver.oj_dockerfile = "FROM oj-tools:latest"
        context.dockerfile_resolver = mock_resolver
        
        expected_names = {
            "image_name": "test_image",
            "container_name": "test_container",
            "oj_image_name": "oj_test_image",
            "oj_container_name": "oj_test_container"
        }
        mock_get_naming.return_value = expected_names
        
        result = context.get_docker_names()
        
        assert result == expected_names
        
        # Verify the pure function was called with correct parameters
        mock_get_naming.assert_called_once()
        call_args = mock_get_naming.call_args[0]
        
        # Check ExecutionFormatData
        assert isinstance(call_args[0], ExecutionFormatData)
        assert call_args[0].command_type == "build"
        assert call_args[0].language == "python"
        assert call_args[0].env_type == "docker"
        
        # Check dockerfile contents
        assert call_args[1] == "FROM python:3.9"
        assert call_args[2] == "FROM oj-tools:latest"
    
    @patch('src.context.execution_context.get_docker_naming_from_data')
    def test_get_docker_names_without_dockerfile_resolver(self, mock_get_naming):
        """Test get_docker_names without dockerfile resolver"""
        context = ExecutionContext("build", "rust", "atcoder", "b", "local", {})
        
        expected_names = {"image_name": "rust_image"}
        mock_get_naming.return_value = expected_names
        
        result = context.get_docker_names()
        
        assert result == expected_names
        
        # Verify dockerfile contents are None
        call_args = mock_get_naming.call_args[0]
        assert call_args[1] is None  # dockerfile_content
        assert call_args[2] is None  # oj_dockerfile_content
    
    @patch('src.context.execution_context.validate_execution_data')
    def test_validate_calls_pure_function(self, mock_validate):
        """Test that validate method calls pure function with correct data"""
        context = ExecutionContext("test", "rust", "contest", "problem", "docker", {"test": "config"})
        
        mock_validate.return_value = (True, None)
        
        is_valid, error = context.validate()
        
        assert is_valid is True
        assert error is None
        
        # Verify pure function was called with ExecutionFormatData
        mock_validate.assert_called_once()
        call_args = mock_validate.call_args[0][0]
        assert isinstance(call_args, ExecutionFormatData)
        assert call_args.command_type == "test"
        assert call_args.language == "rust"
        assert call_args.contest_name == "contest"
        assert call_args.problem_name == "problem"
        assert call_args.env_type == "docker"
        assert call_args.env_json == {"test": "config"}
    
    @patch('src.context.execution_context.validate_execution_data')
    def test_validate_with_error(self, mock_validate):
        """Test validate method with validation error"""
        context = ExecutionContext("", "python", "", "", "local", {})
        
        mock_validate.return_value = (False, "Multiple validation errors")
        
        is_valid, error = context.validate()
        
        assert is_valid is False
        assert error == "Multiple validation errors"
    
    @patch('src.context.execution_context.create_format_dict')
    def test_to_format_dict_calls_pure_function(self, mock_create_format):
        """Test that to_format_dict calls pure function"""
        context = ExecutionContext("build", "python", "abc", "a", "docker", {"key": "value"})
        
        expected_dict = {
            "command_type": "build",
            "language": "python",
            "contest_name": "abc",
            "problem_name": "a",
            "env_type": "docker"
        }
        mock_create_format.return_value = expected_dict
        
        result = context.to_format_dict()
        
        assert result == expected_dict
        
        # Verify pure function was called with ExecutionFormatData
        mock_create_format.assert_called_once()
        call_args = mock_create_format.call_args[0][0]
        assert isinstance(call_args, ExecutionFormatData)
        assert call_args.env_json == {"key": "value"}
    
    @patch('src.context.execution_context.format_template_string')
    def test_format_string_calls_pure_function(self, mock_format_template):
        """Test that format_string calls pure function"""
        context = ExecutionContext("run", "java", "contest", "c", "local", {})
        
        template = "Running {language} for {contest_name}/{problem_name}"
        formatted_result = "Running java for contest/c"
        mock_format_template.return_value = (formatted_result, [])
        
        result = context.format_string(template)
        
        assert result == formatted_result
        
        # Verify pure function was called correctly
        mock_format_template.assert_called_once()
        call_args = mock_format_template.call_args
        assert call_args[0][0] == template
        assert isinstance(call_args[0][1], ExecutionFormatData)
        assert call_args[0][1].language == "java"
        assert call_args[0][1].contest_name == "contest"


class TestExecutionContextEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_string_parameters(self):
        """Test with empty string parameters"""
        context = ExecutionContext("", "", "", "", "", {})
        
        assert context.command_type == ""
        assert context.language == ""
        assert context.contest_name == ""
        assert context.problem_name == ""
        assert context.env_type == ""
    
    def test_none_env_json(self):
        """Test with None env_json"""
        context = ExecutionContext("build", "python", "abc", "a", "local", None)
        
        # Should handle None gracefully
        assert context.env_json is None
    
    def test_unicode_parameters(self):
        """Test with Unicode characters in parameters"""
        context = ExecutionContext(
            "ビルド",
            "パイソン", 
            "コンテスト",
            "問題A",
            "ローカル",
            {"キー": "値", "日本語": "テスト"}
        )
        
        assert context.command_type == "ビルド"
        assert context.language == "パイソン"
        assert context.contest_name == "コンテスト"
        assert context.problem_name == "問題A"
        assert context.env_type == "ローカル"
        assert context.env_json["キー"] == "値"
    
    def test_large_env_json(self):
        """Test with large env_json"""
        large_env = {f"key_{i}": f"value_{i}" for i in range(1000)}
        context = ExecutionContext("build", "python", "abc", "a", "local", large_env)
        
        assert len(context.env_json) == 1000
        assert context.env_json["key_999"] == "value_999"
    
    def test_nested_env_json(self):
        """Test with deeply nested env_json"""
        nested_env = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "value": "deep_value"
                        }
                    }
                }
            }
        }
        context = ExecutionContext("build", "python", "abc", "a", "local", nested_env)
        
        assert context.env_json["level1"]["level2"]["level3"]["level4"]["value"] == "deep_value"
    
    def test_special_characters_in_names(self):
        """Test with special characters in names"""
        context = ExecutionContext(
            "build-test",
            "python-3.9",
            "abc-123",
            "problem_a",
            "docker.local",
            {"special-key": "special_value"}
        )
        
        assert context.command_type == "build-test"
        assert context.language == "python-3.9"
        assert context.contest_name == "abc-123"
        assert context.problem_name == "problem_a"
        assert context.env_type == "docker.local"
    
    def test_property_modification_after_creation(self):
        """Test modifying properties after context creation"""
        context = ExecutionContext("build", "python", "abc", "a", "local", {})
        
        # Modify multiple properties
        context.command_type = "test"
        context.language = "rust"
        context.contest_name = "new_contest"
        context.problem_name = "new_problem"
        context.env_type = "docker"
        context.env_json = {"new": "config"}
        
        # Verify all changes
        assert context.command_type == "test"
        assert context.language == "rust"
        assert context.contest_name == "new_contest"
        assert context.problem_name == "new_problem"
        assert context.env_type == "docker"
        assert context.env_json == {"new": "config"}
    
    def test_resolver_none_assignment(self):
        """Test assigning None to resolver"""
        context = ExecutionContext("build", "python", "abc", "a", "local", {})
        
        # Set resolver to None
        context.resolver = None
        assert context.resolver is None
    
    def test_dockerfile_resolver_none_assignment(self):
        """Test assigning None to dockerfile_resolver"""
        context = ExecutionContext("build", "python", "abc", "a", "local", {})
        
        # Set dockerfile resolver
        mock_resolver = Mock(spec=DockerfileResolver)
        context.dockerfile_resolver = mock_resolver
        assert context.dockerfile_resolver == mock_resolver
        
        # Set back to None
        context.dockerfile_resolver = None
        assert context.dockerfile_resolver is None
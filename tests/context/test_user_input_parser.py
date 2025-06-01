"""
Test user input parser
"""
import pytest
import json
import os
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from src.context.user_input_parser import (
    parse_user_input,
    _load_all_env_jsons,
    _apply_env_json,
    _apply_dockerfile_resolver,
    make_dockerfile_loader,
    CONTEST_ENV_DIR
)
from src.context.execution_context import ExecutionContext


class TestLoadAllEnvJsons:
    """Test _load_all_env_jsons function"""
    
    def test_load_all_env_jsons_directory_not_exists(self):
        """Test loading when directory doesn't exist"""
        mock_operations = MagicMock()
        mock_file_driver = MagicMock()
        mock_operations.resolve.return_value = mock_file_driver
        
        # Mock file exists to return False
        mock_result = MagicMock()
        mock_result.exists = False
        mock_file_driver.execute.return_value = mock_result
        
        env_jsons = _load_all_env_jsons("/nonexistent", mock_operations)
        
        assert env_jsons == []
    
    @patch('glob.glob')
    def test_load_all_env_jsons_success(self, mock_glob):
        """Test successful loading of env JSONs"""
        mock_operations = MagicMock()
        mock_file_driver = MagicMock()
        mock_operations.resolve.return_value = mock_file_driver
        
        # Mock file paths
        mock_glob.return_value = [
            "/contest_env/python/env.json",
            "/contest_env/rust/env.json"
        ]
        
        # Mock file operations
        exists_result = MagicMock()
        exists_result.exists = True
        
        python_env = {"python": {"language_name": "Python"}}
        rust_env = {"rust": {"language_name": "Rust"}}
        
        # Mock file operations - first call is exists, then reads
        read_result1 = MagicMock()
        read_result1.content = json.dumps(python_env)
        read_result2 = MagicMock()
        read_result2.content = json.dumps(rust_env)
        
        # Create mock FileRequest instances
        mock_requests = []
        
        def create_file_request(op_type, path):
            mock_req = MagicMock()
            if len(mock_requests) == 0:  # First call is exists check
                mock_req.execute.return_value = exists_result
            elif len(mock_requests) == 1:  # Second call reads python env
                mock_req.execute.return_value = read_result1
            elif len(mock_requests) == 2:  # Third call reads rust env
                mock_req.execute.return_value = read_result2
            mock_requests.append(mock_req)
            return mock_req
        
        # Patch FileRequest where it's imported
        with patch('src.operations.file.file_request.FileRequest', side_effect=create_file_request):
        
            with patch('src.context.user_input_parser.ValidationService.validate_env_json'):
                env_jsons = _load_all_env_jsons(CONTEST_ENV_DIR, mock_operations)
        
        assert len(env_jsons) == 2
        assert env_jsons[0] == python_env
        assert env_jsons[1] == rust_env
    
    @patch('glob.glob')
    @patch('builtins.print')
    def test_load_all_env_jsons_with_invalid_json(self, mock_print, mock_glob):
        """Test loading with invalid JSON file"""
        mock_operations = MagicMock()
        mock_file_driver = MagicMock()
        mock_operations.resolve.return_value = mock_file_driver
        
        mock_glob.return_value = ["/contest_env/invalid/env.json"]
        
        exists_result = MagicMock()
        exists_result.exists = True
        
        read_result = MagicMock()
        read_result.content = "invalid json"
        
        mock_file_driver.execute.side_effect = [exists_result, read_result]
        
        env_jsons = _load_all_env_jsons(CONTEST_ENV_DIR, mock_operations)
        
        assert env_jsons == []
        mock_print.assert_called_once()
        assert "Warning: Failed to load" in mock_print.call_args[0][0]


class TestApplyEnvJson:
    """Test _apply_env_json function"""
    
    def test_apply_env_json_already_set(self):
        """Test when env_json is already set"""
        context = MagicMock()
        context.env_json = {"existing": "data"}
        env_jsons = [{"python": {"new": "data"}}]
        
        result = _apply_env_json(context, env_jsons)
        
        assert result.env_json == {"existing": "data"}
    
    def test_apply_env_json_with_language_match(self):
        """Test applying env_json when language matches"""
        context = MagicMock()
        context.env_json = None
        context.language = "python"
        
        env_jsons = [
            {"rust": {"language_name": "Rust"}},
            {"python": {"language_name": "Python"}}
        ]
        
        result = _apply_env_json(context, env_jsons)
        
        assert result.env_json == {"python": {"language_name": "Python"}}
    
    def test_apply_env_json_no_match(self):
        """Test when no language matches"""
        context = MagicMock()
        context.env_json = None
        context.language = "go"
        
        env_jsons = [
            {"rust": {"language_name": "Rust"}},
            {"python": {"language_name": "Python"}}
        ]
        
        result = _apply_env_json(context, env_jsons)
        
        assert result.env_json is None


class TestApplyDockerfileResolver:
    """Test _apply_dockerfile_resolver function"""
    
    def test_apply_dockerfile_resolver_no_env_json(self):
        """Test when env_json is not set"""
        context = MagicMock()
        context.env_json = None
        mock_operations = MagicMock()
        
        result = _apply_dockerfile_resolver(context, mock_operations)
        
        assert result == context
        assert hasattr(result, 'dockerfile_resolver')
    
    def test_apply_dockerfile_resolver_with_path(self):
        """Test creating resolver when dockerfile path is specified"""
        context = MagicMock()
        context.env_json = {
            "python": {
                "env_types": {
                    "docker": {
                        "dockerfile_path": "/path/to/Dockerfile"
                    }
                }
            }
        }
        context.language = "python"
        context.env_type = "docker"
        mock_operations = MagicMock()
        
        result = _apply_dockerfile_resolver(context, mock_operations)
        
        assert result == context
        assert hasattr(result, 'dockerfile_resolver')
        assert result.dockerfile_resolver is not None


class TestMakeDockerfileLoader:
    """Test make_dockerfile_loader function"""
    
    def test_make_dockerfile_loader(self):
        """Test creating dockerfile loader"""
        mock_operations = MagicMock()
        mock_file_driver = MagicMock()
        mock_operations.resolve.return_value = mock_file_driver
        
        mock_result = MagicMock()
        mock_result.content = "Dockerfile content"
        # Create loader first
        loader = make_dockerfile_loader(mock_operations)
        
        # Mock the FileRequest import where it's used
        mock_request = MagicMock()
        mock_request.execute.return_value = mock_result
        
        with patch('src.operations.file.file_request.FileRequest', return_value=mock_request):
            content = loader("/path/to/Dockerfile")
        
        assert content == "Dockerfile content"
        mock_operations.resolve.assert_called_once_with("file_driver")


class TestParseUserInput:
    """Test parse_user_input function"""
    
    @patch('src.context.user_input_parser.SystemInfoManager')
    @patch('src.context.user_input_parser.ValidationService')
    @patch('src.context.user_input_parser._load_all_env_jsons')
    @patch('src.context.user_input_parser.create_config_root_from_dict')
    @patch('src.context.user_input_parser.InputParser')
    @patch('src.context.user_input_parser._apply_env_json')
    @patch('src.context.user_input_parser._apply_dockerfile')
    @patch('src.context.user_input_parser._apply_oj_dockerfile')
    def test_parse_user_input_success(
        self,
        mock_apply_oj,
        mock_apply_dockerfile,
        mock_apply_env_json,
        mock_input_parser,
        mock_create_root,
        mock_load_env_jsons,
        mock_validation_service,
        mock_system_info_manager
    ):
        """Test successful user input parsing"""
        # Setup mocks
        mock_operations = MagicMock()
        
        # Mock system info
        mock_system_info = {
            "command": "test",
            "language": "python",
            "contest_name": "abc300",
            "problem_name": "a",
            "env_type": "local",
            "env_json": None
        }
        mock_system_info_manager.return_value.load_system_info.return_value = mock_system_info
        
        # Mock env jsons
        mock_env_jsons = [{"python": {"language_name": "Python"}}]
        mock_load_env_jsons.return_value = mock_env_jsons
        
        # Mock config root
        mock_root = MagicMock()
        mock_create_root.return_value = mock_root
        
        # Mock input parser
        mock_input_parser.parse_command_line.return_value = ([], MagicMock())
        
        # Mock context validation
        mock_context = MagicMock()
        mock_context.validate.return_value = (True, None)
        
        # Setup side effects to return modified context
        def apply_env_json_side_effect(ctx, env_jsons):
            ctx.env_json = {"python": {"language_name": "Python"}}
            return ctx
        
        def apply_dockerfile_side_effect(ctx, loader):
            ctx.dockerfile = "FROM python:3.8"
            return ctx
        
        def apply_oj_dockerfile_side_effect(ctx):
            ctx.oj_dockerfile = "OJ Dockerfile"
            return ctx
        
        mock_apply_env_json.side_effect = apply_env_json_side_effect
        mock_apply_dockerfile.side_effect = apply_dockerfile_side_effect
        mock_apply_oj.side_effect = apply_oj_dockerfile_side_effect
        
        # Create proper ExecutionContext mock that returns itself from apply functions
        mock_context = MagicMock()
        mock_context.validate.return_value = (True, None)
        mock_context.command_type = "test"
        mock_context.language = "python"
        mock_context.contest_name = "abc300"
        mock_context.problem_name = "a"
        mock_context.env_type = "local"
        mock_context.env_json = None
        
        # Make apply functions return the context
        mock_apply_env_json.return_value = mock_context
        mock_apply_dockerfile.return_value = mock_context  
        mock_apply_oj.return_value = mock_context
        
        # Make parse_command_line return empty args and the context
        mock_input_parser.parse_command_line.return_value = ([], mock_context)
        
        with patch('src.context.user_input_parser.ExecutionContext', return_value=mock_context):
            result = parse_user_input(["py", "local", "t", "abc300", "a"], mock_operations)
        
        # Verify system info was saved
        mock_system_info_manager.return_value.save_system_info.assert_called_once()
    
    @patch('src.context.user_input_parser.SystemInfoManager')
    @patch('src.context.user_input_parser._load_all_env_jsons')
    @patch('src.context.user_input_parser.create_config_root_from_dict')
    @patch('src.context.user_input_parser.InputParser')
    def test_parse_user_input_too_many_args(
        self,
        mock_input_parser,
        mock_create_root,
        mock_load_env_jsons,
        mock_system_info_manager
    ):
        """Test parsing with too many arguments"""
        mock_operations = MagicMock()
        
        mock_system_info = {
            "command": "test",
            "language": "python",
            "contest_name": "abc300",
            "problem_name": "a",
            "env_type": "local",
            "env_json": None
        }
        mock_system_info_manager.return_value.load_system_info.return_value = mock_system_info
        
        mock_load_env_jsons.return_value = []
        mock_create_root.return_value = MagicMock()
        
        # Return extra arguments
        mock_input_parser.parse_command_line.return_value = (["extra", "args"], MagicMock())
        
        with patch('src.context.user_input_parser.ExecutionContext'):
            with pytest.raises(ValueError, match="引数が多すぎます"):
                parse_user_input(["py", "local", "t", "abc300", "a", "extra", "args"], mock_operations)
    
    @patch('src.context.user_input_parser.SystemInfoManager')
    @patch('src.context.user_input_parser._load_all_env_jsons')
    @patch('src.context.user_input_parser.create_config_root_from_dict')
    @patch('src.context.user_input_parser.InputParser')
    @patch('src.context.user_input_parser._apply_env_json')
    @patch('src.context.user_input_parser._apply_dockerfile')
    @patch('src.context.user_input_parser._apply_oj_dockerfile')
    def test_parse_user_input_validation_fails(
        self,
        mock_apply_oj,
        mock_apply_dockerfile,
        mock_apply_env_json,
        mock_input_parser,
        mock_create_root,
        mock_load_env_jsons,
        mock_system_info_manager
    ):
        """Test parsing when validation fails"""
        mock_operations = MagicMock()
        
        mock_system_info = {
            "command": "test",
            "language": "python",
            "contest_name": "abc300",
            "problem_name": "a",
            "env_type": "local",
            "env_json": None
        }
        mock_system_info_manager.return_value.load_system_info.return_value = mock_system_info
        
        mock_load_env_jsons.return_value = []
        mock_create_root.return_value = MagicMock()
        mock_input_parser.parse_command_line.return_value = ([], MagicMock())
        
        # Make validation fail
        mock_context = MagicMock()
        mock_context.validate.return_value = (False, "Validation error message")
        
        # Setup side effects
        mock_apply_env_json.side_effect = lambda ctx, env_jsons: ctx
        mock_apply_dockerfile.side_effect = lambda ctx, loader: ctx
        mock_apply_oj.side_effect = lambda ctx: ctx
        
        # Make parse_command_line return empty args and the context
        mock_input_parser.parse_command_line.return_value = ([], mock_context)
        
        with patch('src.context.user_input_parser.ExecutionContext', return_value=mock_context):
            with pytest.raises(ValueError, match="Validation error message"):
                parse_user_input(["py", "local", "t", "abc300", "a"], mock_operations)
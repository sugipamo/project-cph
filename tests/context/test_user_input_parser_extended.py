"""Extended tests for user input parser."""
import json
import os
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.configuration.adapters.execution_context_adapter import ExecutionContextAdapter
from src.configuration.integration.user_input_parser_integration import create_new_execution_context
from src.context.user_input_parser import (
    _apply_command,
    _apply_contest_name,
    _apply_env_json,
    _apply_env_type,
    _apply_language,
    _apply_problem_name,
    _load_all_env_jsons,
    _load_current_context_sqlite,
    _load_shared_config,
    _merge_with_shared_config,
    _parse_command_line_args,
    _save_current_context_sqlite,
    make_dockerfile_loader,
    parse_user_input,
)


class TestUserInputParserHelpers:
    """Test helper functions in user input parser."""

    def test_load_current_context_sqlite(self):
        """Test loading current context from SQLite."""
        mock_operations = MagicMock()
        mock_config_loader = MagicMock()
        mock_context = {
            "command": "test",
            "language": "python",
            "env_type": "local",
            "contest_name": "abc123",
            "problem_name": "a"
        }
        mock_config = {"env_json": {"test": "data"}}

        mock_config_loader.get_current_context.return_value = mock_context
        mock_config_loader.load_config.return_value = mock_config

        with patch('src.context.user_input_parser.SystemConfigLoader', return_value=mock_config_loader):
            result = _load_current_context_sqlite(mock_operations)

        assert result["command"] == "test"
        assert result["language"] == "python"
        assert result["env_type"] == "local"
        assert result["contest_name"] == "abc123"
        assert result["problem_name"] == "a"
        assert result["env_json"] == {"test": "data"}

    def test_save_current_context_sqlite(self):
        """Test saving current context to SQLite."""
        mock_operations = MagicMock()
        mock_config_loader = MagicMock()
        context_info = {
            "command": "test",
            "language": "python",
            "env_type": "local",
            "contest_name": "abc123",
            "problem_name": "a",
            "env_json": {"test": "data"}
        }

        with patch('src.context.user_input_parser.SystemConfigLoader', return_value=mock_config_loader):
            _save_current_context_sqlite(mock_operations, context_info)

        mock_config_loader.update_current_context.assert_called_once_with(
            command="test",
            language="python",
            env_type="local",
            contest_name="abc123",
            problem_name="a"
        )
        mock_config_loader.save_config.assert_called_once_with(
            "env_json", {"test": "data"}, "environment"
        )

    def test_save_current_context_sqlite_no_env_json(self):
        """Test saving context without env_json."""
        mock_operations = MagicMock()
        mock_config_loader = MagicMock()
        context_info = {
            "command": "test",
            "language": "python",
            "env_type": "local",
            "contest_name": "abc123",
            "problem_name": "a"
        }

        with patch('src.context.user_input_parser.SystemConfigLoader', return_value=mock_config_loader):
            _save_current_context_sqlite(mock_operations, context_info)

        mock_config_loader.update_current_context.assert_called_once()
        mock_config_loader.save_config.assert_not_called()

    def test_apply_language(self):
        """Test language application from arguments."""
        mock_root = MagicMock()
        mock_lang_node = MagicMock()
        mock_lang_node.matches = ["python", "py"]
        mock_lang_node.key = "python"
        mock_root.next_nodes = [mock_lang_node]

        context = create_new_execution_context(
            command_type=None,
            language=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            env_json={}
        )
        args = ["python", "test", "a"]

        new_args, new_context = _apply_language(args, context, mock_root)

        assert new_args == ["test", "a"]
        assert new_context.language == "python"

    def test_apply_language_no_match(self):
        """Test language application with no match."""
        mock_root = MagicMock()
        mock_lang_node = MagicMock()
        mock_lang_node.matches = ["cpp", "c++"]
        mock_lang_node.key = "cpp"
        mock_root.next_nodes = [mock_lang_node]

        context = create_new_execution_context(
            command_type=None,
            language="existing",
            contest_name=None,
            problem_name=None,
            env_type=None,
            env_json={}
        )
        args = ["python", "test", "a"]

        new_args, new_context = _apply_language(args, context, mock_root)

        assert new_args == ["python", "test", "a"]
        assert new_context.language == "existing"

    def test_apply_env_type(self):
        """Test env_type application."""
        mock_root = MagicMock()
        context = create_new_execution_context(
            command_type=None,
            language="python",
            contest_name=None,
            problem_name=None,
            env_type=None,
            env_json={}
        )

        mock_env_node = MagicMock()
        mock_env_node.next_nodes = [MagicMock()]
        mock_env_node.next_nodes[0].matches = ["local"]
        mock_env_node.next_nodes[0].key = "local"

        with patch('src.context.user_input_parser.resolve_by_match_desc', return_value=[mock_env_node]):
            args = ["local", "test", "a"]
            new_args, new_context = _apply_env_type(args, context, mock_root)

        assert new_args == ["test", "a"]
        assert new_context.env_type == "local"

    def test_apply_env_type_no_language(self):
        """Test env_type application with no language set."""
        mock_root = MagicMock()
        context = create_new_execution_context(
            command_type=None,
            language=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            env_json={}
        )
        args = ["local", "test", "a"]

        new_args, new_context = _apply_env_type(args, context, mock_root)

        assert new_args == ["local", "test", "a"]
        assert new_context.env_type is None

    def test_apply_command(self):
        """Test command application."""
        mock_root = MagicMock()
        context = create_new_execution_context(
            command_type=None,
            language="python",
            contest_name=None,
            problem_name=None,
            env_type=None,
            env_json={}
        )

        mock_cmd_node = MagicMock()
        mock_cmd_node.next_nodes = [MagicMock()]
        mock_cmd_node.next_nodes[0].matches = ["test"]
        mock_cmd_node.next_nodes[0].key = "test"

        with patch('src.context.user_input_parser.resolve_by_match_desc', return_value=[mock_cmd_node]):
            args = ["test", "abc123", "a"]
            new_args, new_context = _apply_command(args, context, mock_root)

        assert new_args == ["abc123", "a"]
        assert new_context.command_type == "test"

    def test_apply_problem_name(self):
        """Test problem name application."""
        context = create_new_execution_context(
            command_type=None,
            language=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            env_json={}
        )
        args = ["abc123", "a"]

        new_args, new_context = _apply_problem_name(args, context)

        assert new_args == ["abc123"]
        assert new_context.problem_name == "a"

    def test_apply_problem_name_empty_args(self):
        """Test problem name application with empty args."""
        context = create_new_execution_context(
            command_type=None,
            language=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            env_json={}
        )
        args = []

        new_args, new_context = _apply_problem_name(args, context)

        assert new_args == []
        assert new_context.problem_name is None

    def test_apply_contest_name(self):
        """Test contest name application."""
        context = create_new_execution_context(
            command_type=None,
            language=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            env_json={}
        )
        args = ["abc123"]

        new_args, new_context = _apply_contest_name(args, context)

        assert new_args == []
        assert new_context.contest_name == "abc123"

    def test_load_shared_config_success(self):
        """Test loading shared config successfully."""
        mock_operations = MagicMock()
        mock_file_driver = MagicMock()
        mock_operations.resolve.return_value = mock_file_driver

        mock_result = MagicMock()
        mock_result.content = '{"shared": {"test": "value"}}'

        with patch('src.context.user_input_parser.FileRequest') as mock_file_request:
            mock_request = MagicMock()
            mock_request.execute_operation.return_value = mock_result
            mock_file_request.return_value = mock_request

            result = _load_shared_config("base_dir", mock_operations)

        assert result == {"shared": {"test": "value"}}

    def test_load_shared_config_failure(self):
        """Test loading shared config with failure."""
        mock_operations = MagicMock()
        mock_file_driver = MagicMock()
        mock_operations.resolve.return_value = mock_file_driver

        with patch('src.context.user_input_parser.FileRequest') as mock_file_request:
            mock_request = MagicMock()
            mock_request.execute_operation.side_effect = Exception("File error")
            mock_file_request.return_value = mock_request

            result = _load_shared_config("base_dir", mock_operations)

        assert result is None

    @patch('glob.glob')
    def test_load_all_env_jsons(self, mock_glob):
        """Test loading all env JSON files."""
        mock_operations = MagicMock()
        mock_file_driver = MagicMock()
        mock_operations.resolve.return_value = mock_file_driver

        # Mock directory existence check
        mock_exists_result = MagicMock()
        mock_exists_result.exists = True

        # Mock file content
        mock_content_result = MagicMock()
        mock_content_result.content = '{"python": {"test": "value"}}'

        mock_glob.return_value = ["/path/to/contest/env.json"]

        with patch('src.context.user_input_parser.FileRequest') as mock_file_request:
            def side_effect(*args, **kwargs):
                mock_request = MagicMock()
                if args[0].name == "EXISTS":
                    mock_request.execute_operation.return_value = mock_exists_result
                else:  # READ
                    mock_request.execute_operation.return_value = mock_content_result
                return mock_request

            mock_file_request.side_effect = side_effect

            with patch('src.context.user_input_parser._load_shared_config', return_value=None), \
                 patch('src.context.user_input_parser.ValidationService'):
                    result = _load_all_env_jsons("base_dir", mock_operations)

        assert len(result) == 1
        assert result[0] == {"python": {"test": "value"}}

    def test_merge_with_shared_config(self):
        """Test merging env.json with shared config."""
        env_json = {
            "python": {
                "commands": {"test": "pytest"}
            }
        }
        shared_config = {
            "shared": {
                "paths": {"base": "/base"},
                "output": {"format": "json"}
            }
        }

        result = _merge_with_shared_config(env_json, shared_config)

        assert result["shared"] == shared_config["shared"]
        assert result["python"]["base"] == "/base"
        assert result["python"]["output"]["format"] == "json"

    def test_merge_with_shared_config_no_shared(self):
        """Test merging with no shared config."""
        env_json = {"python": {"test": "value"}}

        result = _merge_with_shared_config(env_json, None)
        assert result == env_json

        result = _merge_with_shared_config(env_json, {"other": "data"})
        assert result == env_json

    def test_apply_env_json(self):
        """Test applying env JSON to context."""
        context = create_new_execution_context(
            command_type=None,
            language="python",
            contest_name=None,
            problem_name=None,
            env_type=None,
            env_json={}
        )

        env_jsons = [
            {"python": {"test": "value1"}},
            {"cpp": {"test": "value2"}}
        ]

        # Mock JsonConfigLoader to return the expected merged configuration
        with patch('src.context.user_input_parser.JsonConfigLoader') as mock_loader:
            mock_instance = MagicMock()
            mock_loader.return_value = mock_instance
            mock_instance.get_language_config.return_value = {"test": "value1", "other": "merged_value"}

            result_context = _apply_env_json(context, env_jsons, "base_dir", MagicMock())

        # New implementation returns merged config directly (no language wrapper)
        assert result_context.env_json["test"] == "value1"
        assert result_context.env_json["other"] == "merged_value"

    def test_make_dockerfile_loader(self):
        """Test dockerfile loader creation."""
        mock_operations = MagicMock()
        mock_file_driver = MagicMock()
        mock_operations.resolve.return_value = mock_file_driver

        mock_result = MagicMock()
        mock_result.content = "FROM ubuntu"

        with patch('src.context.user_input_parser.FileRequest') as mock_file_request:
            mock_request = MagicMock()
            mock_request.execute_operation.return_value = mock_result
            mock_file_request.return_value = mock_request

            loader = make_dockerfile_loader(mock_operations)
            result = loader("/path/to/dockerfile")

        assert result == "FROM ubuntu"


class TestParseUserInputIntegration:
    """Test parse_user_input function integration."""

    @patch('src.context.user_input_parser._load_current_context_sqlite')
    @patch('src.context.user_input_parser._load_all_env_jsons')
    @patch('src.context.user_input_parser.create_config_root_from_dict')
    @patch('src.context.user_input_parser._save_current_context_sqlite')
    @patch('src.context.user_input_parser.DockerfileResolver')
    @patch('src.context.user_input_parser.ValidationService')
    def test_parse_user_input_basic(self, mock_validation_service, mock_dockerfile_resolver,
                                  mock_save_context, mock_create_root, mock_load_env_jsons,
                                  mock_load_context):
        """Test basic parse_user_input functionality."""
        # Setup mocks
        mock_operations = MagicMock()
        mock_context_info = {
            "command": None,
            "language": None,
            "env_type": None,
            "contest_name": None,
            "problem_name": None,
            "env_json": None
        }
        mock_env_jsons = [{"python": {"commands": {"test": "pytest"}}}]
        mock_root = MagicMock()
        mock_root.next_nodes = []

        mock_load_context.return_value = mock_context_info
        mock_load_env_jsons.return_value = mock_env_jsons
        mock_create_root.return_value = mock_root

        # Mock validation
        mock_validation_service.return_value = MagicMock()

        # Mock dockerfile resolver
        mock_resolver_instance = MagicMock()
        mock_dockerfile_resolver.return_value = mock_resolver_instance

        # Mock ExecutionContext validation
        with patch.object(ExecutionContextAdapter, 'validate_execution_data', return_value=(True, None)):
            result = parse_user_input([], mock_operations)

        assert isinstance(result, ExecutionContextAdapter)
        assert result.dockerfile_resolver == mock_resolver_instance
        mock_save_context.assert_called_once()

    @patch('src.context.user_input_parser._load_current_context_sqlite')
    @patch('src.context.user_input_parser._load_all_env_jsons')
    @patch('src.context.user_input_parser.create_config_root_from_dict')
    def test_parse_user_input_validation_failure(self, mock_create_root, mock_load_env_jsons, mock_load_context):
        """Test parse_user_input with validation failure."""
        mock_operations = MagicMock()
        mock_context_info = {
            "command": None,
            "language": None,
            "env_type": None,
            "contest_name": None,
            "problem_name": None,
            "env_json": None
        }

        mock_load_context.return_value = mock_context_info
        mock_load_env_jsons.return_value = []
        mock_create_root.return_value = MagicMock()

        with patch('src.context.user_input_parser.ValidationService'), \
             patch.object(ExecutionContextAdapter, 'validate_execution_data', return_value=(False, "Validation error")), \
             pytest.raises(ValueError, match="Validation error"):
            parse_user_input([], mock_operations)

    @patch('src.context.user_input_parser._load_current_context_sqlite')
    @patch('src.context.user_input_parser._load_all_env_jsons')
    @patch('src.context.user_input_parser.create_config_root_from_dict')
    def test_parse_user_input_too_many_args(self, mock_create_root, mock_load_env_jsons, mock_load_context):
        """Test parse_user_input with too many arguments."""
        mock_operations = MagicMock()
        # Provide valid context to pass validation, but with extra args
        mock_context_info = {
            "command": "test",
            "language": "python",
            "env_type": "local",
            "contest_name": "abc123",
            "problem_name": "a",
            "env_json": {"python": {"test": "value"}}
        }
        mock_root = MagicMock()
        mock_root.next_nodes = []

        mock_load_context.return_value = mock_context_info
        mock_load_env_jsons.return_value = [{"python": {"test": "value"}}]
        mock_create_root.return_value = mock_root

        with patch('src.context.user_input_parser.ValidationService'), \
             patch('src.context.user_input_parser.DockerfileResolver'):
                # Mock _parse_command_line_args to return args unchanged with a valid context
                mock_context_with_args = create_new_execution_context(
                    command_type="test",
                    language="python",
                    contest_name="abc123",
                    problem_name="a",
                    env_type="local",
                    env_json={"python": {"test": "value"}}
                )
                with patch('src.context.user_input_parser._parse_command_line_args', return_value=(["extra", "args"], mock_context_with_args)), \
                     patch('src.context.user_input_parser._apply_env_json', return_value=create_new_execution_context(
                        command_type="test",
                        language="python",
                        contest_name="abc123",
                        problem_name="a",
                        env_type="local",
                        env_json={"python": {"test": "value"}}
                    )), \
                     patch.object(ExecutionContextAdapter, 'validate_execution_data', return_value=(True, None)), \
                     pytest.raises(ValueError, match="引数が多すぎます"):
                    parse_user_input(["extra", "args"], mock_operations)

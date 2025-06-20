"""Tests for user input parser module"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.context.user_input_parser.user_input_parser import (
    CONTEST_ENV_DIR,
    _apply_contest_name,
    _apply_problem_name,
    _create_execution_config,
    _load_current_context_sqlite,
    _parse_command_line_args,
    _save_current_context_sqlite,
    _scan_and_apply_command,
    _scan_and_apply_env_type,
    _scan_and_apply_language,
)


class TestCreateExecutionConfig:
    """Tests for _create_execution_config function"""

    @patch('src.context.user_input_parser.user_input_parser.TypeSafeConfigNodeManager')
    def test_create_execution_config_with_all_params(self, mock_manager_class):
        """Test creating execution config with all parameters"""
        mock_infrastructure = Mock()
        mock_manager = Mock()
        mock_config = Mock()

        mock_manager_class.return_value = mock_manager
        mock_manager.create_execution_config.return_value = mock_config

        result = _create_execution_config(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            infrastructure=mock_infrastructure
        )

        # Verify manager initialization
        mock_manager_class.assert_called_once_with(mock_infrastructure)

        # Verify load_from_files call
        mock_manager.load_from_files.assert_called_once_with(
            system_dir="./config/system",
            env_dir=CONTEST_ENV_DIR,
            language="python"
        )

        # Verify create_execution_config call
        mock_manager.create_execution_config.assert_called_once_with(
            contest_name="abc123",
            problem_name="a",
            language="python",
            env_type="docker",
            command_type="test"
        )

        assert result == mock_config

    @patch('src.context.user_input_parser.user_input_parser.TypeSafeConfigNodeManager')
    def test_create_execution_config_with_defaults(self, mock_manager_class):
        """Test creating execution config with default values"""
        mock_infrastructure = Mock()
        mock_manager = Mock()
        mock_config = Mock()

        mock_manager_class.return_value = mock_manager
        mock_manager.create_execution_config.return_value = mock_config

        result = _create_execution_config(infrastructure=mock_infrastructure)

        # Verify defaults are applied
        mock_manager.load_from_files.assert_called_once_with(
            system_dir="./config/system",
            env_dir=CONTEST_ENV_DIR,
            language="python"
        )

        mock_manager.create_execution_config.assert_called_once_with(
            contest_name="",
            problem_name="",
            language="python",
            env_type="local",
            command_type="open"
        )

        assert result == mock_config


class TestSQLiteContextOperations:
    """Tests for SQLite context load/save operations"""

    @patch('src.context.user_input_parser.user_input_parser.SystemConfigLoader')
    def test_load_current_context_sqlite(self, mock_loader_class):
        """Test loading current context from SQLite"""
        mock_infrastructure = Mock()
        mock_loader = Mock()
        mock_context = {
            "command": "test",
            "language": "python",
            "env_type": "docker",
            "contest_name": "abc123",
            "problem_name": "a"
        }

        mock_loader_class.return_value = mock_loader
        mock_loader.get_current_context.return_value = mock_context

        result = _load_current_context_sqlite(mock_infrastructure)

        # Verify loader initialization
        mock_loader_class.assert_called_once_with(mock_infrastructure)

        # Verify method calls
        mock_loader.get_current_context.assert_called_once()
        mock_loader.load_config.assert_called_once()

        # Verify returned data
        assert result == mock_context

    @patch('src.context.user_input_parser.user_input_parser.SystemConfigLoader')
    def test_save_current_context_sqlite(self, mock_loader_class):
        """Test saving current context to SQLite"""
        mock_infrastructure = Mock()
        mock_loader = Mock()
        context_info = {
            "command": "test",
            "language": "python",
            "env_type": "docker",
            "contest_name": "abc123",
            "problem_name": "a"
        }

        mock_loader_class.return_value = mock_loader

        _save_current_context_sqlite(mock_infrastructure, context_info)

        # Verify loader initialization
        mock_loader_class.assert_called_once_with(mock_infrastructure)

        # Verify context update call
        mock_loader.update_current_context.assert_called_once_with(
            command="test",
            language="python",
            env_type="docker",
            contest_name="abc123",
            problem_name="a"
        )


class TestParseCommandLineArgs:
    """Tests for _parse_command_line_args function"""

    @patch('src.context.user_input_parser.user_input_parser._scan_and_apply_language')
    @patch('src.context.user_input_parser.user_input_parser._scan_and_apply_env_type')
    @patch('src.context.user_input_parser.user_input_parser._scan_and_apply_command')
    @patch('src.context.user_input_parser.user_input_parser._apply_problem_name')
    @patch('src.context.user_input_parser.user_input_parser._apply_contest_name')
    def test_parse_command_line_args_sequence(self, mock_contest, mock_problem,
                                            mock_command, mock_env_type, mock_language):
        """Test that command line parsing follows correct sequence"""
        args = ["python", "docker", "test", "abc123", "a"]
        mock_context = Mock()
        mock_root = Mock()
        mock_infrastructure = Mock()

        # Set up chain of function calls
        mock_language.return_value = (["docker", "test", "abc123", "a"], mock_context)
        mock_env_type.return_value = (["test", "abc123", "a"], mock_context)
        mock_command.return_value = (["abc123", "a"], mock_context)
        mock_problem.return_value = (["abc123"], mock_context)
        mock_contest.return_value = ([], mock_context)

        result_args, result_context = _parse_command_line_args(
            args, mock_context, mock_root, mock_infrastructure
        )

        # Verify all functions called in correct order
        mock_language.assert_called_once_with(args, mock_context, mock_root, mock_infrastructure)
        mock_env_type.assert_called_once_with(["docker", "test", "abc123", "a"], mock_context, mock_root, mock_infrastructure)
        mock_command.assert_called_once_with(["test", "abc123", "a"], mock_context, mock_root, mock_infrastructure)
        mock_problem.assert_called_once_with(["abc123", "a"], mock_context, mock_infrastructure)
        mock_contest.assert_called_once_with(["abc123"], mock_context, mock_infrastructure)

        assert result_args == []
        assert result_context == mock_context


class TestScanAndApplyLanguage:
    """Tests for _scan_and_apply_language function"""

    @patch('src.configuration.config_manager.FileLoader')
    @patch('src.context.user_input_parser.user_input_parser._create_execution_config')
    def test_scan_and_apply_language_found(self, mock_create_config, mock_file_loader_class):
        """Test language scanning when language is found in arguments"""
        mock_infrastructure = Mock()
        mock_context = Mock()
        mock_context.command_type = "test"
        mock_context.contest_name = "abc123"
        mock_context.problem_name = "a"
        mock_context.env_type = "docker"

        mock_root = Mock()
        mock_lang_node = Mock()
        mock_lang_node.key = "python"
        mock_lang_node.matches = ["py", "python"]
        mock_root.next_nodes = [mock_lang_node]

        mock_file_loader = Mock()
        mock_file_loader.get_available_languages.return_value = ["python", "cpp"]
        mock_file_loader_class.return_value = mock_file_loader

        mock_new_context = Mock()
        mock_create_config.return_value = mock_new_context

        args = ["py", "docker", "abc123", "a"]
        result_args, result_context = _scan_and_apply_language(
            args, mock_context, mock_root, mock_infrastructure
        )

        # Verify file loader initialization
        mock_file_loader_class.assert_called_once_with(mock_infrastructure)
        mock_file_loader.get_available_languages.assert_called_once_with(Path("contest_env"))

        # Verify new config creation
        mock_create_config.assert_called_once_with(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            infrastructure=mock_infrastructure
        )

        # Verify results
        assert result_args == ["docker", "abc123", "a"]  # "py" removed
        assert result_context == mock_new_context

    @patch('src.configuration.config_manager.FileLoader')
    def test_scan_and_apply_language_not_found(self, mock_file_loader_class):
        """Test language scanning when language is not found in arguments"""
        mock_infrastructure = Mock()
        mock_context = Mock()
        mock_root = Mock()
        mock_root.next_nodes = []

        mock_file_loader = Mock()
        mock_file_loader.get_available_languages.return_value = ["python", "cpp"]
        mock_file_loader_class.return_value = mock_file_loader

        args = ["docker", "test", "abc123", "a"]
        result_args, result_context = _scan_and_apply_language(
            args, mock_context, mock_root, mock_infrastructure
        )

        # Verify original values returned unchanged
        assert result_args == args
        assert result_context == mock_context


class TestScanAndApplyEnvType:
    """Tests for _scan_and_apply_env_type function"""

    @patch('src.context.user_input_parser.user_input_parser.resolve_by_match_desc')
    @patch('src.context.user_input_parser.user_input_parser._create_execution_config')
    def test_scan_and_apply_env_type_found(self, mock_create_config, mock_resolve):
        """Test env type scanning when env type is found in arguments"""
        mock_infrastructure = Mock()
        mock_context = Mock()
        mock_context.language = "python"
        mock_context.command_type = "test"
        mock_context.contest_name = "abc123"
        mock_context.problem_name = "a"

        mock_root = Mock()

        # Mock env type node structure
        mock_env_node = Mock()
        mock_env_node.key = "docker"
        mock_env_node.matches = ["docker", "d"]

        mock_env_type_node = Mock()
        mock_env_type_node.next_nodes = [mock_env_node]

        mock_resolve.return_value = [mock_env_type_node]

        mock_new_context = Mock()
        mock_create_config.return_value = mock_new_context

        args = ["docker", "abc123", "a"]
        result_args, result_context = _scan_and_apply_env_type(
            args, mock_context, mock_root, mock_infrastructure
        )

        # Verify resolution call
        mock_resolve.assert_called_once_with(mock_root, ["python", "env_types"])

        # Verify new config creation
        mock_create_config.assert_called_once_with(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            infrastructure=mock_infrastructure
        )

        # Verify results
        assert result_args == ["abc123", "a"]  # "docker" removed
        assert result_context == mock_new_context

    def test_scan_and_apply_env_type_no_language(self):
        """Test env type scanning when context has no language"""
        mock_infrastructure = Mock()
        mock_context = Mock()
        mock_context.language = None
        mock_root = Mock()

        args = ["docker", "abc123", "a"]
        result_args, result_context = _scan_and_apply_env_type(
            args, mock_context, mock_root, mock_infrastructure
        )

        # Verify original values returned unchanged
        assert result_args == args
        assert result_context == mock_context


class TestScanAndApplyCommand:
    """Tests for _scan_and_apply_command function"""

    @patch('src.context.user_input_parser.user_input_parser.resolve_by_match_desc')
    @patch('src.context.user_input_parser.user_input_parser._create_execution_config')
    def test_scan_and_apply_command_found(self, mock_create_config, mock_resolve):
        """Test command scanning when command is found in arguments"""
        mock_infrastructure = Mock()
        mock_context = Mock()
        mock_context.language = "python"
        mock_context.contest_name = "abc123"
        mock_context.problem_name = "a"
        mock_context.env_type = "docker"

        mock_root = Mock()

        # Mock command node structure
        mock_cmd_node = Mock()
        mock_cmd_node.key = "test"
        mock_cmd_node.matches = ["test", "t"]

        mock_command_node = Mock()
        mock_command_node.next_nodes = [mock_cmd_node]

        mock_resolve.return_value = [mock_command_node]

        mock_new_context = Mock()
        mock_create_config.return_value = mock_new_context

        args = ["test", "abc123", "a"]
        result_args, result_context = _scan_and_apply_command(
            args, mock_context, mock_root, mock_infrastructure
        )

        # Verify resolution call
        mock_resolve.assert_called_once_with(mock_root, ["python", "commands"])

        # Verify new config creation
        mock_create_config.assert_called_once_with(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            infrastructure=mock_infrastructure
        )

        # Verify results
        assert result_args == ["abc123", "a"]  # "test" removed
        assert result_context == mock_new_context


class TestApplyProblemName:
    """Tests for _apply_problem_name function"""

    @patch('src.context.user_input_parser.user_input_parser._create_execution_config')
    def test_apply_problem_name_with_args(self, mock_create_config):
        """Test applying problem name when args are available"""
        mock_infrastructure = Mock()
        mock_context = Mock()
        mock_context.command_type = "test"
        mock_context.language = "python"
        mock_context.contest_name = "abc123"
        mock_context.env_type = "docker"

        mock_new_context = Mock()
        mock_create_config.return_value = mock_new_context

        args = ["abc123", "a"]
        result_args, result_context = _apply_problem_name(
            args, mock_context, mock_infrastructure
        )

        # Verify new config creation with problem name from last arg
        mock_create_config.assert_called_once_with(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",  # Last arg used as problem name
            env_type="docker",
            infrastructure=mock_infrastructure
        )

        # Verify results
        assert result_args == ["abc123"]  # "a" removed
        assert result_context == mock_new_context

    def test_apply_problem_name_no_args(self):
        """Test applying problem name when no args are available"""
        mock_infrastructure = Mock()
        mock_context = Mock()

        args = []
        result_args, result_context = _apply_problem_name(
            args, mock_context, mock_infrastructure
        )

        # Verify original values returned unchanged
        assert result_args == args
        assert result_context == mock_context


class TestApplyContestName:
    """Tests for _apply_contest_name function"""

    @patch('src.context.user_input_parser.user_input_parser._create_execution_config')
    def test_apply_contest_name_with_args(self, mock_create_config):
        """Test applying contest name when args are available"""
        mock_infrastructure = Mock()
        mock_context = Mock()
        mock_context.command_type = "test"
        mock_context.language = "python"
        mock_context.problem_name = "a"
        mock_context.env_type = "docker"

        mock_new_context = Mock()
        mock_create_config.return_value = mock_new_context

        args = ["abc123"]
        result_args, result_context = _apply_contest_name(
            args, mock_context, mock_infrastructure
        )

        # Verify new config creation with contest name from last arg
        mock_create_config.assert_called_once_with(
            command_type="test",
            language="python",
            contest_name="abc123",  # Last arg used as contest name
            problem_name="a",
            env_type="docker",
            infrastructure=mock_infrastructure
        )

        # Verify results
        assert result_args == []  # "abc123" removed
        assert result_context == mock_new_context

    def test_apply_contest_name_no_args(self):
        """Test applying contest name when no args are available"""
        mock_infrastructure = Mock()
        mock_context = Mock()

        args = []
        result_args, result_context = _apply_contest_name(
            args, mock_context, mock_infrastructure
        )

        # Verify original values returned unchanged
        assert result_args == args
        assert result_context == mock_context


class TestConstantsAndDefaults:
    """Tests for constants and default values"""

    def test_contest_env_dir_constant(self):
        """Test that CONTEST_ENV_DIR constant is properly defined"""
        assert CONTEST_ENV_DIR == "contest_env"


class TestEdgeCases:
    """Tests for edge cases and error conditions"""

    @patch('src.context.user_input_parser.user_input_parser.TypeSafeConfigNodeManager')
    def test_create_execution_config_manager_exception(self, mock_manager_class):
        """Test execution config creation when manager raises exception"""
        mock_infrastructure = Mock()
        mock_manager_class.side_effect = Exception("Manager creation failed")

        with pytest.raises(Exception, match="Manager creation failed"):
            _create_execution_config(infrastructure=mock_infrastructure)

    @patch('src.context.user_input_parser.user_input_parser.SystemConfigLoader')
    def test_load_context_sqlite_exception(self, mock_loader_class):
        """Test SQLite context loading when loader raises exception"""
        mock_infrastructure = Mock()
        mock_loader_class.side_effect = Exception("SQLite connection failed")

        with pytest.raises(Exception, match="SQLite connection failed"):
            _load_current_context_sqlite(mock_infrastructure)

    @patch('src.configuration.config_manager.FileLoader')
    def test_scan_language_file_loader_exception(self, mock_file_loader_class):
        """Test language scanning when file loader raises exception"""
        mock_infrastructure = Mock()
        mock_context = Mock()
        mock_root = Mock()
        mock_file_loader_class.side_effect = Exception("File loading failed")

        with pytest.raises(Exception, match="File loading failed"):
            _scan_and_apply_language([], mock_context, mock_root, mock_infrastructure)

    def test_empty_args_handling(self):
        """Test handling of empty argument lists"""
        mock_infrastructure = Mock()
        mock_context = Mock()

        # Test problem name with empty args
        result_args, result_context = _apply_problem_name([], mock_context, mock_infrastructure)
        assert result_args == []
        assert result_context == mock_context

        # Test contest name with empty args
        result_args, result_context = _apply_contest_name([], mock_context, mock_infrastructure)
        assert result_args == []
        assert result_context == mock_context

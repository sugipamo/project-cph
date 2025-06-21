"""Tests for user_input_parser module."""
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.context.user_input_parser.user_input_parser import (
    _apply_contest_name,
    _apply_problem_name,
    _apply_remaining_arguments_flexibly,
    _create_execution_config,
    _create_initial_context,
    _finalize_environment_configuration,
    _initialize_and_load_base_data,
    _load_current_context_sqlite,
    _load_shared_config,
    _parse_command_line_args,
    _resolve_environment_configuration,
    _save_current_context_sqlite,
    _scan_and_apply_command,
    _scan_and_apply_env_type,
    _scan_and_apply_language,
    _setup_context_persistence_and_docker,
    _validate_and_return_context,
    make_dockerfile_loader,
    parse_user_input,
)


class TestUserInputParser:
    """Test cases for user_input_parser module."""

    @pytest.fixture
    def mock_infrastructure(self):
        """Create mock infrastructure/DI container."""
        infrastructure = Mock()
        return infrastructure

    @pytest.fixture
    def mock_config_manager(self):
        """Create mock TypeSafeConfigNodeManager."""
        config_manager = Mock()
        config_manager.create_execution_config.return_value = Mock()
        return config_manager

    @pytest.fixture
    def mock_context(self):
        """Create mock execution context."""
        context = Mock()
        context.command_type = "build"
        context.language = "python"
        context.contest_name = "abc123"
        context.problem_name = "A"
        context.env_type = "local"
        context.validate_execution_data.return_value = (True, None)
        return context

    def test_create_execution_config_success(self, mock_infrastructure):
        """Test successful creation of execution config."""
        with patch('src.context.user_input_parser.user_input_parser.TypeSafeConfigNodeManager') as mock_config_class:
            mock_config_manager = Mock()
            mock_context = Mock()
            mock_config_class.return_value = mock_config_manager
            mock_config_manager.create_execution_config.return_value = mock_context

            result = _create_execution_config(
                command_type="build",
                language="python",
                contest_name="abc123",
                problem_name="A",
                env_type="local",
                infrastructure=mock_infrastructure
            )

            assert result == mock_context
            mock_config_manager.load_from_files.assert_called_once_with(
                system_dir="./config/system",
                env_dir="contest_env",
                language="python"
            )

    def test_create_execution_config_none_language(self, mock_infrastructure):
        """Test creation fails when language is None."""
        with pytest.raises(ValueError, match="language parameter cannot be None"):
            _create_execution_config(
                command_type="build",
                language=None,
                contest_name="abc123",
                problem_name="A",
                env_type="local",
                infrastructure=mock_infrastructure
            )

    def test_create_execution_config_none_contest_name(self, mock_infrastructure):
        """Test creation fails when contest_name is None."""
        with pytest.raises(ValueError, match="contest_name parameter cannot be None"):
            _create_execution_config(
                command_type="build",
                language="python",
                contest_name=None,
                problem_name="A",
                env_type="local",
                infrastructure=mock_infrastructure
            )

    def test_create_execution_config_none_problem_name(self, mock_infrastructure):
        """Test creation fails when problem_name is None."""
        with pytest.raises(ValueError, match="problem_name parameter cannot be None"):
            _create_execution_config(
                command_type="build",
                language="python",
                contest_name="abc123",
                problem_name=None,
                env_type="local",
                infrastructure=mock_infrastructure
            )

    def test_load_current_context_sqlite(self, mock_infrastructure):
        """Test loading current context from SQLite."""
        mock_config_loader = Mock()
        mock_config_loader.get_current_context.return_value = {
            "command": "build",
            "language": "python",
            "env_type": "local",
            "contest_name": "abc123",
            "problem_name": "A"
        }

        with patch('src.context.user_input_parser.user_input_parser.SystemConfigLoader') as mock_loader_class:
            mock_loader_class.return_value = mock_config_loader

            result = _load_current_context_sqlite(mock_infrastructure)

            expected = {
                "command": "build",
                "language": "python",
                "env_type": "local",
                "contest_name": "abc123",
                "problem_name": "A"
            }
            assert result == expected

    def test_save_current_context_sqlite(self, mock_infrastructure):
        """Test saving current context to SQLite."""
        mock_config_loader = Mock()
        context_info = {
            "command": "build",
            "language": "python",
            "env_type": "local",
            "contest_name": "abc123",
            "problem_name": "A"
        }

        with patch('src.context.user_input_parser.user_input_parser.SystemConfigLoader') as mock_loader_class:
            mock_loader_class.return_value = mock_config_loader

            _save_current_context_sqlite(mock_infrastructure, context_info)

            mock_config_loader.update_current_context.assert_called_once_with(
                command="build",
                language="python",
                env_type="local",
                contest_name="abc123",
                problem_name="A"
            )

    def test_scan_and_apply_language_found(self, mock_infrastructure):
        """Test scanning and applying language when found in args."""
        args = ["python", "build", "contest", "A"]
        mock_context = Mock()
        mock_context.command_type = "build"
        mock_context.contest_name = "contest"
        mock_context.problem_name = "A"
        mock_context.env_type = "local"

        # Mock root with language nodes
        mock_root = Mock()
        mock_lang_node = Mock()
        mock_lang_node.key = "python"
        mock_lang_node.matches = ["python", "py"]
        mock_root.next_nodes = [mock_lang_node]

        # Mock FileLoader
        mock_file_loader = Mock()
        mock_file_loader.get_available_languages.return_value = ["python", "cpp", "java"]

        with patch('src.configuration.config_manager.FileLoader') as mock_loader_class:
            mock_loader_class.return_value = mock_file_loader

            with patch('src.context.user_input_parser.user_input_parser._create_execution_config') as mock_create:
                mock_new_context = Mock()
                mock_create.return_value = mock_new_context

                new_args, new_context = _scan_and_apply_language(args, mock_context, mock_root, mock_infrastructure)

                assert new_args == ["build", "contest", "A"]
                assert new_context == mock_new_context

    def test_scan_and_apply_language_not_found(self, mock_infrastructure):
        """Test scanning and applying language when not found in args."""
        args = ["build", "contest", "A"]
        mock_context = Mock()

        # Mock root with language nodes
        mock_root = Mock()
        mock_lang_node = Mock()
        mock_lang_node.key = "python"
        mock_lang_node.matches = ["python", "py"]
        mock_root.next_nodes = [mock_lang_node]

        # Mock FileLoader
        mock_file_loader = Mock()
        mock_file_loader.get_available_languages.return_value = ["python", "cpp", "java"]

        with patch('src.configuration.config_manager.FileLoader') as mock_loader_class:
            mock_loader_class.return_value = mock_file_loader

            new_args, new_context = _scan_and_apply_language(args, mock_context, mock_root, mock_infrastructure)

            assert new_args == args
            assert new_context == mock_context

    def test_scan_and_apply_env_type_found(self, mock_infrastructure):
        """Test scanning and applying env_type when found."""
        args = ["local", "build"]
        mock_context = Mock()
        mock_context.language = "python"
        mock_context.command_type = "build"
        mock_context.contest_name = "contest"
        mock_context.problem_name = "A"

        # Mock root and nodes
        mock_root = Mock()
        mock_env_type_container = Mock()
        mock_env_type_node = Mock()
        mock_env_type_node.key = "local"
        mock_env_type_node.matches = ["local", "loc"]
        mock_env_type_container.next_nodes = [mock_env_type_node]

        with patch('src.context.user_input_parser.user_input_parser.resolve_by_match_desc') as mock_resolve:
            mock_resolve.return_value = [mock_env_type_container]

            with patch('src.context.user_input_parser.user_input_parser._create_execution_config') as mock_create:
                mock_new_context = Mock()
                mock_create.return_value = mock_new_context

                new_args, new_context = _scan_and_apply_env_type(args, mock_context, mock_root, mock_infrastructure)

                assert new_args == ["build"]
                assert new_context == mock_new_context

    def test_scan_and_apply_command_found(self, mock_infrastructure):
        """Test scanning and applying command when found."""
        args = ["build", "contest"]
        mock_context = Mock()
        mock_context.language = "python"
        mock_context.contest_name = "contest"
        mock_context.problem_name = "A"
        mock_context.env_type = "local"

        # Mock root and nodes
        mock_root = Mock()
        mock_command_container = Mock()
        mock_command_node = Mock()
        mock_command_node.key = "build"
        mock_command_node.matches = ["build", "b"]
        mock_command_container.next_nodes = [mock_command_node]

        with patch('src.context.user_input_parser.user_input_parser.resolve_by_match_desc') as mock_resolve:
            mock_resolve.return_value = [mock_command_container]

            with patch('src.context.user_input_parser.user_input_parser._create_execution_config') as mock_create:
                mock_new_context = Mock()
                mock_create.return_value = mock_new_context

                new_args, new_context = _scan_and_apply_command(args, mock_context, mock_root, mock_infrastructure)

                assert new_args == ["contest"]
                assert new_context == mock_new_context

    def test_apply_problem_name(self, mock_infrastructure):
        """Test applying problem name from args."""
        args = ["contest", "A"]
        mock_context = Mock()
        mock_context.command_type = "build"
        mock_context.language = "python"
        mock_context.contest_name = "contest"
        mock_context.env_type = "local"

        with patch('src.context.user_input_parser.user_input_parser._create_execution_config') as mock_create:
            mock_new_context = Mock()
            mock_create.return_value = mock_new_context

            new_args, new_context = _apply_problem_name(args, mock_context, mock_infrastructure)

            assert new_args == ["contest"]
            assert new_context == mock_new_context
            mock_create.assert_called_with(
                command_type="build",
                language="python",
                contest_name="contest",
                problem_name="A",
                env_type="local",
                infrastructure=mock_infrastructure
            )

    def test_apply_contest_name(self, mock_infrastructure):
        """Test applying contest name from args."""
        args = ["contest"]
        mock_context = Mock()
        mock_context.command_type = "build"
        mock_context.language = "python"
        mock_context.problem_name = "A"
        mock_context.env_type = "local"

        with patch('src.context.user_input_parser.user_input_parser._create_execution_config') as mock_create:
            mock_new_context = Mock()
            mock_create.return_value = mock_new_context

            new_args, new_context = _apply_contest_name(args, mock_context, mock_infrastructure)

            assert new_args == []
            assert new_context == mock_new_context
            mock_create.assert_called_with(
                command_type="build",
                language="python",
                contest_name="contest",
                problem_name="A",
                env_type="local",
                infrastructure=mock_infrastructure
            )

    def test_load_shared_config_success(self, mock_infrastructure):
        """Test loading shared config successfully."""
        mock_file_driver = Mock()
        mock_os_provider = Mock()
        mock_json_provider = Mock()
        mock_result = Mock()
        mock_result.content = '{"test": "data"}'

        mock_infrastructure.resolve.side_effect = lambda key: {
            "file_driver": mock_file_driver,
            "DIKey.OS_PROVIDER": mock_os_provider,
            "DIKey.JSON_PROVIDER": mock_json_provider
        }.get(str(key))

        mock_os_provider.path_join.return_value = "/base/shared/env.json"
        mock_json_provider.loads.return_value = {"test": "data"}

        with patch('src.context.user_input_parser.user_input_parser.FileRequest') as mock_file_request:
            mock_request_instance = Mock()
            mock_file_request.return_value = mock_request_instance
            mock_request_instance.execute_operation.return_value = mock_result

            result = _load_shared_config("/base", mock_infrastructure)

            assert result == {"test": "data"}

    def test_load_shared_config_failure(self, mock_infrastructure):
        """Test loading shared config failure."""
        mock_file_driver = Mock()
        mock_os_provider = Mock()
        mock_json_provider = Mock()

        mock_infrastructure.resolve.side_effect = lambda key: {
            "file_driver": mock_file_driver,
            "DIKey.OS_PROVIDER": mock_os_provider,
            "DIKey.JSON_PROVIDER": mock_json_provider
        }.get(str(key))

        mock_os_provider.path_join.return_value = "/base/shared/env.json"

        with patch('src.context.user_input_parser.user_input_parser.FileRequest') as mock_file_request:
            mock_request_instance = Mock()
            mock_file_request.return_value = mock_request_instance
            mock_request_instance.execute_operation.side_effect = Exception("File not found")

            with pytest.raises(ValueError, match="Failed to load shared JSON"):
                _load_shared_config("/base", mock_infrastructure)

    def test_make_dockerfile_loader(self, mock_infrastructure):
        """Test creating dockerfile loader function."""
        mock_file_driver = Mock()
        mock_result = Mock()
        mock_result.content = "FROM ubuntu"

        mock_infrastructure.resolve.return_value = mock_file_driver

        with patch('src.context.user_input_parser.user_input_parser.FileRequest') as mock_file_request:
            mock_request_instance = Mock()
            mock_file_request.return_value = mock_request_instance
            mock_request_instance.execute_operation.return_value = mock_result

            loader = make_dockerfile_loader(mock_infrastructure)
            result = loader("/path/to/dockerfile")

            assert result == "FROM ubuntu"

    def test_initialize_and_load_base_data(self, mock_infrastructure):
        """Test initializing and loading base data."""
        mock_context_info = {
            "command": "build",
            "language": "python",
            "env_type": "local",
            "contest_name": "abc123",
            "problem_name": "A"
        }

        with patch('src.context.user_input_parser.user_input_parser.ValidationService'), \
             patch('src.context.user_input_parser.user_input_parser._load_current_context_sqlite') as mock_load:
            mock_load.return_value = mock_context_info

            result = _initialize_and_load_base_data(mock_infrastructure)

            assert result == mock_context_info

    def test_resolve_environment_configuration(self, mock_infrastructure):
        """Test resolving environment configuration."""
        mock_context_data = {"language": "python"}

        mock_file_loader = Mock()
        mock_file_loader.get_available_languages.return_value = ["python", "cpp"]
        mock_file_loader.load_and_merge_configs.return_value = {"python": {"test": "config"}}

        mock_root = Mock()

        with patch('src.configuration.config_manager.FileLoader') as mock_loader_class:
            mock_loader_class.return_value = mock_file_loader

            with patch('src.context.user_input_parser.user_input_parser.create_config_root_from_dict') as mock_create_root:
                mock_create_root.return_value = mock_root

                result = _resolve_environment_configuration(mock_context_data, mock_infrastructure)

                assert 'file_loader' in result
                assert 'env_config' in result
                assert 'root' in result
                assert result['root'] == mock_root

    def test_create_initial_context(self, mock_infrastructure):
        """Test creating initial context."""
        context_data = {
            "command": "build",
            "language": "python",
            "contest_name": "abc123",
            "problem_name": "A",
            "env_type": "local"
        }

        mock_root = Mock()
        env_config = {'root': mock_root}

        with patch('src.context.user_input_parser.user_input_parser._create_execution_config') as mock_create:
            mock_context = Mock()
            mock_create.return_value = mock_context

            result = _create_initial_context(context_data, env_config, mock_infrastructure)

            assert result == mock_context
            assert result.resolver == mock_root

    def test_apply_remaining_arguments_flexibly(self):
        """Test applying remaining arguments flexibly."""
        args = ["contest", "A"]
        mock_context = Mock()
        mock_context.problem_name = None
        mock_context.contest_name = None

        result = _apply_remaining_arguments_flexibly(args, mock_context)

        assert result.problem_name == "A"
        assert result.contest_name == "contest"

    def test_validate_and_return_context_valid(self):
        """Test validating and returning valid context."""
        mock_context = Mock()
        mock_context.validate_execution_data.return_value = (True, None)

        result = _validate_and_return_context(mock_context)

        assert result == mock_context

    def test_validate_and_return_context_invalid(self):
        """Test validating and returning invalid context."""
        mock_context = Mock()
        mock_context.validate_execution_data.return_value = (False, "Invalid context")

        with pytest.raises(ValueError, match="Invalid context"):
            _validate_and_return_context(mock_context)

    def test_parse_user_input_integration(self, mock_infrastructure):
        """Test parse_user_input integration."""
        args = ["python", "build", "abc123", "A"]

        # Mock all the dependencies
        mock_context_data = {
            "command": "build",
            "language": "python",
            "env_type": "local",
            "contest_name": "abc123",
            "problem_name": "A"
        }

        mock_env_config = {
            'root': Mock(),
            'file_loader': Mock(),
            'env_config': {}
        }

        mock_context = Mock()
        mock_context.validate_execution_data.return_value = (True, None)

        with patch('src.context.user_input_parser.user_input_parser._initialize_and_load_base_data') as mock_init:
            mock_init.return_value = mock_context_data

            with patch('src.context.user_input_parser.user_input_parser._resolve_environment_configuration') as mock_resolve:
                mock_resolve.return_value = mock_env_config

                with patch('src.context.user_input_parser.user_input_parser._create_initial_context') as mock_create:
                    mock_create.return_value = mock_context

                    with patch('src.context.user_input_parser.user_input_parser._parse_command_line_args') as mock_parse:
                        mock_parse.return_value = ([], mock_context)

                        with patch('src.context.user_input_parser.user_input_parser._finalize_environment_configuration') as mock_finalize:
                            mock_finalize.return_value = mock_context

                            with patch('src.context.user_input_parser.user_input_parser._setup_context_persistence_and_docker'), \
                                 patch('src.context.user_input_parser.user_input_parser._validate_and_return_context') as mock_validate:
                                mock_validate.return_value = mock_context

                                result = parse_user_input(args, mock_infrastructure)

                                assert result == mock_context

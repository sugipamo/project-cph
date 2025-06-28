"""Tests for user_input_parser module."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.presentation.user_input_parser import (
    parse_user_input,
    _create_execution_config,
    _load_current_context_sqlite,
    _save_current_context_sqlite,
    _parse_command_line_args,
    _scan_and_apply_language,
    _scan_and_apply_env_type,
    _scan_and_apply_command,
    _apply_problem_name,
    _apply_contest_name,
    _load_shared_config,
    make_dockerfile_loader,
    _scan_and_apply_options,
    _enable_debug_mode,
)


class TestExecutionConfig:
    """Test execution config creation."""

    def test_create_execution_config_success(self):
        """Test successful execution config creation."""
        infrastructure = Mock()
        config_manager = Mock()
        config_manager.resolve_config.return_value = "python3"
        infrastructure.resolve.return_value = config_manager
        
        context = _create_execution_config(
            command_type="run",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="local",
            infrastructure=infrastructure
        )
        
        assert context['command_type'] == "run"
        assert context['language'] == "python"
        assert context['language_id'] == "python3"
        assert context['contest_name'] == "abc123"
        assert context['problem_name'] == "a"
        assert context['env_type'] == "local"

    def test_create_execution_config_with_none_params(self):
        """Test execution config creation with None parameters."""
        infrastructure = Mock()
        
        with pytest.raises(ValueError, match="language parameter cannot be None"):
            _create_execution_config("run", None, "abc", "a", "local", infrastructure)
        
        with pytest.raises(ValueError, match="contest_name parameter cannot be None"):
            _create_execution_config("run", "python", None, "a", "local", infrastructure)
        
        with pytest.raises(ValueError, match="problem_name parameter cannot be None"):
            _create_execution_config("run", "python", "abc", None, "local", infrastructure)
        
        with pytest.raises(ValueError, match="env_type parameter cannot be None"):
            _create_execution_config("run", "python", "abc", "a", None, infrastructure)
        
        with pytest.raises(ValueError, match="command_type parameter cannot be None"):
            _create_execution_config(None, "python", "abc", "a", "local", infrastructure)

    def test_create_execution_config_fallback_language_id(self):
        """Test execution config creation with fallback language ID."""
        infrastructure = Mock()
        config_manager = Mock()
        config_manager.resolve_config.side_effect = KeyError("Not found")
        infrastructure.resolve.return_value = config_manager
        
        context = _create_execution_config(
            command_type="run",
            language="rust",
            contest_name="abc123",
            problem_name="a",
            env_type="local",
            infrastructure=infrastructure
        )
        
        assert context['language_id'] == "rust"  # Falls back to language


class TestSQLiteContextFunctions:
    """Test SQLite context functions."""

    def test_load_current_context_sqlite(self):
        """Test loading current context from SQLite."""
        infrastructure = Mock()
        
        result = _load_current_context_sqlite(infrastructure)
        
        # Currently returns empty dict
        assert result == {}

    def test_save_current_context_sqlite(self):
        """Test saving current context to SQLite."""
        infrastructure = Mock()
        context_info = {"language": "python", "contest_name": "abc123"}
        
        # Should not raise any exceptions
        _save_current_context_sqlite(infrastructure, context_info)


class TestSharedConfigLoading:
    """Test shared config loading."""

    def test_load_shared_config_success(self):
        """Test successful shared config loading."""
        infrastructure = Mock()
        
        # Mock dependencies
        file_driver = Mock()
        os_provider = Mock()
        json_provider = Mock()
        file_request_factory = Mock()
        
        os_provider.path_join.return_value = "/base/shared/env.json"
        
        # Mock file request and result
        file_request = Mock()
        file_result = Mock()
        file_result.content = '{"key": "value"}'
        file_request.execute_operation.return_value = file_result
        file_request_factory.create_file_request.return_value = file_request
        
        json_provider.loads.return_value = {"key": "value"}
        
        infrastructure.resolve.side_effect = lambda key: {
            "file_driver": file_driver,
            "OS_PROVIDER": os_provider,
            "JSON_PROVIDER": json_provider,
            "file_request_factory": file_request_factory
        }.get(key)
        
        result = _load_shared_config("/base", infrastructure)
        
        assert result == {"key": "value"}
        os_provider.path_join.assert_called_once_with("/base", "shared", "env.json")
        file_request_factory.create_file_request.assert_called_once_with("READ", "/base/shared/env.json")
        file_request.execute_operation.assert_called_once()
        json_provider.loads.assert_called_once_with('{"key": "value"}')

    def test_load_shared_config_failure(self):
        """Test shared config loading failure."""
        infrastructure = Mock()
        file_driver = Mock()
        os_provider = Mock()
        json_provider = Mock()
        file_request_factory = Mock()
        
        # Set up infrastructure to return mocks for the first few calls, then fail
        infrastructure.resolve.side_effect = [
            file_driver,  # file_driver
            os_provider,  # OS_PROVIDER
            json_provider,  # JSON_PROVIDER
            Exception("File not found")  # file_request_factory
        ]
        
        os_provider.path_join.return_value = "/base/shared/env.json"
        
        with pytest.raises(ValueError, match="Failed to load shared JSON"):
            _load_shared_config("/base", infrastructure)


class TestDockerfileLoader:
    """Test Dockerfile loader creation."""

    def test_make_dockerfile_loader(self):
        """Test creating a Dockerfile loader function."""
        infrastructure = Mock()
        
        # Mock dependencies
        file_driver = Mock()
        file_request_factory = Mock()
        
        # Mock file request and result
        file_request = Mock()
        file_result = Mock()
        file_result.content = "FROM python:3.9"
        file_request.execute_operation.return_value = file_result
        file_request_factory.create_file_request.return_value = file_request
        
        infrastructure.resolve.side_effect = lambda key: {
            "file_driver": file_driver,
            "file_request_factory": file_request_factory
        }.get(key)
        
        loader = make_dockerfile_loader(infrastructure)
        
        result = loader("/path/to/Dockerfile")
        
        assert result == "FROM python:3.9"
        file_request_factory.create_file_request.assert_called_once_with("READ", "/path/to/Dockerfile")
        file_request.execute_operation.assert_called_once_with(driver=file_driver, logger=None)


class TestCommandLineParsing:
    """Test command line argument parsing."""

    def test_scan_and_apply_language(self):
        """Test language scanning and application."""
        infrastructure = Mock()
        config_manager = Mock()
        config_manager.get_available_languages.return_value = ["python", "rust", "cpp"]
        infrastructure.resolve.return_value = config_manager
        
        # Create mock context and root
        context = Mock()
        context.command_type = "run"
        context.contest_name = "abc"
        context.problem_name = "a"
        context.env_type = "local"
        
        # Create mock root with language nodes
        root = Mock()
        python_node = Mock()
        python_node.key = "python"
        python_node.matches = ["python", "py"]
        rust_node = Mock()
        rust_node.key = "rust"
        rust_node.matches = ["rust", "rs"]
        root.next_nodes = [python_node, rust_node]
        
        args = ["py", "abc", "a"]
        
        new_args, new_context = _scan_and_apply_language(args, context, root, infrastructure)
        
        assert new_args == ["abc", "a"]
        assert new_context['language'] == "python"

    def test_scan_and_apply_env_type(self):
        """Test environment type scanning and application."""
        infrastructure = Mock()
        
        # Create mock context with language
        context = Mock()
        context.language = "python"
        context.command_type = "run"
        context.contest_name = "abc"
        context.problem_name = "a"
        context.env_type = "default"
        
        # Create mock root with env_type nodes
        root = Mock()
        env_node = Mock()
        env_node.key = "local"
        env_node.matches = ["local", "l"]
        env_types_node = Mock()
        env_types_node.next_nodes = [env_node]
        
        with patch('src.presentation.user_input_parser.resolve_by_match_desc') as mock_resolve:
            mock_resolve.return_value = [env_types_node]
            
            args = ["local", "abc"]
            new_args, new_context = _scan_and_apply_env_type(args, context, root, infrastructure)
            
            assert new_args == ["abc"]
            assert new_context['env_type'] == "local"

    def test_scan_and_apply_command(self):
        """Test command scanning and application."""
        infrastructure = Mock()
        
        # Create mock context with language
        context = Mock()
        context.language = "python"
        context.command_type = "help"
        context.contest_name = "abc"
        context.problem_name = "a"
        context.env_type = "local"
        
        # Create mock root with command nodes
        root = Mock()
        command_node = Mock()
        command_node.key = "run"
        command_node.matches = ["run", "r"]
        commands_node = Mock()
        commands_node.next_nodes = [command_node]
        
        with patch('src.presentation.user_input_parser.resolve_by_match_desc') as mock_resolve:
            mock_resolve.return_value = [commands_node]
            
            args = ["run", "abc"]
            new_args, new_context = _scan_and_apply_command(args, context, root, infrastructure)
            
            assert new_args == ["abc"]
            assert new_context['command_type'] == "run"

    def test_apply_problem_name(self):
        """Test applying problem name from args."""
        infrastructure = Mock()
        
        context = Mock()
        context.command_type = "run"
        context.language = "python"
        context.contest_name = "abc"
        context.problem_name = None
        context.env_type = "local"
        
        args = ["problem_x"]
        
        new_args, new_context = _apply_problem_name(args, context, infrastructure)
        
        assert new_args == []
        assert new_context['problem_name'] == "problem_x"

    def test_apply_contest_name(self):
        """Test applying contest name from args."""
        infrastructure = Mock()
        
        context = Mock()
        context.command_type = "run"
        context.language = "python"
        context.contest_name = None
        context.problem_name = "a"
        context.env_type = "local"
        
        args = ["contest123"]
        
        new_args, new_context = _apply_contest_name(args, context, infrastructure)
        
        assert new_args == []
        assert new_context['contest_name'] == "contest123"


class TestOptionsHandling:
    """Test command line options handling."""

    def test_scan_and_apply_options_with_debug(self):
        """Test scanning and applying --debug option."""
        infrastructure = Mock()
        context = Mock()
        
        args = ["--debug", "python", "run", "abc"]
        
        with patch('src.presentation.user_input_parser._enable_debug_mode') as mock_enable:
            new_args, new_context = _scan_and_apply_options(args, context, infrastructure)
            
            assert new_args == ["python", "run", "abc"]
            assert new_context.debug_mode is True
            mock_enable.assert_called_once_with(infrastructure)

    def test_scan_and_apply_options_without_debug(self):
        """Test scanning args without debug option."""
        infrastructure = Mock()
        context = {}  # Use dict instead of Mock to avoid attribute issues
        
        args = ["python", "run", "abc"]
        
        new_args, new_context = _scan_and_apply_options(args, context, infrastructure)
        
        assert new_args == ["python", "run", "abc"]
        assert 'debug_mode' not in new_context or new_context['debug_mode'] is False

    def test_enable_debug_mode_success(self):
        """Test enabling debug mode successfully."""
        infrastructure = Mock()
        
        # Mock debug service factory
        debug_service_factory = Mock()
        debug_service = Mock()
        debug_service_factory.create_debug_service.return_value = debug_service
        
        infrastructure.resolve.return_value = debug_service_factory
        infrastructure.register = Mock()
        
        _enable_debug_mode(infrastructure)
        
        debug_service_factory.create_debug_service.assert_called_once_with(infrastructure)
        debug_service.enable_debug_mode.assert_called_once()
        # The actual implementation registers a lambda that returns debug_service
        infrastructure.register.assert_called_once()
        call_args = infrastructure.register.call_args
        assert call_args[0][0] == "debug_service"
        # Verify the lambda returns the debug_service
        assert callable(call_args[0][1])
        assert call_args[0][1]() == debug_service

    def test_enable_debug_mode_failure(self):
        """Test debug mode enablement failure."""
        infrastructure = Mock()
        infrastructure.resolve.return_value = None
        infrastructure.is_registered.return_value = False
        
        # Should not raise exception, just handle gracefully
        _enable_debug_mode(infrastructure)


class TestParseUserInput:
    """Test the main parse_user_input function."""

    @patch('src.presentation.user_input_parser.ConfigLoaderService')
    @patch('src.presentation.user_input_parser.ValidationService')
    @patch('src.presentation.user_input_parser.create_config_root_from_dict')
    @patch('src.presentation.user_input_parser.DockerfileResolver')
    def test_parse_user_input_minimal(self, mock_dockerfile_resolver, mock_create_root, 
                                     mock_validation_service, mock_config_loader_service):
        """Test minimal parse_user_input execution."""
        # Setup infrastructure mock
        infrastructure = Mock()
        
        # Mock config manager
        config_manager = Mock()
        config_manager.resolve_config.return_value = "python3"
        config_manager.get_available_languages.return_value = ["python"]
        
        # Mock other services
        os_provider = Mock()
        os_provider.path_dirname.return_value = "/test/path"
        os_provider.path_join.return_value = "/test/path/oj.Dockerfile"
        
        # Mock config loader service
        config_loader = Mock()
        config_loader.load_config_files.return_value = {"python": {"commands": {"run": {}}}}
        mock_config_loader_service.return_value = config_loader
        
        # Mock config root
        mock_root = Mock()
        mock_root.value = {"python": {"commands": {"run": {}}}}
        mock_root.next_nodes = []
        mock_create_root.return_value = mock_root
        
        # Setup infrastructure resolution
        infrastructure.resolve.side_effect = lambda key: {
            'CONFIG_MANAGER': config_manager,
            'OS_PROVIDER': os_provider,
        }.get(key)
        
        # Create mock context that validates successfully
        mock_context = MagicMock()
        mock_context.validate_execution_data.return_value = (True, None)
        mock_context.__getitem__.side_effect = lambda k: {
            'command_type': 'help',
            'language': 'python',
            'contest_name': 'default',
            'problem_name': 'a',
            'env_type': 'default',
            'language_id': 'python3'
        }.get(k)
        
        # Patch _create_execution_config to return our mock context
        with patch('src.presentation.user_input_parser._create_execution_config') as mock_create_config:
            mock_create_config.return_value = mock_context
            
            args = []
            result = parse_user_input(args, infrastructure)
            
            assert result is not None
            mock_context.validate_execution_data.assert_called_once()

    def test_parse_user_input_with_invalid_context(self):
        """Test parse_user_input with invalid context."""
        infrastructure = Mock()
        
        # Mock config manager
        config_manager = Mock()
        config_manager.get_available_languages.return_value = ["python"]
        
        # Mock OS provider
        os_provider = Mock()
        os_provider.path_dirname.return_value = "/test/path"
        os_provider.path_join.return_value = "/test/path/oj.Dockerfile"
        
        # Setup infrastructure resolution
        infrastructure.resolve.side_effect = lambda key: {
            'CONFIG_MANAGER': config_manager,
            'OS_PROVIDER': os_provider,
        }.get(key)
        
        # Setup minimal mocks
        with patch('src.presentation.user_input_parser.ConfigLoaderService'):
            with patch('src.presentation.user_input_parser.ValidationService'):
                with patch('src.presentation.user_input_parser.create_config_root_from_dict') as mock_create_root:
                    # Mock config root
                    mock_root = Mock()
                    mock_root.next_nodes = []
                    mock_create_root.return_value = mock_root
                    
                    with patch('src.presentation.user_input_parser._create_execution_config') as mock_create:
                        # Create context that fails validation
                        mock_context = MagicMock()
                        mock_context.validate_execution_data.return_value = (False, "Invalid data")
                        mock_create.return_value = mock_context
                        
                        args = []
                        with pytest.raises(ValueError, match="Invalid data"):
                            parse_user_input(args, infrastructure)
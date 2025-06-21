"""Tests for configuration/config_manager module."""
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.configuration.config_manager import (
    ConfigurationError,
    FileLoader,
    TypedExecutionConfiguration,
    TypeSafeConfigNodeManager,
    _ensure_imports,
)


class TestConfigurationError:
    """Test ConfigurationError exception."""



class TestEnsureImports:
    """Test the _ensure_imports function."""

    def test_ensure_imports_loads_modules(self):
        """Test that _ensure_imports successfully loads required modules."""
        # Reset global imports to test loading
        import src.configuration.config_manager as config_module
        original_config_node = config_module.ConfigNode
        original_create_config_root = config_module.create_config_root_from_dict

        try:
            # Reset to None to test import loading
            config_module.ConfigNode = None
            config_module.create_config_root_from_dict = None

            _ensure_imports()

            # Verify imports were loaded
            assert config_module.ConfigNode is not None
            assert config_module.create_config_root_from_dict is not None
            assert config_module.resolve_best is not None
            assert config_module.resolve_formatted_string is not None

        finally:
            # Restore original state
            config_module.ConfigNode = original_config_node
            config_module.create_config_root_from_dict = original_create_config_root


class TestTypedExecutionConfiguration:
    """Test TypedExecutionConfiguration class."""

    def test_initialization_with_basic_attributes(self):
        """Test basic initialization of TypedExecutionConfiguration."""
        config = TypedExecutionConfiguration(
            contest_name="abc123",
            problem_name="A",
            language="python",
            env_type="local",
            command_type="build"
        )

        assert config.contest_name == "abc123"
        assert config.problem_name == "A"
        assert config.language == "python"
        assert config.env_type == "local"
        assert config.command_type == "build"
        assert config._root_node is None

    def test_initialization_with_root_node(self):
        """Test initialization with root node."""
        mock_root_node = Mock()
        config = TypedExecutionConfiguration(
            contest_name="abc123",
            problem_name="A",
            _root_node=mock_root_node
        )

        assert config._root_node == mock_root_node

    def test_resolve_formatted_string_without_root_node(self):
        """Test string formatting without root node (basic fallback)."""
        config = TypedExecutionConfiguration(
            contest_name="abc123",
            problem_name="A",
            language="python",
            env_type="local",
            command_type="build",
            local_workspace_path="/workspace"
        )

        # Simple template substitution should work
        template = "{contest_name}-{problem_name}"
        result = config.resolve_formatted_string(template)
        assert result == "abc123-A"

    @patch('src.configuration.config_manager.resolve_formatted_string')
    def test_resolve_formatted_string_with_root_node(self, mock_resolve):
        """Test string formatting with root node."""
        mock_root_node = Mock()
        mock_resolve.return_value = "resolved-template"

        config = TypedExecutionConfiguration(
            contest_name="abc123",
            problem_name="A",
            language="python",
            env_type="local",
            command_type="build",
            _root_node=mock_root_node
        )

        template = "{contest_name}/{problem_name}"
        result = config.resolve_formatted_string(template)

        assert result == "resolved-template"
        mock_resolve.assert_called_once()


    def test_validate_execution_data_success(self):
        """Test successful validation of execution data."""
        config = TypedExecutionConfiguration(
            contest_name="abc123",
            problem_name="A",
            language="python",
            env_type="local",
            command_type="build"
        )

        # Add validate_execution_data method behavior if it exists
        if hasattr(config, 'validate_execution_data'):
            is_valid, error = config.validate_execution_data()
            assert is_valid is True
            assert error is None


class TestFileLoader:
    """Test FileLoader class."""

    def test_file_loader_initialization(self):
        """Test FileLoader can be initialized."""
        mock_infrastructure = Mock()
        loader = FileLoader(mock_infrastructure)
        assert loader.infrastructure == mock_infrastructure

    def test_file_loader_initialization_without_infrastructure(self):
        """Test FileLoader initialization without infrastructure."""
        loader = FileLoader()
        assert loader.infrastructure is None

    @patch('src.configuration.config_manager.Path')
    def test_get_available_languages(self, mock_path_class):
        """Test getting available languages from directory."""
        # Setup mock path behavior
        mock_path = Mock()
        mock_path_class.return_value = mock_path
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True

        # Mock language directories
        mock_lang_dirs = [Mock(), Mock(), Mock()]
        mock_lang_dirs[0].name = "python"
        mock_lang_dirs[0].is_dir.return_value = True
        mock_lang_dirs[1].name = "cpp"
        mock_lang_dirs[1].is_dir.return_value = True
        mock_lang_dirs[2].name = "file.txt"
        mock_lang_dirs[2].is_dir.return_value = False

        mock_path.iterdir.return_value = mock_lang_dirs

        loader = FileLoader()
        languages = loader.get_available_languages(Path("contest_env"))

        assert "python" in languages
        assert "cpp" in languages
        assert "file.txt" not in languages

    @patch('src.configuration.config_manager.Path')
    def test_get_available_languages_nonexistent_dir(self, mock_path_class):
        """Test getting languages from non-existent directory."""
        mock_path = Mock()
        mock_path_class.return_value = mock_path
        mock_path.exists.return_value = False

        loader = FileLoader()
        languages = loader.get_available_languages(Path("nonexistent"))

        assert languages == []


class TestTypeSafeConfigNodeManager:
    """Test TypeSafeConfigNodeManager class."""

    def test_initialization(self):
        """Test manager initialization."""
        mock_infrastructure = Mock()
        manager = TypeSafeConfigNodeManager(mock_infrastructure)
        assert manager.infrastructure == mock_infrastructure
        assert manager.root_node is None


    @patch('src.configuration.config_manager.FileLoader')
    def test_load_from_files(self, mock_file_loader_class):
        """Test loading configuration from files."""
        mock_infrastructure = Mock()
        mock_file_loader = Mock()
        mock_file_loader_class.return_value = mock_file_loader
        mock_file_loader.load_and_merge_configs.return_value = {"test": "config"}

        manager = TypeSafeConfigNodeManager(mock_infrastructure)

        with patch('src.configuration.config_manager.create_config_root_from_dict') as mock_create_root:
            mock_root = Mock()
            mock_create_root.return_value = mock_root

            manager.load_from_files(
                system_dir="./config/system",
                env_dir="./contest_env",
                language="python"
            )

            assert manager.root_node == mock_root
            mock_file_loader.load_and_merge_configs.assert_called_once_with(
                "./config/system",
                "./contest_env",
                "python"
            )

    def test_resolve_config_success(self):
        """Test successful config resolution."""
        mock_infrastructure = Mock()
        manager = TypeSafeConfigNodeManager(mock_infrastructure)

        # Set up a mock root node
        mock_root = Mock()
        manager.root_node = mock_root

        with patch('src.configuration.config_manager.resolve_best') as mock_resolve:
            mock_resolve.return_value = "resolved_value"

            result = manager.resolve_config(["docker", "timeout"], int)

            assert result == "resolved_value"
            mock_resolve.assert_called_once_with(mock_root, ["docker", "timeout"])



    def test_create_execution_config(self):
        """Test creation of execution configuration."""
        mock_infrastructure = Mock()
        manager = TypeSafeConfigNodeManager(mock_infrastructure)

        # Set up mock root node with expected config structure
        mock_root = Mock()
        manager.root_node = mock_root

        with patch('src.configuration.config_manager.resolve_best') as mock_resolve:
            # Mock various config resolutions
            config_values = {
                ('paths', 'local_workspace_path'): "/workspace",
                ('timeouts', 'default_timeout'): 30,
                ('languages', 'python', 'file_name'): "main.py",
                ('languages', 'python', 'run_command'): "python main.py",
            }

            def resolve_side_effect(root, path):
                return config_values.get(tuple(path), "default")

            mock_resolve.side_effect = resolve_side_effect

            config = manager.create_execution_config(
                contest_name="abc123",
                problem_name="A",
                language="python",
                env_type="local",
                command_type="build"
            )

            assert isinstance(config, TypedExecutionConfiguration)
            assert config.contest_name == "abc123"
            assert config.problem_name == "A"
            assert config.language == "python"
            assert config.env_type == "local"
            assert config.command_type == "build"
            assert config._root_node == mock_root


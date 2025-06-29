"""Tests for context formatter functionality."""
from unittest.mock import Mock, patch

import pytest

from src.presentation.context_formatter import (
    ExecutionFormatData,
    create_format_data_from_typed_config,
    create_format_dict,
    create_format_dict_from_typed_config,
    format_template_string,
    format_values_with_context_dict,
    get_docker_naming_from_data,
    validate_execution_data,
)
from src.utils.mock_regex_provider import MockRegexProvider


class TestExecutionFormatData:
    """Test ExecutionFormatData dataclass."""

    def test_creation(self):
        """Test ExecutionFormatData creation."""
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="local"
        )
        
        assert data.command_type == "test"
        assert data.language == "python"
        assert data.contest_name == "abc123"
        assert data.problem_name == "a"
        assert data.env_type == "local"

    def test_immutability(self):
        """Test that ExecutionFormatData is immutable."""
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="local"
        )
        
        with pytest.raises(AttributeError):
            data.command_type = "run"


class TestCreateFormatDataFromTypedConfig:
    """Test create_format_data_from_typed_config function."""

    def test_creation_from_typed_config(self):
        """Test creating ExecutionFormatData from TypedExecutionConfiguration."""
        config = Mock()
        config.command_type = "test"
        config.language = "python"
        config.contest_name = "abc123"
        config.problem_name = "a"
        config.env_type = "local"
        
        data = create_format_data_from_typed_config(config)
        
        assert data.command_type == "test"
        assert data.language == "python"
        assert data.contest_name == "abc123"
        assert data.problem_name == "a"
        assert data.env_type == "local"


class TestCreateFormatDict:
    """Test create_format_dict function."""

    def test_basic_format_dict(self):
        """Test creating basic format dictionary."""
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="local"
        )
        
        format_dict = create_format_dict(data)
        
        assert format_dict["command_type"] == "test"
        assert format_dict["language"] == "python"
        assert format_dict["contest_name"] == "abc123"
        assert format_dict["problem_name"] == "a"
        assert format_dict["env_type"] == "local"
        assert format_dict["language_name"] == "python"


class TestCreateFormatDictFromTypedConfig:
    """Test create_format_dict_from_typed_config function."""

    def test_basic_config(self):
        """Test creating format dict from basic config."""
        config = Mock()
        config.command_type = "test"
        config.language = "python"
        config.contest_name = "abc123"
        config.problem_name = "a"
        config.env_type = "local"
        config.local_workspace_path = "/path/to/workspace"
        config.contest_current_path = "/path/to/contest"
        config.language_id = "py"
        config.source_file_name = "main.py"
        config.run_command = "python main.py"
        
        format_dict = create_format_dict_from_typed_config(config)
        
        assert format_dict["command_type"] == "test"
        assert format_dict["language"] == "python"
        assert format_dict["contest_name"] == "abc123"
        assert format_dict["problem_name"] == "a"
        assert format_dict["env_type"] == "local"
        assert format_dict["local_workspace_path"] == "/path/to/workspace"
        assert format_dict["contest_current_path"] == "/path/to/contest"
        assert format_dict["language_id"] == "py"
        assert format_dict["source_file_name"] == "main.py"
        assert format_dict["run_command"] == "python main.py"
        assert format_dict["language_name"] == "python"

    def test_with_optional_paths(self):
        """Test creating format dict with optional paths."""
        config = Mock()
        config.command_type = "test"
        config.language = "python"
        config.contest_name = "abc123"
        config.problem_name = "a"
        config.env_type = "local"
        config.local_workspace_path = "/path/to/workspace"
        config.contest_current_path = "/path/to/contest"
        config.language_id = "py"
        config.source_file_name = "main.py"
        config.run_command = "python main.py"
        config.contest_stock_path = "/path/to/stock"
        config.contest_template_path = "/path/to/template"
        config.contest_temp_path = "/path/to/temp"
        
        format_dict = create_format_dict_from_typed_config(config)
        
        assert format_dict["contest_stock_path"] == "/path/to/stock"
        assert format_dict["contest_template_path"] == "/path/to/template"
        assert format_dict["contest_temp_path"] == "/path/to/temp"


class TestFormatTemplateString:
    """Test format_template_string function."""

    def test_format_with_execution_format_data(self):
        """Test formatting with ExecutionFormatData."""
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="local"
        )
        
        template = "Running {command_type} for {language} in {contest_name}/{problem_name}"
        formatted, missing = format_template_string(template, data)
        
        assert formatted == "Running test for python in abc123/a"
        assert len(missing) == 0

    def test_format_with_missing_keys(self):
        """Test formatting with missing keys."""
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="local"
        )
        
        template = "Running {command_type} with {unknown_key}"
        formatted, missing = format_template_string(template, data)
        
        assert "test" in formatted
        assert "{unknown_key}" in formatted
        assert "unknown_key" in missing

    def test_format_with_typed_config_with_resolver(self):
        """Test formatting with TypedExecutionConfiguration with resolve_formatted_string."""
        config = Mock()
        config.command_type = "test"
        config.language = "python"
        config.resolve_formatted_string = Mock(return_value="Resolved string")
        
        template = "Some template"
        formatted, missing = format_template_string(template, config)
        
        assert formatted == "Resolved string"
        assert len(missing) == 0
        config.resolve_formatted_string.assert_called_once_with(template)

    def test_format_with_typed_config_resolver_error(self):
        """Test formatting when resolver raises error."""
        config = Mock()
        config.command_type = "test"
        config.language = "python"
        config.resolve_formatted_string = Mock(side_effect=Exception("Resolver error"))
        
        template = "Some template"
        with pytest.raises(ValueError, match="文字列フォーマット解決エラー"):
            format_template_string(template, config)

    def test_format_with_typed_config_without_resolver(self):
        """Test formatting with TypedExecutionConfiguration without resolver."""
        config = Mock()
        config.command_type = "test"
        config.language = "python"
        config.contest_name = "abc123"
        config.problem_name = "a"
        config.env_type = "local"
        config.local_workspace_path = "/path"
        config.contest_current_path = "/contest"
        config.language_id = "py"
        config.source_file_name = "main.py"
        config.run_command = "python main.py"
        
        # Remove resolve_formatted_string if it exists
        if hasattr(config, 'resolve_formatted_string'):
            delattr(config, 'resolve_formatted_string')
        
        template = "Running {command_type} for {language}"
        formatted, missing = format_template_string(template, config)
        
        assert formatted == "Running test for python"
        assert len(missing) == 0


class TestValidateExecutionData:
    """Test validate_execution_data function."""

    def test_valid_execution_format_data(self):
        """Test validation of valid ExecutionFormatData."""
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="local"
        )
        
        is_valid, error = validate_execution_data(data)
        
        assert is_valid is True
        assert error is None

    def test_invalid_execution_format_data_missing_fields(self):
        """Test validation with missing fields."""
        test_cases = [
            (ExecutionFormatData("", "python", "abc123", "a", "local"), "command_type is required"),
            (ExecutionFormatData("test", "", "abc123", "a", "local"), "language is required"),
            (ExecutionFormatData("test", "python", "", "a", "local"), "contest_name is required"),
            (ExecutionFormatData("test", "python", "abc123", "", "local"), "problem_name is required"),
            (ExecutionFormatData("test", "python", "abc123", "a", ""), "env_type is required"),
        ]
        
        for data, expected_error in test_cases:
            is_valid, error = validate_execution_data(data)
            assert is_valid is False
            assert error == expected_error

    def test_valid_typed_config_with_validator(self):
        """Test validation with TypedExecutionConfiguration with validate_execution_data."""
        config = Mock()
        config.command_type = "test"
        config.language = "python"
        config.validate_execution_data = Mock(return_value=(True, None))
        
        is_valid, error = validate_execution_data(config)
        
        assert is_valid is True
        assert error is None
        config.validate_execution_data.assert_called_once()

    def test_invalid_typed_config_with_validator(self):
        """Test validation with invalid TypedExecutionConfiguration."""
        config = Mock()
        config.command_type = "test"
        config.language = "python"
        config.validate_execution_data = Mock(return_value=(False, "Some error"))
        
        is_valid, error = validate_execution_data(config)
        
        assert is_valid is False
        assert error == "Some error"

    def test_typed_config_without_validator(self):
        """Test validation with TypedExecutionConfiguration without validator."""
        config = Mock()
        config.command_type = "test"
        config.language = "python"
        config.contest_name = "abc123"
        config.problem_name = "a"
        config.env_type = "local"
        
        # Remove validate_execution_data if it exists
        if hasattr(config, 'validate_execution_data'):
            delattr(config, 'validate_execution_data')
        
        is_valid, error = validate_execution_data(config)
        
        assert is_valid is True
        assert error is None

    def test_typed_config_without_validator_missing_fields(self):
        """Test validation with missing fields in TypedExecutionConfiguration."""
        config = Mock()
        config.command_type = ""
        config.language = "python"
        config.contest_name = "abc123"
        config.problem_name = "a"
        config.env_type = "local"
        
        # Remove validate_execution_data if it exists
        if hasattr(config, 'validate_execution_data'):
            delattr(config, 'validate_execution_data')
        
        is_valid, error = validate_execution_data(config)
        
        assert is_valid is False
        assert error == "command_type is required"


class TestFormatValuesWithContextDict:
    """Test format_values_with_context_dict function."""

    def test_format_string_values(self):
        """Test formatting string values."""
        values = ["Hello {name}", "Test {language}"]
        context = {"name": "World", "language": "Python"}
        
        result = format_values_with_context_dict(values, context)
        
        assert result == ["Hello World", "Test Python"]

    def test_format_mixed_types(self):
        """Test formatting mixed type values."""
        values = ["Hello {name}", 123, True, None]
        context = {"name": "World"}
        
        result = format_values_with_context_dict(values, context)
        
        assert result == ["Hello World", "123", "True", "None"]

    def test_format_with_missing_keys(self):
        """Test formatting with missing keys in context."""
        values = ["Hello {name}", "Test {unknown}"]
        context = {"name": "World"}
        
        result = format_values_with_context_dict(values, context)
        
        assert result[0] == "Hello World"
        assert "{unknown}" in result[1]


class TestGetDockerNamingFromData:
    """Test get_docker_naming_from_data function."""

    def test_with_execution_format_data(self):
        """Test Docker naming with ExecutionFormatData."""
        data = ExecutionFormatData(
            command_type="test",
            language="Python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker"
        )
        
        naming = get_docker_naming_from_data(data, None, None)
        
        assert naming["image_name"] == "cph_python_image"
        assert naming["container_name"] == "cph_python"
        assert naming["oj_image_name"] == "cph_oj_image"
        assert naming["oj_container_name"] == "cph_oj"

    def test_with_typed_config(self):
        """Test Docker naming with TypedExecutionConfiguration."""
        config = Mock()
        config.language = "C++"
        
        naming = get_docker_naming_from_data(config, None, None)
        
        assert naming["image_name"] == "cph_c++_image"
        assert naming["container_name"] == "cph_c++"
        assert naming["oj_image_name"] == "cph_oj_image"
        assert naming["oj_container_name"] == "cph_oj"

    def test_with_dockerfile_content(self):
        """Test Docker naming with dockerfile content (currently not used)."""
        data = ExecutionFormatData(
            command_type="test",
            language="Python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker"
        )
        
        dockerfile_content = "FROM python:3.9"
        oj_dockerfile_content = "FROM ubuntu:20.04"
        
        naming = get_docker_naming_from_data(data, dockerfile_content, oj_dockerfile_content)
        
        # Currently, dockerfile content is not used for naming
        assert naming["image_name"] == "cph_python_image"
        assert naming["container_name"] == "cph_python"
        assert naming["oj_image_name"] == "cph_oj_image"
        assert naming["oj_container_name"] == "cph_oj"
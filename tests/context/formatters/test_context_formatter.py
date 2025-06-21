"""Tests for context_formatter module"""
from dataclasses import dataclass
from unittest.mock import Mock, patch

import pytest

from src.context.formatters.context_formatter import (
    ExecutionFormatData,
    create_format_data_from_typed_config,
    create_format_dict,
    create_format_dict_from_typed_config,
    format_template_string,
    format_values_with_context_dict,
    get_docker_naming_from_data,
    validate_execution_data,
)


@dataclass
class MockTypedExecutionConfiguration:
    """Mock TypedExecutionConfiguration for testing"""
    command_type: str = "test"
    language: str = "python"
    contest_name: str = "abc123"
    problem_name: str = "a"
    env_type: str = "docker"
    local_workspace_path: str = "/workspace"
    contest_current_path: str = "/contest/current"
    language_id: str = "py"
    source_file_name: str = "main.py"
    run_command: str = "python main.py"
    contest_stock_path: str = "/contest/stock"
    contest_template_path: str = "/contest/template"
    contest_temp_path: str = "/contest/temp"


class TestExecutionFormatData:
    def test_creation(self):
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker"
        )
        assert data.command_type == "test"
        assert data.language == "python"
        assert data.contest_name == "abc123"
        assert data.problem_name == "a"
        assert data.env_type == "docker"

    def test_immutability(self):
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker"
        )
        with pytest.raises(AttributeError):
            data.command_type = "new_test"


class TestCreateFormatDataFromTypedConfig:
    def test_create_from_typed_config(self):
        config = MockTypedExecutionConfiguration()
        data = create_format_data_from_typed_config(config)

        assert data.command_type == "test"
        assert data.language == "python"
        assert data.contest_name == "abc123"
        assert data.problem_name == "a"
        assert data.env_type == "docker"


class TestCreateFormatDictFromTypedConfig:
    def test_create_dict_with_all_fields(self):
        config = MockTypedExecutionConfiguration()
        format_dict = create_format_dict_from_typed_config(config)

        assert format_dict["command_type"] == "test"
        assert format_dict["language"] == "python"
        assert format_dict["contest_name"] == "abc123"
        assert format_dict["problem_name"] == "a"
        assert format_dict["env_type"] == "docker"
        assert format_dict["local_workspace_path"] == "/workspace"
        assert format_dict["contest_current_path"] == "/contest/current"
        assert format_dict["language_id"] == "py"
        assert format_dict["source_file_name"] == "main.py"
        assert format_dict["run_command"] == "python main.py"
        assert format_dict["language_name"] == "python"
        assert format_dict["contest_stock_path"] == "/contest/stock"
        assert format_dict["contest_template_path"] == "/contest/template"
        assert format_dict["contest_temp_path"] == "/contest/temp"

    def test_create_dict_without_optional_fields(self):
        config = Mock(spec=[
            'command_type', 'language', 'contest_name', 'problem_name',
            'env_type', 'local_workspace_path', 'contest_current_path',
            'language_id', 'source_file_name', 'run_command'
        ])
        config.command_type = "test"
        config.language = "python"
        config.contest_name = "abc123"
        config.problem_name = "a"
        config.env_type = "docker"
        config.local_workspace_path = "/workspace"
        config.contest_current_path = "/contest/current"
        config.language_id = "py"
        config.source_file_name = "main.py"
        config.run_command = "python main.py"

        format_dict = create_format_dict_from_typed_config(config)

        assert "contest_stock_path" not in format_dict
        assert "contest_template_path" not in format_dict
        assert "contest_temp_path" not in format_dict


class TestCreateFormatDict:
    def test_create_dict_from_data(self):
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker"
        )
        format_dict = create_format_dict(data)

        assert format_dict["command_type"] == "test"
        assert format_dict["language"] == "python"
        assert format_dict["contest_name"] == "abc123"
        assert format_dict["problem_name"] == "a"
        assert format_dict["env_type"] == "docker"
        assert format_dict["language_name"] == "python"


class TestFormatTemplateString:
    def test_format_with_execution_format_data(self):
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker"
        )
        template = "Running {command_type} for {language} in {contest_name}/{problem_name}"
        result, missing = format_template_string(template, data)

        assert result == "Running test for python in abc123/a"
        assert len(missing) == 0

    def test_format_with_missing_keys(self):
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker"
        )
        template = "Missing key: {nonexistent_key}"
        result, missing = format_template_string(template, data)

        assert "nonexistent_key" in missing

    @patch('src.context.formatters.context_formatter.TypedExecutionConfiguration', MockTypedExecutionConfiguration)
    def test_format_with_typed_config(self):
        config = MockTypedExecutionConfiguration()
        template = "Running {command_type} for {language}"
        result, missing = format_template_string(template, config)

        assert result == "Running test for python"
        assert len(missing) == 0

    @patch('src.context.formatters.context_formatter.TypedExecutionConfiguration', MockTypedExecutionConfiguration)
    def test_format_with_typed_config_resolve_method(self):
        config = Mock(spec=MockTypedExecutionConfiguration)
        config.resolve_formatted_string = Mock(return_value="Resolved string")

        # Need to check if it's an instance of TypedExecutionConfiguration
        with patch('src.context.formatters.context_formatter.isinstance') as mock_isinstance:
            mock_isinstance.return_value = True

            template = "Test template"
            result, missing = format_template_string(template, config)

            assert result == "Resolved string"
            assert len(missing) == 0



class TestValidateExecutionData:
    def test_validate_valid_data(self):
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker"
        )
        is_valid, error = validate_execution_data(data)

        assert is_valid is True
        assert error is None

    def test_validate_missing_command_type(self):
        data = ExecutionFormatData(
            command_type="",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker"
        )
        is_valid, error = validate_execution_data(data)

        assert is_valid is False
        assert error == "command_type is required"

    def test_validate_missing_language(self):
        data = ExecutionFormatData(
            command_type="test",
            language="",
            contest_name="abc123",
            problem_name="a",
            env_type="docker"
        )
        is_valid, error = validate_execution_data(data)

        assert is_valid is False
        assert error == "language is required"

    def test_validate_missing_contest_name(self):
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="",
            problem_name="a",
            env_type="docker"
        )
        is_valid, error = validate_execution_data(data)

        assert is_valid is False
        assert error == "contest_name is required"

    def test_validate_missing_problem_name(self):
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="",
            env_type="docker"
        )
        is_valid, error = validate_execution_data(data)

        assert is_valid is False
        assert error == "problem_name is required"

    def test_validate_missing_env_type(self):
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type=""
        )
        is_valid, error = validate_execution_data(data)

        assert is_valid is False
        assert error == "env_type is required"

    @patch('src.context.formatters.context_formatter.TypedExecutionConfiguration', MockTypedExecutionConfiguration)
    def test_validate_typed_config_with_validate_method(self):
        config = Mock()
        config.validate_execution_data = Mock(return_value=(True, None))

        is_valid, error = validate_execution_data(config)

        assert is_valid is True
        assert error is None



class TestFormatValuesWithContextDict:
    def test_format_string_values(self):
        values = ["Hello {name}", "Age: {age}"]
        context = {"name": "Alice", "age": "30"}
        result = format_values_with_context_dict(values, context)

        assert result == ["Hello Alice", "Age: 30"]

    def test_format_mixed_values(self):
        values = ["Hello {name}", 42, None]
        context = {"name": "Bob"}
        result = format_values_with_context_dict(values, context)

        assert result == ["Hello Bob", "42", "None"]

    def test_format_empty_list(self):
        result = format_values_with_context_dict([], {})
        assert result == []


class TestGetDockerNamingFromData:
    @patch('src.context.formatters.context_formatter.get_docker_container_name')
    @patch('src.context.formatters.context_formatter.get_oj_container_name')
    @patch('src.context.formatters.context_formatter.get_docker_image_name')
    @patch('src.context.formatters.context_formatter.get_oj_image_name')
    def test_get_naming_with_execution_format_data(self, mock_oj_image, mock_docker_image,
                                                  mock_oj_container, mock_docker_container):
        mock_docker_container.return_value = "python-container"
        mock_oj_container.return_value = "oj-container"
        mock_docker_image.return_value = "python-image"
        mock_oj_image.return_value = "oj-image"

        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker"
        )

        result = get_docker_naming_from_data(data)

        assert result["container_name"] == "python-container"
        assert result["oj_container_name"] == "oj-container"
        assert result["image_name"] == "python-image"
        assert result["oj_image_name"] == "oj-image"

        mock_docker_container.assert_called_once_with("python")
        mock_docker_image.assert_called_once_with("python", None)

    @patch('src.context.formatters.context_formatter.get_docker_container_name')
    @patch('src.context.formatters.context_formatter.get_oj_container_name')
    @patch('src.context.formatters.context_formatter.get_docker_image_name')
    @patch('src.context.formatters.context_formatter.get_oj_image_name')
    def test_get_naming_with_dockerfile_content(self, mock_oj_image, mock_docker_image,
                                               mock_oj_container, mock_docker_container):
        mock_docker_container.return_value = "python-container"
        mock_oj_container.return_value = "oj-container"
        mock_docker_image.return_value = "python-image-hash"
        mock_oj_image.return_value = "oj-image-hash"

        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker"
        )

        dockerfile_content = "FROM python:3.9"
        oj_dockerfile_content = "FROM ubuntu:20.04"

        get_docker_naming_from_data(data, dockerfile_content, oj_dockerfile_content)

        mock_docker_image.assert_called_once_with("python", dockerfile_content)
        mock_oj_image.assert_called_once_with(oj_dockerfile_content)

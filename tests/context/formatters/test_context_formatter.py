"""Tests for context_formatter module"""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from src.context.formatters.context_formatter import (
    ExecutionFormatData,
    create_format_data_from_typed_config,
    create_format_dict_from_typed_config,
    create_format_dict,
    format_template_string,
    validate_execution_data,
    format_values_with_context_dict,
    get_docker_naming_from_data,
)


class TestExecutionFormatData:
    """Tests for ExecutionFormatData class"""
    
    def test_execution_format_data_creation(self):
        """Test ExecutionFormatData creation with all fields"""
        data = ExecutionFormatData(
            command_type="run",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="docker"
        )
        
        assert data.command_type == "run"
        assert data.language == "python"
        assert data.contest_name == "abc001"
        assert data.problem_name == "a"
        assert data.env_type == "docker"
    
    def test_execution_format_data_immutable(self):
        """Test that ExecutionFormatData is immutable"""
        data = ExecutionFormatData(
            command_type="run",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="docker"
        )
        
        with pytest.raises(AttributeError):
            data.command_type = "test"


class TestCreateFormatDataFromTypedConfig:
    """Tests for create_format_data_from_typed_config function"""
    
    def test_create_format_data_from_typed_config(self):
        """Test creating ExecutionFormatData from TypedExecutionConfiguration"""
        mock_config = Mock()
        mock_config.command_type = "run"
        mock_config.language = "python"
        mock_config.contest_name = "abc001"
        mock_config.problem_name = "a"
        mock_config.env_type = "docker"
        
        data = create_format_data_from_typed_config(mock_config)
        
        assert isinstance(data, ExecutionFormatData)
        assert data.command_type == "run"
        assert data.language == "python"
        assert data.contest_name == "abc001"
        assert data.problem_name == "a"
        assert data.env_type == "docker"


class TestCreateFormatDictFromTypedConfig:
    """Tests for create_format_dict_from_typed_config function"""
    
    def test_create_format_dict_basic(self):
        """Test creating format dict with basic fields"""
        mock_config = Mock()
        mock_config.command_type = "run"
        mock_config.language = "python"
        mock_config.contest_name = "abc001"
        mock_config.problem_name = "a"
        mock_config.env_type = "docker"
        mock_config.local_workspace_path = Path("/workspace")
        mock_config.contest_current_path = Path("/contest/current")
        mock_config.language_id = "py"
        mock_config.source_file_name = "main.py"
        mock_config.run_command = "python main.py"
        
        # Mock optional attributes as not present
        mock_config.__class__ = type('MockConfig', (), {})
        
        format_dict = create_format_dict_from_typed_config(mock_config)
        
        assert format_dict["command_type"] == "run"
        assert format_dict["language"] == "python"
        assert format_dict["contest_name"] == "abc001"
        assert format_dict["problem_name"] == "a"
        assert format_dict["env_type"] == "docker"
        assert format_dict["local_workspace_path"] == "/workspace"
        assert format_dict["contest_current_path"] == "/contest/current"
        assert format_dict["language_id"] == "py"
        assert format_dict["source_file_name"] == "main.py"
        assert format_dict["run_command"] == "python main.py"
        assert format_dict["language_name"] == "python"
    
    def test_create_format_dict_with_optional_paths(self):
        """Test creating format dict with optional path fields"""
        mock_config = Mock()
        mock_config.command_type = "run"
        mock_config.language = "python"
        mock_config.contest_name = "abc001"
        mock_config.problem_name = "a"
        mock_config.env_type = "docker"
        mock_config.local_workspace_path = Path("/workspace")
        mock_config.contest_current_path = Path("/contest/current")
        mock_config.language_id = "py"
        mock_config.source_file_name = "main.py"
        mock_config.run_command = "python main.py"
        mock_config.contest_stock_path = Path("/contest/stock")
        mock_config.contest_template_path = Path("/contest/template")
        mock_config.contest_temp_path = Path("/contest/temp")
        
        format_dict = create_format_dict_from_typed_config(mock_config)
        
        assert format_dict["contest_stock_path"] == "/contest/stock"
        assert format_dict["contest_template_path"] == "/contest/template"
        assert format_dict["contest_temp_path"] == "/contest/temp"


class TestCreateFormatDict:
    """Tests for create_format_dict function"""
    
    def test_create_format_dict(self):
        """Test creating format dict from ExecutionFormatData"""
        data = ExecutionFormatData(
            command_type="run",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="docker"
        )
        
        format_dict = create_format_dict(data)
        
        assert format_dict["command_type"] == "run"
        assert format_dict["language"] == "python"
        assert format_dict["contest_name"] == "abc001"
        assert format_dict["problem_name"] == "a"
        assert format_dict["env_type"] == "docker"
        assert format_dict["language_name"] == "python"


class TestFormatTemplateString:
    """Tests for format_template_string function"""
    
    def test_format_with_execution_format_data(self):
        """Test formatting template string with ExecutionFormatData"""
        data = ExecutionFormatData(
            command_type="run",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="docker"
        )
        
        template = "Running {language} for {contest_name}/{problem_name}"
        result, missing = format_template_string(template, data)
        
        assert result == "Running python for abc001/a"
        assert len(missing) == 0
    
    def test_format_with_missing_keys(self):
        """Test formatting with missing keys"""
        data = ExecutionFormatData(
            command_type="run",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="docker"
        )
        
        template = "Running {language} with {unknown_key}"
        result, missing = format_template_string(template, data)
        
        assert "{unknown_key}" in result
        assert "unknown_key" in missing
    
    @patch('src.context.formatters.context_formatter.TypedExecutionConfiguration')
    def test_format_with_typed_config_resolve_method(self, mock_typed_config_class):
        """Test formatting with TypedExecutionConfiguration that has resolve_formatted_string"""
        mock_config = Mock()
        mock_config.resolve_formatted_string = Mock(return_value="Resolved string")
        
        # Make isinstance check work
        mock_typed_config_class.__bool__.return_value = True
        mock_typed_config_class.__class__ = type
        
        with patch('src.context.formatters.context_formatter.isinstance', return_value=True):
            template = "Test template"
            result, missing = format_template_string(template, mock_config)
            
            assert result == "Resolved string"
            assert len(missing) == 0
            mock_config.resolve_formatted_string.assert_called_once_with(template)
    
    @patch('src.context.formatters.context_formatter.TypedExecutionConfiguration')
    def test_format_with_typed_config_without_resolve_method(self, mock_typed_config_class):
        """Test formatting with TypedExecutionConfiguration without resolve_formatted_string"""
        mock_config = Mock()
        mock_config.command_type = "run"
        mock_config.language = "python"
        mock_config.contest_name = "abc001"
        mock_config.problem_name = "a"
        mock_config.env_type = "docker"
        mock_config.local_workspace_path = Path("/workspace")
        mock_config.contest_current_path = Path("/contest/current")
        mock_config.language_id = "py"
        mock_config.source_file_name = "main.py"
        mock_config.run_command = "python main.py"
        
        # Remove resolve_formatted_string method
        del mock_config.resolve_formatted_string
        
        # Make isinstance check work
        mock_typed_config_class.__bool__.return_value = True
        
        with patch('src.context.formatters.context_formatter.isinstance', return_value=True):
            template = "Running {language} for {contest_name}"
            result, missing = format_template_string(template, mock_config)
            
            assert result == "Running python for abc001"
            assert len(missing) == 0


class TestValidateExecutionData:
    """Tests for validate_execution_data function"""
    
    def test_validate_valid_execution_format_data(self):
        """Test validation of valid ExecutionFormatData"""
        data = ExecutionFormatData(
            command_type="run",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="docker"
        )
        
        is_valid, error = validate_execution_data(data)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_missing_command_type(self):
        """Test validation with missing command_type"""
        data = ExecutionFormatData(
            command_type="",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="docker"
        )
        
        is_valid, error = validate_execution_data(data)
        
        assert is_valid is False
        assert error == "command_type is required"
    
    def test_validate_missing_language(self):
        """Test validation with missing language"""
        data = ExecutionFormatData(
            command_type="run",
            language="",
            contest_name="abc001",
            problem_name="a",
            env_type="docker"
        )
        
        is_valid, error = validate_execution_data(data)
        
        assert is_valid is False
        assert error == "language is required"
    
    def test_validate_missing_contest_name(self):
        """Test validation with missing contest_name"""
        data = ExecutionFormatData(
            command_type="run",
            language="python",
            contest_name="",
            problem_name="a",
            env_type="docker"
        )
        
        is_valid, error = validate_execution_data(data)
        
        assert is_valid is False
        assert error == "contest_name is required"
    
    def test_validate_missing_problem_name(self):
        """Test validation with missing problem_name"""
        data = ExecutionFormatData(
            command_type="run",
            language="python",
            contest_name="abc001",
            problem_name="",
            env_type="docker"
        )
        
        is_valid, error = validate_execution_data(data)
        
        assert is_valid is False
        assert error == "problem_name is required"
    
    def test_validate_missing_env_type(self):
        """Test validation with missing env_type"""
        data = ExecutionFormatData(
            command_type="run",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type=""
        )
        
        is_valid, error = validate_execution_data(data)
        
        assert is_valid is False
        assert error == "env_type is required"
    
    @patch('src.context.formatters.context_formatter.TypedExecutionConfiguration')
    def test_validate_typed_config_with_validate_method(self, mock_typed_config_class):
        """Test validation with TypedExecutionConfiguration that has validate_execution_data"""
        mock_config = Mock()
        mock_config.validate_execution_data = Mock(return_value=(True, None))
        
        # Make isinstance check work
        mock_typed_config_class.__bool__.return_value = True
        
        with patch('src.context.formatters.context_formatter.isinstance', return_value=True):
            is_valid, error = validate_execution_data(mock_config)
            
            assert is_valid is True
            assert error is None
            mock_config.validate_execution_data.assert_called_once()
    
    @patch('src.context.formatters.context_formatter.TypedExecutionConfiguration')
    def test_validate_typed_config_without_validate_method(self, mock_typed_config_class):
        """Test validation with TypedExecutionConfiguration without validate_execution_data"""
        mock_config = Mock()
        mock_config.command_type = "run"
        mock_config.language = "python"
        mock_config.contest_name = "abc001"
        mock_config.problem_name = "a"
        mock_config.env_type = "docker"
        
        # Remove validate_execution_data method
        del mock_config.validate_execution_data
        
        # Make isinstance check work
        mock_typed_config_class.__bool__.return_value = True
        
        with patch('src.context.formatters.context_formatter.isinstance', return_value=True):
            is_valid, error = validate_execution_data(mock_config)
            
            assert is_valid is True
            assert error is None


class TestFormatValuesWithContextDict:
    """Tests for format_values_with_context_dict function"""
    
    def test_format_string_values(self):
        """Test formatting list of string values"""
        values = ["Hello {name}", "Language: {language}"]
        context_dict = {"name": "World", "language": "Python"}
        
        result = format_values_with_context_dict(values, context_dict)
        
        assert result == ["Hello World", "Language: Python"]
    
    def test_format_mixed_types(self):
        """Test formatting list with mixed types"""
        values = ["Test {name}", 42, True, None]
        context_dict = {"name": "Value"}
        
        result = format_values_with_context_dict(values, context_dict)
        
        assert result == ["Test Value", "42", "True", "None"]
    
    def test_format_empty_list(self):
        """Test formatting empty list"""
        values = []
        context_dict = {"key": "value"}
        
        result = format_values_with_context_dict(values, context_dict)
        
        assert result == []
    
    def test_format_with_missing_keys(self):
        """Test formatting with missing keys in context"""
        values = ["Hello {name}", "Missing {unknown}"]
        context_dict = {"name": "World"}
        
        result = format_values_with_context_dict(values, context_dict)
        
        # The format_string_simple function should handle missing keys gracefully
        assert result[0] == "Hello World"
        assert "{unknown}" in result[1]


class TestGetDockerNamingFromData:
    """Tests for get_docker_naming_from_data function"""
    
    @patch('src.context.formatters.context_formatter.get_docker_container_name')
    @patch('src.context.formatters.context_formatter.get_docker_image_name')
    @patch('src.context.formatters.context_formatter.get_oj_container_name')
    @patch('src.context.formatters.context_formatter.get_oj_image_name')
    def test_get_docker_naming_with_execution_format_data(
        self, mock_oj_image, mock_oj_container, mock_image, mock_container
    ):
        """Test getting Docker naming info with ExecutionFormatData"""
        mock_container.return_value = "cph-python"
        mock_image.return_value = "cph-python:latest"
        mock_oj_container.return_value = "cph-oj"
        mock_oj_image.return_value = "cph-oj:latest"
        
        data = ExecutionFormatData(
            command_type="run",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="docker"
        )
        
        result = get_docker_naming_from_data(data, "dockerfile content", "oj dockerfile")
        
        assert result["container_name"] == "cph-python"
        assert result["image_name"] == "cph-python:latest"
        assert result["oj_container_name"] == "cph-oj"
        assert result["oj_image_name"] == "cph-oj:latest"
        
        mock_container.assert_called_once_with("python", "")
        mock_image.assert_called_once_with("python", "dockerfile content")
        mock_oj_container.assert_called_once_with("")
        mock_oj_image.assert_called_once_with("oj dockerfile")
    
    @patch('src.context.formatters.context_formatter.get_docker_container_name')
    @patch('src.context.formatters.context_formatter.get_docker_image_name')
    @patch('src.context.formatters.context_formatter.get_oj_container_name')
    @patch('src.context.formatters.context_formatter.get_oj_image_name')
    def test_get_docker_naming_without_dockerfile_content(
        self, mock_oj_image, mock_oj_container, mock_image, mock_container
    ):
        """Test getting Docker naming info without dockerfile content"""
        mock_container.return_value = "cph-python"
        mock_image.return_value = "cph-python:latest"
        mock_oj_container.return_value = "cph-oj"
        mock_oj_image.return_value = "cph-oj:latest"
        
        data = ExecutionFormatData(
            command_type="run",
            language="python",
            contest_name="abc001",
            problem_name="a",
            env_type="docker"
        )
        
        result = get_docker_naming_from_data(data, None, None)
        
        mock_image.assert_called_once_with("python", None)
        mock_oj_image.assert_called_once_with(None)
    
    @patch('src.context.formatters.context_formatter.get_docker_container_name')
    @patch('src.context.formatters.context_formatter.get_docker_image_name')
    @patch('src.context.formatters.context_formatter.get_oj_container_name')
    @patch('src.context.formatters.context_formatter.get_oj_image_name')
    def test_get_docker_naming_with_typed_config(
        self, mock_oj_image, mock_oj_container, mock_image, mock_container
    ):
        """Test getting Docker naming info with TypedExecutionConfiguration"""
        mock_container.return_value = "cph-cpp"
        mock_image.return_value = "cph-cpp:latest"
        mock_oj_container.return_value = "cph-oj"
        mock_oj_image.return_value = "cph-oj:latest"
        
        mock_config = Mock()
        mock_config.language = "cpp"
        
        result = get_docker_naming_from_data(mock_config, None, None)
        
        assert result["container_name"] == "cph-cpp"
        assert result["image_name"] == "cph-cpp:latest"
        mock_container.assert_called_once_with("cpp", "")
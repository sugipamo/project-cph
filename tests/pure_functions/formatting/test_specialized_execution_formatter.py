"""
Comprehensive tests for execution formatter module
"""
import pytest
from unittest.mock import patch, Mock
from src.pure_functions.formatting.specialized.execution_formatter import (
    ExecutionFormatData,
    create_execution_format_dict,
    format_execution_template,
    validate_execution_format_data,
    get_docker_naming_context,
    create_extended_format_dict,
    # Backward compatibility aliases
    create_format_dict,
    format_template_string,
    validate_execution_data,
    get_docker_naming_from_data
)


class TestExecutionFormatData:
    """Test ExecutionFormatData dataclass"""
    
    def test_dataclass_creation(self):
        """Test creating ExecutionFormatData instance"""
        data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={"python": {"language_id": "5078"}}
        )
        
        assert data.command_type == "build"
        assert data.language == "python"
        assert data.contest_name == "abc123"
        assert data.problem_name == "a"
        assert data.env_type == "docker"
        assert data.env_json == {"python": {"language_id": "5078"}}
    
    def test_dataclass_immutable(self):
        """Test that ExecutionFormatData is immutable (frozen)"""
        data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        with pytest.raises(Exception):  # Should raise FrozenInstanceError or AttributeError
            data.language = "cpp"


class TestCreateExecutionFormatDict:
    """Test create_execution_format_dict function"""
    
    def test_basic_format_dict_creation(self):
        """Test basic format dictionary creation"""
        data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        format_dict = create_execution_format_dict(data)
        
        assert format_dict["command_type"] == "build"
        assert format_dict["language"] == "python"
        assert format_dict["contest_name"] == "abc123"
        assert format_dict["problem_name"] == "a"
        assert format_dict["problem_id"] == "a"  # Compatibility alias
        assert format_dict["env_type"] == "docker"
    
    def test_format_dict_with_env_json(self):
        """Test format dictionary creation with env_json"""
        env_json = {
            "python": {
                "language_id": "5078",
                "source_file_name": "main.py",
                "contest_current_path": "./contest_current",
                "contest_stock_path": "./contest_stock",
                "contest_template_path": "./contest_template/python",
                "contest_temp_path": "./.temp",
                "workspace_path": "./workspace"
            }
        }
        
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="b",
            env_type="docker",
            env_json=env_json
        )
        
        format_dict = create_execution_format_dict(data)
        
        # Check env_json values are included
        assert format_dict["language_id"] == "5078"
        assert format_dict["source_file_name"] == "main.py"
        assert format_dict["contest_current_path"] == "./contest_current"
        assert format_dict["contest_stock_path"] == "./contest_stock"
        assert format_dict["contest_template_path"] == "./contest_template/python"
        assert format_dict["contest_temp_path"] == "./.temp"
        assert format_dict["workspace_path"] == "./workspace"
        assert format_dict["language_name"] == "python"
    
    def test_format_dict_with_partial_env_json(self):
        """Test format dictionary with partial env_json configuration"""
        env_json = {
            "python": {
                "language_id": "5078",
                "source_file_name": "solution.py"
                # Missing other fields
            }
        }
        
        data = ExecutionFormatData(
            command_type="run",
            language="python",
            contest_name="abc456",
            problem_name="c",
            env_type="docker",
            env_json=env_json
        )
        
        format_dict = create_execution_format_dict(data)
        
        # Check provided values
        assert format_dict["language_id"] == "5078"
        assert format_dict["source_file_name"] == "solution.py"
        
        # Check default values
        assert format_dict["contest_current_path"] == "./contest_current"
        assert format_dict["contest_stock_path"] == "./contest_stock"
        assert format_dict["workspace_path"] == "./workspace"
    
    def test_format_dict_missing_language_in_env_json(self):
        """Test format dictionary when language is not in env_json"""
        env_json = {
            "cpp": {
                "language_id": "5077"
            }
        }
        
        data = ExecutionFormatData(
            command_type="build",
            language="python",  # Not in env_json
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json=env_json
        )
        
        format_dict = create_execution_format_dict(data)
        
        # Should only have basic fields
        assert format_dict["command_type"] == "build"
        assert format_dict["language"] == "python"
        assert format_dict["contest_name"] == "abc123"
        
        # Should not have env_json derived fields
        assert "language_id" not in format_dict
        assert "source_file_name" not in format_dict
    
    def test_format_dict_none_env_json(self):
        """Test format dictionary with None env_json"""
        data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json=None
        )
        
        format_dict = create_execution_format_dict(data)
        
        # Should only have basic fields
        basic_fields = ["command_type", "language", "contest_name", "problem_name", "problem_id", "env_type"]
        for field in basic_fields:
            assert field in format_dict
        
        # Should not have env_json derived fields
        env_fields = ["language_id", "source_file_name", "contest_current_path"]
        for field in env_fields:
            assert field not in format_dict


class TestFormatExecutionTemplate:
    """Test format_execution_template function"""
    
    def test_basic_template_formatting(self):
        """Test basic template formatting"""
        data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        template = "/{contest_name}/{problem_name}/{language}"
        result, missing = format_execution_template(template, data)
        
        assert result == "/abc123/a/python"
        assert missing == set()
    
    def test_template_with_missing_keys(self):
        """Test template formatting with missing keys"""
        data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        template = "/{contest_name}/{missing_key}/{language}"
        result, missing = format_execution_template(template, data)
        
        assert result == "/abc123/{missing_key}/python"
        assert missing == {"missing_key"}
    
    def test_template_with_env_json_values(self):
        """Test template formatting using env_json values"""
        env_json = {
            "python": {
                "source_file_name": "main.py",
                "contest_current_path": "./current"
            }
        }
        
        data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json=env_json
        )
        
        template = "{contest_current_path}/{source_file_name}"
        result, missing = format_execution_template(template, data)
        
        assert result == "./current/main.py"
        assert missing == set()
    
    def test_complex_template_formatting(self):
        """Test complex template with multiple substitutions"""
        env_json = {
            "python": {
                "language_id": "5078",
                "source_file_name": "solution.py",
                "workspace_path": "/workspace"
            }
        }
        
        data = ExecutionFormatData(
            command_type="run",
            language="python",
            contest_name="abc123",
            problem_name="d",
            env_type="docker",
            env_json=env_json
        )
        
        template = "{workspace_path}/{contest_name}/{problem_id}/{source_file_name}"
        result, missing = format_execution_template(template, data)
        
        assert result == "/workspace/abc123/d/solution.py"
        assert missing == set()


class TestValidateExecutionFormatData:
    """Test validate_execution_format_data function"""
    
    def test_valid_data(self):
        """Test validation of valid data"""
        data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={"python": {}}
        )
        
        is_valid, error = validate_execution_format_data(data)
        assert is_valid is True
        assert error is None
    
    def test_missing_required_field(self):
        """Test validation with missing required field"""
        data = ExecutionFormatData(
            command_type="",  # Empty required field
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        is_valid, error = validate_execution_format_data(data)
        assert is_valid is False
        assert "command_type" in error
    
    def test_language_not_in_env_json(self):
        """Test validation when language is not in env_json"""
        data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={"cpp": {}}  # Python not in env_json
        )
        
        is_valid, error = validate_execution_format_data(data)
        assert is_valid is False
        assert "Language 'python' not found in env_json" in error
    
    def test_none_env_json(self):
        """Test validation with None env_json"""
        data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json=None
        )
        
        is_valid, error = validate_execution_format_data(data)
        assert is_valid is True
        assert error is None


class TestGetDockerNamingContext:
    """Test get_docker_naming_context function"""
    
    @patch('src.operations.utils.docker_naming.get_docker_image_name')
    @patch('src.operations.utils.docker_naming.get_docker_container_name')
    @patch('src.operations.utils.docker_naming.get_oj_image_name')
    @patch('src.operations.utils.docker_naming.get_oj_container_name')
    def test_docker_naming_context(self, mock_oj_container, mock_oj_image, mock_container, mock_image):
        """Test Docker naming context generation"""
        # Setup mocks
        mock_image.return_value = "python:hash123"
        mock_container.return_value = "cph_python"
        mock_oj_image.return_value = "ojtools:hash456"
        mock_oj_container.return_value = "cph_ojtools"
        
        data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        dockerfile_content = "FROM python:3.9"
        oj_dockerfile_content = "FROM ojtools"
        
        context = get_docker_naming_context(data, dockerfile_content, oj_dockerfile_content)
        
        assert context["image_name"] == "python:hash123"
        assert context["container_name"] == "cph_python"
        assert context["oj_image_name"] == "ojtools:hash456"
        assert context["oj_container_name"] == "cph_ojtools"
        
        # Verify function calls
        mock_image.assert_called_once_with("python", dockerfile_content)
        mock_container.assert_called_once_with("python")
        mock_oj_image.assert_called_once_with(oj_dockerfile_content)
        mock_oj_container.assert_called_once()
    
    @patch('src.operations.utils.docker_naming.get_docker_image_name')
    @patch('src.operations.utils.docker_naming.get_docker_container_name')
    @patch('src.operations.utils.docker_naming.get_oj_image_name')
    @patch('src.operations.utils.docker_naming.get_oj_container_name')
    def test_docker_naming_context_no_dockerfile(self, mock_oj_container, mock_oj_image, mock_container, mock_image):
        """Test Docker naming context without dockerfile content"""
        mock_image.return_value = "python:latest"
        mock_container.return_value = "cph_python"
        mock_oj_image.return_value = "ojtools:latest"
        mock_oj_container.return_value = "cph_ojtools"
        
        data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        context = get_docker_naming_context(data)
        
        # Should call with None dockerfile content
        mock_image.assert_called_once_with("python", None)
        mock_oj_image.assert_called_once_with(None)


class TestCreateExtendedFormatDict:
    """Test create_extended_format_dict function"""
    
    def test_basic_extended_format_dict(self):
        """Test creating extended format dictionary"""
        data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        format_dict = create_extended_format_dict(data)
        
        # Should have basic fields
        assert format_dict["command_type"] == "build"
        assert format_dict["language"] == "python"
        assert format_dict["contest_name"] == "abc123"
    
    def test_extended_format_dict_with_docker_context(self):
        """Test extended format dictionary with Docker context"""
        data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        docker_context = {
            "image_name": "python:hash123",
            "container_name": "cph_python"
        }
        
        format_dict = create_extended_format_dict(data, docker_context=docker_context)
        
        # Should have both basic and Docker fields
        assert format_dict["language"] == "python"
        assert format_dict["image_name"] == "python:hash123"
        assert format_dict["container_name"] == "cph_python"
    
    def test_extended_format_dict_with_additional_context(self):
        """Test extended format dictionary with additional context"""
        data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        additional_context = {
            "custom_field": "custom_value",
            "numeric_field": 42,
            "boolean_field": True
        }
        
        format_dict = create_extended_format_dict(data, additional_context=additional_context)
        
        # Should have basic fields plus additional context (converted to strings)
        assert format_dict["language"] == "python"
        assert format_dict["custom_field"] == "custom_value"
        assert format_dict["numeric_field"] == "42"
        assert format_dict["boolean_field"] == "True"
    
    def test_extended_format_dict_with_all_contexts(self):
        """Test extended format dictionary with all context types"""
        data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        docker_context = {"image_name": "python:hash123"}
        additional_context = {"custom": "value"}
        
        format_dict = create_extended_format_dict(
            data, 
            docker_context=docker_context, 
            additional_context=additional_context
        )
        
        # Should have all fields
        assert format_dict["language"] == "python"
        assert format_dict["image_name"] == "python:hash123"
        assert format_dict["custom"] == "value"


class TestBackwardCompatibility:
    """Test backward compatibility aliases"""
    
    def test_create_format_dict_alias(self):
        """Test create_format_dict is an alias for create_execution_format_dict"""
        assert create_format_dict == create_execution_format_dict
    
    def test_format_template_string_alias(self):
        """Test format_template_string is an alias for format_execution_template"""
        assert format_template_string == format_execution_template
    
    def test_validate_execution_data_alias(self):
        """Test validate_execution_data is an alias for validate_execution_format_data"""
        assert validate_execution_data == validate_execution_format_data
    
    def test_get_docker_naming_from_data_alias(self):
        """Test get_docker_naming_from_data is an alias for get_docker_naming_context"""
        assert get_docker_naming_from_data == get_docker_naming_context
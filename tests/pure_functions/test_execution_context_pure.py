"""
Tests for pure execution context functions
No mocks - just pure function testing
"""
import pytest
from src.pure_functions.execution_context_pure import (
    ExecutionData,
    DockerNames,
    StepContextData,
    create_docker_names_pure,
    validate_execution_data_pure,
    create_format_dict_pure,
    format_string_pure,
    resolve_config_path_pure,
    execution_data_to_step_context_pure
)


class TestExecutionDataValidation:
    """Test validation of execution data"""
    
    def test_valid_data(self):
        """Test validation of valid execution data"""
        data = ExecutionData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={
                "python": {
                    "commands": {
                        "build": {"steps": []}
                    }
                }
            }
        )
        
        errors = validate_execution_data_pure(data)
        assert errors == []
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields"""
        data = ExecutionData(
            command_type="",
            language="",
            contest_name="",
            problem_name="",
            env_type=""
        )
        
        errors = validate_execution_data_pure(data)
        assert len(errors) == 6  # 5 required fields + 1 invalid env_type
        assert "command_type is required" in errors
        assert "language is required" in errors
        assert "contest_name is required" in errors
        assert "problem_name is required" in errors
        assert "env_type is required" in errors
    
    def test_invalid_env_type(self):
        """Test validation with invalid env_type"""
        data = ExecutionData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="invalid"
        )
        
        errors = validate_execution_data_pure(data)
        assert "env_type must be 'local' or 'docker', got 'invalid'" in errors
    
    def test_language_not_in_env_json(self):
        """Test validation when language not in env_json"""
        data = ExecutionData(
            command_type="build",
            language="rust",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={"python": {}}
        )
        
        errors = validate_execution_data_pure(data)
        assert "language 'rust' not found in env_json" in errors
    
    def test_command_not_in_language(self):
        """Test validation when command not in language config"""
        data = ExecutionData(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={
                "python": {
                    "commands": {
                        "build": {}
                    }
                }
            }
        )
        
        errors = validate_execution_data_pure(data)
        assert "command_type 'test' not found for language 'python'" in errors


class TestDockerNameCreation:
    """Test Docker name generation"""
    
    def test_create_docker_names(self):
        """Test creating Docker names"""
        names = create_docker_names_pure(
            contest_name="abc123",
            problem_name="a",
            language="python",
            env_type="docker"
        )
        
        assert isinstance(names, DockerNames)
        assert names.image_name == "cph_abc123_a_python_image"
        assert names.container_name == "cph_abc123_a_python_container"
        assert names.oj_image_name == "cph_abc123_a_python_oj_image"
        assert names.oj_container_name == "cph_abc123_a_python_oj_container"
    
    def test_docker_names_are_immutable(self):
        """Test that DockerNames is immutable"""
        names = create_docker_names_pure("abc", "x", "py", "docker")
        
        with pytest.raises(AttributeError):
            names.image_name = "new_name"


class TestFormatDictCreation:
    """Test format dictionary creation"""
    
    def test_basic_format_dict(self):
        """Test creating basic format dictionary"""
        data = ExecutionData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="local"
        )
        
        format_dict = create_format_dict_pure(data)
        
        assert format_dict["command_type"] == "build"
        assert format_dict["language"] == "python"
        assert format_dict["contest_name"] == "abc123"
        assert format_dict["problem_name"] == "a"
        assert format_dict["env_type"] == "local"
        assert format_dict["task_label"] == "a"
    
    def test_format_dict_with_optional_fields(self):
        """Test format dict with optional fields"""
        data = ExecutionData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="local",
            working_directory="/work",
            workspace_path="/workspace",
            source_file_name="main.py",
            task_label="task_a"
        )
        
        format_dict = create_format_dict_pure(data)
        
        assert format_dict["working_directory"] == "/work"
        assert format_dict["workspace_path"] == "/workspace"
        assert format_dict["source_file_name"] == "main.py"
        assert format_dict["task_label"] == "task_a"
    
    def test_format_dict_with_docker(self):
        """Test format dict includes Docker names for Docker env"""
        data = ExecutionData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker"
        )
        
        format_dict = create_format_dict_pure(data)
        
        assert "image_name" in format_dict
        assert "container_name" in format_dict
        assert "oj_image_name" in format_dict
        assert "oj_container_name" in format_dict


class TestStringFormatting:
    """Test string formatting functions"""
    
    def test_format_string_all_keys_present(self):
        """Test formatting when all keys are present"""
        template = "Contest {contest_name}, Problem {problem_name}"
        format_dict = {
            "contest_name": "abc123",
            "problem_name": "a"
        }
        
        result = format_string_pure(template, format_dict)
        assert result == "Contest abc123, Problem a"
    
    def test_format_string_missing_keys(self):
        """Test formatting with missing keys"""
        template = "Contest {contest_name}, Missing {missing_key}"
        format_dict = {
            "contest_name": "abc123"
        }
        
        result = format_string_pure(template, format_dict)
        assert result == "Contest abc123, Missing {missing_key}"
    
    def test_format_string_empty_dict(self):
        """Test formatting with empty dictionary"""
        template = "{key1} and {key2}"
        format_dict = {}
        
        result = format_string_pure(template, format_dict)
        assert result == "{key1} and {key2}"


class TestConfigResolution:
    """Test configuration path resolution"""
    
    def test_resolve_simple_path(self):
        """Test resolving a simple configuration path"""
        env_json = {
            "python": {
                "commands": {
                    "build": {
                        "steps": ["step1", "step2"]
                    }
                }
            }
        }
        
        result = resolve_config_path_pure(
            ["commands", "build", "steps"],
            env_json,
            "python",
            "build"
        )
        
        assert result == ["step1", "step2"]
    
    def test_resolve_nonexistent_path(self):
        """Test resolving a non-existent path"""
        env_json = {"python": {"commands": {}}}
        
        result = resolve_config_path_pure(
            ["commands", "build", "steps"],
            env_json,
            "python",
            "build"
        )
        
        assert result is None
    
    def test_resolve_with_empty_env_json(self):
        """Test resolving with empty env_json"""
        result = resolve_config_path_pure(
            ["commands"],
            {},
            "python",
            "build"
        )
        
        assert result is None


class TestStepContextConversion:
    """Test conversion to step context"""
    
    def test_basic_conversion(self):
        """Test basic conversion to step context"""
        data = ExecutionData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker"
        )
        
        step_context = execution_data_to_step_context_pure(data)
        
        assert isinstance(step_context, StepContextData)
        assert step_context.contest_name == "abc123"
        assert step_context.problem_name == "a"
        assert step_context.language == "python"
        assert step_context.env_type == "docker"
        assert step_context.command_type == "build"
        assert step_context.workspace_path == "./workspace"
        assert step_context.contest_current_path == "./contest_current"
    
    def test_conversion_with_paths(self):
        """Test conversion with custom paths"""
        data = ExecutionData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            workspace_path="/custom/workspace",
            contest_current_path="/custom/current",
            contest_stock_path="/custom/stock"
        )
        
        step_context = execution_data_to_step_context_pure(data)
        
        assert step_context.workspace_path == "/custom/workspace"
        assert step_context.contest_current_path == "/custom/current"
        assert step_context.contest_stock_path == "/custom/stock"
    
    def test_immutable_data_structures(self):
        """Test that data structures are immutable"""
        data = ExecutionData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker"
        )
        
        # ExecutionData should be immutable
        with pytest.raises(AttributeError):
            data.command_type = "test"
        
        step_context = execution_data_to_step_context_pure(data)
        
        # StepContextData should be immutable
        with pytest.raises(AttributeError):
            step_context.contest_name = "xyz"
"""
Comprehensive tests for unified formatting API
"""
import pytest
from unittest.mock import Mock
from src.pure_functions.formatting import (
    # Core functions
    extract_format_keys,
    format_with_missing_keys,
    format_with_context,
    SafeFormatter,
    build_path_template,
    validate_template_keys,
    TemplateValidator,
    validate_format_data,
    FormatDataValidator,
    
    # Specialized functions
    ExecutionFormatData,
    create_execution_format_dict,
    format_execution_template,
    validate_execution_format_data,
    get_docker_naming_context,
    OutputFormatData,
    extract_output_data,
    format_output_content,
    decide_output_action,
    should_show_output,
    build_context_path,
    format_path_template,
    validate_path_template,
    
    # Backward compatibility aliases
    extract_template_keys,
    safe_format_template,
    create_format_dict,
    format_template_string,
    validate_execution_data,
    get_docker_naming_from_data,
    SimpleOutputData,
    
    # Unified API classes
    UnifiedFormatter,
    ExecutionContextFormatter,
    OutputFormatter
)


class TestUnifiedAPIImports:
    """Test that all functions are properly imported"""
    
    def test_core_functions_imported(self):
        """Test that core functions are imported"""
        # Test that functions exist and are callable
        assert callable(extract_format_keys)
        assert callable(format_with_missing_keys)
        assert callable(format_with_context)
        assert callable(build_path_template)
        assert callable(validate_template_keys)
        assert callable(validate_format_data)
        
        # Test that classes exist
        assert SafeFormatter
        assert TemplateValidator
        assert FormatDataValidator
    
    def test_specialized_functions_imported(self):
        """Test that specialized functions are imported"""
        # Test that functions exist and are callable
        assert callable(create_execution_format_dict)
        assert callable(format_execution_template)
        assert callable(validate_execution_format_data)
        assert callable(get_docker_naming_context)
        assert callable(extract_output_data)
        assert callable(format_output_content)
        assert callable(decide_output_action)
        assert callable(should_show_output)
        assert callable(build_context_path)
        assert callable(format_path_template)
        assert callable(validate_path_template)
        
        # Test that classes exist
        assert ExecutionFormatData
        assert OutputFormatData
    
    def test_backward_compatibility_aliases(self):
        """Test that backward compatibility aliases work"""
        # Test aliases are the same as original functions
        assert extract_template_keys == extract_format_keys
        assert safe_format_template == format_with_missing_keys
        assert create_format_dict == create_execution_format_dict
        assert format_template_string == format_execution_template
        assert validate_execution_data == validate_execution_format_data
        assert get_docker_naming_from_data == get_docker_naming_context
        assert SimpleOutputData == OutputFormatData
        
        # Test functional compatibility
        result = extract_template_keys("/path/{foo}/{bar}")
        assert result == ["foo", "bar"]


class TestUnifiedFormatter:
    """Test UnifiedFormatter class"""
    
    def test_unified_formatter_initialization(self):
        """Test UnifiedFormatter initialization"""
        formatter = UnifiedFormatter()
        assert formatter.string_formatter is not None
        assert formatter.template_validator is not None
        assert formatter.data_validator is not None
    
    def test_unified_formatter_with_default_context(self):
        """Test UnifiedFormatter with default context"""
        default_context = {"env": "test", "project": "myapp"}
        formatter = UnifiedFormatter(default_context)
        
        result = formatter.format_string("{env}/{project}/file.txt")
        assert result == "test/myapp/file.txt"
    
    def test_format_string_method(self):
        """Test format_string method"""
        formatter = UnifiedFormatter()
        
        result = formatter.format_string(
            "/path/{name}/{type}",
            {"name": "myfile", "type": "source"}
        )
        assert result == "/path/myfile/source"
    
    def test_format_with_validation_method(self):
        """Test format_with_validation method"""
        formatter = UnifiedFormatter()
        
        result, missing = formatter.format_with_validation(
            "/path/{name}/{missing}",
            {"name": "myfile"}
        )
        assert result == "/path/myfile/{missing}"
        assert missing == ["missing"]
    
    def test_validate_template_method(self):
        """Test validate_template method"""
        formatter = UnifiedFormatter()
        
        is_valid, missing = formatter.validate_template(
            "/path/{name}/{type}",
            ["name", "type", "extra"]
        )
        assert is_valid is False
        assert missing == ["extra"]
    
    def test_get_template_keys_method(self):
        """Test get_template_keys method"""
        formatter = UnifiedFormatter()
        
        keys = formatter.get_template_keys("/path/{name}/{type}")
        assert keys == ["name", "type"]
    
    def test_validate_data_method(self):
        """Test validate_data method"""
        formatter = UnifiedFormatter()
        
        data = {"name": "test", "value": 42}
        is_valid, errors = formatter.validate_data(data, ["name", "value"])
        assert is_valid is True
        assert errors == []
        
        # Test with missing field
        is_valid, errors = formatter.validate_data(data, ["name", "missing"])
        assert is_valid is False
        assert len(errors) > 0


class TestExecutionContextFormatter:
    """Test ExecutionContextFormatter class"""
    
    def test_execution_formatter_initialization_no_data(self):
        """Test ExecutionContextFormatter without default data"""
        formatter = ExecutionContextFormatter()
        assert formatter.execution_data is None
    
    def test_execution_formatter_initialization_with_data(self):
        """Test ExecutionContextFormatter with default data"""
        data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        formatter = ExecutionContextFormatter(data)
        assert formatter.execution_data == data
    
    def test_format_template_method(self):
        """Test format_template method"""
        data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        formatter = ExecutionContextFormatter(data)
        
        result, missing = formatter.format_template("/{contest_name}/{problem_name}")
        assert result == "/abc123/a"
        assert missing == set()
    
    def test_format_template_with_explicit_data(self):
        """Test format_template method with explicit data"""
        formatter = ExecutionContextFormatter()
        
        data = ExecutionFormatData(
            command_type="test",
            language="cpp",
            contest_name="def456",
            problem_name="b",
            env_type="local",
            env_json={}
        )
        
        result, missing = formatter.format_template("/{contest_name}/{language}", data)
        assert result == "/def456/cpp"
        assert missing == set()
    
    def test_format_template_no_data_error(self):
        """Test format_template method without data raises error"""
        formatter = ExecutionContextFormatter()
        
        with pytest.raises(ValueError, match="ExecutionFormatData is required"):
            formatter.format_template("/{contest_name}")
    
    def test_create_format_dict_method(self):
        """Test create_format_dict method"""
        data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        formatter = ExecutionContextFormatter(data)
        
        format_dict = formatter.create_format_dict()
        assert format_dict["command_type"] == "build"
        assert format_dict["language"] == "python"
        assert format_dict["contest_name"] == "abc123"
    
    def test_validate_data_method(self):
        """Test validate_data method"""
        data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        formatter = ExecutionContextFormatter(data)
        
        is_valid, error = formatter.validate_data()
        assert is_valid is True
        assert error is None
    
    @pytest.mark.skip(reason="Requires Docker naming utils which may not be available")
    def test_get_docker_context_method(self):
        """Test get_docker_context method"""
        data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        formatter = ExecutionContextFormatter(data)
        
        # This test might fail if Docker naming utils are not available
        try:
            docker_context = formatter.get_docker_context()
            assert isinstance(docker_context, dict)
        except ImportError:
            pytest.skip("Docker naming utils not available")


class TestOutputFormatterUnified:
    """Test unified OutputFormatter class"""
    
    def test_output_formatter_initialization(self):
        """Test OutputFormatter initialization"""
        formatter = OutputFormatter()
        assert formatter.formatter is not None
    
    def test_output_formatter_custom_prefixes(self):
        """Test OutputFormatter with custom prefixes"""
        formatter = OutputFormatter(stdout_prefix="[OUT] ", stderr_prefix="[ERR] ")
        
        # The formatter should use these prefixes
        assert formatter.formatter.stdout_prefix == "[OUT] "
        assert formatter.formatter.stderr_prefix == "[ERR] "
    
    def test_extract_data_method(self):
        """Test extract_data method"""
        formatter = OutputFormatter()
        
        mock_result = Mock()
        mock_result.stdout = "Hello"
        mock_result.stderr = "Error"
        
        data = formatter.extract_data(mock_result)
        assert data.stdout == "Hello"
        assert data.stderr == "Error"
    
    def test_format_content_method(self):
        """Test format_content method"""
        formatter = OutputFormatter(stdout_prefix="[OUT] ", stderr_prefix="[ERR] ")
        
        data = OutputFormatData(stdout="Hello", stderr="Error")
        result = formatter.format_content(data)
        
        assert result == "[OUT] Hello[ERR] Error"
    
    def test_decide_action_method(self):
        """Test decide_action method"""
        formatter = OutputFormatter()
        
        data = OutputFormatData(stdout="Hello")
        should_output, content = formatter.decide_action(True, data)
        
        assert should_output is True
        assert "Hello" in content
    
    def test_should_show_method(self):
        """Test should_show method"""
        formatter = OutputFormatter()
        
        mock_request = Mock()
        mock_request.show_output = True
        
        result = formatter.should_show(mock_request)
        assert result is True


class TestIntegrationWorkflows:
    """Test complete integration workflows"""
    
    def test_complete_execution_workflow(self):
        """Test complete execution context formatting workflow"""
        # Create execution data
        execution_data = ExecutionFormatData(
            command_type="build",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={
                "python": {
                    "source_file_name": "main.py",
                    "workspace_path": "/workspace"
                }
            }
        )
        
        # Create formatter
        formatter = ExecutionContextFormatter(execution_data)
        
        # Validate data
        is_valid, error = formatter.validate_data()
        assert is_valid is True
        assert error is None
        
        # Create format dictionary
        format_dict = formatter.create_format_dict()
        assert format_dict["language"] == "python"
        assert format_dict["source_file_name"] == "main.py"
        
        # Format template
        template = "{workspace_path}/{contest_name}/{problem_name}/{source_file_name}"
        result, missing = formatter.format_template(template)
        
        assert result == "/workspace/abc123/a/main.py"
        assert missing == set()
    
    def test_complete_output_workflow(self):
        """Test complete output formatting workflow"""
        # Create mock result
        mock_result = Mock()
        mock_result.stdout = "Build successful\n"
        mock_result.stderr = "Warning: deprecated function\n"
        
        # Create mock request
        mock_request = Mock()
        mock_request.show_output = True
        
        # Create formatter
        formatter = OutputFormatter(stdout_prefix="[BUILD] ", stderr_prefix="[WARN] ")
        
        # Extract data
        output_data = formatter.extract_data(mock_result)
        assert output_data.stdout == "Build successful\n"
        assert output_data.stderr == "Warning: deprecated function\n"
        
        # Check if should show
        should_show = formatter.should_show(mock_request)
        assert should_show is True
        
        # Format content
        formatted = formatter.format_content(output_data)
        assert formatted == "[BUILD] Build successful\n[WARN] Warning: deprecated function\n"
        
        # Decide action
        should_output, content = formatter.decide_action(should_show, output_data)
        assert should_output is True
        assert content == formatted
    
    def test_unified_formatter_complete_workflow(self):
        """Test UnifiedFormatter complete workflow"""
        # Create formatter with default context
        default_context = {"base_path": "/projects", "env": "development"}
        formatter = UnifiedFormatter(default_context)
        
        # Template validation
        template = "{base_path}/{project_name}/{env}/src"
        is_valid, missing = formatter.validate_template(template, ["base_path", "project_name", "env"])
        assert is_valid is True
        assert missing == []
        
        # Get template keys
        keys = formatter.get_template_keys(template)
        assert keys == ["base_path", "project_name", "env"]
        
        # Format with additional context
        additional_context = {"project_name": "myapp"}
        result = formatter.format_string(template, additional_context)
        assert result == "/projects/myapp/development/src"
        
        # Format with validation
        result, missing = formatter.format_with_validation(template, additional_context)
        assert result == "/projects/myapp/development/src"
        assert missing == []
    
    def test_cross_layer_integration(self):
        """Test integration between different layers"""
        # Test using core functions directly
        template = "/base/{project}/{env}"
        keys = extract_format_keys(template)
        assert keys == ["project", "env"]
        
        # Test using unified API
        formatter = UnifiedFormatter()
        unified_keys = formatter.get_template_keys(template)
        assert unified_keys == keys
        
        # Test backward compatibility
        legacy_keys = extract_template_keys(template)
        assert legacy_keys == keys
        
        # Test execution formatting integration
        execution_data = ExecutionFormatData(
            command_type="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="docker",
            env_json={}
        )
        
        # Direct function call
        direct_result, direct_missing = format_execution_template("/{contest_name}/{language}", execution_data)
        
        # Unified API call
        exec_formatter = ExecutionContextFormatter(execution_data)
        unified_result, unified_missing = exec_formatter.format_template("/{contest_name}/{language}")
        
        # Legacy function call
        legacy_result, legacy_missing = format_template_string("/{contest_name}/{language}", execution_data)
        
        # All should produce the same result
        assert direct_result == unified_result == legacy_result == "/abc123/python"
        assert direct_missing == unified_missing == legacy_missing == set()


class TestErrorHandling:
    """Test error handling across the unified API"""
    
    def test_unified_formatter_error_handling(self):
        """Test UnifiedFormatter error handling"""
        formatter = UnifiedFormatter()
        
        # Invalid data validation
        invalid_data = None
        is_valid, errors = formatter.validate_data(invalid_data, ["required_field"])
        assert is_valid is False
        assert len(errors) > 0
    
    def test_execution_formatter_error_handling(self):
        """Test ExecutionContextFormatter error handling"""
        formatter = ExecutionContextFormatter()
        
        # No data provided
        with pytest.raises(ValueError):
            formatter.format_template("/{test}")
        
        with pytest.raises(ValueError):
            formatter.create_format_dict()
        
        with pytest.raises(ValueError):
            formatter.validate_data()
    
    def test_output_formatter_error_handling(self):
        """Test OutputFormatter error handling"""
        formatter = OutputFormatter()
        
        # Empty result object
        mock_result = Mock(spec=[])  # No attributes
        data = formatter.extract_data(mock_result)
        
        assert data.stdout is None
        assert data.stderr is None
        
        # Should handle gracefully
        formatted = formatter.format_content(data)
        assert formatted == ""
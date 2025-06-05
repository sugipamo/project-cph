"""
Comprehensive tests for output formatter module
"""
import pytest
from unittest.mock import Mock
from src.pure_functions.formatting.specialized.output_formatter import (
    OutputFormatData,
    extract_output_data,
    should_show_output,
    format_output_content,
    decide_output_action,
    format_with_prefix,
    filter_output_content,
    OutputFormatter,
    # Backward compatibility aliases
    SimpleOutputData
)


class TestOutputFormatData:
    """Test OutputFormatData dataclass"""
    
    def test_dataclass_creation_with_defaults(self):
        """Test creating OutputFormatData with default values"""
        data = OutputFormatData()
        assert data.stdout is None
        assert data.stderr is None
    
    def test_dataclass_creation_with_values(self):
        """Test creating OutputFormatData with explicit values"""
        data = OutputFormatData(stdout="Hello", stderr="Error")
        assert data.stdout == "Hello"
        assert data.stderr == "Error"
    
    def test_dataclass_immutable(self):
        """Test that OutputFormatData is immutable (frozen)"""
        data = OutputFormatData(stdout="Hello")
        
        with pytest.raises(Exception):  # Should raise FrozenInstanceError or AttributeError
            data.stdout = "Modified"


class TestExtractOutputData:
    """Test extract_output_data function"""
    
    def test_extract_from_object_with_both_outputs(self):
        """Test extracting output data from object with both stdout and stderr"""
        mock_result = Mock()
        mock_result.stdout = "Standard output"
        mock_result.stderr = "Error output"
        
        data = extract_output_data(mock_result)
        
        assert data.stdout == "Standard output"
        assert data.stderr == "Error output"
    
    def test_extract_from_object_with_stdout_only(self):
        """Test extracting output data from object with stdout only"""
        mock_result = Mock()
        mock_result.stdout = "Only stdout"
        del mock_result.stderr  # Remove stderr attribute
        
        data = extract_output_data(mock_result)
        
        assert data.stdout == "Only stdout"
        assert data.stderr is None
    
    def test_extract_from_object_with_stderr_only(self):
        """Test extracting output data from object with stderr only"""
        mock_result = Mock()
        del mock_result.stdout  # Remove stdout attribute
        mock_result.stderr = "Only stderr"
        
        data = extract_output_data(mock_result)
        
        assert data.stdout is None
        assert data.stderr == "Only stderr"
    
    def test_extract_from_object_with_no_outputs(self):
        """Test extracting output data from object with no output attributes"""
        mock_result = Mock(spec=[])  # Empty spec means no attributes
        
        data = extract_output_data(mock_result)
        
        assert data.stdout is None
        assert data.stderr is None
    
    def test_extract_from_object_with_none_outputs(self):
        """Test extracting output data when outputs are None"""
        mock_result = Mock()
        mock_result.stdout = None
        mock_result.stderr = None
        
        data = extract_output_data(mock_result)
        
        assert data.stdout is None
        assert data.stderr is None


class TestShouldShowOutput:
    """Test should_show_output function"""
    
    def test_should_show_output_true(self):
        """Test should_show_output when show_output is True"""
        mock_request = Mock()
        mock_request.show_output = True
        
        result = should_show_output(mock_request)
        assert result is True
    
    def test_should_show_output_false(self):
        """Test should_show_output when show_output is False"""
        mock_request = Mock()
        mock_request.show_output = False
        
        result = should_show_output(mock_request)
        assert result is False
    
    def test_should_show_output_missing_attribute(self):
        """Test should_show_output when show_output attribute is missing"""
        mock_request = Mock(spec=[])  # No show_output attribute
        
        result = should_show_output(mock_request)
        assert result is False
    
    def test_should_show_output_truthy_values(self):
        """Test should_show_output with various truthy values"""
        mock_request = Mock()
        
        # Test with different truthy values
        truthy_values = [True, 1, "true", [1], {"key": "value"}]
        for value in truthy_values:
            mock_request.show_output = value
            assert should_show_output(mock_request) is True
    
    def test_should_show_output_falsy_values(self):
        """Test should_show_output with various falsy values"""
        mock_request = Mock()
        
        # Test with different falsy values
        falsy_values = [False, 0, "", [], {}, None]
        for value in falsy_values:
            mock_request.show_output = value
            assert should_show_output(mock_request) is False


class TestFormatOutputContent:
    """Test format_output_content function"""
    
    def test_format_with_both_outputs(self):
        """Test formatting with both stdout and stderr"""
        data = OutputFormatData(stdout="Hello", stderr="Error")
        result = format_output_content(data)
        assert result == "HelloError"
    
    def test_format_with_stdout_only(self):
        """Test formatting with stdout only"""
        data = OutputFormatData(stdout="Hello")
        result = format_output_content(data)
        assert result == "Hello"
    
    def test_format_with_stderr_only(self):
        """Test formatting with stderr only"""
        data = OutputFormatData(stderr="Error")
        result = format_output_content(data)
        assert result == "Error"
    
    def test_format_with_no_outputs(self):
        """Test formatting with no outputs"""
        data = OutputFormatData()
        result = format_output_content(data)
        assert result == ""
    
    def test_format_with_empty_strings(self):
        """Test formatting with empty string outputs"""
        data = OutputFormatData(stdout="", stderr="")
        result = format_output_content(data)
        assert result == ""
    
    def test_format_with_multiline_outputs(self):
        """Test formatting with multiline outputs"""
        data = OutputFormatData(
            stdout="Line 1\nLine 2\n",
            stderr="Error line 1\nError line 2\n"
        )
        result = format_output_content(data)
        assert result == "Line 1\nLine 2\nError line 1\nError line 2\n"


class TestDecideOutputAction:
    """Test decide_output_action function"""
    
    def test_decide_action_show_true_with_output(self):
        """Test decision when show_output is True and there is output"""
        data = OutputFormatData(stdout="Hello")
        should_output, content = decide_output_action(True, data)
        
        assert should_output is True
        assert content == "Hello"
    
    def test_decide_action_show_false(self):
        """Test decision when show_output is False"""
        data = OutputFormatData(stdout="Hello")
        should_output, content = decide_output_action(False, data)
        
        assert should_output is False
        assert content == ""
    
    def test_decide_action_show_true_no_output(self):
        """Test decision when show_output is True but no output"""
        data = OutputFormatData()
        should_output, content = decide_output_action(True, data)
        
        assert should_output is False
        assert content == ""
    
    def test_decide_action_show_true_empty_outputs(self):
        """Test decision when show_output is True but outputs are empty"""
        data = OutputFormatData(stdout="", stderr="")
        should_output, content = decide_output_action(True, data)
        
        assert should_output is False
        assert content == ""
    
    def test_decide_action_show_true_whitespace_only(self):
        """Test decision when show_output is True but outputs are whitespace only"""
        data = OutputFormatData(stdout="   ", stderr="\n\t")
        should_output, content = decide_output_action(True, data)
        
        assert should_output is True  # Whitespace is still considered content
        assert content == "   \n\t"


class TestFormatWithPrefix:
    """Test format_with_prefix function"""
    
    def test_format_with_default_prefixes(self):
        """Test formatting with default prefixes"""
        data = OutputFormatData(stdout="Hello", stderr="Error")
        result = format_with_prefix(data)
        
        assert result == "Hello[ERROR] Error"
    
    def test_format_with_custom_prefixes(self):
        """Test formatting with custom prefixes"""
        data = OutputFormatData(stdout="Hello", stderr="Error")
        result = format_with_prefix(data, stdout_prefix="[OUT] ", stderr_prefix="[ERR] ")
        
        assert result == "[OUT] Hello[ERR] Error"
    
    def test_format_with_no_prefixes(self):
        """Test formatting with no prefixes"""
        data = OutputFormatData(stdout="Hello", stderr="Error")
        result = format_with_prefix(data, stdout_prefix="", stderr_prefix="")
        
        assert result == "HelloError"
    
    def test_format_with_stdout_only(self):
        """Test formatting stdout only with prefix"""
        data = OutputFormatData(stdout="Hello")
        result = format_with_prefix(data, stdout_prefix="[OUT] ")
        
        assert result == "[OUT] Hello"
    
    def test_format_with_stderr_only(self):
        """Test formatting stderr only with prefix"""
        data = OutputFormatData(stderr="Error")
        result = format_with_prefix(data, stderr_prefix="[ERR] ")
        
        assert result == "[ERR] Error"
    
    def test_format_with_multiline_and_prefixes(self):
        """Test formatting multiline content with prefixes"""
        data = OutputFormatData(
            stdout="Line 1\nLine 2",
            stderr="Error 1\nError 2"
        )
        result = format_with_prefix(data, stdout_prefix="[OUT] ", stderr_prefix="[ERR] ")
        
        assert result == "[OUT] Line 1\nLine 2[ERR] Error 1\nError 2"


class TestFilterOutputContent:
    """Test filter_output_content function"""
    
    def test_filter_empty_default(self):
        """Test filtering empty strings (default behavior)"""
        data = OutputFormatData(stdout="", stderr="Error")
        filtered = filter_output_content(data)
        
        assert filtered.stdout is None
        assert filtered.stderr == "Error"
    
    def test_filter_empty_disabled(self):
        """Test with empty string filtering disabled"""
        data = OutputFormatData(stdout="", stderr="Error")
        filtered = filter_output_content(data, filter_empty=False)
        
        assert filtered.stdout == ""
        assert filtered.stderr == "Error"
    
    def test_filter_whitespace_enabled(self):
        """Test filtering whitespace-only strings"""
        data = OutputFormatData(stdout="   \n\t", stderr="Error")
        filtered = filter_output_content(data, filter_whitespace=True)
        
        assert filtered.stdout is None
        assert filtered.stderr == "Error"
    
    def test_filter_whitespace_disabled(self):
        """Test with whitespace filtering disabled"""
        data = OutputFormatData(stdout="   \n\t", stderr="Error")
        filtered = filter_output_content(data, filter_whitespace=False)
        
        assert filtered.stdout == "   \n\t"
        assert filtered.stderr == "Error"
    
    def test_filter_none_values(self):
        """Test filtering None values"""
        data = OutputFormatData(stdout=None, stderr="Error")
        filtered = filter_output_content(data)
        
        assert filtered.stdout is None
        assert filtered.stderr == "Error"
    
    def test_filter_both_options(self):
        """Test with both filtering options enabled"""
        data = OutputFormatData(stdout="", stderr="   ")
        filtered = filter_output_content(data, filter_empty=True, filter_whitespace=True)
        
        assert filtered.stdout is None
        assert filtered.stderr is None
    
    def test_filter_preserves_valid_content(self):
        """Test that valid content is preserved"""
        data = OutputFormatData(stdout="Valid content", stderr="Error message")
        filtered = filter_output_content(data, filter_empty=True, filter_whitespace=True)
        
        assert filtered.stdout == "Valid content"
        assert filtered.stderr == "Error message"


class TestOutputFormatter:
    """Test OutputFormatter class"""
    
    def test_formatter_initialization_defaults(self):
        """Test OutputFormatter with default values"""
        formatter = OutputFormatter()
        
        assert formatter.stdout_prefix == ""
        assert formatter.stderr_prefix == "[ERROR] "
        assert formatter.filter_empty is True
        assert formatter.filter_whitespace is False
    
    def test_formatter_initialization_custom(self):
        """Test OutputFormatter with custom values"""
        formatter = OutputFormatter(
            stdout_prefix="[OUT] ",
            stderr_prefix="[ERR] ",
            filter_empty=False,
            filter_whitespace=True
        )
        
        assert formatter.stdout_prefix == "[OUT] "
        assert formatter.stderr_prefix == "[ERR] "
        assert formatter.filter_empty is False
        assert formatter.filter_whitespace is True
    
    def test_formatter_format_method(self):
        """Test OutputFormatter format method"""
        formatter = OutputFormatter(stdout_prefix="[OUT] ", stderr_prefix="[ERR] ")
        data = OutputFormatData(stdout="Hello", stderr="Error")
        
        result = formatter.format(data)
        assert result == "[OUT] Hello[ERR] Error"
    
    def test_formatter_format_with_filtering(self):
        """Test OutputFormatter format method with filtering"""
        formatter = OutputFormatter(
            stdout_prefix="[OUT] ",
            stderr_prefix="[ERR] ",
            filter_empty=True
        )
        data = OutputFormatData(stdout="", stderr="Error")
        
        result = formatter.format(data)
        assert result == "[ERR] Error"
    
    def test_formatter_decide_action_method(self):
        """Test OutputFormatter decide_action method"""
        formatter = OutputFormatter(stdout_prefix="[OUT] ")
        data = OutputFormatData(stdout="Hello")
        
        should_output, content = formatter.decide_action(True, data)
        assert should_output is True
        assert content == "[OUT] Hello"
    
    def test_formatter_decide_action_no_show(self):
        """Test OutputFormatter decide_action when show_output is False"""
        formatter = OutputFormatter()
        data = OutputFormatData(stdout="Hello")
        
        should_output, content = formatter.decide_action(False, data)
        assert should_output is False
        assert content == ""
    
    def test_formatter_decide_action_filtered_empty(self):
        """Test OutputFormatter decide_action with filtered empty content"""
        formatter = OutputFormatter(filter_empty=True)
        data = OutputFormatData(stdout="", stderr="")
        
        should_output, content = formatter.decide_action(True, data)
        assert should_output is False
        assert content == ""


class TestBackwardCompatibility:
    """Test backward compatibility aliases"""
    
    def test_simple_output_data_alias(self):
        """Test SimpleOutputData is an alias for OutputFormatData"""
        assert SimpleOutputData == OutputFormatData
        
        # Functional test
        data = SimpleOutputData(stdout="test", stderr="error")
        assert data.stdout == "test"
        assert data.stderr == "error"


class TestIntegrationScenarios:
    """Test real-world integration scenarios"""
    
    def test_complete_output_processing_pipeline(self):
        """Test complete output processing from result to formatted output"""
        # Mock result object
        mock_result = Mock()
        mock_result.stdout = "Build successful\n"
        mock_result.stderr = "Warning: deprecated function\n"
        
        # Mock request object
        mock_request = Mock()
        mock_request.show_output = True
        
        # Extract data
        output_data = extract_output_data(mock_result)
        
        # Check if should show output
        show_output = should_show_output(mock_request)
        
        # Format with custom formatter
        formatter = OutputFormatter(
            stdout_prefix="[BUILD] ",
            stderr_prefix="[WARN] ",
            filter_empty=True
        )
        
        # Decide action
        should_output, formatted_content = formatter.decide_action(show_output, output_data)
        
        assert should_output is True
        assert formatted_content == "[BUILD] Build successful\n[WARN] Warning: deprecated function\n"
    
    def test_empty_output_handling(self):
        """Test handling of completely empty output"""
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        
        mock_request = Mock()
        mock_request.show_output = True
        
        output_data = extract_output_data(mock_result)
        show_output = should_show_output(mock_request)
        
        should_output, content = decide_output_action(show_output, output_data)
        
        assert should_output is False
        assert content == ""
    
    def test_error_only_output(self):
        """Test handling of error-only output"""
        mock_result = Mock()
        del mock_result.stdout  # No stdout
        mock_result.stderr = "Fatal error occurred"
        
        mock_request = Mock()
        mock_request.show_output = True
        
        output_data = extract_output_data(mock_result)
        show_output = should_show_output(mock_request)
        
        formatter = OutputFormatter(stderr_prefix="[ERROR] ")
        should_output, formatted_content = formatter.decide_action(show_output, output_data)
        
        assert should_output is True
        assert formatted_content == "[ERROR] Fatal error occurred"
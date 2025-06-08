"""Tests for output formatters module"""

from unittest.mock import Mock

import pytest

from src.application.orchestration.output_formatters import (
    SimpleOutputData,
    decide_output_action,
    extract_output_data,
    format_output_content,
    should_show_output,
)


class TestSimpleOutputData:
    """Test cases for SimpleOutputData dataclass"""

    def test_simple_output_data_creation(self):
        """Test SimpleOutputData creation with default values"""
        data = SimpleOutputData()

        assert data.stdout is None
        assert data.stderr is None

    def test_simple_output_data_with_stdout(self):
        """Test SimpleOutputData creation with stdout"""
        data = SimpleOutputData(stdout="test output")

        assert data.stdout == "test output"
        assert data.stderr is None

    def test_simple_output_data_with_stderr(self):
        """Test SimpleOutputData creation with stderr"""
        data = SimpleOutputData(stderr="error output")

        assert data.stdout is None
        assert data.stderr == "error output"

    def test_simple_output_data_with_both(self):
        """Test SimpleOutputData creation with both stdout and stderr"""
        data = SimpleOutputData(stdout="output", stderr="error")

        assert data.stdout == "output"
        assert data.stderr == "error"

    def test_simple_output_data_immutable(self):
        """Test that SimpleOutputData is immutable (frozen=True)"""
        data = SimpleOutputData(stdout="test")

        with pytest.raises(AttributeError):
            data.stdout = "modified"


class TestExtractOutputData:
    """Test cases for extract_output_data function"""

    def test_extract_output_data_with_stdout(self):
        """Test extracting output data with stdout"""
        result = Mock()
        result.stdout = "test output"
        result.stderr = None

        data = extract_output_data(result)

        assert isinstance(data, SimpleOutputData)
        assert data.stdout == "test output"
        assert data.stderr is None

    def test_extract_output_data_with_stderr(self):
        """Test extracting output data with stderr"""
        result = Mock()
        result.stdout = None
        result.stderr = "error output"

        data = extract_output_data(result)

        assert data.stdout is None
        assert data.stderr == "error output"

    def test_extract_output_data_with_both(self):
        """Test extracting output data with both stdout and stderr"""
        result = Mock()
        result.stdout = "output"
        result.stderr = "error"

        data = extract_output_data(result)

        assert data.stdout == "output"
        assert data.stderr == "error"

    def test_extract_output_data_no_attributes(self):
        """Test extracting output data from object without stdout/stderr"""
        result = Mock(spec=[])  # Mock with no attributes

        data = extract_output_data(result)

        assert data.stdout is None
        assert data.stderr is None

    def test_extract_output_data_partial_attributes(self):
        """Test extracting output data with only one attribute"""
        result = Mock()
        result.stdout = "only stdout"
        # Don't set stderr attribute
        delattr(result, 'stderr')

        data = extract_output_data(result)

        assert data.stdout == "only stdout"
        assert data.stderr is None


class TestShouldShowOutput:
    """Test cases for should_show_output function"""

    def test_should_show_output_true(self):
        """Test should_show_output with show_output=True"""
        request = Mock()
        request.show_output = True

        result = should_show_output(request)

        assert result

    def test_should_show_output_false(self):
        """Test should_show_output with show_output=False"""
        request = Mock()
        request.show_output = False

        result = should_show_output(request)

        assert not result

    def test_should_show_output_no_attribute(self):
        """Test should_show_output with no show_output attribute"""
        request = Mock(spec=[])  # Mock with no attributes

        result = should_show_output(request)

        assert not result

    def test_should_show_output_none_value(self):
        """Test should_show_output with show_output=None"""
        request = Mock()
        request.show_output = None

        result = should_show_output(request)

        assert not result

    def test_should_show_output_truthy_value(self):
        """Test should_show_output with truthy non-boolean value"""
        request = Mock()
        request.show_output = "yes"

        result = should_show_output(request)

        assert result

    def test_should_show_output_falsy_value(self):
        """Test should_show_output with falsy non-boolean value"""
        request = Mock()
        request.show_output = ""

        result = should_show_output(request)

        assert not result


class TestFormatOutputContent:
    """Test cases for format_output_content function"""

    def test_format_output_content_stdout_only(self):
        """Test formatting with stdout only"""
        data = SimpleOutputData(stdout="test output")

        result = format_output_content(data)

        assert result == "test output"

    def test_format_output_content_stderr_only(self):
        """Test formatting with stderr only"""
        data = SimpleOutputData(stderr="error output")

        result = format_output_content(data)

        assert result == "error output"

    def test_format_output_content_both(self):
        """Test formatting with both stdout and stderr"""
        data = SimpleOutputData(stdout="output", stderr="error")

        result = format_output_content(data)

        assert result == "outputerror"

    def test_format_output_content_neither(self):
        """Test formatting with neither stdout nor stderr"""
        data = SimpleOutputData()

        result = format_output_content(data)

        assert result == ""

    def test_format_output_content_empty_strings(self):
        """Test formatting with empty strings"""
        data = SimpleOutputData(stdout="", stderr="")

        result = format_output_content(data)

        assert result == ""

    def test_format_output_content_multiline(self):
        """Test formatting with multiline output"""
        data = SimpleOutputData(
            stdout="line1\nline2\n",
            stderr="error1\nerror2\n"
        )

        result = format_output_content(data)

        assert result == "line1\nline2\nerror1\nerror2\n"


class TestDecideOutputAction:
    """Test cases for decide_output_action function"""

    def test_decide_output_action_show_with_content(self):
        """Test deciding output action when show_output=True and has content"""
        data = SimpleOutputData(stdout="test output")

        should_output, content = decide_output_action(True, data)

        assert should_output
        assert content == "test output"

    def test_decide_output_action_no_show(self):
        """Test deciding output action when show_output=False"""
        data = SimpleOutputData(stdout="test output")

        should_output, content = decide_output_action(False, data)

        assert not should_output
        assert content == ""

    def test_decide_output_action_show_no_content(self):
        """Test deciding output action when show_output=True but no content"""
        data = SimpleOutputData()

        should_output, content = decide_output_action(True, data)

        assert not should_output
        assert content == ""

    def test_decide_output_action_show_empty_content(self):
        """Test deciding output action when show_output=True but empty content"""
        data = SimpleOutputData(stdout="", stderr="")

        should_output, content = decide_output_action(True, data)

        assert not should_output
        assert content == ""

    def test_decide_output_action_show_with_stderr(self):
        """Test deciding output action with stderr only"""
        data = SimpleOutputData(stderr="error message")

        should_output, content = decide_output_action(True, data)

        assert should_output
        assert content == "error message"

    def test_decide_output_action_show_with_both(self):
        """Test deciding output action with both stdout and stderr"""
        data = SimpleOutputData(stdout="output", stderr="error")

        should_output, content = decide_output_action(True, data)

        assert should_output
        assert content == "outputerror"

    def test_decide_output_action_whitespace_only(self):
        """Test deciding output action with whitespace-only content"""
        data = SimpleOutputData(stdout="   \n  \t  ")

        should_output, content = decide_output_action(True, data)

        assert should_output  # bool("   \n  \t  ") is True
        assert content == "   \n  \t  "


class TestIntegrationScenarios:
    """Integration test scenarios combining multiple functions"""

    def test_full_workflow_with_output(self):
        """Test full workflow from result extraction to output decision"""
        # Setup mock result
        result = Mock()
        result.stdout = "Command executed successfully"
        result.stderr = None

        # Setup mock request
        request = Mock()
        request.show_output = True

        # Execute workflow
        output_data = extract_output_data(result)
        show_output = should_show_output(request)
        should_output, content = decide_output_action(show_output, output_data)

        # Verify results
        assert should_output
        assert content == "Command executed successfully"

    def test_full_workflow_no_output(self):
        """Test full workflow when output should not be shown"""
        # Setup mock result
        result = Mock()
        result.stdout = "Command executed"
        result.stderr = None

        # Setup mock request
        request = Mock()
        request.show_output = False

        # Execute workflow
        output_data = extract_output_data(result)
        show_output = should_show_output(request)
        should_output, content = decide_output_action(show_output, output_data)

        # Verify results
        assert not should_output
        assert content == ""

    def test_full_workflow_error_case(self):
        """Test full workflow with error output"""
        # Setup mock result
        result = Mock()
        result.stdout = None
        result.stderr = "Command failed with error"

        # Setup mock request
        request = Mock()
        request.show_output = True

        # Execute workflow
        output_data = extract_output_data(result)
        show_output = should_show_output(request)
        should_output, content = decide_output_action(show_output, output_data)

        # Verify results
        assert should_output
        assert content == "Command failed with error"

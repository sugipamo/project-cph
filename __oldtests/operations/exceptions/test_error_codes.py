"""Tests for error codes and suggestions."""
import pytest

from src.operations.exceptions.error_codes import ErrorCode, ErrorSuggestion, classify_error


class TestErrorCode:
    """Test ErrorCode enum."""

    def test_error_code_values(self):
        """Test that error codes have expected values."""
        assert ErrorCode.FILE_NOT_FOUND.value == "FILE_NOT_FOUND"
        assert ErrorCode.COMMAND_NOT_FOUND.value == "COMMAND_NOT_FOUND"
        assert ErrorCode.DOCKER_NOT_AVAILABLE.value == "DOCKER_NOT_AVAILABLE"


class TestErrorSuggestion:
    """Test ErrorSuggestion functionality."""

    def test_get_suggestion_known_error(self):
        """Test getting suggestion for known error code."""
        suggestion = ErrorSuggestion.get_suggestion(ErrorCode.FILE_NOT_FOUND)
        assert "file path exists" in suggestion

    def test_get_suggestion_unknown_error(self):
        """Test getting suggestion for unknown error code."""
        suggestion = ErrorSuggestion.get_suggestion(ErrorCode.UNKNOWN_ERROR)
        assert "Contact support" in suggestion

    def test_get_recovery_actions_known_error(self):
        """Test getting recovery actions for known error code."""
        actions = ErrorSuggestion.get_recovery_actions(ErrorCode.FILE_NOT_FOUND)
        assert isinstance(actions, list)
        assert len(actions) > 0
        assert any("file path" in action for action in actions)

    def test_get_recovery_actions_unknown_error(self):
        """Test getting recovery actions for unknown error code."""
        actions = ErrorSuggestion.get_recovery_actions(ErrorCode.UNKNOWN_ERROR)
        assert actions == ["Contact support for assistance"]


class TestClassifyError:
    """Test error classification functionality."""

    def test_classify_file_not_found(self):
        """Test classification of file not found error."""
        error = FileNotFoundError("No such file or directory")
        result = classify_error(error, "file operation")
        assert result == ErrorCode.FILE_NOT_FOUND

    def test_classify_permission_denied_file(self):
        """Test classification of permission denied for file operations."""
        error = PermissionError("Permission denied")
        result = classify_error(error, "file operation")
        assert result == ErrorCode.FILE_PERMISSION_DENIED

    def test_classify_command_not_found(self):
        """Test classification of command not found error."""
        error = OSError("command not found")
        result = classify_error(error, "shell command")
        assert result == ErrorCode.COMMAND_NOT_FOUND

    def test_classify_timeout_error(self):
        """Test classification of timeout error."""
        error = TimeoutError("timeout")
        result = classify_error(error, "shell command")
        assert result == ErrorCode.COMMAND_TIMEOUT

    def test_classify_docker_error(self):
        """Test classification of Docker-related errors."""
        error = RuntimeError("docker: container not found")
        result = classify_error(error, "docker operation")
        assert result == ErrorCode.CONTAINER_NOT_FOUND

    def test_classify_python_syntax_error(self):
        """Test classification of Python syntax error."""
        error = SyntaxError("invalid syntax")
        result = classify_error(error, "python execution")
        assert result == ErrorCode.PYTHON_SYNTAX_ERROR

    def test_classify_python_module_not_found(self):
        """Test classification of Python module not found error."""
        error = ModuleNotFoundError("No module named 'test'")
        result = classify_error(error, "python execution")
        assert result == ErrorCode.PYTHON_MODULE_NOT_FOUND

    def test_classify_unknown_error(self):
        """Test classification of unknown error."""
        error = ValueError("Some unknown error")
        result = classify_error(error, "unknown context")
        assert result == ErrorCode.UNKNOWN_ERROR

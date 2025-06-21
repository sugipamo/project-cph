"""
Tests for CompositeStepFailureError exception
"""
import pytest

from src.operations.exceptions.composite_step_failure import CompositeStepFailureError


class TestCompositeStepFailureError:

    def test_init_with_message_only(self):
        """Test initialization with message only"""
        exc = CompositeStepFailureError("Test error message")

        assert str(exc) == "Test error message"
        assert exc.result is None
        assert exc.original_exception is None

    def test_init_with_result(self):
        """Test initialization with result"""
        mock_result = {"status": "failed", "error": "Command not found"}
        exc = CompositeStepFailureError("Step failed", result=mock_result)

        assert str(exc) == "Step failed"
        assert exc.result == mock_result
        assert exc.original_exception is None

    def test_init_with_original_exception(self):
        """Test initialization with original exception"""
        original = ValueError("Original error")
        exc = CompositeStepFailureError("Wrapper error", original_exception=original)

        assert str(exc) == "Wrapper error"
        assert exc.result is None
        assert exc.original_exception is original

    def test_init_with_all_parameters(self):
        """Test initialization with all parameters"""
        mock_result = {"status": "failed"}
        original = RuntimeError("Runtime error")
        exc = CompositeStepFailureError(
            "Complete failure",
            result=mock_result,
            original_exception=original
        )

        assert str(exc) == "Complete failure"
        assert exc.result == mock_result
        assert exc.original_exception is original

    def test_inheritance(self):
        """Test that CompositeStepFailureError inherits from Exception"""
        exc = CompositeStepFailureError("Test")

        assert isinstance(exc, Exception)
        assert isinstance(exc, CompositeStepFailureError)



    def test_empty_message(self):
        """Test with empty message"""
        exc = CompositeStepFailureError("")

        assert str(exc) == ""
        assert exc.result is None
        assert exc.original_exception is None

    def test_complex_result_object(self):
        """Test with complex result object"""
        from unittest.mock import Mock

        mock_result = Mock()
        mock_result.success = False
        mock_result.stdout = "Output"
        mock_result.stderr = "Error output"
        mock_result.returncode = 1

        exc = CompositeStepFailureError(
            "Execution failed",
            result=mock_result
        )

        assert exc.result is mock_result
        assert exc.result.success is False
        assert exc.result.returncode == 1

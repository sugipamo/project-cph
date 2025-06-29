"""Tests for Result type implementation."""
import pytest
from typing import Optional

from src.operations.results.result import Result, OperationResult, ValidationResult


class CustomError(Exception):
    """Custom error for testing."""
    pass


class TestResult:
    """Test cases for Result type."""

    def test_init_success_with_value(self):
        """Test initialization of success result with value."""
        result = Result(success=True, value=42, error=None)
        
        assert result._success is True
        assert result._value == 42
        assert result._error is None

    def test_init_failure_with_error(self):
        """Test initialization of failure result with error."""
        error = CustomError("Test error")
        result = Result(success=False, value=None, error=error)
        
        assert result._success is False
        assert result._value is None
        assert result._error is error

    def test_init_success_without_value_raises(self):
        """Test that success result without value raises ValueError."""
        with pytest.raises(ValueError, match="Success result requires value"):
            Result(success=True, value=None, error=None)

    def test_init_failure_without_error_raises(self):
        """Test that failure result without error raises ValueError."""
        with pytest.raises(ValueError, match="Failure result requires error"):
            Result(success=False, value=None, error=None)

    def test_success_class_method(self):
        """Test success class method."""
        result = Result.success("test value")
        
        assert result.is_success()
        assert not result.is_failure()
        assert result._value == "test value"
        assert result._error is None

    def test_failure_class_method(self):
        """Test failure class method."""
        error = CustomError("Test failure")
        result = Result.failure(error)
        
        assert result.is_failure()
        assert not result.is_success()
        assert result._value is None
        assert result._error is error

    def test_is_success(self):
        """Test is_success method."""
        success_result = Result.success(123)
        failure_result = Result.failure(CustomError())
        
        assert success_result.is_success() is True
        assert failure_result.is_success() is False

    def test_is_failure(self):
        """Test is_failure method."""
        success_result = Result.success(123)
        failure_result = Result.failure(CustomError())
        
        assert success_result.is_failure() is False
        assert failure_result.is_failure() is True

    def test_get_value_success(self):
        """Test get_value for successful result."""
        result = Result.success("success value")
        
        assert result.get_value() == "success value"

    def test_get_value_failure_raises(self):
        """Test get_value for failure result raises."""
        result = Result.failure(CustomError("Error"))
        
        with pytest.raises(ValueError, match="Cannot get value from failure result"):
            result.get_value()

    def test_get_error_failure(self):
        """Test get_error for failure result."""
        error = CustomError("Test error")
        result = Result.failure(error)
        
        assert result.get_error() is error

    def test_get_error_success_raises(self):
        """Test get_error for success result raises."""
        result = Result.success(42)
        
        with pytest.raises(ValueError, match="Cannot get error from success result"):
            result.get_error()

    def test_or_else_success(self):
        """Test or_else with success result."""
        result = Result.success("success")
        
        assert result.or_else("default") == "success"

    def test_or_else_failure(self):
        """Test or_else with failure result."""
        result = Result.failure(CustomError())
        
        assert result.or_else("default") == "default"

    def test_map_success(self):
        """Test map with success result."""
        result = Result.success(5)
        mapped = result.map(lambda x: x * 2)
        
        assert mapped.is_success()
        assert mapped.get_value() == 10

    def test_map_failure(self):
        """Test map with failure result."""
        error = CustomError("Error")
        result = Result.failure(error)
        mapped = result.map(lambda x: x * 2)
        
        assert mapped.is_failure()
        assert mapped.get_error() is error


    def test_flat_map_success_to_success(self):
        """Test flat_map with success result returning success."""
        result = Result.success(5)
        flat_mapped = result.flat_map(lambda x: Result.success(x * 2))
        
        assert flat_mapped.is_success()
        assert flat_mapped.get_value() == 10

    def test_flat_map_success_to_failure(self):
        """Test flat_map with success result returning failure."""
        result = Result.success(5)
        flat_mapped = result.flat_map(lambda x: Result.failure(CustomError("Error")))
        
        assert flat_mapped.is_failure()
        assert isinstance(flat_mapped.get_error(), CustomError)

    def test_flat_map_failure(self):
        """Test flat_map with failure result."""
        error = CustomError("Original")
        result = Result.failure(error)
        flat_mapped = result.flat_map(lambda x: Result.success(x * 2))
        
        assert flat_mapped.is_failure()
        assert flat_mapped.get_error() is error


    def test_unwrap_or_raise_success(self):
        """Test unwrap_or_raise with success result."""
        result = Result.success("value")
        
        assert result.unwrap_or_raise() == "value"

    def test_unwrap_or_raise_failure_raises(self):
        """Test unwrap_or_raise with failure result raises."""
        error = CustomError("Test error")
        result = Result.failure(error)
        
        with pytest.raises(CustomError, match="Test error"):
            result.unwrap_or_raise()


class TestOperationResult:
    """Test cases for OperationResult class."""

    def test_init(self):
        """Test initialization of OperationResult."""
        result = OperationResult(
            success=True,
            message="Operation completed",
            details={"key": "value"},
            error_code=None
        )
        
        assert result.success is True
        assert result.message == "Operation completed"
        assert result.details == {"key": "value"}
        assert result.error_code is None

    def test_init_with_none_details(self):
        """Test initialization with None details."""
        result = OperationResult(
            success=False,
            message="Failed",
            details=None,
            error_code="ERR001"
        )
        
        assert result.details == {}

    def test_create_success(self):
        """Test create_success class method."""
        result = OperationResult.create_success(
            message="Success",
            details={"data": 123}
        )
        
        assert result.success is True
        assert result.message == "Success"
        assert result.details == {"data": 123}
        assert result.error_code is None

    def test_create_failure(self):
        """Test create_failure class method."""
        result = OperationResult.create_failure(
            message="Failed",
            error_code="ERR_IO",
            details={"path": "/tmp/file"}
        )
        
        assert result.success is False
        assert result.message == "Failed"
        assert result.error_code == "ERR_IO"
        assert result.details == {"path": "/tmp/file"}

    def test_is_success(self):
        """Test is_success method."""
        success = OperationResult.create_success("OK", None)
        failure = OperationResult.create_failure("Fail", "ERR", None)
        
        assert success.is_success() is True
        assert failure.is_success() is False

    def test_is_failure(self):
        """Test is_failure method."""
        success = OperationResult.create_success("OK", None)
        failure = OperationResult.create_failure("Fail", "ERR", None)
        
        assert success.is_failure() is False
        assert failure.is_failure() is True

    def test_get_message(self):
        """Test get_message method."""
        result = OperationResult(True, "Test message", None, None)
        assert result.get_message() == "Test message"

    def test_get_details(self):
        """Test get_details method."""
        details = {"key": "value", "count": 42}
        result = OperationResult(True, "msg", details, None)
        assert result.get_details() == details

    def test_get_error_code(self):
        """Test get_error_code method."""
        result = OperationResult(False, "msg", None, "ERR_CODE")
        assert result.get_error_code() == "ERR_CODE"

    def test_combine_with_both_success(self):
        """Test combine_with when both results are successful."""
        result1 = OperationResult.create_success("First", {"a": 1})
        result2 = OperationResult.create_success("Second", {"b": 2})
        
        combined = result1.combine_with(result2)
        
        assert combined.is_success()
        assert combined.get_message() == "First; Second"
        assert combined.get_details() == {"a": 1, "b": 2}
        assert combined.get_error_code() is None

    def test_combine_with_first_failure(self):
        """Test combine_with when first result failed."""
        result1 = OperationResult.create_failure("First failed", "ERR1", {"a": 1})
        result2 = OperationResult.create_success("Second", {"b": 2})
        
        combined = result1.combine_with(result2)
        
        assert combined.is_failure()
        assert combined.get_message() == "First failed"
        assert combined.get_details() == {"a": 1, "b": 2}
        assert combined.get_error_code() == "ERR1"

    def test_combine_with_second_failure(self):
        """Test combine_with when second result failed."""
        result1 = OperationResult.create_success("First", {"a": 1})
        result2 = OperationResult.create_failure("Second failed", "ERR2", {"b": 2})
        
        combined = result1.combine_with(result2)
        
        assert combined.is_failure()
        assert combined.get_message() == "Second failed"
        assert combined.get_details() == {"a": 1, "b": 2}
        assert combined.get_error_code() == "ERR2"

    def test_combine_with_both_failure(self):
        """Test combine_with when both results failed."""
        result1 = OperationResult.create_failure("First failed", "ERR1", {"a": 1})
        result2 = OperationResult.create_failure("Second failed", "ERR2", {"b": 2})
        
        combined = result1.combine_with(result2)
        
        assert combined.is_failure()
        assert combined.get_message() == "First failed; Second failed"
        assert combined.get_details() == {"a": 1, "b": 2}
        assert combined.get_error_code() == "ERR1"  # First error code takes precedence


class TestValidationResult:
    """Test cases for ValidationResult class."""

    def test_init(self):
        """Test initialization of ValidationResult."""
        result = ValidationResult(is_valid=True, error_message="")
        
        assert result.is_valid is True
        assert result.error_message == ""

    def test_valid_class_method(self):
        """Test valid class method."""
        result = ValidationResult.valid()
        
        assert result.is_valid is True
        assert result.error_message == ""

    def test_invalid_class_method(self):
        """Test invalid class method."""
        result = ValidationResult.invalid("Field is required")
        
        assert result.is_valid is False
        assert result.error_message == "Field is required"

    def test_raise_if_invalid_valid(self):
        """Test raise_if_invalid with valid result."""
        result = ValidationResult.valid()
        
        # Should not raise
        result.raise_if_invalid(ValueError)

    def test_raise_if_invalid_invalid(self):
        """Test raise_if_invalid with invalid result."""
        result = ValidationResult.invalid("Validation failed")
        
        with pytest.raises(ValueError, match="Validation failed"):
            result.raise_if_invalid(ValueError)


def test_validate_not_none_with_value():
    """Test validate_not_none with non-None value."""
    from src.operations.results.result import validate_not_none
    
    result = validate_not_none("test", "field")
    assert result.is_valid is True

def test_validate_not_none_with_none():
    """Test validate_not_none with None value."""
    from src.operations.results.result import validate_not_none
    
    result = validate_not_none(None, "field")
    assert result.is_valid is False
    assert result.error_message == "field cannot be None"
"""Tests for base result infrastructure types."""
import pytest
from typing import Any

from src.operations.results.base_result import InfrastructureResult, InfrastructureOperationResult


class TestInfrastructureResult:
    """Test cases for InfrastructureResult class."""

    def test_success_creation(self):
        """Test creating a successful result."""
        result = InfrastructureResult.success("test_value")
        
        assert result.is_success()
        assert not result.is_failure()
        assert result.get_value() == "test_value"

    def test_failure_creation(self):
        """Test creating a failure result."""
        error = ValueError("test error")
        result = InfrastructureResult.failure(error)
        
        assert not result.is_success()
        assert result.is_failure()
        assert result.get_error() == error

    def test_init_success_without_value_raises(self):
        """Test that success result requires value."""
        with pytest.raises(ValueError, match="Success result requires value"):
            InfrastructureResult(success=True, value=None, error=None)

    def test_init_failure_without_error_raises(self):
        """Test that failure result requires error."""
        with pytest.raises(ValueError, match="Failure result requires error"):
            InfrastructureResult(success=False, value=None, error=None)

    def test_get_value_from_failure_raises(self):
        """Test getting value from failure result raises error."""
        result = InfrastructureResult.failure(ValueError("error"))
        
        with pytest.raises(ValueError, match="Cannot get value from failure result"):
            result.get_value()

    def test_get_error_from_success_raises(self):
        """Test getting error from success result raises error."""
        result = InfrastructureResult.success("value")
        
        with pytest.raises(ValueError, match="Cannot get error from success result"):
            result.get_error()

    def test_map_success(self):
        """Test mapping function on successful result."""
        result = InfrastructureResult.success(5)
        mapped = result.map(lambda x: x * 2)
        
        assert mapped.is_success()
        assert mapped.get_value() == 10

    def test_map_failure(self):
        """Test mapping function on failure result."""
        error = ValueError("error")
        result = InfrastructureResult.failure(error)
        mapped = result.map(lambda x: x * 2)
        
        assert mapped.is_failure()
        assert mapped.get_error() == error

    def test_flat_map_success(self):
        """Test flat mapping on successful result."""
        result = InfrastructureResult.success(5)
        
        def double_if_positive(x):
            if x > 0:
                return InfrastructureResult.success(x * 2)
            else:
                return InfrastructureResult.failure(ValueError("negative"))
        
        mapped = result.flat_map(double_if_positive)
        
        assert mapped.is_success()
        assert mapped.get_value() == 10

    def test_flat_map_failure(self):
        """Test flat mapping on failure result."""
        error = ValueError("original error")
        result = InfrastructureResult.failure(error)
        
        def double_if_positive(x):
            return InfrastructureResult.success(x * 2)
        
        mapped = result.flat_map(double_if_positive)
        
        assert mapped.is_failure()
        assert mapped.get_error() == error

    def test_or_else_success(self):
        """Test or_else on successful result."""
        result = InfrastructureResult.success("value")
        
        assert result.or_else("default") == "value"

    def test_or_else_failure(self):
        """Test or_else on failure result."""
        result = InfrastructureResult.failure(ValueError("error"))
        
        assert result.or_else("default") == "default"

    def test_unwrap_or_raise_success(self):
        """Test unwrap_or_raise on successful result."""
        result = InfrastructureResult.success("value")
        
        assert result.unwrap_or_raise() == "value"

    def test_unwrap_or_raise_failure(self):
        """Test unwrap_or_raise on failure result."""
        error = ValueError("test error")
        result = InfrastructureResult.failure(error)
        
        with pytest.raises(ValueError, match="test error"):
            result.unwrap_or_raise()

    def test_to_dict_success(self):
        """Test converting successful result to dict."""
        result = InfrastructureResult.success("test_value")
        
        assert result.to_dict() == {
            'success': True,
            'value': 'test_value',
            'error': None
        }

    def test_to_dict_failure(self):
        """Test converting failure result to dict."""
        result = InfrastructureResult.failure(ValueError("test error"))
        
        dict_repr = result.to_dict()
        assert dict_repr['success'] is False
        assert dict_repr['value'] is None
        assert "test error" in dict_repr['error']

    def test_to_dict_complex_values(self):
        """Test converting result with complex values to dict."""
        # Test with dict value
        complex_value = {"nested": {"key": "value"}, "list": [1, 2, 3]}
        result = InfrastructureResult.success(complex_value)
        
        dict_repr = result.to_dict()
        assert dict_repr['success'] is True
        assert dict_repr['value'] == complex_value
        assert dict_repr['error'] is None

    def test_repr_success(self):
        """Test string representation of successful result."""
        result = InfrastructureResult.success("test_value")
        
        assert repr(result) == "<InfrastructureResult.Success: test_value>"

    def test_repr_failure(self):
        """Test string representation of failure result."""
        error = ValueError("test error")
        result = InfrastructureResult.failure(error)
        
        repr_str = repr(result)
        assert "<InfrastructureResult.Failure:" in repr_str
        assert "test error" in repr_str

    def test_type_parameters(self):
        """Test that type parameters work correctly."""
        # Test with int value type
        int_result: InfrastructureResult[int, ValueError] = InfrastructureResult.success(42)
        assert int_result.get_value() == 42
        
        # Test with custom error type
        class CustomError(Exception):
            pass
        
        error_result: InfrastructureResult[str, CustomError] = InfrastructureResult.failure(CustomError("custom"))
        assert isinstance(error_result.get_error(), CustomError)


class TestInfrastructureOperationResult:
    """Test cases for InfrastructureOperationResult class."""

    def test_create_success(self):
        """Test creating successful operation result."""
        data = {"status": "ok", "value": 42}
        result = InfrastructureOperationResult.create_success(data)
        
        assert result.is_success()
        assert result.get_operation_data() == data

    def test_create_failure(self):
        """Test creating failed operation result."""
        error = RuntimeError("operation failed")
        result = InfrastructureOperationResult.create_failure(error)
        
        assert result.is_failure()
        assert result.get_operation_error() == error

    def test_get_operation_data(self):
        """Test getting operation data."""
        data = {"key": "value"}
        result = InfrastructureOperationResult.create_success(data)
        
        assert result.get_operation_data() == data

    def test_get_operation_error(self):
        """Test getting operation error."""
        error = ValueError("test error")
        result = InfrastructureOperationResult.create_failure(error)
        
        assert result.get_operation_error() == error

    def test_inheritance(self):
        """Test that InfrastructureOperationResult inherits from InfrastructureResult."""
        result = InfrastructureOperationResult.create_success({"test": True})
        
        # Should have all base class methods
        assert isinstance(result, InfrastructureResult)
        assert result.is_success()
        assert result.get_value() == {"test": True}
        
        # Test mapping
        mapped = result.map(lambda d: d["test"])
        assert mapped.get_value() is True

    def test_operation_result_repr(self):
        """Test repr for operation results."""
        success_result = InfrastructureOperationResult.create_success({"status": "ok"})
        failure_result = InfrastructureOperationResult.create_failure(RuntimeError("failed"))
        
        assert "Success" in repr(success_result)
        assert "Failure" in repr(failure_result)
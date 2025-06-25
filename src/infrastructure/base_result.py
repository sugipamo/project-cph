"""Base infrastructure result type for explicit error handling."""
from typing import Any, Callable, Generic, Optional, TypeVar

T = TypeVar('T')
E = TypeVar('E', bound=Exception)


class InfrastructureResult(Generic[T, E]):
    """Base infrastructure result type for explicit success/failure handling.

    This replaces try-catch blocks with explicit error state management.
    All exception handling is confined to the infrastructure layer.
    """

    def __init__(self, success: bool, value: Optional[T], error: Optional[E]):
        """Initialize infrastructure result.

        Args:
            success: Whether operation succeeded
            value: Success value (required if success=True)
            error: Error information (required if success=False)
        """
        if success and value is None:
            raise ValueError("Success result requires value")
        if not success and error is None:
            raise ValueError("Failure result requires error")

        self._success = success
        self._value = value
        self._error = error

    @classmethod
    def success(cls, value: T) -> 'InfrastructureResult[T, E]':
        """Create successful result."""
        return cls(True, value, None)

    @classmethod
    def failure(cls, error: E) -> 'InfrastructureResult[T, E]':
        """Create failure result."""
        return cls(False, None, error)

    def is_success(self) -> bool:
        """Check if operation succeeded."""
        return self._success

    def is_failure(self) -> bool:
        """Check if operation failed."""
        return not self._success

    def get_value(self) -> T:
        """Get success value.

        Raises:
            ValueError: If result is failure
        """
        if not self._success:
            raise ValueError("Cannot get value from failure result")
        return self._value

    def get_error(self) -> E:
        """Get error information.

        Raises:
            ValueError: If result is success
        """
        if self._success:
            raise ValueError("Cannot get error from success result")
        return self._error

    def map(self, func: Callable[[T], Any]) -> 'InfrastructureResult[Any, E]':
        """Transform success value if result is successful."""
        if self._success:
            transformed_value = func(self._value)
            return InfrastructureResult.success(transformed_value)
        return InfrastructureResult.failure(self._error)

    def flat_map(self, func: Callable[[T], 'InfrastructureResult[Any, E]']) -> 'InfrastructureResult[Any, E]':
        """Chain operations that return Results."""
        if self._success:
            return func(self._value)
        return InfrastructureResult.failure(self._error)

    def or_else(self, default_value: T) -> T:
        """Get value or default if failure."""
        if self._success:
            return self._value
        return default_value

    def unwrap_or_raise(self) -> T:
        """Get value or raise the contained error."""
        if self._success:
            return self._value
        raise self._error

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        if self._success:
            return {
                'success': True,
                'value': self._value,
                'error': None
            }
        return {
            'success': False,
            'value': None,
            'error': str(self._error) if self._error else None
        }

    def __repr__(self) -> str:
        """String representation of the result."""
        if self._success:
            return f"<InfrastructureResult.Success: {self._value}>"
        return f"<InfrastructureResult.Failure: {self._error}>"


class InfrastructureOperationResult(InfrastructureResult[dict[str, Any], Exception]):
    """Specialized infrastructure result for operation results."""

    @classmethod
    def create_success(cls, operation_data: dict[str, Any]) -> 'InfrastructureOperationResult':
        """Create successful operation result."""
        return cls.success(operation_data)

    @classmethod
    def create_failure(cls, error: Exception) -> 'InfrastructureOperationResult':
        """Create failed operation result."""
        return cls.failure(error)

    def get_operation_data(self) -> dict[str, Any]:
        """Get operation data for successful results."""
        return self.get_value()

    def get_operation_error(self) -> Exception:
        """Get operation error for failed results."""
        return self.get_error()


__all__ = ["InfrastructureOperationResult", "InfrastructureResult"]

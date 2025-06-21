"""Result type for explicit error handling without try-catch."""
from typing import Any, Callable, Generic, Optional, TypeVar

T = TypeVar('T')
E = TypeVar('E', bound=Exception)


class Result(Generic[T, E]):
    """Result type for explicit success/failure handling.

    Replaces try-catch blocks with explicit error state management.
    """

    def __init__(self, success: bool, value: Optional[T], error: Optional[E]):
        """Initialize result.

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
    def success(cls, value: T) -> 'Result[T, E]':
        """Create successful result."""
        return cls(True, value=value, error=None)

    @classmethod
    def failure(cls, error: E) -> 'Result[T, E]':
        """Create failure result."""
        return cls(False, value=None, error=error)

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

    def map(self, func: Callable[[T], Any]) -> 'Result[Any, E]':
        """Transform success value if result is successful."""
        if self._success:
            transformed_value = func(self._value)
            return Result.success(transformed_value)
        return Result.failure(self._error)

    def flat_map(self, func: Callable[[T], 'Result[Any, E]']) -> 'Result[Any, E]':
        """Chain operations that return Results."""
        if self._success:
            return func(self._value)
        return Result.failure(self._error)

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


class OperationResult:
    """Specific result type for infrastructure operations."""

    def __init__(self, success: bool, message: str, details: Optional[dict], error_code: Optional[str]):
        """Initialize operation result.

        Args:
            success: Whether operation succeeded
            message: Human-readable message
            details: Additional operation details
            error_code: Specific error code for failure cases
        """
        self.success = success
        self.message = message
        self.details = details or {}
        self.error_code = error_code

    @classmethod
    def create_success(cls, message: str, details: Optional[dict]) -> 'OperationResult':
        """Create successful operation result."""
        return cls(True, message, details, None)

    @classmethod
    def create_failure(cls, message: str, error_code: Optional[str], details: Optional[dict]) -> 'OperationResult':
        """Create failed operation result."""
        return cls(False, message, details, error_code)

    def is_success(self) -> bool:
        """Check if operation succeeded."""
        return self.success

    def is_failure(self) -> bool:
        """Check if operation failed."""
        return not self.success

    def get_message(self) -> str:
        """Get operation message."""
        return self.message

    def get_details(self) -> dict:
        """Get operation details."""
        return self.details

    def get_error_code(self) -> Optional[str]:
        """Get error code for failed operations."""
        return self.error_code

    def combine_with(self, other: 'OperationResult') -> 'OperationResult':
        """Combine two operation results (both must succeed for combined success)."""
        if self.success and other.success:
            combined_message = f"{self.message}; {other.message}"
            combined_details = {**self.details, **other.details}
            return OperationResult.create_success(combined_message, combined_details)

        # If either failed, combine error messages
        error_parts = []
        if not self.success:
            error_parts.append(self.message)
        if not other.success:
            error_parts.append(other.message)

        combined_error = "; ".join(error_parts)
        combined_details = {**self.details, **other.details}
        error_code = self.error_code or other.error_code

        return OperationResult.create_failure(combined_error, error_code, combined_details)


# Validation utilities for pre-condition checking
class ValidationResult:
    """Result of validation operations."""

    def __init__(self, is_valid: bool, error_message: str):
        """Initialize validation result.

        Args:
            is_valid: Whether validation passed
            error_message: Error message if validation failed
        """
        self.is_valid = is_valid
        self.error_message = error_message

    @classmethod
    def valid(cls) -> 'ValidationResult':
        """Create valid result."""
        return cls(True, "")

    @classmethod
    def invalid(cls, error_message: str) -> 'ValidationResult':
        """Create invalid result with error message."""
        return cls(False, error_message)

    def raise_if_invalid(self, exception_type: type) -> None:
        """Raise exception if validation failed."""
        if not self.is_valid:
            raise exception_type(self.error_message)


def validate_not_none(value: Any, name: str) -> ValidationResult:
    """Validate that value is not None."""
    if value is None:
        return ValidationResult.invalid(f"{name} cannot be None")
    return ValidationResult.valid()


def validate_not_empty(value: str, name: str) -> ValidationResult:
    """Validate that string is not empty."""
    if not value or not value.strip():
        return ValidationResult.invalid(f"{name} cannot be empty")
    return ValidationResult.valid()


def validate_positive_int(value: int, name: str) -> ValidationResult:
    """Validate that integer is positive."""
    if value <= 0:
        return ValidationResult.invalid(f"{name} must be positive")
    return ValidationResult.valid()

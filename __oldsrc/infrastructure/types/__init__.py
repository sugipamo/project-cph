"""Infrastructure types for explicit error handling."""

from .result import (
    OperationResult,
    Result,
    ValidationResult,
    validate_not_empty,
    validate_not_none,
    validate_positive_int,
)

__all__ = [
    'OperationResult',
    'Result',
    'ValidationResult',
    'validate_not_empty',
    'validate_not_none',
    'validate_positive_int'
]

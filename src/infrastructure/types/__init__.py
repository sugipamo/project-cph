"""Infrastructure types for explicit error handling."""

from .result import (
    Result,
    OperationResult,
    ValidationResult,
    validate_not_none,
    validate_not_empty,
    validate_positive_int
)

__all__ = [
    'Result',
    'OperationResult', 
    'ValidationResult',
    'validate_not_none',
    'validate_not_empty',
    'validate_positive_int'
]
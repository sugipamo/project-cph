"""
Core domain abstractions and types
"""
# Exception system
from .exceptions import (
    CPHException, ValidationError, ConfigurationError, ExecutionError,
    ResourceError, DependencyError, OperationTimeoutError,
    ErrorHandler, ErrorLogger, ErrorRecovery, ErrorMessageFormatter
)

__all__ = [
    # Base exceptions
    'CPHException',
    'ValidationError', 
    'ConfigurationError',
    'ExecutionError',
    'ResourceError',
    'DependencyError',
    'OperationTimeoutError',
    
    # Error handling system
    'ErrorHandler',
    'ErrorLogger',
    'ErrorRecovery', 
    'ErrorMessageFormatter'
]
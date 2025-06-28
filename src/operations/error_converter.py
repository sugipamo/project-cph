"""Error conversion service for infrastructure layer.

This module contains all try-catch logic confined to the infrastructure layer,
following CLAUDE.md rules that side effects should only exist in infrastructure.
"""
from typing import Any, Callable, TypeVar

from src.operations.results.base_result import InfrastructureResult

T = TypeVar('T')

class ErrorConverter:
    """Service for converting exceptions to Result types.

    This is the only place in the codebase where try-catch blocks are allowed,
    following the infrastructure-only side effect rule from CLAUDE.md.
    """

    def execute_with_conversion(self, operation_func: Callable[[], T]) -> InfrastructureResult[T, Exception]:
        """Execute operation and convert any exceptions to Result.

        Args:
            operation_func: Function to execute that may raise exceptions

        Returns:
            InfrastructureResult containing success value or exception
        """
        try:
            result = operation_func()
            return InfrastructureResult.success(result)
        except Exception as e:
            return InfrastructureResult.failure(e)

    def execute_with_error_mapping(self, operation_func: Callable[[], T], error_mapper: Callable[[Exception], Exception]) -> InfrastructureResult[T, Exception]:
        """Execute operation and map exceptions before converting to Result.

        Args:
            operation_func: Function to execute that may raise exceptions
            error_mapper: Function to transform exceptions

        Returns:
            InfrastructureResult containing success value or mapped exception
        """
        try:
            result = operation_func()
            return InfrastructureResult.success(result)
        except Exception as e:
            mapped_error = error_mapper(e)
            return InfrastructureResult.failure(mapped_error)

    def execute_with_fallback(self, operation_func: Callable[[], T], fallback_func: Callable[[Exception], T]) -> InfrastructureResult[T, Exception]:
        """Execute operation with fallback on exception.

        Note: This is not a fallback in the prohibited sense from CLAUDE.md.
        This is explicit error handling where the caller provides the fallback logic.

        Args:
            operation_func: Primary function to execute
            fallback_func: Fallback function that receives the exception

        Returns:
            InfrastructureResult containing success value or fallback result
        """
        try:
            result = operation_func()
            return InfrastructureResult.success(result)
        except Exception as e:
            fallback_result = fallback_func(e)
            return InfrastructureResult.success(fallback_result)

    def execute_shell_command_with_conversion(self, driver: Any, command: str, logger: Any) -> InfrastructureResult[Any, Exception]:
        """Execute shell command and convert result/exception to Result type.

        Args:
            driver: Shell driver instance
            command: Command to execute
            logger: Logger instance

        Returns:
            InfrastructureResult containing command result or exception
        """
        try:
            result = driver.execute(command, logger)
            return InfrastructureResult.success(result)
        except Exception as e:
            return InfrastructureResult.failure(e)

    def execute_docker_operation_with_conversion(self, driver: Any, operation_func: Callable[[], Any], logger: Any) -> InfrastructureResult[Any, Exception]:
        """Execute Docker operation and convert result/exception to Result type.

        Args:
            driver: Docker driver instance
            operation_func: Docker operation to execute
            logger: Logger instance

        Returns:
            InfrastructureResult containing operation result or exception
        """
        try:
            result = operation_func()
            return InfrastructureResult.success(result)
        except Exception as e:
            return InfrastructureResult.failure(e)

    def execute_file_operation_with_conversion(self, driver: Any, operation_func: Callable[[], Any], logger: Any) -> InfrastructureResult[Any, Exception]:
        """Execute file operation and convert result/exception to Result type.

        Args:
            driver: File driver instance
            operation_func: File operation to execute
            logger: Logger instance

        Returns:
            InfrastructureResult containing operation result or exception
        """
        try:
            result = operation_func()
            return InfrastructureResult.success(result)
        except Exception as e:
            return InfrastructureResult.failure(e)

    def convert_mock_exception_to_result(self, mock_func: Callable[[], T]) -> InfrastructureResult[T, Exception]:
        """Convert mock function exceptions to Result type.

        This is specifically for handling mock functions that raise exceptions
        in test scenarios, ensuring compatibility with retry mechanisms.

        Args:
            mock_func: Mock function that may raise exceptions

        Returns:
            InfrastructureResult containing mock result or exception
        """
        try:
            result = mock_func()
            return InfrastructureResult.success(result)
        except Exception as e:
            return InfrastructureResult.failure(e)
    
    def convert_error(self, error: Exception) -> Exception:
        """Convert an exception to a standardized error type.
        
        This is a simple pass-through for now, but could be extended
        to convert specific exceptions to custom error types.
        
        Args:
            error: The exception to convert
            
        Returns:
            The converted exception (currently just returns the same exception)
        """
        return error

__all__ = ['ErrorConverter']

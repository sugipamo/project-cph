"""Retry mechanism for handling transient failures without try-catch."""
import time
from functools import wraps
from typing import Any, Callable, Optional, Tuple, Type

from src.infrastructure.types.result import Result
from src.operations.exceptions.error_codes import ErrorCode


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(self, max_attempts: int, base_delay: float,
                 max_delay: float, backoff_factor: float,
                 retryable_errors: Optional[Tuple[Type[Exception], ...]],
                 retryable_error_codes: Optional[Tuple[ErrorCode, ...]],
                 logger: Optional[Any]):
        """Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            backoff_factor: Exponential backoff factor
            retryable_errors: Exception types that should trigger retries
            retryable_error_codes: Error codes that should trigger retries
            logger: Logger instance for logging retry attempts
        """
        self._initialize_basic_config(max_attempts, base_delay, max_delay, backoff_factor)
        self._initialize_error_config(retryable_errors, retryable_error_codes)
        self.logger = logger

    def _initialize_basic_config(self, max_attempts: int, base_delay: float,
                                max_delay: float, backoff_factor: float) -> None:
        """Initialize basic retry configuration parameters."""
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor

    def _initialize_error_config(self, retryable_errors: Optional[Tuple[Type[Exception], ...]],
                                retryable_error_codes: Optional[Tuple[ErrorCode, ...]]) -> None:
        """Initialize error-related configuration parameters."""
        if retryable_errors is None:
            raise ValueError("retryable_errors parameter is required")
        self.retryable_errors = retryable_errors

        if retryable_error_codes is None:
            raise ValueError("retryable_error_codes parameter is required")
        self.retryable_error_codes = retryable_error_codes


def _determine_retry_eligibility(error_type: type, error_message: str, config: RetryConfig) -> bool:
    """Determine if an error should trigger a retry based on explicit logic.

    Args:
        error_type: The type of error that occurred
        error_message: Error message for additional context
        config: Retry configuration containing retry policies

    Returns:
        bool: True if the error should trigger a retry, False otherwise

    Raises:
        ValueError: If retry configuration is invalid
    """
    # Validate configuration integrity
    if not config or not hasattr(config, 'retryable_errors') or not hasattr(config, 'retryable_error_codes'):
        raise ValueError("Retry configuration is invalid or incomplete")

    # Check by error type
    return issubclass(error_type, config.retryable_errors)


def _should_retry_error(error: Exception, config: RetryConfig) -> bool:
    """Determine if error should trigger retry."""
    error_type = type(error)
    should_retry = _determine_retry_eligibility(error_type, str(error), config)

    if hasattr(error, 'error_code') and error.error_code in config.retryable_error_codes:
        should_retry = True

    return should_retry


def _wait_before_retry(attempt: int, config: RetryConfig, func_name: str, error: Exception) -> None:
    """Wait before retry with exponential backoff."""
    delay = min(
        config.base_delay * (config.backoff_factor ** attempt),
        config.max_delay
    )

    if config.logger:
        config.logger.warning(
            f"Attempt {attempt + 1} failed for {func_name}: {error}. "
            f"Retrying in {delay:.1f} seconds..."
        )

    time.sleep(delay)


def retry_on_failure_with_result(config: RetryConfig):
    """Decorator to retry function calls that return Result objects.

    Args:
        config: Retry configuration. If None, uses default config.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Result:
            for attempt in range(config.max_attempts):
                result = func(*args, **kwargs)

                if result.is_success():
                    return result

                error = result.get_error()
                should_retry = _should_retry_error(error, config)

                if not should_retry or attempt == config.max_attempts - 1:
                    return Result.failure(error)

                _wait_before_retry(attempt, config, func.__name__, error)

            return Result.failure(error)

        return wrapper
    return decorator


class RetryableOperation:
    """Base class for operations that support retry logic."""

    def __init__(self, retry_config: RetryConfig, logger: Optional[Any]):
        """Initialize retryable operation.

        Args:
            retry_config: Retry configuration
            logger: Logger instance for logging retry attempts
        """
        self.retry_config = retry_config
        if logger and not self.retry_config.logger:
            self.retry_config.logger = logger

    def execute_with_retry(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute an operation with retry logic.

        Args:
            operation: The operation to execute
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            Result of the operation
        """
        @retry_on_failure(self.retry_config)
        def wrapped_operation():
            return operation(*args, **kwargs)

        return wrapped_operation()


# 互換性維持のための従来のretry_on_failure関数
def retry_on_failure(config: RetryConfig):
    """Decorator for retry functionality (DEPRECATED - avoid exceptions).

    DEPRECATED: This function exists for backward compatibility only.
    New code should use retry_on_failure_with_result and Result-based error handling.

    This implementation removes try-except by requiring functions to return Result objects.
    Functions using this decorator must handle their own errors and return Result.

    Args:
        config: Retry configuration.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):

            @retry_on_failure_with_result(config)
            def retryable_operation():
                # Call the function - it should return Result for proper error handling
                result = func(*args, **kwargs)

                # If function doesn't return Result, wrap it as success
                # This maintains compatibility while encouraging Result usage
                if not hasattr(result, 'is_success'):
                    return Result.success(result)

                return result

            result = retryable_operation()

            # For backward compatibility, unwrap the result
            return result.unwrap_or_raise()

        return wrapper
    return decorator


# Predefined retry configurations for common scenarios
NETWORK_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=2.0,
    max_delay=30.0,
    backoff_factor=2.0,
    retryable_errors=(ConnectionError, TimeoutError, OSError),
    retryable_error_codes=(
        ErrorCode.NETWORK_TIMEOUT,
        ErrorCode.NETWORK_CONNECTION_FAILED,
    ),
    logger=None
)

DOCKER_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    base_delay=5.0,
    max_delay=30.0,
    backoff_factor=2.0,
    retryable_errors=(ConnectionError, OSError, RuntimeError),
    retryable_error_codes=(
        ErrorCode.DOCKER_NOT_AVAILABLE,
        ErrorCode.CONTAINER_START_FAILED,
    ),
    logger=None
)

COMMAND_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    base_delay=1.0,
    max_delay=30.0,
    backoff_factor=2.0,
    retryable_errors=(TimeoutError, OSError),
    retryable_error_codes=(
        ErrorCode.COMMAND_TIMEOUT,
    ),
    logger=None
)

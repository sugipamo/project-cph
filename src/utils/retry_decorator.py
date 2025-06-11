"""Retry mechanism for handling transient failures."""
import logging
import time
from functools import wraps
from typing import Any, Callable, Optional, Tuple, Type

from src.domain.exceptions.error_codes import ErrorCode


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0,
                 max_delay: float = 30.0, backoff_factor: float = 2.0,
                 retryable_errors: Optional[Tuple[Type[Exception], ...]] = None,
                 retryable_error_codes: Optional[Tuple[ErrorCode, ...]] = None):
        """Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            backoff_factor: Exponential backoff factor
            retryable_errors: Exception types that should trigger retries
            retryable_error_codes: Error codes that should trigger retries
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.retryable_errors = retryable_errors or (
            ConnectionError, TimeoutError, OSError
        )
        self.retryable_error_codes = retryable_error_codes or (
            ErrorCode.NETWORK_TIMEOUT,
            ErrorCode.NETWORK_CONNECTION_FAILED,
            ErrorCode.COMMAND_TIMEOUT,
            ErrorCode.DOCKER_NOT_AVAILABLE,
        )


def retry_on_failure(config: Optional[RetryConfig] = None):
    """Decorator to retry function calls on transient failures.

    Args:
        config: Retry configuration. If None, uses default config.
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Check if this error should be retried
                    should_retry = False

                    # Check by exception type
                    if isinstance(e, config.retryable_errors):
                        should_retry = True

                    # Check by error code (if exception has error_code attribute)
                    if hasattr(e, 'error_code') and e.error_code in config.retryable_error_codes:
                        should_retry = True

                    # Don't retry on final attempt or non-retryable errors
                    if not should_retry or attempt == config.max_attempts - 1:
                        break

                    # Calculate delay with exponential backoff
                    delay = min(
                        config.base_delay * (config.backoff_factor ** attempt),
                        config.max_delay
                    )

                    logging.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.1f} seconds..."
                    )

                    time.sleep(delay)

            # All attempts failed, raise the last exception
            raise last_exception

        return wrapper
    return decorator


class RetryableOperation:
    """Base class for operations that support retry logic."""

    def __init__(self, retry_config: Optional[RetryConfig] = None):
        """Initialize retryable operation.

        Args:
            retry_config: Retry configuration
        """
        self.retry_config = retry_config or RetryConfig()

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


# Predefined retry configurations for common scenarios
NETWORK_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=2.0,
    retryable_error_codes=(
        ErrorCode.NETWORK_TIMEOUT,
        ErrorCode.NETWORK_CONNECTION_FAILED,
    )
)

DOCKER_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    base_delay=5.0,
    retryable_error_codes=(
        ErrorCode.DOCKER_NOT_AVAILABLE,
        ErrorCode.CONTAINER_START_FAILED,
    )
)

COMMAND_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    base_delay=1.0,
    retryable_error_codes=(
        ErrorCode.COMMAND_TIMEOUT,
    )
)

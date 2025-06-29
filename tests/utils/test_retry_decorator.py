"""Tests for retry decorator functionality."""
import time
from unittest.mock import Mock, patch

import pytest

from src.operations.error_codes import ErrorCode
from src.operations.results.result import Result
from src.utils.retry_decorator import (
    COMMAND_RETRY_CONFIG,
    DOCKER_RETRY_CONFIG,
    NETWORK_RETRY_CONFIG,
    RetryConfig,
    RetryableOperation,
    _determine_retry_eligibility,
    _should_retry_error,
    _wait_before_retry,
    retry_on_failure,
    retry_on_failure_with_result,
)


class TestRetryConfig:
    """Test RetryConfig initialization and behavior."""

    def test_init_with_all_parameters(self):
        """Test initialization with all parameters."""
        logger = Mock()
        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            retryable_errors=(ConnectionError, TimeoutError),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,),
            logger=logger
        )
        
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 10.0
        assert config.backoff_factor == 2.0
        assert config.retryable_errors == (ConnectionError, TimeoutError)
        assert config.retryable_error_codes == (ErrorCode.NETWORK_TIMEOUT,)
        assert config.logger == logger

    def test_init_without_retryable_errors(self):
        """Test initialization fails without retryable_errors."""
        with pytest.raises(ValueError, match="retryable_errors parameter is required"):
            RetryConfig(
                max_attempts=3,
                base_delay=1.0,
                max_delay=10.0,
                backoff_factor=2.0,
                retryable_errors=None,
                retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,),
                logger=None
            )

    def test_init_without_retryable_error_codes(self):
        """Test initialization fails without retryable_error_codes."""
        with pytest.raises(ValueError, match="retryable_error_codes parameter is required"):
            RetryConfig(
                max_attempts=3,
                base_delay=1.0,
                max_delay=10.0,
                backoff_factor=2.0,
                retryable_errors=(ConnectionError,),
                retryable_error_codes=None,
                logger=None
            )


class TestDetermineRetryEligibility:
    """Test retry eligibility determination."""

    def test_should_retry_for_retryable_error(self):
        """Test that retryable errors are identified correctly."""
        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            retryable_errors=(ConnectionError, TimeoutError),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,),
            logger=None
        )
        
        assert _determine_retry_eligibility(ConnectionError, "test error", config) is True
        assert _determine_retry_eligibility(TimeoutError, "test error", config) is True

    def test_should_not_retry_for_non_retryable_error(self):
        """Test that non-retryable errors are not retried."""
        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            retryable_errors=(ConnectionError,),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,),
            logger=None
        )
        
        assert _determine_retry_eligibility(ValueError, "test error", config) is False
        assert _determine_retry_eligibility(RuntimeError, "test error", config) is False

    def test_invalid_config_raises_error(self):
        """Test that invalid config raises ValueError."""
        with pytest.raises(ValueError, match="Retry configuration is invalid"):
            _determine_retry_eligibility(ConnectionError, "test error", None)

        # Config without required attributes
        incomplete_config = Mock(spec=[])  # Mock with no attributes
        with pytest.raises(ValueError, match="Retry configuration is invalid"):
            _determine_retry_eligibility(ConnectionError, "test error", incomplete_config)


class TestShouldRetryError:
    """Test _should_retry_error function."""

    def test_should_retry_based_on_error_type(self):
        """Test retry based on error type."""
        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            retryable_errors=(ConnectionError,),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,),
            logger=None
        )
        
        error = ConnectionError("Connection failed")
        assert _should_retry_error(error, config) is True
        
        error = ValueError("Bad value")
        assert _should_retry_error(error, config) is False

    def test_should_retry_based_on_error_code(self):
        """Test retry based on error code."""
        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            retryable_errors=(),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,),
            logger=None
        )
        
        # Create a custom exception class with error_code attribute
        class NetworkError(Exception):
            def __init__(self):
                self.error_code = ErrorCode.NETWORK_TIMEOUT
        
        error = NetworkError()
        assert _should_retry_error(error, config) is True
        
        # Different error code
        class CommandError(Exception):
            def __init__(self):
                self.error_code = ErrorCode.SHELL_EXECUTION_ERROR
        
        error = CommandError()
        assert _should_retry_error(error, config) is False


class TestWaitBeforeRetry:
    """Test wait before retry functionality."""

    @patch('time.sleep')
    def test_wait_with_exponential_backoff(self, mock_sleep):
        """Test exponential backoff calculation."""
        logger = Mock()
        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            retryable_errors=(ConnectionError,),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,),
            logger=logger
        )
        
        error = ConnectionError("test error")
        
        # First retry (attempt 0)
        _wait_before_retry(0, config, "test_func", error)
        mock_sleep.assert_called_with(1.0)  # base_delay * 2^0
        
        # Second retry (attempt 1)
        _wait_before_retry(1, config, "test_func", error)
        mock_sleep.assert_called_with(2.0)  # base_delay * 2^1
        
        # Third retry (attempt 2)
        _wait_before_retry(2, config, "test_func", error)
        mock_sleep.assert_called_with(4.0)  # base_delay * 2^2

    @patch('time.sleep')
    def test_wait_respects_max_delay(self, mock_sleep):
        """Test that wait time doesn't exceed max_delay."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=1.0,
            max_delay=3.0,
            backoff_factor=2.0,
            retryable_errors=(ConnectionError,),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,),
            logger=None
        )
        
        error = ConnectionError("test error")
        
        # This would be 8.0 without max_delay
        _wait_before_retry(3, config, "test_func", error)
        mock_sleep.assert_called_with(3.0)  # capped at max_delay


class TestRetryOnFailureWithResult:
    """Test retry_on_failure_with_result decorator."""

    def test_successful_operation_returns_immediately(self):
        """Test that successful operations return without retry."""
        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            retryable_errors=(ConnectionError,),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,),
            logger=None
        )
        
        call_count = 0
        
        @retry_on_failure_with_result(config)
        def successful_operation():
            nonlocal call_count
            call_count += 1
            return Result.success("success")
        
        result = successful_operation()
        assert result.is_success()
        assert result.get_value() == "success"
        assert call_count == 1

    @patch('time.sleep')
    def test_retries_on_retryable_failure(self, mock_sleep):
        """Test that retryable failures trigger retries."""
        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            retryable_errors=(ConnectionError,),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,),
            logger=None
        )
        
        call_count = 0
        
        @retry_on_failure_with_result(config)
        def failing_then_succeeding_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return Result.failure(ConnectionError("Connection failed"))
            return Result.success("success")
        
        result = failing_then_succeeding_operation()
        assert result.is_success()
        assert result.get_value() == "success"
        assert call_count == 3
        assert mock_sleep.call_count == 2  # Two retries

    def test_non_retryable_failure_returns_immediately(self):
        """Test that non-retryable failures don't trigger retries."""
        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            retryable_errors=(ConnectionError,),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,),
            logger=None
        )
        
        call_count = 0
        
        @retry_on_failure_with_result(config)
        def non_retryable_failure():
            nonlocal call_count
            call_count += 1
            return Result.failure(ValueError("Bad value"))
        
        result = non_retryable_failure()
        assert result.is_failure()
        assert isinstance(result.get_error(), ValueError)
        assert call_count == 1

    @patch('time.sleep')
    def test_exhausts_max_attempts(self, mock_sleep):
        """Test that retries stop after max_attempts."""
        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            retryable_errors=(ConnectionError,),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,),
            logger=None
        )
        
        call_count = 0
        
        @retry_on_failure_with_result(config)
        def always_failing_operation():
            nonlocal call_count
            call_count += 1
            return Result.failure(ConnectionError("Connection failed"))
        
        result = always_failing_operation()
        assert result.is_failure()
        assert isinstance(result.get_error(), ConnectionError)
        assert call_count == 3


class TestRetryableOperation:
    """Test RetryableOperation class."""

    def test_init_with_logger(self):
        """Test initialization with logger."""
        logger = Mock()
        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            retryable_errors=(ConnectionError,),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,),
            logger=None
        )
        
        operation = RetryableOperation(config, logger)
        assert operation.retry_config.logger == logger

    def test_init_preserves_existing_logger(self):
        """Test that existing logger in config is preserved."""
        existing_logger = Mock()
        new_logger = Mock()
        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            retryable_errors=(ConnectionError,),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,),
            logger=existing_logger
        )
        
        operation = RetryableOperation(config, new_logger)
        assert operation.retry_config.logger == existing_logger

    def test_execute_with_retry(self):
        """Test execute_with_retry method."""
        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            retryable_errors=(ConnectionError,),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,),
            logger=None
        )
        
        operation = RetryableOperation(config, None)
        
        def test_func(x, y):
            return x + y
        
        result = operation.execute_with_retry(test_func, 1, 2)
        assert result == 3


class TestRetryOnFailure:
    """Test legacy retry_on_failure decorator."""

    def test_successful_operation(self):
        """Test successful operation with legacy decorator."""
        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            retryable_errors=(ConnectionError,),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,),
            logger=None
        )
        
        @retry_on_failure(config)
        def successful_operation():
            return "success"
        
        result = successful_operation()
        assert result == "success"

    def test_result_object_handling(self):
        """Test handling of Result objects with legacy decorator."""
        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            retryable_errors=(ConnectionError,),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,),
            logger=None
        )
        
        @retry_on_failure(config)
        def operation_returning_result():
            return Result.success("success")
        
        result = operation_returning_result()
        assert result == "success"

    def test_failure_raises_exception(self):
        """Test that failures raise exceptions with legacy decorator."""
        config = RetryConfig(
            max_attempts=1,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            retryable_errors=(ConnectionError,),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,),
            logger=None
        )
        
        @retry_on_failure(config)
        def failing_operation():
            return Result.failure(ValueError("Bad value"))
        
        with pytest.raises(ValueError, match="Bad value"):
            failing_operation()


class TestPredefinedConfigs:
    """Test predefined retry configurations."""

    def test_network_retry_config(self):
        """Test NETWORK_RETRY_CONFIG."""
        assert NETWORK_RETRY_CONFIG.max_attempts == 3
        assert NETWORK_RETRY_CONFIG.base_delay == 2.0
        assert NETWORK_RETRY_CONFIG.max_delay == 30.0
        assert NETWORK_RETRY_CONFIG.backoff_factor == 2.0
        assert ConnectionError in NETWORK_RETRY_CONFIG.retryable_errors
        assert TimeoutError in NETWORK_RETRY_CONFIG.retryable_errors
        assert OSError in NETWORK_RETRY_CONFIG.retryable_errors
        assert ErrorCode.NETWORK_TIMEOUT in NETWORK_RETRY_CONFIG.retryable_error_codes
        assert ErrorCode.NETWORK_CONNECTION_FAILED in NETWORK_RETRY_CONFIG.retryable_error_codes

    def test_docker_retry_config(self):
        """Test DOCKER_RETRY_CONFIG."""
        assert DOCKER_RETRY_CONFIG.max_attempts == 2
        assert DOCKER_RETRY_CONFIG.base_delay == 5.0
        assert DOCKER_RETRY_CONFIG.max_delay == 30.0
        assert DOCKER_RETRY_CONFIG.backoff_factor == 2.0
        assert ConnectionError in DOCKER_RETRY_CONFIG.retryable_errors
        assert OSError in DOCKER_RETRY_CONFIG.retryable_errors
        assert RuntimeError in DOCKER_RETRY_CONFIG.retryable_errors
        assert ErrorCode.DOCKER_NOT_AVAILABLE in DOCKER_RETRY_CONFIG.retryable_error_codes
        assert ErrorCode.CONTAINER_START_FAILED in DOCKER_RETRY_CONFIG.retryable_error_codes

    def test_command_retry_config(self):
        """Test COMMAND_RETRY_CONFIG."""
        assert COMMAND_RETRY_CONFIG.max_attempts == 2
        assert COMMAND_RETRY_CONFIG.base_delay == 1.0
        assert COMMAND_RETRY_CONFIG.max_delay == 30.0
        assert COMMAND_RETRY_CONFIG.backoff_factor == 2.0
        assert TimeoutError in COMMAND_RETRY_CONFIG.retryable_errors
        assert OSError in COMMAND_RETRY_CONFIG.retryable_errors
        assert ErrorCode.COMMAND_TIMEOUT in COMMAND_RETRY_CONFIG.retryable_error_codes
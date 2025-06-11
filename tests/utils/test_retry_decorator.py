"""Tests for retry decorator functionality."""
import time
from unittest.mock import Mock, patch

import pytest

from src.domain.exceptions.error_codes import ErrorCode
from src.utils.retry_decorator import (
    COMMAND_RETRY_CONFIG,
    DOCKER_RETRY_CONFIG,
    NETWORK_RETRY_CONFIG,
    RetryableOperation,
    RetryConfig,
    retry_on_failure,
)


class TestRetryConfig:
    """Test RetryConfig class."""

    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0
        assert config.backoff_factor == 2.0

    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            retryable_errors=(ConnectionError,)
        )
        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.retryable_errors == (ConnectionError,)


class TestRetryDecorator:
    """Test retry_on_failure decorator."""

    def test_successful_operation(self):
        """Test that successful operations are not retried."""
        mock_func = Mock(return_value="success")

        @retry_on_failure()
        def test_func():
            return mock_func()

        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 1

    def test_retryable_error_with_eventual_success(self):
        """Test that retryable errors are retried until success."""
        mock_func = Mock()
        mock_func.side_effect = [ConnectionError("fail"), ConnectionError("fail"), "success"]

        config = RetryConfig(max_attempts=3, base_delay=0.01)

        @retry_on_failure(config)
        def test_func():
            return mock_func()

        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 3

    def test_retryable_error_max_attempts_exceeded(self):
        """Test that retries stop after max attempts."""
        mock_func = Mock(side_effect=ConnectionError("always fail"))

        config = RetryConfig(max_attempts=2, base_delay=0.01)

        @retry_on_failure(config)
        def test_func():
            return mock_func()

        with pytest.raises(ConnectionError):
            test_func()

        assert mock_func.call_count == 2

    def test_non_retryable_error(self):
        """Test that non-retryable errors are not retried."""
        mock_func = Mock(side_effect=ValueError("not retryable"))

        @retry_on_failure()
        def test_func():
            return mock_func()

        with pytest.raises(ValueError):
            test_func()

        assert mock_func.call_count == 1

    @patch('time.sleep')
    def test_exponential_backoff(self, mock_sleep):
        """Test that exponential backoff is applied."""
        mock_func = Mock()
        mock_func.side_effect = [ConnectionError("fail"), "success"]

        config = RetryConfig(max_attempts=3, base_delay=1.0, backoff_factor=2.0)

        @retry_on_failure(config)
        def test_func():
            return mock_func()

        test_func()

        # Should sleep for base_delay * backoff_factor^0 = 1.0
        mock_sleep.assert_called_once_with(1.0)

    def test_error_code_based_retry(self):
        """Test retry based on error codes."""
        class CustomError(Exception):
            def __init__(self, message, error_code):
                super().__init__(message)
                self.error_code = error_code

        mock_func = Mock()
        mock_func.side_effect = [
            CustomError("timeout", ErrorCode.NETWORK_TIMEOUT),
            "success"
        ]

        config = RetryConfig(
            max_attempts=3,
            base_delay=0.01,
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,)
        )

        @retry_on_failure(config)
        def test_func():
            return mock_func()

        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 2


class TestRetryableOperation:
    """Test RetryableOperation class."""

    def test_execute_with_retry_success(self):
        """Test successful execution with retry logic."""
        operation = RetryableOperation()
        mock_func = Mock(return_value="success")

        result = operation.execute_with_retry(mock_func, "arg1", key="value")

        assert result == "success"
        mock_func.assert_called_once_with("arg1", key="value")

    def test_execute_with_retry_failure_then_success(self):
        """Test execution with initial failure then success."""
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        operation = RetryableOperation(config)

        mock_func = Mock()
        mock_func.side_effect = [ConnectionError("fail"), "success"]

        result = operation.execute_with_retry(mock_func)

        assert result == "success"
        assert mock_func.call_count == 2


class TestPredefinedConfigs:
    """Test predefined retry configurations."""

    def test_network_retry_config(self):
        """Test network retry configuration."""
        assert NETWORK_RETRY_CONFIG.max_attempts == 3
        assert NETWORK_RETRY_CONFIG.base_delay == 2.0
        assert ErrorCode.NETWORK_TIMEOUT in NETWORK_RETRY_CONFIG.retryable_error_codes

    def test_docker_retry_config(self):
        """Test Docker retry configuration."""
        assert DOCKER_RETRY_CONFIG.max_attempts == 2
        assert DOCKER_RETRY_CONFIG.base_delay == 5.0
        assert ErrorCode.DOCKER_NOT_AVAILABLE in DOCKER_RETRY_CONFIG.retryable_error_codes

    def test_command_retry_config(self):
        """Test command retry configuration."""
        assert COMMAND_RETRY_CONFIG.max_attempts == 2
        assert COMMAND_RETRY_CONFIG.base_delay == 1.0
        assert ErrorCode.COMMAND_TIMEOUT in COMMAND_RETRY_CONFIG.retryable_error_codes

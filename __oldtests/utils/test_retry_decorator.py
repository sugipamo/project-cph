"""Tests for retry decorator functionality."""
import time
from unittest.mock import Mock, patch

import pytest

from src.infrastructure.patterns.retry_decorator import (
    COMMAND_RETRY_CONFIG,
    DOCKER_RETRY_CONFIG,
    NETWORK_RETRY_CONFIG,
    RetryableOperation,
    RetryConfig,
    retry_on_failure,
)
from src.operations.exceptions.error_codes import ErrorCode


class TestRetryConfig:
    """Test RetryConfig class."""

    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=30.0,
            backoff_factor=2.0,
            retryable_errors=(ConnectionError, TimeoutError),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,),
            logger=None
        )
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0
        assert config.backoff_factor == 2.0

    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            max_delay=60.0,
            backoff_factor=1.5,
            retryable_errors=(ConnectionError,),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT,),
            logger=None
        )
        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.retryable_errors == (ConnectionError,)


class TestRetryDecorator:
    """Test retry_on_failure decorator."""

    def test_successful_operation(self):
        """Test that successful operations are not retried."""
        mock_func = Mock(return_value="success")

        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=30.0,
            backoff_factor=2.0,
            retryable_errors=(ConnectionError, TimeoutError, OSError),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT, ErrorCode.NETWORK_CONNECTION_FAILED),
            logger=None
        )

        @retry_on_failure(config)
        def test_func():
            return mock_func()

        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 1







class TestRetryableOperation:
    """Test RetryableOperation class."""

    def test_execute_with_retry_success(self):
        """Test successful execution with retry logic."""
        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=30.0,
            backoff_factor=2.0,
            retryable_errors=(ConnectionError, TimeoutError, OSError),
            retryable_error_codes=(ErrorCode.NETWORK_TIMEOUT, ErrorCode.NETWORK_CONNECTION_FAILED),
            logger=None
        )
        operation = RetryableOperation(config, None)
        mock_func = Mock(return_value="success")

        result = operation.execute_with_retry(mock_func, "arg1", key="value")

        assert result == "success"
        mock_func.assert_called_once_with("arg1", key="value")



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

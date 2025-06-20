"""Tests for ApplicationLoggerAdapter"""
from unittest.mock import Mock, call

import pytest

from src.infrastructure.drivers.logging.adapters.application_logger_adapter import ApplicationLoggerAdapter
from src.infrastructure.drivers.logging.format_info import FormatInfo
from src.infrastructure.drivers.logging.types import LogLevel


class TestApplicationLoggerAdapter:

    @pytest.fixture
    def mock_output_manager(self):
        """Create a mock output manager."""
        return Mock()

    @pytest.fixture
    def logger(self, mock_output_manager):
        """Create an ApplicationLoggerAdapter instance."""
        return ApplicationLoggerAdapter(mock_output_manager, name="test_logger")

    def test_initialization(self, mock_output_manager):
        """Test adapter initialization."""
        logger = ApplicationLoggerAdapter(mock_output_manager, name="test_logger")

        assert logger.output_manager == mock_output_manager
        assert logger.name == "test_logger"
        assert len(logger.session_id) == 8  # UUID truncated to 8 chars

    def test_debug(self, logger, mock_output_manager):
        """Test debug logging."""
        logger.debug("Debug message")

        mock_output_manager.add.assert_called_once_with(
            "Debug message",
            LogLevel.DEBUG,
            formatinfo=FormatInfo(color="gray")
        )

    def test_info(self, logger, mock_output_manager):
        """Test info logging."""
        logger.info("Info message")

        mock_output_manager.add.assert_called_once_with(
            "Info message",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="cyan")
        )

    def test_warning(self, logger, mock_output_manager):
        """Test warning logging."""
        logger.warning("Warning message")

        mock_output_manager.add.assert_called_once_with(
            "Warning message",
            LogLevel.WARNING,
            formatinfo=FormatInfo(color="yellow", bold=True)
        )

    def test_error(self, logger, mock_output_manager):
        """Test error logging."""
        logger.error("Error message")

        mock_output_manager.add.assert_called_once_with(
            "Error message",
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def test_critical(self, logger, mock_output_manager):
        """Test critical logging."""
        logger.critical("Critical message")

        mock_output_manager.add.assert_called_once_with(
            "Critical message",
            LogLevel.CRITICAL,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def test_format_message_with_args(self, logger, mock_output_manager):
        """Test message formatting with arguments."""
        logger.info("Hello %s, you have %d messages", "Alice", 5)

        mock_output_manager.add.assert_called_once_with(
            "Hello Alice, you have 5 messages",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="cyan")
        )

    def test_format_message_with_invalid_args(self, logger, mock_output_manager):
        """Test message formatting with invalid arguments."""
        logger.info("Hello %s", 123, 456)  # Too many args

        # Should fall back to concatenation
        mock_output_manager.add.assert_called_once_with(
            "Hello %s (123, 456)",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="cyan")
        )

    def test_log_error_with_correlation(self, logger, mock_output_manager):
        """Test error logging with correlation ID."""
        logger.log_error_with_correlation(
            error_id="ERR123",
            error_code="VALIDATION_ERROR",
            message="Invalid input",
            context={"field": "email", "value": "invalid"}
        )

        expected_message = (
            f"[ERROR#ERR123] [VALIDATION_ERROR] Invalid input "
            f"(session: {logger.session_id}) "
            f"Context: {{'field': 'email', 'value': 'invalid'}}"
        )

        mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def test_log_error_with_correlation_no_context(self, logger, mock_output_manager):
        """Test error logging with correlation ID but no context."""
        logger.log_error_with_correlation(
            error_id="ERR456",
            error_code="SYSTEM_ERROR",
            message="System failure"
        )

        expected_message = (
            f"[ERROR#ERR456] [SYSTEM_ERROR] System failure "
            f"(session: {logger.session_id})"
        )

        mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def test_log_operation_start(self, logger, mock_output_manager):
        """Test operation start logging."""
        logger.log_operation_start(
            operation_id="OP001",
            operation_type="DATABASE_QUERY",
            details={"table": "users", "action": "select"}
        )

        expected_message = (
            f"[OP#OP001] DATABASE_QUERY started (session: {logger.session_id}) "
            f"Details: {{'table': 'users', 'action': 'select'}}"
        )

        mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue")
        )

    def test_log_operation_start_no_details(self, logger, mock_output_manager):
        """Test operation start logging without details."""
        logger.log_operation_start(
            operation_id="OP002",
            operation_type="CACHE_CLEAR"
        )

        expected_message = (
            f"[OP#OP002] CACHE_CLEAR started (session: {logger.session_id})"
        )

        mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue")
        )

    def test_log_operation_end_success(self, logger, mock_output_manager):
        """Test operation end logging for successful operation."""
        logger.log_operation_end(
            operation_id="OP003",
            operation_type="FILE_UPLOAD",
            success=True,
            details={"filename": "test.pdf", "size": 1024}
        )

        expected_message = (
            f"[OP#OP003] FILE_UPLOAD completed (session: {logger.session_id}) "
            f"Details: {{'filename': 'test.pdf', 'size': 1024}}"
        )

        mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="green", bold=False)
        )

    def test_log_operation_end_failure(self, logger, mock_output_manager):
        """Test operation end logging for failed operation."""
        logger.log_operation_end(
            operation_id="OP004",
            operation_type="API_CALL",
            success=False,
            details={"endpoint": "/api/v1/users", "status": 500}
        )

        expected_message = (
            f"[OP#OP004] API_CALL failed (session: {logger.session_id}) "
            f"Details: {{'endpoint': '/api/v1/users', 'status': 500}}"
        )

        mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def test_log_operation_end_no_details(self, logger, mock_output_manager):
        """Test operation end logging without details."""
        logger.log_operation_end(
            operation_id="OP005",
            operation_type="CLEANUP",
            success=True
        )

        expected_message = (
            f"[OP#OP005] CLEANUP completed (session: {logger.session_id})"
        )

        mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="green", bold=False)
        )

    def test_kwargs_are_ignored(self, logger, mock_output_manager):
        """Test that kwargs are properly ignored."""
        logger.info("Test message", extra={"key": "value"}, exc_info=True)

        mock_output_manager.add.assert_called_once_with(
            "Test message",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="cyan")
        )

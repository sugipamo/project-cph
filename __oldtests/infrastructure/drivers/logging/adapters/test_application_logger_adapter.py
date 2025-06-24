"""Tests for ApplicationLoggerAdapter"""

import uuid
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.infrastructure.drivers.logging.adapters.application_logger_adapter import ApplicationLoggerAdapter
from src.infrastructure.drivers.logging.format_info import FormatInfo
from src.infrastructure.drivers.logging.interfaces.output_manager_interface import OutputManagerInterface
from src.infrastructure.drivers.logging.types import LogLevel


class TestApplicationLoggerAdapter:
    """Tests for ApplicationLoggerAdapter class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.output_manager = Mock(spec=OutputManagerInterface)
        self.adapter = ApplicationLoggerAdapter(self.output_manager, "test_logger")

    def test_init_with_output_manager(self):
        """Test initialization with output manager"""
        adapter = ApplicationLoggerAdapter(self.output_manager, "test")
        assert adapter.output_manager == self.output_manager
        assert adapter.name == "test"
        assert len(adapter.session_id) == 8

    def test_init_default_name(self):
        """Test initialization with default name"""
        adapter = ApplicationLoggerAdapter(self.output_manager)
        assert adapter.name == "src.infrastructure.drivers.logging.adapters.application_logger_adapter"

    @patch('src.infrastructure.drivers.logging.adapters.application_logger_adapter.DIContainer')
    def test_init_with_di_container_config(self, mock_di_container):
        """Test initialization with DI container config manager"""
        mock_config = Mock()
        mock_di_container.resolve.return_value = mock_config

        adapter = ApplicationLoggerAdapter(self.output_manager)

        mock_di_container.resolve.assert_called_once_with("config_manager")
        assert adapter._config_manager == mock_config


    def test_debug(self):
        """Test debug logging method"""
        self.adapter.debug("Test debug message")

        self.output_manager.add.assert_called_once_with(
            "Test debug message",
            LogLevel.DEBUG,
            formatinfo=FormatInfo(color="gray"),
            realtime=False
        )

    def test_debug_with_args(self):
        """Test debug logging with arguments"""
        self.adapter.debug("Test %s message", "formatted")

        self.output_manager.add.assert_called_once_with(
            "Test formatted message",
            LogLevel.DEBUG,
            formatinfo=FormatInfo(color="gray"),
            realtime=False
        )

    def test_info(self):
        """Test info logging method"""
        self.adapter.info("Test info message")

        self.output_manager.add.assert_called_once_with(
            "Test info message",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="cyan"),
            realtime=False
        )

    def test_info_with_args(self):
        """Test info logging with arguments"""
        self.adapter.info("Count: %d", 42)

        self.output_manager.add.assert_called_once_with(
            "Count: 42",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="cyan"),
            realtime=False
        )

    def test_warning(self):
        """Test warning logging method"""
        self.adapter.warning("Test warning message")

        self.output_manager.add.assert_called_once_with(
            "Test warning message",
            LogLevel.WARNING,
            formatinfo=FormatInfo(color="yellow", bold=True),
            realtime=False
        )

    def test_error(self):
        """Test error logging method"""
        self.adapter.error("Test error message")

        self.output_manager.add.assert_called_once_with(
            "Test error message",
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True),
            realtime=False
        )

    def test_critical(self):
        """Test critical logging method"""
        self.adapter.critical("Test critical message")

        self.output_manager.add.assert_called_once_with(
            "Test critical message",
            LogLevel.CRITICAL,
            formatinfo=FormatInfo(color="red", bold=True),
            realtime=False
        )

    def test_log_error_with_correlation(self):
        """Test log_error_with_correlation method"""
        self.adapter.log_error_with_correlation("ERR001", "AUTH_FAILED", "Authentication failed", context=None)

        expected_message = f"[ERROR#ERR001] [AUTH_FAILED] Authentication failed (session: {self.adapter.session_id})"
        self.output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True),
            realtime=False
        )

    def test_log_error_with_correlation_and_context(self):
        """Test log_error_with_correlation method with context"""
        context = {"user": "test_user", "ip": "127.0.0.1"}
        self.adapter.log_error_with_correlation("ERR002", "LOGIN_FAILED", "Login failed", context=context)

        expected_message = (f"[ERROR#ERR002] [LOGIN_FAILED] Login failed (session: {self.adapter.session_id}) "
                          f"Context: {context}")
        self.output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True),
            realtime=False
        )

    def test_log_operation_start(self):
        """Test log_operation_start method"""
        self.adapter.log_operation_start("OP001", "file_copy", None)

        expected_message = f"[OP#OP001] file_copy started (session: {self.adapter.session_id})"
        self.output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue"),
            realtime=False
        )

    def test_log_operation_start_with_details(self):
        """Test log_operation_start method with details"""
        details = {"source": "/tmp/src", "dest": "/tmp/dst"}
        self.adapter.log_operation_start("OP002", "file_move", details)

        expected_message = (f"[OP#OP002] file_move started (session: {self.adapter.session_id}) "
                          f"Details: {details}")
        self.output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue"),
            realtime=False
        )

    def test_log_operation_end_success_with_config(self):
        """Test log_operation_end method for successful operation with config"""
        mock_config = Mock()
        mock_config.resolve_config.side_effect = [
            "completed",  # status_success
            "failed",     # status_failure
            "green",      # color_success
            "red"         # color_failure
        ]
        self.adapter._config_manager = mock_config

        self.adapter.log_operation_end("OP001", "file_copy", True, None)

        expected_message = f"[OP#OP001] file_copy completed (session: {self.adapter.session_id})"
        self.output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="green", bold=False),
            realtime=False
        )

    def test_log_operation_end_failure_with_config(self):
        """Test log_operation_end method for failed operation with config"""
        mock_config = Mock()
        mock_config.resolve_config.side_effect = [
            "completed",  # status_success
            "failed",     # status_failure
            "green",      # color_success
            "red"         # color_failure
        ]
        self.adapter._config_manager = mock_config

        details = {"error": "Permission denied"}
        self.adapter.log_operation_end("OP002", "file_delete", False, details)

        expected_message = (f"[OP#OP002] file_delete failed (session: {self.adapter.session_id}) "
                          f"Details: {details}")
        self.output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True),
            realtime=False
        )



    def test_format_message_with_args(self):
        """Test _format_message method with arguments"""
        result = self.adapter._format_message("Hello %s", ("world",))
        assert result == "Hello world"

    def test_format_message_no_args(self):
        """Test _format_message method without arguments"""
        result = self.adapter._format_message("Hello world", ())
        assert result == "Hello world"

    def test_format_message_format_error(self):
        """Test _format_message method handles format errors"""
        result = self.adapter._format_message("Hello %s", (42, "extra"))
        assert result == "Hello %s (42, 'extra')"

    def test_format_message_type_error(self):
        """Test _format_message method handles type errors"""
        result = self.adapter._format_message("Hello %d", ("not_a_number",))
        assert result == "Hello %d ('not_a_number',)"

    def test_session_id_is_uuid_format(self):
        """Test that session_id is in UUID format (8 characters)"""
        adapter = ApplicationLoggerAdapter(self.output_manager)
        assert len(adapter.session_id) == 8
        assert isinstance(adapter.session_id, str)
        # Check that it's a valid hex prefix
        int(adapter.session_id, 16)  # Should not raise ValueError

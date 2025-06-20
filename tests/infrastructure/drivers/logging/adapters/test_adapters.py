"""Tests for logging adapters"""

import uuid
from unittest.mock import Mock, patch

import pytest

from src.infrastructure.drivers.logging.adapters import (
    ApplicationLoggerAdapter,
    WorkflowLoggerAdapter,
)
from src.infrastructure.drivers.logging.format_info import FormatInfo
from src.infrastructure.drivers.logging.types import LogLevel


class TestApplicationLoggerAdapter:
    """Tests for ApplicationLoggerAdapter"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_output_manager = Mock()
        self.adapter = ApplicationLoggerAdapter(self.mock_output_manager, "test_logger")

    def test_init(self):
        """Test adapter initialization"""
        assert self.adapter.output_manager == self.mock_output_manager
        assert self.adapter.name == "test_logger"
        assert len(self.adapter.session_id) == 8

        # Test with default name
        adapter_default = ApplicationLoggerAdapter(self.mock_output_manager)
        assert adapter_default.name == "src.infrastructure.drivers.logging.adapters.application_logger_adapter"

    def test_debug(self):
        """Test debug logging"""
        self.adapter.debug("Test debug message")

        self.mock_output_manager.add.assert_called_once_with(
            "Test debug message",
            LogLevel.DEBUG,
            formatinfo=FormatInfo(color="gray")
        )

    def test_debug_with_args(self):
        """Test debug logging with arguments"""
        self.adapter.debug("Test %s message", "formatted")

        self.mock_output_manager.add.assert_called_once_with(
            "Test formatted message",
            LogLevel.DEBUG,
            formatinfo=FormatInfo(color="gray")
        )

    def test_info(self):
        """Test info logging"""
        self.adapter.info("Test info message")

        self.mock_output_manager.add.assert_called_once_with(
            "Test info message",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="cyan")
        )

    def test_info_with_args(self):
        """Test info logging with arguments"""
        self.adapter.info("Test %s %d", "formatted", 42)

        self.mock_output_manager.add.assert_called_once_with(
            "Test formatted 42",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="cyan")
        )

    def test_warning(self):
        """Test warning logging"""
        self.adapter.warning("Test warning message")

        self.mock_output_manager.add.assert_called_once_with(
            "Test warning message",
            LogLevel.WARNING,
            formatinfo=FormatInfo(color="yellow", bold=True)
        )

    def test_error(self):
        """Test error logging"""
        self.adapter.error("Test error message")

        self.mock_output_manager.add.assert_called_once_with(
            "Test error message",
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def test_critical(self):
        """Test critical logging"""
        self.adapter.critical("Test critical message")

        self.mock_output_manager.add.assert_called_once_with(
            "Test critical message",
            LogLevel.CRITICAL,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def test_log_error_with_correlation(self):
        """Test error logging with correlation ID"""
        self.adapter.log_error_with_correlation(
            "ERR123", "VALIDATION_ERROR", "Invalid input"
        )

        expected_message = (
            f"[ERROR#ERR123] [VALIDATION_ERROR] Invalid input "
            f"(session: {self.adapter.session_id})"
        )

        self.mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def test_log_error_with_correlation_and_context(self):
        """Test error logging with correlation ID and context"""
        context = {"user_id": "123", "action": "login"}
        self.adapter.log_error_with_correlation(
            "ERR123", "AUTH_ERROR", "Login failed", context
        )

        expected_message = (
            f"[ERROR#ERR123] [AUTH_ERROR] Login failed "
            f"(session: {self.adapter.session_id}) Context: {context}"
        )

        self.mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def test_log_operation_start(self):
        """Test operation start logging"""
        self.adapter.log_operation_start("OP123", "file_processing")

        expected_message = (
            f"[OP#OP123] file_processing started (session: {self.adapter.session_id})"
        )

        self.mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue")
        )

    def test_log_operation_start_with_details(self):
        """Test operation start logging with details"""
        details = {"file_count": 5, "total_size": "1.2MB"}
        self.adapter.log_operation_start("OP123", "file_processing", details)

        expected_message = (
            f"[OP#OP123] file_processing started (session: {self.adapter.session_id}) "
            f"Details: {details}"
        )

        self.mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue")
        )

    def test_log_operation_end_success(self):
        """Test operation end logging for successful operations"""
        self.adapter.log_operation_end("OP123", "file_processing", True)

        expected_message = (
            f"[OP#OP123] file_processing completed (session: {self.adapter.session_id})"
        )

        self.mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="green", bold=False)
        )

    def test_log_operation_end_failure(self):
        """Test operation end logging for failed operations"""
        self.adapter.log_operation_end("OP123", "file_processing", False)

        expected_message = (
            f"[OP#OP123] file_processing failed (session: {self.adapter.session_id})"
        )

        self.mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def test_log_operation_end_with_details(self):
        """Test operation end logging with details"""
        details = {"processed_files": 3, "failed_files": 2}
        self.adapter.log_operation_end("OP123", "file_processing", False, details)

        expected_message = (
            f"[OP#OP123] file_processing failed (session: {self.adapter.session_id}) "
            f"Details: {details}"
        )

        self.mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def test_format_message_no_args(self):
        """Test message formatting without arguments"""
        result = self.adapter._format_message("Simple message", ())
        assert result == "Simple message"

    def test_format_message_with_args(self):
        """Test message formatting with arguments"""
        result = self.adapter._format_message("Hello %s", ("World",))
        assert result == "Hello World"

    def test_format_message_multiple_args(self):
        """Test message formatting with multiple arguments"""
        result = self.adapter._format_message("User %s has %d points", ("Alice", 100))
        assert result == "User Alice has 100 points"

    def test_format_message_format_error(self):
        """Test message formatting with format error"""
        result = self.adapter._format_message("Hello %s", ("World", "Extra"))
        assert result == "Hello %s ('World', 'Extra')"

    def test_format_message_type_error(self):
        """Test message formatting with type error"""
        result = self.adapter._format_message("Number %d", ("not_a_number",))
        assert result == "Number %d ('not_a_number',)"


class TestWorkflowLoggerAdapter:
    """Tests for WorkflowLoggerAdapter"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_output_manager = Mock()
        self.config = {
            "enabled": True,
            "format": {
                "icons": {
                    "custom": "🔧"
                }
            }
        }
        self.adapter = WorkflowLoggerAdapter(self.mock_output_manager, self.config)

    def test_init_with_config(self):
        """Test adapter initialization with config"""
        assert self.adapter.output_manager == self.mock_output_manager
        assert self.adapter.config == self.config
        assert self.adapter.enabled is True

        # Test icon merging
        assert self.adapter.icons["start"] == "🚀"  # Default icon
        assert self.adapter.icons["custom"] == "🔧"  # Custom icon

    def test_init_without_config(self):
        """Test adapter initialization without config"""
        # WorkflowLoggerAdapter requires enabled and format.icons in config
        # This test should verify that missing config raises KeyError
        with pytest.raises(KeyError):
            WorkflowLoggerAdapter(self.mock_output_manager)

    def test_debug_enabled(self):
        """Test debug logging when enabled"""
        self.adapter.debug("Test debug message")

        expected_message = "🔍 DEBUG: Test debug message"
        self.mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.DEBUG,
            formatinfo=FormatInfo(color="gray")
        )

    def test_debug_disabled(self):
        """Test debug logging when disabled"""
        self.adapter.enabled = False
        self.adapter.debug("Test debug message")

        self.mock_output_manager.add.assert_not_called()

    def test_info_enabled(self):
        """Test info logging when enabled"""
        self.adapter.info("Test info message")

        expected_message = "ℹ️ Test info message"
        self.mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="cyan")
        )

    def test_info_disabled(self):
        """Test info logging when disabled"""
        self.adapter.enabled = False
        self.adapter.info("Test info message")

        self.mock_output_manager.add.assert_not_called()

    def test_warning_enabled(self):
        """Test warning logging when enabled"""
        self.adapter.warning("Test warning message")

        expected_message = "⚠️ WARNING: Test warning message"
        self.mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.WARNING,
            formatinfo=FormatInfo(color="yellow", bold=True)
        )

    def test_warning_disabled(self):
        """Test warning logging when disabled"""
        self.adapter.enabled = False
        self.adapter.warning("Test warning message")

        self.mock_output_manager.add.assert_not_called()

    def test_error_enabled(self):
        """Test error logging when enabled"""
        self.adapter.error("Test error message")

        expected_message = "💥 ERROR: Test error message"
        self.mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def test_error_disabled(self):
        """Test error logging when disabled"""
        self.adapter.enabled = False
        self.adapter.error("Test error message")

        self.mock_output_manager.add.assert_not_called()

    def test_step_start(self):
        """Test step start logging"""
        self.adapter.step_start("Compile code")

        expected_calls = [
            (("\n🚀 実行開始: Compile code", LogLevel.INFO),
             {"formatinfo": FormatInfo(color="blue", bold=True)}),
            (("  ⏱️ 実行中...", LogLevel.INFO),
             {"formatinfo": FormatInfo(color="blue")})
        ]

        assert self.mock_output_manager.add.call_count == 2
        for i, (expected_args, expected_kwargs) in enumerate(expected_calls):
            actual_call = self.mock_output_manager.add.call_args_list[i]
            assert actual_call[0] == expected_args
            assert actual_call[1] == expected_kwargs

    def test_step_start_disabled(self):
        """Test step start logging when disabled"""
        self.adapter.enabled = False
        self.adapter.step_start("Compile code")

        self.mock_output_manager.add.assert_not_called()

    def test_step_success(self):
        """Test step success logging"""
        self.adapter.step_success("Compile code")

        expected_message = "✅ 完了: Compile code"
        self.mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="green", bold=True)
        )

    def test_step_success_with_message(self):
        """Test step success logging with additional message"""
        self.adapter.step_success("Compile code", "0 warnings")

        expected_message = "✅ 完了: Compile code - 0 warnings"
        self.mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="green", bold=True)
        )

    def test_step_success_disabled(self):
        """Test step success logging when disabled"""
        self.adapter.enabled = False
        self.adapter.step_success("Compile code")

        self.mock_output_manager.add.assert_not_called()

    def test_step_failure(self):
        """Test step failure logging"""
        self.adapter.step_failure("Compile code", "Syntax error")

        expected_calls = [
            (("❌ 失敗: Compile code", LogLevel.ERROR),
             {"formatinfo": FormatInfo(color="red", bold=True)}),
            (("  エラー: Syntax error", LogLevel.ERROR),
             {"formatinfo": FormatInfo(color="red", indent=1)})
        ]

        assert self.mock_output_manager.add.call_count == 2
        for i, (expected_args, expected_kwargs) in enumerate(expected_calls):
            actual_call = self.mock_output_manager.add.call_args_list[i]
            assert actual_call[0] == expected_args
            assert actual_call[1] == expected_kwargs

    def test_step_failure_allowed(self):
        """Test step failure logging with allow_failure=True"""
        self.adapter.step_failure("Compile code", "Syntax error", allow_failure=True)

        expected_calls = [
            (("⚠️ 失敗許可: Compile code", LogLevel.WARNING),
             {"formatinfo": FormatInfo(color="yellow", bold=True)}),
            (("  エラー: Syntax error", LogLevel.WARNING),
             {"formatinfo": FormatInfo(color="yellow", indent=1)})
        ]

        assert self.mock_output_manager.add.call_count == 2
        for i, (expected_args, expected_kwargs) in enumerate(expected_calls):
            actual_call = self.mock_output_manager.add.call_args_list[i]
            assert actual_call[0] == expected_args
            assert actual_call[1] == expected_kwargs

    def test_step_failure_no_error(self):
        """Test step failure logging without error message"""
        self.adapter.step_failure("Compile code", "")

        # Should only log the failure message, not the error
        self.mock_output_manager.add.assert_called_once_with(
            "❌ 失敗: Compile code",
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def test_step_failure_disabled(self):
        """Test step failure logging when disabled"""
        self.adapter.enabled = False
        self.adapter.step_failure("Compile code", "Syntax error")

        self.mock_output_manager.add.assert_not_called()

    def test_log_preparation_start(self):
        """Test preparation start logging"""
        self.adapter.log_preparation_start(5)

        expected_message = "\n🚀 環境準備開始: 5タスク"
        self.mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue", bold=True)
        )

    def test_log_preparation_start_disabled(self):
        """Test preparation start logging when disabled"""
        self.adapter.enabled = False
        self.adapter.log_preparation_start(5)

        self.mock_output_manager.add.assert_not_called()

    def test_log_workflow_start_sequential(self):
        """Test workflow start logging for sequential execution"""
        self.adapter.log_workflow_start(3, parallel=False)

        expected_message = "\n🚀 ワークフロー実行開始: 3ステップ (順次実行)"
        self.mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue", bold=True)
        )

    def test_log_workflow_start_parallel(self):
        """Test workflow start logging for parallel execution"""
        self.adapter.log_workflow_start(3, parallel=True)

        expected_message = "\n🚀 ワークフロー実行開始: 3ステップ (並列実行)"
        self.mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue", bold=True)
        )

    def test_log_workflow_start_disabled(self):
        """Test workflow start logging when disabled"""
        self.adapter.enabled = False
        self.adapter.log_workflow_start(3)

        self.mock_output_manager.add.assert_not_called()

    def test_config_load_warning(self):
        """Test config load warning"""
        self.adapter.config_load_warning("/path/to/config.json", "File not found")

        expected_message = "⚠️ WARNING: Failed to load /path/to/config.json: File not found"
        self.mock_output_manager.add.assert_called_once_with(
            expected_message,
            LogLevel.WARNING,
            formatinfo=FormatInfo(color="yellow", bold=True)
        )

    def test_is_enabled(self):
        """Test is_enabled method"""
        assert self.adapter.is_enabled() is True

        self.adapter.enabled = False
        assert self.adapter.is_enabled() is False

    def test_default_icons(self):
        """Test default icons are properly set"""
        expected_icons = {
            "start": "🚀",
            "success": "✅",
            "failure": "❌",
            "warning": "⚠️",
            "executing": "⏱️",
            "info": "ℹ️",
            "debug": "🔍",
            "error": "💥"
        }

        assert expected_icons == WorkflowLoggerAdapter.DEFAULT_ICONS

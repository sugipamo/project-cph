"""Tests for WorkflowLoggerAdapter"""
from unittest.mock import Mock, call

import pytest

from src.infrastructure.drivers.logging.adapters.workflow_logger_adapter import WorkflowLoggerAdapter
from src.infrastructure.drivers.logging.format_info import FormatInfo
from src.infrastructure.drivers.logging.types import LogLevel


class TestWorkflowLoggerAdapter:

    @pytest.fixture
    def mock_output_manager(self):
        """Create a mock output manager."""
        return Mock()

    @pytest.fixture
    def default_config(self):
        """Create default logger configuration."""
        return {
            "enabled": True,
            "format": {
                "icons": {
                    "custom": "📍"
                }
            }
        }

    @pytest.fixture
    def logger(self, mock_output_manager, default_config):
        """Create a WorkflowLoggerAdapter instance."""
        return WorkflowLoggerAdapter(mock_output_manager, default_config)

    def test_initialization_with_config(self, mock_output_manager, default_config):
        """Test adapter initialization with configuration."""
        logger = WorkflowLoggerAdapter(mock_output_manager, default_config)

        assert logger.output_manager == mock_output_manager
        assert logger.config == default_config
        assert logger.enabled is True
        # Check that custom icon is merged with defaults
        assert logger.icons["custom"] == "📍"
        assert logger.icons["start"] == "🚀"  # Default icon

    def test_initialization_without_config(self, mock_output_manager):
        """Test adapter initialization without configuration."""
        # The implementation expects config to have certain keys
        # So initialization without proper config should raise KeyError
        with pytest.raises(KeyError):
            WorkflowLoggerAdapter(mock_output_manager)

    def test_debug_enabled(self, logger, mock_output_manager):
        """Test debug logging when enabled."""
        logger.debug("Debug message")

        mock_output_manager.add.assert_called_once_with(
            "🔍 DEBUG: Debug message",
            LogLevel.DEBUG,
            formatinfo=FormatInfo(color="gray")
        )

    def test_debug_disabled(self, mock_output_manager):
        """Test debug logging when disabled."""
        config = {"enabled": False, "format": {"icons": {}}}
        logger = WorkflowLoggerAdapter(mock_output_manager, config)

        logger.debug("Debug message")

        mock_output_manager.add.assert_not_called()

    def test_info_enabled(self, logger, mock_output_manager):
        """Test info logging when enabled."""
        logger.info("Info message")

        mock_output_manager.add.assert_called_once_with(
            "ℹ️ Info message",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="cyan")
        )

    def test_warning_enabled(self, logger, mock_output_manager):
        """Test warning logging when enabled."""
        logger.warning("Warning message")

        mock_output_manager.add.assert_called_once_with(
            "⚠️ WARNING: Warning message",
            LogLevel.WARNING,
            formatinfo=FormatInfo(color="yellow", bold=True)
        )

    def test_error_enabled(self, logger, mock_output_manager):
        """Test error logging when enabled."""
        logger.error("Error message")

        mock_output_manager.add.assert_called_once_with(
            "💥 ERROR: Error message",
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def test_step_start(self, logger, mock_output_manager):
        """Test step start logging."""
        logger.step_start("TestStep")

        calls = mock_output_manager.add.call_args_list
        assert len(calls) == 2

        # First call - start message
        assert calls[0] == call(
            "\n🚀 実行開始: TestStep",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue", bold=True)
        )

        # Second call - executing message
        assert calls[1] == call(
            "  ⏱️ 実行中...",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue")
        )

    def test_step_start_disabled(self, mock_output_manager):
        """Test step start logging when disabled."""
        config = {"enabled": False, "format": {"icons": {}}}
        logger = WorkflowLoggerAdapter(mock_output_manager, config)

        logger.step_start("TestStep")

        mock_output_manager.add.assert_not_called()

    def test_step_success_without_message(self, logger, mock_output_manager):
        """Test step success logging without additional message."""
        logger.step_success("TestStep")

        mock_output_manager.add.assert_called_once_with(
            "✅ 完了: TestStep",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="green", bold=True)
        )

    def test_step_success_with_message(self, logger, mock_output_manager):
        """Test step success logging with additional message."""
        logger.step_success("TestStep", "All tests passed")

        mock_output_manager.add.assert_called_once_with(
            "✅ 完了: TestStep - All tests passed",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="green", bold=True)
        )

    def test_step_failure_critical(self, logger, mock_output_manager):
        """Test step failure logging for critical failure."""
        logger.step_failure("TestStep", "Connection timeout")

        calls = mock_output_manager.add.call_args_list
        assert len(calls) == 2

        # First call - failure message
        assert calls[0] == call(
            "❌ 失敗: TestStep",
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True)
        )

        # Second call - error details
        assert calls[1] == call(
            "  エラー: Connection timeout",
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", indent=1)
        )

    def test_step_failure_allowed(self, logger, mock_output_manager):
        """Test step failure logging for allowed failure."""
        logger.step_failure("TestStep", "Optional step failed", allow_failure=True)

        calls = mock_output_manager.add.call_args_list
        assert len(calls) == 2

        # First call - failure message
        assert calls[0] == call(
            "⚠️ 失敗許可: TestStep",
            LogLevel.WARNING,
            formatinfo=FormatInfo(color="yellow", bold=True)
        )

        # Second call - error details
        assert calls[1] == call(
            "  エラー: Optional step failed",
            LogLevel.WARNING,
            formatinfo=FormatInfo(color="yellow", indent=1)
        )

    def test_step_failure_without_error_message(self, logger, mock_output_manager):
        """Test step failure logging without error message."""
        logger.step_failure("TestStep", "")

        # Should only have one call (no error details)
        mock_output_manager.add.assert_called_once_with(
            "❌ 失敗: TestStep",
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def test_log_preparation_start(self, logger, mock_output_manager):
        """Test preparation start logging."""
        logger.log_preparation_start(5)

        mock_output_manager.add.assert_called_once_with(
            "\n🚀 環境準備開始: 5タスク",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue", bold=True)
        )

    def test_log_workflow_start_sequential(self, logger, mock_output_manager):
        """Test workflow start logging for sequential execution."""
        logger.log_workflow_start(3, parallel=False)

        mock_output_manager.add.assert_called_once_with(
            "\n🚀 ワークフロー実行開始: 3ステップ (順次実行)",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue", bold=True)
        )

    def test_log_workflow_start_parallel(self, logger, mock_output_manager):
        """Test workflow start logging for parallel execution."""
        logger.log_workflow_start(3, parallel=True)

        mock_output_manager.add.assert_called_once_with(
            "\n🚀 ワークフロー実行開始: 3ステップ (並列実行)",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue", bold=True)
        )

    def test_config_load_warning(self, logger, mock_output_manager):
        """Test config load warning."""
        logger.config_load_warning("/path/to/config.json", "File not found")

        mock_output_manager.add.assert_called_once_with(
            "⚠️ WARNING: Failed to load /path/to/config.json: File not found",
            LogLevel.WARNING,
            formatinfo=FormatInfo(color="yellow", bold=True)
        )

    def test_is_enabled_true(self, logger):
        """Test is_enabled when logger is enabled."""
        assert logger.is_enabled() is True

    def test_is_enabled_false(self, mock_output_manager):
        """Test is_enabled when logger is disabled."""
        config = {"enabled": False, "format": {"icons": {}}}
        logger = WorkflowLoggerAdapter(mock_output_manager, config)

        assert logger.is_enabled() is False

    def test_custom_icons_override_defaults(self, mock_output_manager):
        """Test that custom icons override default icons."""
        config = {
            "enabled": True,
            "format": {
                "icons": {
                    "start": "🎯",  # Override default
                    "custom": "📍"   # New icon
                }
            }
        }
        logger = WorkflowLoggerAdapter(mock_output_manager, config)

        assert logger.icons["start"] == "🎯"  # Overridden
        assert logger.icons["success"] == "✅"  # Default retained
        assert logger.icons["custom"] == "📍"  # Custom added

    def test_kwargs_are_ignored(self, logger, mock_output_manager):
        """Test that kwargs are properly ignored in all methods."""
        logger.debug("Test", extra="ignored")
        logger.info("Test", level="ignored")
        logger.warning("Test", timestamp=123)
        logger.error("Test", context={})
        logger.step_start("Test", meta="ignored")

        # All methods should have been called without errors
        assert mock_output_manager.add.call_count == 6  # debug, info, warning, error, step_start(2 calls)

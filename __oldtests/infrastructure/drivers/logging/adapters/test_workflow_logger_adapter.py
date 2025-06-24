"""Tests for WorkflowLoggerAdapter"""

from unittest.mock import Mock, patch

import pytest

from src.infrastructure.drivers.logging.adapters.workflow_logger_adapter import WorkflowLoggerAdapter
from src.infrastructure.drivers.logging.format_info import FormatInfo
from src.infrastructure.drivers.logging.interfaces.output_manager_interface import OutputManagerInterface
from src.infrastructure.drivers.logging.types import LogLevel


class TestWorkflowLoggerAdapter:
    """Tests for WorkflowLoggerAdapter class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.output_manager = Mock(spec=OutputManagerInterface)

        # Mock config manager
        self.mock_config_manager = Mock()
        self.mock_config_manager.resolve_config.side_effect = self._config_side_effect

        # Setup minimal config
        self.logger_config = {
            "format": {
                "icons": {
                    "custom": "🎯"
                }
            }
        }

    def _config_side_effect(self, path, data_type):
        """Mock config manager side effect"""
        if path == ['logging_config', 'adapters', 'workflow', 'default_enabled']:
            return True
        if path == ['logging_config', 'adapters', 'workflow', 'default_format', 'icons']:
            return {"config": "⚙️"}
        if path == ['workflow', 'execution_modes', 'parallel']:
            return "並列"
        if path == ['workflow', 'execution_modes', 'sequential']:
            return "順次"
        raise KeyError(f"Unknown config path: {path}")

    @patch('src.infrastructure.drivers.logging.adapters.workflow_logger_adapter.DIContainer')
    def test_init_with_config(self, mock_di_container):
        """Test initialization with config"""
        mock_di_container.resolve.return_value = self.mock_config_manager

        adapter = WorkflowLoggerAdapter(self.output_manager, self.logger_config)

        assert adapter.output_manager == self.output_manager
        assert adapter.config == self.logger_config
        assert adapter.enabled is True
        assert "custom" in adapter.icons
        assert adapter.icons["custom"] == "🎯"
        assert "config" in adapter.icons
        assert adapter.icons["config"] == "⚙️"




    def _create_adapter(self):
        """Helper to create adapter with mocked dependencies"""
        with patch('src.infrastructure.drivers.logging.adapters.workflow_logger_adapter.DIContainer') as mock_di:
            mock_di.resolve.return_value = self.mock_config_manager
            return WorkflowLoggerAdapter(self.output_manager, self.logger_config)

    def test_debug_enabled(self):
        """Test debug method when enabled"""
        adapter = self._create_adapter()

        adapter.debug("Test debug message")

        self.output_manager.add.assert_called_once_with(
            "🔍 DEBUG: Test debug message",
            LogLevel.DEBUG,
            formatinfo=FormatInfo(color="gray")
        )

    def test_debug_disabled(self):
        """Test debug method when disabled"""
        adapter = self._create_adapter()
        adapter.enabled = False

        adapter.debug("Test debug message")

        self.output_manager.add.assert_not_called()

    def test_info_enabled(self):
        """Test info method when enabled"""
        adapter = self._create_adapter()

        adapter.info("Test info message")

        self.output_manager.add.assert_called_once_with(
            "ℹ️ Test info message",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="cyan")
        )

    def test_info_disabled(self):
        """Test info method when disabled"""
        adapter = self._create_adapter()
        adapter.enabled = False

        adapter.info("Test info message")

        self.output_manager.add.assert_not_called()

    def test_warning_enabled(self):
        """Test warning method when enabled"""
        adapter = self._create_adapter()

        adapter.warning("Test warning message")

        self.output_manager.add.assert_called_once_with(
            "⚠️ WARNING: Test warning message",
            LogLevel.WARNING,
            formatinfo=FormatInfo(color="yellow", bold=True)
        )

    def test_error_enabled(self):
        """Test error method when enabled"""
        adapter = self._create_adapter()

        adapter.error("Test error message")

        self.output_manager.add.assert_called_once_with(
            "💥 ERROR: Test error message",
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def test_step_start_enabled(self):
        """Test step_start method when enabled"""
        adapter = self._create_adapter()

        adapter.step_start("Test Step")

        # Should make two calls: start message and executing message
        assert self.output_manager.add.call_count == 2

        # First call: start message
        first_call = self.output_manager.add.call_args_list[0]
        assert first_call[0][0] == "\n🚀 実行開始: Test Step"
        assert first_call[0][1] == LogLevel.INFO
        assert first_call[1]['formatinfo'] == FormatInfo(color="blue", bold=True)

        # Second call: executing message
        second_call = self.output_manager.add.call_args_list[1]
        assert second_call[0][0] == "  ⏱️ 実行中..."
        assert second_call[0][1] == LogLevel.INFO
        assert second_call[1]['formatinfo'] == FormatInfo(color="blue")

    def test_step_start_disabled(self):
        """Test step_start method when disabled"""
        adapter = self._create_adapter()
        adapter.enabled = False

        adapter.step_start("Test Step")

        self.output_manager.add.assert_not_called()

    def test_step_success_enabled(self):
        """Test step_success method when enabled"""
        adapter = self._create_adapter()

        adapter.step_success("Test Step", "Success message")

        self.output_manager.add.assert_called_once_with(
            "✅ 完了: Test Step - Success message",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="green", bold=True)
        )

    def test_step_success_no_message(self):
        """Test step_success method without message"""
        adapter = self._create_adapter()

        adapter.step_success("Test Step")

        self.output_manager.add.assert_called_once_with(
            "✅ 完了: Test Step",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="green", bold=True)
        )

    def test_step_success_disabled(self):
        """Test step_success method when disabled"""
        adapter = self._create_adapter()
        adapter.enabled = False

        adapter.step_success("Test Step")

        self.output_manager.add.assert_not_called()

    def test_step_failure_enabled(self):
        """Test step_failure method when enabled"""
        adapter = self._create_adapter()

        adapter.step_failure("Test Step", "Error occurred")

        # Should make two calls: failure message and error message
        assert self.output_manager.add.call_count == 2

        # First call: failure message
        first_call = self.output_manager.add.call_args_list[0]
        assert first_call[0][0] == "❌ 失敗: Test Step"
        assert first_call[0][1] == LogLevel.ERROR
        assert first_call[1]['formatinfo'] == FormatInfo(color="red", bold=True)

        # Second call: error message
        second_call = self.output_manager.add.call_args_list[1]
        assert second_call[0][0] == "  エラー: Error occurred"
        assert second_call[0][1] == LogLevel.ERROR
        assert second_call[1]['formatinfo'] == FormatInfo(color="red", indent=1)

    def test_step_failure_allow_failure(self):
        """Test step_failure method with allow_failure=True"""
        adapter = self._create_adapter()

        adapter.step_failure("Test Step", "Error occurred", allow_failure=True)

        # Should make two calls with warning level
        assert self.output_manager.add.call_count == 2

        # First call: failure message
        first_call = self.output_manager.add.call_args_list[0]
        assert first_call[0][0] == "⚠️ 失敗許可: Test Step"
        assert first_call[0][1] == LogLevel.WARNING
        assert first_call[1]['formatinfo'] == FormatInfo(color="yellow", bold=True)

        # Second call: error message
        second_call = self.output_manager.add.call_args_list[1]
        assert second_call[0][0] == "  エラー: Error occurred"
        assert second_call[0][1] == LogLevel.WARNING
        assert second_call[1]['formatinfo'] == FormatInfo(color="yellow", indent=1)

    def test_step_failure_no_error(self):
        """Test step_failure method without error message"""
        adapter = self._create_adapter()

        adapter.step_failure("Test Step", "")

        # Should make only one call (no error message)
        self.output_manager.add.assert_called_once_with(
            "❌ 失敗: Test Step",
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def test_log_preparation_start_enabled(self):
        """Test log_preparation_start method when enabled"""
        adapter = self._create_adapter()

        adapter.log_preparation_start(5)

        self.output_manager.add.assert_called_once_with(
            "\n🚀 環境準備開始: 5タスク",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue", bold=True)
        )

    def test_log_preparation_start_disabled(self):
        """Test log_preparation_start method when disabled"""
        adapter = self._create_adapter()
        adapter.enabled = False

        adapter.log_preparation_start(5)

        self.output_manager.add.assert_not_called()

    def test_log_workflow_start_parallel(self):
        """Test log_workflow_start method with parallel execution"""
        adapter = self._create_adapter()

        adapter.log_workflow_start(3, parallel=True)

        self.output_manager.add.assert_called_once_with(
            "\n🚀 ワークフロー実行開始: 3ステップ (並列実行)",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue", bold=True)
        )

    def test_log_workflow_start_sequential(self):
        """Test log_workflow_start method with sequential execution"""
        adapter = self._create_adapter()

        adapter.log_workflow_start(3, parallel=False)

        self.output_manager.add.assert_called_once_with(
            "\n🚀 ワークフロー実行開始: 3ステップ (順次実行)",
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue", bold=True)
        )


    def test_config_load_warning(self):
        """Test config_load_warning method"""
        adapter = self._create_adapter()

        adapter.config_load_warning("/path/to/config.json", "File not found")

        self.output_manager.add.assert_called_once_with(
            "⚠️ WARNING: Failed to load /path/to/config.json: File not found",
            LogLevel.WARNING,
            formatinfo=FormatInfo(color="yellow", bold=True)
        )

    def test_is_enabled_true(self):
        """Test is_enabled method returns True when enabled"""
        adapter = self._create_adapter()
        assert adapter.is_enabled() is True

    def test_is_enabled_false(self):
        """Test is_enabled method returns False when disabled"""
        adapter = self._create_adapter()
        adapter.enabled = False
        assert adapter.is_enabled() is False

    def test_default_icons(self):
        """Test that default icons are properly set"""
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

        adapter = self._create_adapter()

        for key, icon in expected_icons.items():
            assert adapter.icons[key] == icon

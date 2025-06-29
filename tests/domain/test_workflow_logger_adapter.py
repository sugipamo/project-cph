"""Tests for WorkflowLoggerAdapter."""
import pytest
from unittest.mock import Mock, MagicMock
from src.domain.workflow_logger_adapter import WorkflowLoggerAdapter
from src.logging.types import LogLevel
from src.utils.format_info import FormatInfo


class TestWorkflowLoggerAdapter:
    """Test suite for WorkflowLoggerAdapter."""

    def test_init_with_valid_config(self):
        """Test initialization with valid configuration."""
        # Arrange
        mock_output_manager = Mock()
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.side_effect = [
            True,  # enabled status
            {'info': 'ℹ️', 'error': '❌'},  # config icons
        ]
        logger_config = {
            'format': {
                'icons': {'custom': '🔧'}
            }
        }
        
        # Act
        adapter = WorkflowLoggerAdapter(mock_output_manager, mock_config_manager, logger_config)
        
        # Assert
        assert adapter.enabled is True
        assert adapter.output_manager == mock_output_manager
        assert adapter._config_manager == mock_config_manager
        assert adapter.icons['info'] == 'ℹ️'
        assert adapter.icons['error'] == '❌'
        assert adapter.icons['custom'] == '🔧'

    def test_init_without_logger_config(self):
        """Test initialization without logger config raises error."""
        # Arrange
        mock_output_manager = Mock()
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.side_effect = [
            True,  # enabled status
            {},    # config icons
        ]
        
        # Act & Assert
        with pytest.raises(ValueError, match="User icon configuration not found"):
            WorkflowLoggerAdapter(mock_output_manager, mock_config_manager, None)

    def test_init_config_not_available(self):
        """Test initialization when config is not available."""
        # Arrange
        mock_output_manager = Mock()
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.side_effect = KeyError("Config not found")
        logger_config = {'format': {'icons': {}}}
        
        # Act & Assert
        with pytest.raises(ValueError, match="Workflow logger enabled status configuration not available"):
            WorkflowLoggerAdapter(mock_output_manager, mock_config_manager, logger_config)

    def test_debug_when_enabled(self):
        """Test debug message when logging is enabled."""
        # Arrange
        mock_output_manager = Mock()
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.side_effect = [True, {}]
        logger_config = {'format': {'icons': {}}}
        adapter = WorkflowLoggerAdapter(mock_output_manager, mock_config_manager, logger_config)
        
        # Act
        adapter.debug("Test debug message")
        
        # Assert
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args
        assert "🔍 DEBUG: Test debug message" in call_args[0][0]
        assert call_args[0][1] == LogLevel.DEBUG

    def test_info_when_disabled(self):
        """Test info message when logging is disabled."""
        # Arrange
        mock_output_manager = Mock()
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.side_effect = [False, {}]
        logger_config = {'format': {'icons': {}}}
        adapter = WorkflowLoggerAdapter(mock_output_manager, mock_config_manager, logger_config)
        
        # Act
        adapter.info("Test info message")
        
        # Assert
        mock_output_manager.add.assert_not_called()

    def test_step_start(self):
        """Test step start logging."""
        # Arrange
        mock_output_manager = Mock()
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.side_effect = [True, {}]
        logger_config = {'format': {'icons': {}}}
        adapter = WorkflowLoggerAdapter(mock_output_manager, mock_config_manager, logger_config)
        
        # Act
        adapter.step_start("Test Step")
        
        # Assert
        assert mock_output_manager.add.call_count == 2
        first_call = mock_output_manager.add.call_args_list[0]
        assert "🚀 実行開始: Test Step" in first_call[0][0]

    def test_step_failure_with_allow_failure(self):
        """Test step failure with allow_failure flag."""
        # Arrange
        mock_output_manager = Mock()
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.side_effect = [True, {}]
        logger_config = {'format': {'icons': {}}}
        adapter = WorkflowLoggerAdapter(mock_output_manager, mock_config_manager, logger_config)
        
        # Act
        adapter.step_failure("Test Step", "Test error", allow_failure=True)
        
        # Assert
        assert mock_output_manager.add.call_count == 2
        first_call = mock_output_manager.add.call_args_list[0]
        assert "⚠️ 失敗許可: Test Step" in first_call[0][0]
        assert first_call[0][1] == LogLevel.WARNING

    def test_log_workflow_start(self):
        """Test workflow start logging."""
        # Arrange
        mock_output_manager = Mock()
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.side_effect = [
            True,  # enabled
            {},    # icons
            "並列",  # parallel mode
            "順次",  # sequential mode
        ]
        logger_config = {'format': {'icons': {}}}
        adapter = WorkflowLoggerAdapter(mock_output_manager, mock_config_manager, logger_config)
        
        # Act
        adapter.log_workflow_start(5, parallel=True)
        
        # Assert
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args
        assert "🚀 ワークフロー実行開始: 5ステップ (並列実行)" in call_args[0][0]

    def test_set_and_get_level(self):
        """Test setting and getting log level."""
        # Arrange
        mock_output_manager = Mock()
        mock_output_manager.get_level.return_value = LogLevel.WARNING
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.side_effect = [True, {}]
        logger_config = {'format': {'icons': {}}}
        adapter = WorkflowLoggerAdapter(mock_output_manager, mock_config_manager, logger_config)
        
        # Act & Assert
        adapter.set_level("ERROR")
        mock_output_manager.set_level.assert_called_once_with(LogLevel.ERROR)
        
        level = adapter.get_level()
        assert level == "WARNING"

    def test_is_enabled(self):
        """Test is_enabled method."""
        # Arrange
        mock_output_manager = Mock()
        mock_config_manager = Mock()
        mock_config_manager.resolve_config.side_effect = [True, {}]
        logger_config = {'format': {'icons': {}}}
        adapter = WorkflowLoggerAdapter(mock_output_manager, mock_config_manager, logger_config)
        
        # Act & Assert
        assert adapter.is_enabled() is True
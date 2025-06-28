import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import logging

from src.logging.unified_logger import UnifiedLogger
from src.utils.types import LogLevel


class TestUnifiedLogger:
    @pytest.fixture
    def mock_output_manager(self):
        return Mock()
    
    @pytest.fixture
    def mock_di_container(self):
        mock_container = Mock()
        mock_config_manager = Mock()
        
        # Set up config manager responses using string keys
        def resolve_config_side_effect(path, type_):
            key = str(path)  # Convert list to string for comparison
            if key == "['logging_config', 'unified_logger', 'default_enabled']" and type_ == bool:
                return True
            elif key == "['logging_config', 'unified_logger', 'default_format', 'icons']" and type_ == dict:
                return {}
            elif key == "['logging_config', 'unified_logger', 'defaults', 'status_success']" and type_ == str:
                return "SUCCESS"
            elif key == "['logging_config', 'unified_logger', 'defaults', 'status_failure']" and type_ == str:
                return "FAILED"
            elif key == "['logging_config', 'unified_logger', 'defaults', 'color_success']" and type_ == str:
                return "green"
            elif key == "['logging_config', 'unified_logger', 'defaults', 'color_failure']" and type_ == str:
                return "red"
            elif key == "['workflow', 'execution_modes', 'parallel']" and type_ == str:
                return "並列"
            elif key == "['workflow', 'execution_modes', 'sequential']" and type_ == str:
                return "順次"
            else:
                return {}
        
        mock_config_manager.resolve_config.side_effect = resolve_config_side_effect
        
        mock_container.resolve.return_value = mock_config_manager
        return mock_container
    
    @pytest.fixture
    def logger_config(self):
        return {
            'format': {
                'icons': {}
            }
        }

    @pytest.fixture
    def logger(self, mock_output_manager, logger_config, mock_di_container):
        return UnifiedLogger(mock_output_manager, name="test_logger", logger_config=logger_config, di_container=mock_di_container)

    def test_init(self, mock_output_manager, logger_config, mock_di_container):
        logger = UnifiedLogger(mock_output_manager, name="test_logger", logger_config=logger_config, di_container=mock_di_container)
        assert logger.name == "test_logger"
        assert logger.output_manager == mock_output_manager
        assert logger.enabled == True

    def test_set_level(self, logger, mock_output_manager):
        logger.set_level("DEBUG")
        mock_output_manager.set_level.assert_called_once_with(LogLevel.DEBUG)
        
        logger.set_level("ERROR")
        mock_output_manager.set_level.assert_called_with(LogLevel.ERROR)

    def test_debug(self, logger, mock_output_manager):
        logger.set_level("DEBUG")
        logger.debug("Debug message")
        
        mock_output_manager.add.assert_called()
        call_args = mock_output_manager.add.call_args
        # Check the message content
        assert "Debug message" in call_args[0][0]
        # Check the log level
        assert call_args[0][1] == LogLevel.DEBUG

    def test_info(self, logger, mock_output_manager):
        logger.info("Info message")
        
        mock_output_manager.add.assert_called()
        call_args = mock_output_manager.add.call_args
        # Check the message content
        assert "Info message" in call_args[0][0]
        # Check the log level
        assert call_args[0][1] == LogLevel.INFO

    def test_warning(self, logger, mock_output_manager):
        logger.warning("Warning message")
        
        mock_output_manager.add.assert_called()
        call_args = mock_output_manager.add.call_args
        # Check the message content
        assert "Warning message" in call_args[0][0]
        # Check the log level
        assert call_args[0][1] == LogLevel.WARNING

    def test_error(self, logger, mock_output_manager):
        logger.error("Error message")
        
        mock_output_manager.add.assert_called()
        call_args = mock_output_manager.add.call_args
        # Check the message content
        assert "Error message" in call_args[0][0]
        # Check the log level
        assert call_args[0][1] == LogLevel.ERROR

    def test_critical(self, logger, mock_output_manager):
        logger.critical("Critical message")
        
        mock_output_manager.add.assert_called()
        call_args = mock_output_manager.add.call_args
        # Check the message content
        assert "Critical message" in call_args[0][0]
        # Check the log level
        assert call_args[0][1] == LogLevel.CRITICAL

    def test_format_message_string(self, logger):
        result = logger._format_message("Test message", ())
        assert result == "Test message"

    def test_format_message_with_args(self, logger):
        result = logger._format_message("Test %s %d", ("message", 123))
        assert result == "Test message 123"

    def test_log_error_with_correlation(self, logger, mock_output_manager):
        logger.log_error_with_correlation("err123", "TEST_ERROR", "Test error message", {"key": "value"})
        
        mock_output_manager.add.assert_called()
        call_args = mock_output_manager.add.call_args
        assert "[ERROR#err123]" in call_args[0][0]
        assert "[TEST_ERROR]" in call_args[0][0]
        assert "Test error message" in call_args[0][0]
        assert call_args[0][1] == LogLevel.ERROR

    def test_log_operation_start(self, logger, mock_output_manager):
        logger.log_operation_start("op123", "TestOperation", {"param": "value"})
        
        mock_output_manager.add.assert_called()
        call_args = mock_output_manager.add.call_args
        assert "[OP#op123]" in call_args[0][0]
        assert "TestOperation started" in call_args[0][0]
        assert call_args[0][1] == LogLevel.INFO

    def test_log_operation_end(self, logger, mock_output_manager):
        logger.log_operation_end("op123", "TestOperation", True, {"result": "success"})
        
        mock_output_manager.add.assert_called()
        call_args = mock_output_manager.add.call_args
        assert "[OP#op123]" in call_args[0][0]
        assert "TestOperation SUCCESS" in call_args[0][0]
        assert call_args[0][1] == LogLevel.INFO

    def test_step_start(self, logger, mock_output_manager):
        logger.step_start("Test Step")
        
        # Should call add twice (start message and executing message)
        assert mock_output_manager.add.call_count == 2
        first_call = mock_output_manager.add.call_args_list[0]
        assert "実行開始: Test Step" in first_call[0][0]

    def test_step_success(self, logger, mock_output_manager):
        logger.step_success("Test Step", "Success message")
        
        mock_output_manager.add.assert_called()
        call_args = mock_output_manager.add.call_args
        assert "完了: Test Step" in call_args[0][0]
        assert "Success message" in call_args[0][0]

    def test_step_failure(self, logger, mock_output_manager):
        logger.step_failure("Test Step", "Error message", allow_failure=False)
        
        mock_output_manager.add.assert_called()
        # Should call add twice (failure message and error details)
        assert mock_output_manager.add.call_count == 2
        first_call = mock_output_manager.add.call_args_list[0]
        assert "失敗: Test Step" in first_call[0][0]

    def test_is_enabled(self, logger):
        assert logger.is_enabled() == True

    def test_config_load_warning(self, logger, mock_output_manager):
        logger.config_load_warning("/path/to/config.json", "File not found")
        
        mock_output_manager.add.assert_called()
        call_args = mock_output_manager.add.call_args
        assert "Failed to load /path/to/config.json" in call_args[0][0]
        assert "File not found" in call_args[0][0]

    def test_log_preparation_start(self, logger, mock_output_manager):
        logger.log_preparation_start(5)
        
        mock_output_manager.add.assert_called()
        call_args = mock_output_manager.add.call_args
        assert "環境準備開始: 5タスク" in call_args[0][0]

    def test_log_workflow_start(self, logger, mock_output_manager):
        logger.log_workflow_start(3, parallel=True)
        
        mock_output_manager.add.assert_called()
        call_args = mock_output_manager.add.call_args
        assert "ワークフロー実行開始: 3ステップ" in call_args[0][0]
        assert "並列実行" in call_args[0][0]
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import logging

from src.logging.unified_logger import UnifiedLogger
from src.utils.log_types import LogLevel
from src.utils.types import LogEntry


class TestUnifiedLogger:
    @pytest.fixture
    def mock_output_manager(self):
        return Mock()

    @pytest.fixture
    def logger(self, mock_output_manager):
        return UnifiedLogger(mock_output_manager, name="test_logger")

    def test_init(self, mock_output_manager):
        logger = UnifiedLogger(mock_output_manager, name="test_logger")
        assert logger.name == "test_logger"
        assert logger._output_manager == mock_output_manager
        assert logger._min_level == LogLevel.INFO

    def test_init_default_name(self, mock_output_manager):
        logger = UnifiedLogger(mock_output_manager)
        assert logger.name == "UnifiedLogger"

    def test_set_level(self, logger):
        logger.set_level(LogLevel.DEBUG)
        assert logger._min_level == LogLevel.DEBUG
        
        logger.set_level(LogLevel.ERROR)
        assert logger._min_level == LogLevel.ERROR

    def test_debug(self, logger, mock_output_manager):
        logger.set_level(LogLevel.DEBUG)
        logger.debug("Debug message")
        
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args[0][0]
        assert isinstance(call_args, LogEntry)
        assert call_args.level == LogLevel.DEBUG
        assert "Debug message" in str(call_args.content)

    def test_info(self, logger, mock_output_manager):
        logger.info("Info message")
        
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args[0][0]
        assert isinstance(call_args, LogEntry)
        assert call_args.level == LogLevel.INFO
        assert "Info message" in str(call_args.content)

    def test_warning(self, logger, mock_output_manager):
        logger.warning("Warning message")
        
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args[0][0]
        assert isinstance(call_args, LogEntry)
        assert call_args.level == LogLevel.WARNING
        assert "Warning message" in str(call_args.content)

    def test_error(self, logger, mock_output_manager):
        logger.error("Error message")
        
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args[0][0]
        assert isinstance(call_args, LogEntry)
        assert call_args.level == LogLevel.ERROR
        assert "Error message" in str(call_args.content)

    def test_critical(self, logger, mock_output_manager):
        logger.critical("Critical message")
        
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args[0][0]
        assert isinstance(call_args, LogEntry)
        assert call_args.level == LogLevel.CRITICAL
        assert "Critical message" in str(call_args.content)

    def test_log_with_level(self, logger, mock_output_manager):
        logger.log(LogLevel.WARNING, "Test message")
        
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args[0][0]
        assert isinstance(call_args, LogEntry)
        assert call_args.level == LogLevel.WARNING

    def test_level_filtering(self, logger, mock_output_manager):
        logger.set_level(LogLevel.WARNING)
        
        # These should not be logged
        logger.debug("Debug")
        logger.info("Info")
        assert mock_output_manager.add.call_count == 0
        
        # These should be logged
        logger.warning("Warning")
        logger.error("Error")
        logger.critical("Critical")
        assert mock_output_manager.add.call_count == 3

    def test_format_message_string(self, logger):
        result = logger._format_message("Test message")
        assert result == "Test message"

    def test_format_message_with_args(self, logger):
        result = logger._format_message("Test %s %d", "message", 123)
        assert result == "Test message 123"

    def test_format_message_with_kwargs(self, logger):
        result = logger._format_message("Test {name} {value}", name="message", value=123)
        assert result == "Test message 123"

    def test_exception_logging(self, logger, mock_output_manager):
        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("Exception occurred")
        
        mock_output_manager.add.assert_called()
        call_args = mock_output_manager.add.call_args[0][0]
        assert isinstance(call_args, LogEntry)
        assert call_args.level == LogLevel.ERROR
        assert "Exception occurred" in str(call_args.content)
        assert "ValueError" in str(call_args.content)

    def test_add_handler(self, logger):
        handler = Mock()
        logger.add_handler(handler)
        
        logger.info("Test message")
        handler.handle.assert_called_once()

    def test_remove_handler(self, logger):
        handler = Mock()
        logger.add_handler(handler)
        logger.remove_handler(handler)
        
        logger.info("Test message")
        handler.handle.assert_not_called()

    def test_set_formatter(self, logger):
        handler = Mock()
        formatter = Mock()
        
        logger.add_handler(handler)
        logger.set_formatter(formatter)
        
        handler.setFormatter.assert_called_once_with(formatter)

    def test_python_logging_adapter(self, logger):
        with patch('logging.getLogger') as mock_get_logger:
            mock_python_logger = Mock()
            mock_get_logger.return_value = mock_python_logger
            
            logger.info("Test message")
            
            # The UnifiedLogger should also log to Python's logging
            mock_python_logger.info.assert_called()

    def test_structured_logging(self, logger, mock_output_manager):
        logger.info("User action", extra={"user_id": 123, "action": "login"})
        
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args[0][0]
        assert isinstance(call_args, LogEntry)

    def test_is_enabled_for(self, logger):
        logger.set_level(LogLevel.WARNING)
        
        assert not logger.is_enabled_for(LogLevel.DEBUG)
        assert not logger.is_enabled_for(LogLevel.INFO)
        assert logger.is_enabled_for(LogLevel.WARNING)
        assert logger.is_enabled_for(LogLevel.ERROR)
        assert logger.is_enabled_for(LogLevel.CRITICAL)

    def test_child_logger(self, logger):
        child = logger.get_child("child")
        assert child.name == "test_logger.child"
        assert child._output_manager == logger._output_manager

    def test_context_logging(self, logger, mock_output_manager):
        with logger.context(request_id="123"):
            logger.info("Message with context")
        
        mock_output_manager.add.assert_called_once()
        # Context would be added to the log entry
"""Test module for ApplicationLoggerAdapter."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.logging.application_logger_adapter import ApplicationLoggerAdapter
from src.utils.types import LogLevel
from src.utils.format_info import FormatInfo


class TestApplicationLoggerAdapter:
    """Test cases for ApplicationLoggerAdapter."""

    @pytest.fixture
    def mock_output_manager(self):
        """Create a mock output manager."""
        return Mock()

    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock config manager with proper configuration."""
        mock = Mock()
        
        def resolve_config_side_effect(path, type_):
            config_map = {
                "['logging_config', 'adapters', 'application', 'status_success']": "completed",
                "['logging_config', 'adapters', 'application', 'status_failure']": "failed",
                "['logging_config', 'adapters', 'application', 'color_success']": "green",
                "['logging_config', 'adapters', 'application', 'color_failure']": "red",
            }
            key = str(path)
            if key in config_map and type_ == str:
                return config_map[key]
            raise KeyError(f"Configuration not found: {key}")
        
        mock.resolve_config.side_effect = resolve_config_side_effect
        return mock

    @pytest.fixture
    def adapter_with_config(self, mock_output_manager, mock_config_manager):
        """Create an adapter with mocked config manager."""
        with patch('src.infrastructure.di_container.DIContainer.resolve', return_value=mock_config_manager):
            adapter = ApplicationLoggerAdapter(mock_output_manager, "test_logger")
            adapter._config_manager = mock_config_manager
            return adapter

    @pytest.fixture
    def adapter_without_config(self, mock_output_manager):
        """Create an adapter without config manager."""
        with patch('src.infrastructure.di_container.DIContainer.resolve', side_effect=Exception("No config")):
            adapter = ApplicationLoggerAdapter(mock_output_manager, "test_logger")
            return adapter

    def test_init_with_config_manager(self, mock_output_manager, mock_config_manager):
        """Test initialization with config manager available."""
        with patch('src.infrastructure.di_container.DIContainer.resolve', return_value=mock_config_manager):
            adapter = ApplicationLoggerAdapter(mock_output_manager, "test_logger")
            assert adapter.output_manager == mock_output_manager
            assert adapter.name == "test_logger"
            assert adapter.session_id is not None
            assert len(adapter.session_id) == 8
            assert adapter._config_manager == mock_config_manager

    def test_init_without_config_manager(self, mock_output_manager):
        """Test initialization when config manager is not available."""
        with patch('src.infrastructure.di_container.DIContainer.resolve', side_effect=Exception("No config")):
            adapter = ApplicationLoggerAdapter(mock_output_manager, "test_logger")
            assert adapter.output_manager == mock_output_manager
            assert adapter.name == "test_logger"
            assert adapter.session_id is not None
            assert adapter._config_manager is None

    def test_debug(self, adapter_with_config, mock_output_manager):
        """Test debug logging."""
        adapter_with_config.debug("Debug message")
        
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args
        assert call_args[0][0] == "Debug message"
        assert call_args[0][1] == LogLevel.DEBUG
        assert call_args.kwargs['formatinfo'].color == 'gray'
        assert call_args.kwargs['realtime'] is False

    def test_info(self, adapter_with_config, mock_output_manager):
        """Test info logging."""
        adapter_with_config.info("Info message")
        
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args
        assert call_args[0][0] == "Info message"
        assert call_args[0][1] == LogLevel.INFO
        assert call_args.kwargs['formatinfo'].color == 'cyan'
        assert call_args.kwargs['realtime'] is False

    def test_warning(self, adapter_with_config, mock_output_manager):
        """Test warning logging."""
        adapter_with_config.warning("Warning message")
        
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args
        assert call_args[0][0] == "Warning message"
        assert call_args[0][1] == LogLevel.WARNING
        assert call_args.kwargs['formatinfo'].color == 'yellow'
        assert call_args.kwargs['formatinfo'].bold is True
        assert call_args.kwargs['realtime'] is False

    def test_error(self, adapter_with_config, mock_output_manager):
        """Test error logging."""
        adapter_with_config.error("Error message")
        
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args
        assert call_args[0][0] == "Error message"
        assert call_args[0][1] == LogLevel.ERROR
        assert call_args.kwargs['formatinfo'].color == 'red'
        assert call_args.kwargs['formatinfo'].bold is True
        assert call_args.kwargs['realtime'] is False

    def test_critical(self, adapter_with_config, mock_output_manager):
        """Test critical logging."""
        adapter_with_config.critical("Critical message")
        
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args
        assert call_args[0][0] == "Critical message"
        assert call_args[0][1] == LogLevel.CRITICAL
        assert call_args.kwargs['formatinfo'].color == 'red'
        assert call_args.kwargs['formatinfo'].bold is True
        assert call_args.kwargs['realtime'] is False

    def test_log_error_with_correlation_with_context(self, adapter_with_config, mock_output_manager):
        """Test error logging with correlation ID and context."""
        context = {"user": "test", "action": "delete"}
        adapter_with_config.log_error_with_correlation("ERR123", "DB_ERROR", "Database connection failed", context)
        
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args
        message = call_args[0][0]
        assert "[ERROR#ERR123]" in message
        assert "[DB_ERROR]" in message
        assert "Database connection failed" in message
        assert f"(session: {adapter_with_config.session_id})" in message
        assert "Context: {'user': 'test', 'action': 'delete'}" in message
        assert call_args[0][1] == LogLevel.ERROR

    def test_log_error_with_correlation_without_context(self, adapter_with_config, mock_output_manager):
        """Test error logging with correlation ID but no context."""
        adapter_with_config.log_error_with_correlation("ERR456", "AUTH_ERROR", "Authentication failed", None)
        
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args
        message = call_args[0][0]
        assert "[ERROR#ERR456]" in message
        assert "[AUTH_ERROR]" in message
        assert "Authentication failed" in message
        assert "Context:" not in message

    def test_log_operation_start_with_details(self, adapter_with_config, mock_output_manager):
        """Test operation start logging with details."""
        details = {"file": "test.txt", "size": 1024}
        adapter_with_config.log_operation_start("OP001", "FileUpload", details)
        
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args
        message = call_args[0][0]
        assert "[OP#OP001]" in message
        assert "FileUpload started" in message
        assert f"(session: {adapter_with_config.session_id})" in message
        assert "Details: {'file': 'test.txt', 'size': 1024}" in message
        assert call_args[0][1] == LogLevel.INFO

    def test_log_operation_start_without_details(self, adapter_with_config, mock_output_manager):
        """Test operation start logging without details."""
        adapter_with_config.log_operation_start("OP002", "CacheClean", None)
        
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args
        message = call_args[0][0]
        assert "[OP#OP002]" in message
        assert "CacheClean started" in message
        assert "Details:" not in message

    def test_log_operation_end_success(self, adapter_with_config, mock_output_manager):
        """Test operation end logging for successful operation."""
        details = {"duration": 1.5, "records": 100}
        adapter_with_config.log_operation_end("OP003", "DataImport", True, details)
        
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args
        message = call_args[0][0]
        assert "[OP#OP003]" in message
        assert "DataImport completed" in message
        assert f"(session: {adapter_with_config.session_id})" in message
        assert "Details: {'duration': 1.5, 'records': 100}" in message
        assert call_args[0][1] == LogLevel.INFO
        assert call_args.kwargs['formatinfo'].color == 'green'
        assert call_args.kwargs['formatinfo'].bold is False

    def test_log_operation_end_failure(self, adapter_with_config, mock_output_manager):
        """Test operation end logging for failed operation."""
        details = {"error": "Timeout", "retry_count": 3}
        adapter_with_config.log_operation_end("OP004", "APICall", False, details)
        
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args
        message = call_args[0][0]
        assert "[OP#OP004]" in message
        assert "APICall failed" in message
        assert call_args[0][1] == LogLevel.ERROR
        assert call_args.kwargs['formatinfo'].color == 'red'
        assert call_args.kwargs['formatinfo'].bold is True

    def test_log_operation_end_without_config_manager(self, adapter_without_config, mock_output_manager):
        """Test operation end logging when config manager is not available."""
        with pytest.raises(ValueError, match="Application adapter operation status configuration not found"):
            adapter_without_config.log_operation_end("OP005", "TestOp", True, None)

    def test_log_operation_end_with_config_error(self, adapter_with_config, mock_output_manager):
        """Test operation end logging when config retrieval fails."""
        adapter_with_config._config_manager.resolve_config.side_effect = KeyError("Config not found")
        
        with pytest.raises(ValueError, match="Application adapter operation status configuration not found"):
            adapter_with_config.log_operation_end("OP006", "TestOp", True, None)

    def test_format_message_simple(self, adapter_with_config):
        """Test message formatting without arguments."""
        result = adapter_with_config._format_message("Simple message", ())
        assert result == "Simple message"

    def test_format_message_with_args(self, adapter_with_config):
        """Test message formatting with valid arguments."""
        result = adapter_with_config._format_message("Hello %s, you have %d messages", ("Alice", 5))
        assert result == "Hello Alice, you have 5 messages"

    def test_format_message_with_invalid_args(self, adapter_with_config):
        """Test message formatting with invalid arguments."""
        # Too few arguments
        result = adapter_with_config._format_message("Hello %s %s", ("World",))
        assert result == "Hello %s %s ('World',)"

    def test_format_message_with_type_error(self, adapter_with_config):
        """Test message formatting with type mismatch."""
        # Wrong type for format specifier
        result = adapter_with_config._format_message("Count: %d", ("not a number",))
        assert result == "Count: %d ('not a number',)"

    def test_logging_with_args(self, adapter_with_config, mock_output_manager):
        """Test logging methods with format arguments."""
        adapter_with_config.debug("Debug: %s %d", "test", 123)
        adapter_with_config.info("Info: %s", "message")
        adapter_with_config.warning("Warning: %d%%", 50)
        adapter_with_config.error("Error: %s at line %d", "SyntaxError", 42)
        adapter_with_config.critical("Critical: system %s", "failure")
        
        assert mock_output_manager.add.call_count == 5
        
        # Check formatted messages
        calls = mock_output_manager.add.call_args_list
        assert calls[0][0][0] == "Debug: test 123"
        assert calls[1][0][0] == "Info: message"
        assert calls[2][0][0] == "Warning: 50%"
        assert calls[3][0][0] == "Error: SyntaxError at line 42"
        assert calls[4][0][0] == "Critical: system failure"

    def test_logging_with_kwargs(self, adapter_with_config, mock_output_manager):
        """Test that kwargs are accepted but not used in formatting."""
        # The interface accepts kwargs but doesn't use them
        adapter_with_config.info("Message", extra={"user": "test"})
        
        mock_output_manager.add.assert_called_once()
        call_args = mock_output_manager.add.call_args
        assert call_args[0][0] == "Message"

    def test_session_id_uniqueness(self, mock_output_manager):
        """Test that each adapter instance gets a unique session ID."""
        with patch('src.infrastructure.di_container.DIContainer.resolve', side_effect=Exception("No config")):
            adapter1 = ApplicationLoggerAdapter(mock_output_manager, "test1")
            adapter2 = ApplicationLoggerAdapter(mock_output_manager, "test2")
            
            assert adapter1.session_id != adapter2.session_id
            assert len(adapter1.session_id) == 8
            assert len(adapter2.session_id) == 8
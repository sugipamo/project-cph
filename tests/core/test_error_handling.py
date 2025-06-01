"""
Test error handling system
"""
import pytest
import time
from unittest.mock import patch, MagicMock

from src.core.exceptions import (
    CPHException, ValidationError, ExecutionError, ConfigurationError,
    ErrorHandler, ErrorLogger, ErrorRecovery
)


class TestBaseExceptions:
    """Test base exception hierarchy"""
    
    def test_cph_exception_basic(self):
        """Test basic CPH exception"""
        exception = CPHException("Test message")
        
        assert str(exception) == "Test message"
        assert exception.message == "Test message"
        assert exception.context == {}
        assert exception.original_exception is None
    
    def test_cph_exception_with_context(self):
        """Test CPH exception with context"""
        context = {"key": "value", "number": 42}
        exception = CPHException("Test message", context=context)
        
        assert exception.context == context
        full_message = exception.get_full_message()
        assert "key=value" in full_message
        assert "number=42" in full_message
    
    def test_cph_exception_with_original(self):
        """Test CPH exception with original exception"""
        original = ValueError("Original error")
        exception = CPHException("Wrapper message", original_exception=original)
        
        assert exception.original_exception == original
        full_message = exception.get_full_message()
        assert "Caused by: ValueError: Original error" in full_message
    
    def test_add_context(self):
        """Test adding context to exception"""
        exception = CPHException("Test message")
        exception.add_context("key1", "value1")
        exception.add_context("key2", "value2")
        
        assert exception.context["key1"] == "value1"
        assert exception.context["key2"] == "value2"
    
    def test_validation_error(self):
        """Test validation error"""
        error = ValidationError("test_field", "invalid value", "bad_data")
        
        assert error.field == "test_field"
        assert error.reason == "invalid value"
        assert error.value == "bad_data"
        assert "Validation failed for 'test_field'" in str(error)
    
    def test_execution_error(self):
        """Test execution error"""
        error = ExecutionError("test_operation", "operation failed", exit_code=1)
        
        assert error.operation == "test_operation"
        assert error.exit_code == 1
        assert "Execution failed in test_operation" in str(error)
    
    def test_configuration_error(self):
        """Test configuration error"""
        error = ConfigurationError("test_key", "missing value", "/path/to/config")
        
        assert error.config_key == "test_key"
        assert error.config_file == "/path/to/config"
        assert "Configuration error in 'test_key'" in str(error)


class TestErrorHandler:
    """Test error handler functionality"""
    
    def test_handle_operation_error(self):
        """Test operation error handling"""
        error = Exception("Test operation failed")
        context = {"operation": "test", "file": "test.py"}
        
        result = ErrorHandler.handle_operation_error("test_op", error, context)
        
        assert result.success is False
        assert "test_op" in result.error_message
        assert result.exception == error
        assert result.metadata == context
    
    def test_handle_validation_error(self):
        """Test validation error handling"""
        error = ErrorHandler.handle_validation_error("test_field", "invalid", "bad_value")
        
        assert isinstance(error, ValidationError)
        assert error.field == "test_field"
        assert error.reason == "invalid"
        assert error.value == "bad_value"
    
    def test_handle_configuration_error(self):
        """Test configuration error handling"""
        error = ErrorHandler.handle_configuration_error("test_key", "missing", "/config")
        
        assert isinstance(error, ConfigurationError)
        assert error.config_key == "test_key"
        assert error.config_file == "/config"
    
    def test_wrap_exception(self):
        """Test exception wrapping"""
        def failing_function():
            raise ValueError("Original error")
        
        with pytest.raises(ExecutionError) as exc_info:
            ErrorHandler.wrap_exception(failing_function, "test_operation")
        
        error = exc_info.value
        assert error.operation == "test_operation"
        assert isinstance(error.original_exception, ValueError)
    
    def test_convert_to_operation_result(self):
        """Test converting function result to operation result"""
        def successful_function():
            return "success_result"
        
        result = ErrorHandler.convert_to_operation_result(successful_function, "test_op")
        
        assert result.success is True
        assert result.start_time is not None
        assert result.end_time is not None
        assert result.end_time >= result.start_time
    
    def test_convert_to_operation_result_failure(self):
        """Test converting failed function to operation result"""
        def failing_function():
            raise ValueError("Function failed")
        
        result = ErrorHandler.convert_to_operation_result(failing_function, "test_op")
        
        assert result.success is False
        assert "test_op" in result.error_message
        assert isinstance(result.exception, ValueError)
    
    def test_create_error_context(self):
        """Test error context creation"""
        context = ErrorHandler.create_error_context("test_op", key1="value1", key2="value2")
        
        assert context["operation"] == "test_op"
        assert context["key1"] == "value1"
        assert context["key2"] == "value2"
        assert "timestamp" in context
    
    def test_get_root_cause(self):
        """Test root cause extraction"""
        root_cause = ValueError("Root error")
        wrapper1 = CPHException("Wrapper 1", original_exception=root_cause)
        wrapper2 = CPHException("Wrapper 2", original_exception=wrapper1)
        
        found_root = ErrorHandler.get_root_cause(wrapper2)
        assert found_root == root_cause


class TestErrorLogger:
    """Test error logger functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.logger = ErrorLogger(enable_console=False, enable_file=False)
    
    def test_logger_initialization(self):
        """Test logger initialization"""
        logger = ErrorLogger(enable_console=True, enable_file=True, log_file="/tmp/test.log")
        
        assert logger.enable_console is True
        assert logger.enable_file is True
        assert logger.log_file == "/tmp/test.log"
    
    @patch('builtins.print')
    def test_log_operation_error(self, mock_print):
        """Test operation error logging"""
        logger = ErrorLogger(enable_console=True, enable_file=False)
        error = Exception("Test error")
        context = {"key": "value"}
        
        logger.log_operation_error("test_operation", error, context)
        
        # Should have called print at least once
        assert mock_print.called
        
        # Check all print calls to find the one with our operation
        all_calls = [call[0][0] for call in mock_print.call_args_list]
        operation_logged = any("test_operation" in call for call in all_calls)
        error_logged = any("Test error" in call for call in all_calls)
        
        assert operation_logged, f"'test_operation' not found in any print calls: {all_calls}"
        assert error_logged, f"'Test error' not found in any print calls: {all_calls}"
    
    @patch('builtins.print')
    def test_log_validation_error(self, mock_print):
        """Test validation error logging"""
        logger = ErrorLogger(enable_console=True, enable_file=False)
        
        logger.log_validation_error("test_field", "invalid_value", "Value is invalid")
        
        assert mock_print.called
        call_args = mock_print.call_args[0][0]
        assert "test_field" in call_args
    
    @patch('builtins.print')
    def test_log_execution_start(self, mock_print):
        """Test execution start logging"""
        logger = ErrorLogger(enable_console=True, enable_file=False)
        
        logger.log_execution_start("test_operation", {"key": "value"})
        
        assert mock_print.called
        call_args = mock_print.call_args[0][0]
        assert "test_operation" in call_args
    
    @patch('builtins.print')
    def test_log_execution_success(self, mock_print):
        """Test execution success logging"""
        logger = ErrorLogger(enable_console=True, enable_file=False)
        
        logger.log_execution_success("test_operation", 1.5, "Completed successfully")
        
        assert mock_print.called
        call_args = mock_print.call_args[0][0]
        assert "test_operation" in call_args
        assert "1.50s" in call_args


class TestErrorRecovery:
    """Test error recovery functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.recovery = ErrorRecovery()
    
    def test_retry_success_after_failures(self):
        """Test retry mechanism with eventual success"""
        attempt_count = 0
        
        def flaky_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception(f"Attempt {attempt_count} failed")
            return f"Success on attempt {attempt_count}"
        
        from src.core.exceptions.error_recovery import RetryConfig
        config = RetryConfig(max_attempts=3, base_delay=0.01)  # Fast for testing
        
        result = self.recovery.retry_with_config(flaky_function, config, "test_operation")
        
        assert result == "Success on attempt 3"
        assert attempt_count == 3
    
    def test_retry_max_attempts_exceeded(self):
        """Test retry with max attempts exceeded"""
        def always_failing():
            raise Exception("Always fails")
        
        from src.core.exceptions.error_recovery import RetryConfig
        config = RetryConfig(max_attempts=2, base_delay=0.01)
        
        with pytest.raises(ExecutionError) as exc_info:
            self.recovery.retry_with_config(always_failing, config, "test_operation")
        
        error = exc_info.value
        assert "failed after 2 attempts" in error.message
    
    def test_retry_decorator(self):
        """Test retry decorator"""
        attempt_count = 0
        
        @self.recovery.retry(max_attempts=2, delay=0.01, operation_name="decorated_test")
        def decorated_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                raise Exception("First attempt fails")
            return "Success"
        
        result = decorated_function()
        assert result == "Success"
        assert attempt_count == 2
    
    def test_safe_execute_basic(self):
        """Test safe execute with basic function"""
        def simple_function():
            return "success"
        
        result = self.recovery.safe_execute(simple_function, "test_operation")
        assert result == "success"
    
    def test_safe_execute_with_retry(self):
        """Test safe execute with retry configuration"""
        attempt_count = 0
        
        def flaky_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                raise Exception("First fails")
            return "success"
        
        from src.core.exceptions.error_recovery import RetryConfig
        retry_config = RetryConfig(max_attempts=2, base_delay=0.01)
        
        result = self.recovery.safe_execute(
            flaky_function, "test_operation", retry_config=retry_config
        )
        
        assert result == "success"
        assert attempt_count == 2
"""Tests for ErrorConverter."""
import pytest
from unittest.mock import Mock
from src.operations.error_converter import ErrorConverter


class TestErrorConverter:
    """Test cases for ErrorConverter."""
    
    def test_execute_with_conversion_success(self):
        """Test execute_with_conversion with successful function."""
        converter = ErrorConverter()
        
        def successful_func():
            return "Success"
        
        result = converter.execute_with_conversion(successful_func)
        
        assert result.is_success()
        assert result.get_value() == "Success"
    
    def test_execute_with_conversion_failure(self):
        """Test execute_with_conversion with failing function."""
        converter = ErrorConverter()
        
        def failing_func():
            raise ValueError("Test error")
        
        result = converter.execute_with_conversion(failing_func)
        
        assert result.is_failure()
        error = result.get_error()
        assert isinstance(error, ValueError)
        assert "Test error" in str(error)
    
    def test_execute_with_error_mapping_success(self):
        """Test execute_with_error_mapping with successful function."""
        converter = ErrorConverter()
        
        def successful_func():
            return "Success"
        
        def error_mapper(e):
            return RuntimeError(f"Mapped: {e}")
        
        result = converter.execute_with_error_mapping(successful_func, error_mapper)
        
        assert result.is_success()
        assert result.get_value() == "Success"
    
    def test_execute_with_error_mapping_failure(self):
        """Test execute_with_error_mapping with failing function."""
        converter = ErrorConverter()
        
        def failing_func():
            raise ValueError("Test error")
        
        def error_mapper(e):
            return RuntimeError(f"Mapped: {e}")
        
        result = converter.execute_with_error_mapping(failing_func, error_mapper)
        
        assert result.is_failure()
        error = result.get_error()
        assert isinstance(error, RuntimeError)
        assert "Mapped: Test error" in str(error)
    
    def test_execute_with_fallback_success(self):
        """Test execute_with_fallback with successful function."""
        converter = ErrorConverter()
        
        def successful_func():
            return "Success"
        
        def fallback_func(e):
            return "Fallback"
        
        result = converter.execute_with_fallback(successful_func, fallback_func)
        
        assert result.is_success()
        assert result.get_value() == "Success"
    
    def test_execute_with_fallback_failure(self):
        """Test execute_with_fallback with failing function."""
        converter = ErrorConverter()
        
        def failing_func():
            raise ValueError("Test error")
        
        def fallback_func(e):
            return f"Fallback: {e}"
        
        result = converter.execute_with_fallback(failing_func, fallback_func)
        
        assert result.is_success()
        assert result.get_value() == "Fallback: Test error"
    
    def test_execute_shell_command_with_conversion_success(self):
        """Test execute_shell_command_with_conversion with successful command."""
        converter = ErrorConverter()
        
        mock_driver = Mock()
        mock_driver.execute.return_value = {"success": True, "output": "Command output"}
        mock_logger = Mock()
        
        result = converter.execute_shell_command_with_conversion(mock_driver, "echo test", mock_logger)
        
        assert result.is_success()
        assert result.get_value() == {"success": True, "output": "Command output"}
        mock_driver.execute.assert_called_once_with("echo test", mock_logger)
    
    def test_execute_shell_command_with_conversion_failure(self):
        """Test execute_shell_command_with_conversion with failing command."""
        converter = ErrorConverter()
        
        mock_driver = Mock()
        mock_driver.execute.side_effect = RuntimeError("Command failed")
        mock_logger = Mock()
        
        result = converter.execute_shell_command_with_conversion(mock_driver, "bad command", mock_logger)
        
        assert result.is_failure()
        error = result.get_error()
        assert isinstance(error, RuntimeError)
        assert "Command failed" in str(error)
    
    def test_execute_docker_operation_with_conversion_success(self):
        """Test execute_docker_operation_with_conversion with successful operation."""
        converter = ErrorConverter()
        
        def docker_operation():
            return {"status": "success", "container_id": "12345"}
        
        mock_driver = Mock()
        mock_logger = Mock()
        
        result = converter.execute_docker_operation_with_conversion(mock_driver, docker_operation, mock_logger)
        
        assert result.is_success()
        assert result.get_value() == {"status": "success", "container_id": "12345"}
    
    def test_execute_docker_operation_with_conversion_failure(self):
        """Test execute_docker_operation_with_conversion with failing operation."""
        converter = ErrorConverter()
        
        def docker_operation():
            raise RuntimeError("Docker operation failed")
        
        mock_driver = Mock()
        mock_logger = Mock()
        
        result = converter.execute_docker_operation_with_conversion(mock_driver, docker_operation, mock_logger)
        
        assert result.is_failure()
        error = result.get_error()
        assert isinstance(error, RuntimeError)
        assert "Docker operation failed" in str(error)
    
    def test_execute_file_operation_with_conversion_success(self):
        """Test execute_file_operation_with_conversion with successful operation."""
        converter = ErrorConverter()
        
        def file_operation():
            return {"content": "File content", "size": 1024}
        
        mock_driver = Mock()
        mock_logger = Mock()
        
        result = converter.execute_file_operation_with_conversion(mock_driver, file_operation, mock_logger)
        
        assert result.is_success()
        assert result.get_value() == {"content": "File content", "size": 1024}
    
    def test_execute_file_operation_with_conversion_failure(self):
        """Test execute_file_operation_with_conversion with failing operation."""
        converter = ErrorConverter()
        
        def file_operation():
            raise IOError("File not found")
        
        mock_driver = Mock()
        mock_logger = Mock()
        
        result = converter.execute_file_operation_with_conversion(mock_driver, file_operation, mock_logger)
        
        assert result.is_failure()
        error = result.get_error()
        assert isinstance(error, IOError)
        assert "File not found" in str(error)
    
    def test_convert_mock_exception_to_result_success(self):
        """Test convert_mock_exception_to_result with successful mock."""
        converter = ErrorConverter()
        
        mock_func = Mock(return_value="Mock result")
        
        result = converter.convert_mock_exception_to_result(mock_func)
        
        assert result.is_success()
        assert result.get_value() == "Mock result"
    
    def test_convert_mock_exception_to_result_failure(self):
        """Test convert_mock_exception_to_result with failing mock."""
        converter = ErrorConverter()
        
        mock_func = Mock(side_effect=RuntimeError("Mock error"))
        
        result = converter.convert_mock_exception_to_result(mock_func)
        
        assert result.is_failure()
        error = result.get_error()
        assert isinstance(error, RuntimeError)
        assert "Mock error" in str(error)
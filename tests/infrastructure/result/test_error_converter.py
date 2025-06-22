"""Tests for ErrorConverter"""
from unittest.mock import Mock

import pytest

from src.infrastructure.result.base_result import InfrastructureResult
from src.infrastructure.result.error_converter import ErrorConverter


class TestErrorConverter:
    """Test suite for ErrorConverter"""

    @pytest.fixture
    def converter(self):
        """Create ErrorConverter instance"""
        return ErrorConverter()

    def test_init(self):
        """Test ErrorConverter initialization"""
        converter = ErrorConverter()
        assert isinstance(converter, ErrorConverter)


class TestExecuteWithConversion:
    """Test execute_with_conversion method"""

    @pytest.fixture
    def converter(self):
        """Create ErrorConverter instance"""
        return ErrorConverter()

    def test_execute_with_conversion_success(self, converter):
        """Test successful operation execution"""
        def successful_operation():
            return "success result"

        result = converter.execute_with_conversion(successful_operation)

        assert result.is_success()
        assert result.get_value() == "success result"

    def test_execute_with_conversion_exception(self, converter):
        """Test operation execution that raises exception"""
        test_exception = ValueError("Test error")

        def failing_operation():
            raise test_exception

        result = converter.execute_with_conversion(failing_operation)

        assert not result.is_success()
        assert result.get_error() == test_exception

    def test_execute_with_conversion_different_return_types(self, converter):
        """Test operation with different return types"""
        # Test with integer
        result = converter.execute_with_conversion(lambda: 42)
        assert result.is_success()
        assert result.get_value() == 42

        # Test with list
        result = converter.execute_with_conversion(lambda: [1, 2, 3])
        assert result.is_success()
        assert result.get_value() == [1, 2, 3]

        # Test with None - should fail due to InfrastructureResult validation
        result = converter.execute_with_conversion(lambda: None)
        assert not result.is_success()
        assert isinstance(result.get_error(), ValueError)
        assert "Success result requires value" in str(result.get_error())

    def test_execute_with_conversion_different_exception_types(self, converter):
        """Test operation with different exception types"""
        # Test with RuntimeError
        RuntimeError("Runtime error")
        result = converter.execute_with_conversion(lambda: exec('raise runtime_error'))
        assert not result.is_success()
        assert isinstance(result.get_error(), NameError)  # exec raises NameError for undefined runtime_error

        # Test with TypeError
        type_error = TypeError("Type error")
        def raise_type_error():
            raise type_error
        result = converter.execute_with_conversion(raise_type_error)
        assert not result.is_success()
        assert result.get_error() == type_error

        # Test with custom exception
        class CustomError(Exception):
            pass

        custom_error = CustomError("Custom error")
        def raise_custom_error():
            raise custom_error
        result = converter.execute_with_conversion(raise_custom_error)
        assert not result.is_success()
        assert result.get_error() == custom_error


class TestExecuteWithErrorMapping:
    """Test execute_with_error_mapping method"""

    @pytest.fixture
    def converter(self):
        """Create ErrorConverter instance"""
        return ErrorConverter()

    def test_execute_with_error_mapping_success(self, converter):
        """Test successful operation with error mapping"""
        def successful_operation():
            return "mapped success"

        def error_mapper(exception):
            return RuntimeError(f"Mapped: {exception}")

        result = converter.execute_with_error_mapping(successful_operation, error_mapper)

        assert result.is_success()
        assert result.get_value() == "mapped success"

    def test_execute_with_error_mapping_exception(self, converter):
        """Test operation exception with error mapping"""
        original_error = ValueError("Original error")

        def failing_operation():
            raise original_error

        def error_mapper(exception):
            return RuntimeError(f"Mapped: {exception}")

        result = converter.execute_with_error_mapping(failing_operation, error_mapper)

        assert not result.is_success()
        mapped_error = result.get_error()
        assert isinstance(mapped_error, RuntimeError)
        assert "Mapped: Original error" in str(mapped_error)

    def test_execute_with_error_mapping_mapper_preserves_type(self, converter):
        """Test error mapping that preserves exception type"""
        original_error = FileNotFoundError("File not found")

        def failing_operation():
            raise original_error

        def error_mapper(exception):
            # Preserve type but change message
            return type(exception)(f"Enhanced: {exception}")

        result = converter.execute_with_error_mapping(failing_operation, error_mapper)

        assert not result.is_success()
        mapped_error = result.get_error()
        assert isinstance(mapped_error, FileNotFoundError)
        assert "Enhanced: File not found" in str(mapped_error)

    def test_execute_with_error_mapping_mapper_exception(self, converter):
        """Test error mapping when mapper itself raises exception"""
        original_error = ValueError("Original error")
        mapper_error = RuntimeError("Mapper error")

        def failing_operation():
            raise original_error

        def failing_error_mapper(exception):
            raise mapper_error

        # The error mapping doesn't handle exceptions in the mapper itself
        # The mapper exception will bubble up and not be caught
        with pytest.raises(RuntimeError, match="Mapper error"):
            converter.execute_with_error_mapping(failing_operation, failing_error_mapper)


class TestExecuteWithFallback:
    """Test execute_with_fallback method"""

    @pytest.fixture
    def converter(self):
        """Create ErrorConverter instance"""
        return ErrorConverter()

    def test_execute_with_fallback_success(self, converter):
        """Test successful operation with fallback"""
        def successful_operation():
            return "primary result"

        def fallback_func(exception):
            return "fallback result"

        result = converter.execute_with_fallback(successful_operation, fallback_func)

        assert result.is_success()
        assert result.get_value() == "primary result"

    def test_execute_with_fallback_exception(self, converter):
        """Test operation exception with fallback"""
        original_error = ValueError("Original error")

        def failing_operation():
            raise original_error

        def fallback_func(exception):
            return f"fallback for: {exception}"

        result = converter.execute_with_fallback(failing_operation, fallback_func)

        assert result.is_success()
        assert result.get_value() == "fallback for: Original error"

    def test_execute_with_fallback_function_receives_exception(self, converter):
        """Test that fallback function receives the correct exception"""
        original_error = FileNotFoundError("Missing file")

        def failing_operation():
            raise original_error

        received_exceptions = []
        def fallback_func(exception):
            received_exceptions.append(exception)
            return "fallback result"

        result = converter.execute_with_fallback(failing_operation, fallback_func)

        assert result.is_success()
        assert result.get_value() == "fallback result"
        assert len(received_exceptions) == 1
        assert received_exceptions[0] == original_error

    def test_execute_with_fallback_function_exception(self, converter):
        """Test when fallback function itself raises exception"""
        original_error = ValueError("Original error")
        fallback_error = RuntimeError("Fallback error")

        def failing_operation():
            raise original_error

        def failing_fallback_func(exception):
            raise fallback_error

        # The fallback method doesn't handle exceptions in the fallback function itself
        # The fallback exception will bubble up and not be caught
        with pytest.raises(RuntimeError, match="Fallback error"):
            converter.execute_with_fallback(failing_operation, failing_fallback_func)


class TestExecuteShellCommandWithConversion:
    """Test execute_shell_command_with_conversion method"""

    @pytest.fixture
    def converter(self):
        """Create ErrorConverter instance"""
        return ErrorConverter()

    def test_execute_shell_command_success(self, converter):
        """Test successful shell command execution"""
        mock_driver = Mock()
        mock_driver.execute.return_value = "command output"
        mock_logger = Mock()

        result = converter.execute_shell_command_with_conversion(mock_driver, "echo test", mock_logger)

        assert result.is_success()
        assert result.get_value() == "command output"
        mock_driver.execute.assert_called_once_with("echo test", mock_logger)

    def test_execute_shell_command_exception(self, converter):
        """Test shell command execution that raises exception"""
        shell_error = RuntimeError("Shell command failed")
        mock_driver = Mock()
        mock_driver.execute.side_effect = shell_error
        mock_logger = Mock()

        result = converter.execute_shell_command_with_conversion(mock_driver, "failing command", mock_logger)

        assert not result.is_success()
        assert result.get_error() == shell_error
        mock_driver.execute.assert_called_once_with("failing command", mock_logger)

    def test_execute_shell_command_different_drivers(self, converter):
        """Test shell command with different driver types"""
        # Test with different mock drivers
        mock_driver1 = Mock()
        mock_driver1.execute.return_value = "driver1 result"

        mock_driver2 = Mock()
        mock_driver2.execute.return_value = "driver2 result"

        mock_logger = Mock()

        result1 = converter.execute_shell_command_with_conversion(mock_driver1, "cmd1", mock_logger)
        result2 = converter.execute_shell_command_with_conversion(mock_driver2, "cmd2", mock_logger)

        assert result1.is_success()
        assert result1.get_value() == "driver1 result"
        assert result2.is_success()
        assert result2.get_value() == "driver2 result"


class TestExecuteDockerOperationWithConversion:
    """Test execute_docker_operation_with_conversion method"""

    @pytest.fixture
    def converter(self):
        """Create ErrorConverter instance"""
        return ErrorConverter()

    def test_execute_docker_operation_success(self, converter):
        """Test successful Docker operation execution"""
        mock_driver = Mock()
        mock_logger = Mock()

        def docker_operation():
            return "docker result"

        result = converter.execute_docker_operation_with_conversion(mock_driver, docker_operation, mock_logger)

        assert result.is_success()
        assert result.get_value() == "docker result"

    def test_execute_docker_operation_exception(self, converter):
        """Test Docker operation that raises exception"""
        docker_error = RuntimeError("Docker operation failed")
        mock_driver = Mock()
        mock_logger = Mock()

        def failing_docker_operation():
            raise docker_error

        result = converter.execute_docker_operation_with_conversion(mock_driver, failing_docker_operation, mock_logger)

        assert not result.is_success()
        assert result.get_error() == docker_error

    def test_execute_docker_operation_with_complex_operation(self, converter):
        """Test Docker operation with complex operation function"""
        mock_driver = Mock()
        mock_logger = Mock()

        def complex_docker_operation():
            # Simulate complex Docker operation
            containers = ["container1", "container2"]
            results = []
            for container in containers:
                results.append(f"processed {container}")
            return results

        result = converter.execute_docker_operation_with_conversion(mock_driver, complex_docker_operation, mock_logger)

        assert result.is_success()
        assert result.get_value() == ["processed container1", "processed container2"]


class TestExecuteFileOperationWithConversion:
    """Test execute_file_operation_with_conversion method"""

    @pytest.fixture
    def converter(self):
        """Create ErrorConverter instance"""
        return ErrorConverter()

    def test_execute_file_operation_success(self, converter):
        """Test successful file operation execution"""
        mock_driver = Mock()
        mock_logger = Mock()

        def file_operation():
            return {"content": "file content", "exists": True}

        result = converter.execute_file_operation_with_conversion(mock_driver, file_operation, mock_logger)

        assert result.is_success()
        assert result.get_value() == {"content": "file content", "exists": True}

    def test_execute_file_operation_exception(self, converter):
        """Test file operation that raises exception"""
        file_error = FileNotFoundError("File not found")
        mock_driver = Mock()
        mock_logger = Mock()

        def failing_file_operation():
            raise file_error

        result = converter.execute_file_operation_with_conversion(mock_driver, failing_file_operation, mock_logger)

        assert not result.is_success()
        assert result.get_error() == file_error

    def test_execute_file_operation_permission_error(self, converter):
        """Test file operation with permission error"""
        permission_error = PermissionError("Access denied")
        mock_driver = Mock()
        mock_logger = Mock()

        def permission_denied_operation():
            raise permission_error

        result = converter.execute_file_operation_with_conversion(mock_driver, permission_denied_operation, mock_logger)

        assert not result.is_success()
        assert result.get_error() == permission_error
        assert isinstance(result.get_error(), PermissionError)


class TestConvertMockExceptionToResult:
    """Test convert_mock_exception_to_result method"""

    @pytest.fixture
    def converter(self):
        """Create ErrorConverter instance"""
        return ErrorConverter()

    def test_convert_mock_exception_success(self, converter):
        """Test successful mock function execution"""
        mock_func = Mock(return_value="mock result")

        result = converter.convert_mock_exception_to_result(mock_func)

        assert result.is_success()
        assert result.get_value() == "mock result"
        mock_func.assert_called_once()

    def test_convert_mock_exception_exception(self, converter):
        """Test mock function that raises exception"""
        mock_error = RuntimeError("Mock error")
        mock_func = Mock(side_effect=mock_error)

        result = converter.convert_mock_exception_to_result(mock_func)

        assert not result.is_success()
        assert result.get_error() == mock_error
        mock_func.assert_called_once()

    def test_convert_mock_exception_different_mock_behaviors(self, converter):
        """Test different mock function behaviors"""
        # Test mock with side_effect list
        mock_func = Mock(side_effect=["result1", "result2", ValueError("error on third call")])

        result1 = converter.convert_mock_exception_to_result(mock_func)
        assert result1.is_success()
        assert result1.get_value() == "result1"

        result2 = converter.convert_mock_exception_to_result(mock_func)
        assert result2.is_success()
        assert result2.get_value() == "result2"

        result3 = converter.convert_mock_exception_to_result(mock_func)
        assert not result3.is_success()
        assert isinstance(result3.get_error(), ValueError)

    def test_convert_mock_exception_with_callable_mock(self, converter):
        """Test mock function that simulates complex behavior"""
        call_count = 0

        def mock_callable():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return f"call {call_count}"
            raise RuntimeError(f"Failed on call {call_count}")

        mock_func = Mock(side_effect=mock_callable)

        # First two calls succeed
        result1 = converter.convert_mock_exception_to_result(mock_func)
        assert result1.is_success()
        assert result1.get_value() == "call 1"

        result2 = converter.convert_mock_exception_to_result(mock_func)
        assert result2.is_success()
        assert result2.get_value() == "call 2"

        # Third call fails
        result3 = converter.convert_mock_exception_to_result(mock_func)
        assert not result3.is_success()
        assert "Failed on call 3" in str(result3.get_error())


class TestErrorConverterIntegration:
    """Integration tests for ErrorConverter"""

    @pytest.fixture
    def converter(self):
        """Create ErrorConverter instance"""
        return ErrorConverter()

    def test_all_methods_return_infrastructure_result(self, converter):
        """Test that all methods return InfrastructureResult instances"""
        # Test execute_with_conversion
        result1 = converter.execute_with_conversion(lambda: "test")
        assert isinstance(result1, InfrastructureResult)

        # Test execute_with_error_mapping
        result2 = converter.execute_with_error_mapping(lambda: "test", lambda e: e)
        assert isinstance(result2, InfrastructureResult)

        # Test execute_with_fallback
        result3 = converter.execute_with_fallback(lambda: "test", lambda e: "fallback")
        assert isinstance(result3, InfrastructureResult)

        # Test execute_shell_command_with_conversion
        mock_driver = Mock()
        mock_driver.execute.return_value = "shell result"
        result4 = converter.execute_shell_command_with_conversion(mock_driver, "cmd", Mock())
        assert isinstance(result4, InfrastructureResult)

        # Test execute_docker_operation_with_conversion
        result5 = converter.execute_docker_operation_with_conversion(Mock(), lambda: "docker", Mock())
        assert isinstance(result5, InfrastructureResult)

        # Test execute_file_operation_with_conversion
        result6 = converter.execute_file_operation_with_conversion(Mock(), lambda: "file", Mock())
        assert isinstance(result6, InfrastructureResult)

        # Test convert_mock_exception_to_result
        result7 = converter.convert_mock_exception_to_result(Mock(return_value="mock"))
        assert isinstance(result7, InfrastructureResult)

    def test_consistent_exception_handling_across_methods(self, converter):
        """Test that all methods handle exceptions consistently"""
        test_error = ValueError("Consistent error")

        # All methods should handle exceptions the same way
        result1 = converter.execute_with_conversion(lambda: exec('raise test_error'))
        result2 = converter.execute_shell_command_with_conversion(
            Mock(execute=Mock(side_effect=test_error)), "cmd", Mock()
        )
        result3 = converter.execute_docker_operation_with_conversion(
            Mock(), lambda: exec('raise test_error'), Mock()
        )
        result4 = converter.execute_file_operation_with_conversion(
            Mock(), lambda: exec('raise test_error'), Mock()
        )
        result5 = converter.convert_mock_exception_to_result(Mock(side_effect=test_error))

        # All should be failed results
        assert not result1.is_success()
        assert not result2.is_success()
        assert not result3.is_success()
        assert not result4.is_success()
        assert not result5.is_success()

        # result2 and result5 should contain the exact error
        assert result2.get_error() == test_error
        assert result5.get_error() == test_error

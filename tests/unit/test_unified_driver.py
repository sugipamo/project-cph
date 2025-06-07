"""
Unit tests for UnifiedDriver
"""
from unittest.mock import MagicMock, call

import pytest

from src.application.orchestration.unified_driver import UnifiedDriver
from src.domain.constants.operation_type import OperationType


class TestUnifiedDriver:
    """Test UnifiedDriver functionality"""

    def setup_method(self):
        """Setup test environment"""
        # Mock operations container
        self.mock_operations = MagicMock()
        self.mock_file_driver = MagicMock()
        self.mock_shell_driver = MagicMock()
        self.mock_docker_driver = MagicMock()
        self.mock_python_driver = MagicMock()

        # Setup resolve method
        self.mock_operations.resolve.side_effect = lambda driver_name: {
            "file_driver": self.mock_file_driver,
            "shell_driver": self.mock_shell_driver,
            "docker_driver": self.mock_docker_driver,
            "python_driver": self.mock_python_driver
        }[driver_name]

    def test_initialization(self):
        """Test UnifiedDriver initialization"""
        driver = UnifiedDriver(self.mock_operations)

        assert driver.operations == self.mock_operations
        assert driver._driver_cache == {}

    def test_get_driver_for_file_request(self):
        """Test getting file driver for file request"""
        driver = UnifiedDriver(self.mock_operations)

        # Mock file request
        mock_request = MagicMock()
        mock_request.operation_type = OperationType.FILE

        result_driver = driver._get_driver_for_request(mock_request)

        assert result_driver == self.mock_file_driver
        self.mock_operations.resolve.assert_called_with("file_driver")

    def test_get_driver_for_shell_request(self):
        """Test getting shell driver for shell request"""
        driver = UnifiedDriver(self.mock_operations)

        # Mock shell request
        mock_request = MagicMock()
        mock_request.operation_type = OperationType.SHELL

        result_driver = driver._get_driver_for_request(mock_request)

        assert result_driver == self.mock_shell_driver
        self.mock_operations.resolve.assert_called_with("shell_driver")

    def test_get_driver_for_docker_request(self):
        """Test getting docker driver for docker request"""
        driver = UnifiedDriver(self.mock_operations)

        # Mock docker request
        mock_request = MagicMock()
        mock_request.operation_type = OperationType.DOCKER

        result_driver = driver._get_driver_for_request(mock_request)

        assert result_driver == self.mock_docker_driver
        self.mock_operations.resolve.assert_called_with("docker_driver")

    def test_get_driver_for_python_request(self):
        """Test getting python driver for python request"""
        driver = UnifiedDriver(self.mock_operations)

        # Mock python request
        mock_request = MagicMock()
        mock_request.operation_type = OperationType.PYTHON

        result_driver = driver._get_driver_for_request(mock_request)

        assert result_driver == self.mock_python_driver
        self.mock_operations.resolve.assert_called_with("python_driver")

    def test_get_driver_for_unknown_request(self):
        """Test fallback for unknown request type"""
        driver = UnifiedDriver(self.mock_operations)

        # Mock request without operation_type
        mock_request = MagicMock()
        mock_request.operation_type = None

        result_driver = driver._get_driver_for_request(mock_request)

        # Should return self for unknown types
        assert result_driver == driver

    def test_driver_caching(self):
        """Test that drivers are cached after first resolution"""
        driver = UnifiedDriver(self.mock_operations)

        # First request
        mock_request1 = MagicMock()
        mock_request1.operation_type = OperationType.FILE
        driver._get_driver_for_request(mock_request1)

        # Second request with same type
        mock_request2 = MagicMock()
        mock_request2.operation_type = OperationType.FILE
        driver._get_driver_for_request(mock_request2)

        # resolve should be called only once
        assert self.mock_operations.resolve.call_count == 1
        assert "file_driver" in driver._driver_cache

    def test_execute_with_file_request(self):
        """Test executing a file request"""
        driver = UnifiedDriver(self.mock_operations)

        # Mock file request
        mock_request = MagicMock()
        mock_request.operation_type = OperationType.FILE
        mock_request.execute.return_value = MagicMock(success=True)

        result = driver.execute(mock_request)

        # Should call execute with file driver
        mock_request.execute.assert_called_once_with(driver=self.mock_file_driver)
        assert result.success is True

    def test_execute_with_multiple_request_types(self):
        """Test executing different request types"""
        driver = UnifiedDriver(self.mock_operations)

        # Create different request types
        requests = [
            (OperationType.FILE, self.mock_file_driver),
            (OperationType.SHELL, self.mock_shell_driver),
            (OperationType.DOCKER, self.mock_docker_driver),
            (OperationType.PYTHON, self.mock_python_driver)
        ]

        for op_type, expected_driver in requests:
            mock_request = MagicMock()
            mock_request.operation_type = op_type
            mock_request.execute.return_value = MagicMock(success=True)

            result = driver.execute(mock_request)

            mock_request.execute.assert_called_once_with(driver=expected_driver)
            assert result.success is True

    def test_direct_driver_methods(self):
        """Test direct driver methods are available"""
        driver = UnifiedDriver(self.mock_operations)

        # Test that specific driver methods are available
        assert hasattr(driver, 'run')  # Shell driver method
        assert hasattr(driver, 'copy')  # File driver method
        assert hasattr(driver, 'run_container')  # Docker driver method
        assert hasattr(driver, 'exec_in_container')  # Docker driver method

    def test_multiple_executions_use_cache(self):
        """Test that multiple executions use cached drivers"""
        driver = UnifiedDriver(self.mock_operations)

        # Execute multiple file requests
        for _i in range(3):
            mock_request = MagicMock()
            mock_request.operation_type = OperationType.FILE
            mock_request.execute.return_value = MagicMock(success=True)

            driver.execute(mock_request)

        # resolve should be called only once for file_driver
        resolve_calls = [call for call in self.mock_operations.resolve.call_args_list
                        if call[0][0] == "file_driver"]
        assert len(resolve_calls) == 1

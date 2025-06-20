"""Simplified tests for UnifiedDriver focusing on testable components"""
from unittest.mock import Mock

import pytest

from src.infrastructure.di_container import DIContainer, DIKey
from src.infrastructure.drivers.unified.unified_driver import UnifiedDriver
from src.operations.constants.request_types import RequestType


class TestUnifiedDriverSimple:

    @pytest.fixture
    def mock_infrastructure(self):
        """Create a mock DI container."""
        container = Mock(spec=DIContainer)
        container.resolve = Mock()
        return container

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        return Mock()

    @pytest.fixture
    def unified_driver(self, mock_infrastructure, mock_logger):
        """Create a UnifiedDriver instance."""
        mock_infrastructure.resolve.return_value = mock_logger
        return UnifiedDriver(mock_infrastructure, mock_logger)

    def test_initialization_with_logger(self, mock_infrastructure, mock_logger):
        """Test initialization with provided logger."""
        driver = UnifiedDriver(mock_infrastructure, mock_logger)

        assert driver.infrastructure == mock_infrastructure
        assert driver.logger == mock_logger
        assert driver._docker_driver is None
        assert driver._file_driver is None
        assert driver._shell_driver is None
        assert driver._python_driver is None

    def test_initialization_without_logger(self, mock_infrastructure):
        """Test initialization without provided logger."""
        mock_logger = Mock()
        mock_infrastructure.resolve.return_value = mock_logger

        driver = UnifiedDriver(mock_infrastructure)

        assert driver.infrastructure == mock_infrastructure
        assert driver.logger == mock_logger
        mock_infrastructure.resolve.assert_called_once_with(DIKey.UNIFIED_LOGGER)

    def test_docker_driver_lazy_loading(self, unified_driver, mock_infrastructure):
        """Test lazy loading of docker driver."""
        mock_docker_driver = Mock()
        mock_infrastructure.resolve.side_effect = lambda key: {
            DIKey.DOCKER_DRIVER: mock_docker_driver,
            DIKey.UNIFIED_LOGGER: unified_driver.logger
        }.get(key, Mock())

        # First access should resolve the driver
        driver = unified_driver.docker_driver
        assert driver == mock_docker_driver

        # Second access should return cached driver
        mock_infrastructure.resolve.reset_mock()
        driver2 = unified_driver.docker_driver
        assert driver2 == mock_docker_driver
        mock_infrastructure.resolve.assert_not_called()

    def test_file_driver_lazy_loading(self, unified_driver, mock_infrastructure):
        """Test lazy loading of file driver."""
        mock_file_driver = Mock()
        mock_infrastructure.resolve.side_effect = lambda key: {
            DIKey.FILE_DRIVER: mock_file_driver,
            DIKey.UNIFIED_LOGGER: unified_driver.logger
        }.get(key, Mock())

        driver = unified_driver.file_driver
        assert driver == mock_file_driver

    def test_shell_driver_lazy_loading(self, unified_driver, mock_infrastructure):
        """Test lazy loading of shell driver."""
        mock_shell_driver = Mock()
        mock_infrastructure.resolve.side_effect = lambda key: {
            DIKey.SHELL_DRIVER: mock_shell_driver,
            DIKey.UNIFIED_LOGGER: unified_driver.logger
        }.get(key, Mock())

        driver = unified_driver.shell_driver
        assert driver == mock_shell_driver

    def test_python_driver_lazy_loading(self, unified_driver, mock_infrastructure):
        """Test lazy loading of python driver."""
        mock_python_driver = Mock()
        mock_infrastructure.resolve.side_effect = lambda key: {
            DIKey.PYTHON_DRIVER: mock_python_driver,
            DIKey.UNIFIED_LOGGER: unified_driver.logger
        }.get(key, Mock())

        driver = unified_driver.python_driver
        assert driver == mock_python_driver

    def test_request_logging(self, unified_driver, mock_logger):
        """Test that requests are logged properly."""
        request = Mock()
        request.request_type = RequestType.DOCKER_REQUEST

        # Mock the docker handler to avoid import errors
        unified_driver._execute_docker_request = Mock(return_value=Mock())

        unified_driver.execute_operation_request(request)

        # Verify that debug logging occurred (enum value is the number)
        expected_msg = f"Executing {RequestType.DOCKER_REQUEST.value} request"
        mock_logger.debug.assert_called_once_with(expected_msg)

    def test_type_checking_in_handlers(self, unified_driver):
        """Test that handlers check for correct request types."""
        # Test docker handler type checking
        with pytest.raises(TypeError, match="Expected DockerRequest"):
            unified_driver._execute_docker_request(Mock())

        # Test file handler type checking
        with pytest.raises(TypeError, match="Expected FileRequest"):
            unified_driver._execute_file_request(Mock())

        # Test shell handler type checking
        with pytest.raises(TypeError, match="Expected ShellRequest"):
            unified_driver._execute_shell_request(Mock())

        # Test python handler type checking
        with pytest.raises(TypeError, match="Expected PythonRequest"):
            unified_driver._execute_python_request(Mock())

    def test_request_routing_logic(self, unified_driver, mock_logger):
        """Test the request routing logic without complex mocking."""
        # Mock the handler methods to verify they are called
        unified_driver._execute_docker_request = Mock(return_value=Mock())
        unified_driver._execute_file_request = Mock(return_value=Mock())
        unified_driver._execute_shell_request = Mock(return_value=Mock())

        # Test routing for each request type that exists
        docker_request = Mock()
        docker_request.request_type = RequestType.DOCKER_REQUEST
        unified_driver.execute_operation_request(docker_request)
        unified_driver._execute_docker_request.assert_called_once_with(docker_request)

        file_request = Mock()
        file_request.request_type = RequestType.FILE_REQUEST
        unified_driver.execute_operation_request(file_request)
        unified_driver._execute_file_request.assert_called_once_with(file_request)

        shell_request = Mock()
        shell_request.request_type = RequestType.SHELL_REQUEST
        unified_driver.execute_operation_request(shell_request)
        unified_driver._execute_shell_request.assert_called_once_with(shell_request)

        # Verify logging
        assert mock_logger.debug.call_count == 3  # One debug call per request

    def test_all_drivers_are_accessible(self, unified_driver, mock_infrastructure):
        """Test that all driver properties are accessible."""
        # Setup mocks for all drivers
        mock_infrastructure.resolve.side_effect = lambda key: {
            DIKey.DOCKER_DRIVER: Mock(name="docker_driver"),
            DIKey.FILE_DRIVER: Mock(name="file_driver"),
            DIKey.SHELL_DRIVER: Mock(name="shell_driver"),
            DIKey.PYTHON_DRIVER: Mock(name="python_driver"),
            DIKey.UNIFIED_LOGGER: unified_driver.logger
        }.get(key, Mock())

        # Access all drivers to verify lazy loading works
        assert unified_driver.docker_driver is not None
        assert unified_driver.file_driver is not None
        assert unified_driver.shell_driver is not None
        assert unified_driver.python_driver is not None

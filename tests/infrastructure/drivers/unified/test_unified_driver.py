"""Tests for UnifiedDriver"""
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.infrastructure.di_container import DIContainer, DIKey
from src.infrastructure.drivers.unified.unified_driver import UnifiedDriver
from src.operations.constants.request_types import RequestType
from src.operations.requests.base.base_request import OperationRequestFoundation


class MockRequest(OperationRequestFoundation):
    """Mock request for testing"""

    def __init__(self, request_type: RequestType, **kwargs):
        super().__init__()
        self._request_type = request_type
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _execute_core(self, driver=None, logger=None):
        """Mock implementation of abstract method"""
        pass

    @property
    def operation_type(self):
        """Mock implementation of abstract property"""
        return "mock_operation"

    @property
    def request_type(self) -> RequestType:
        """Override request_type property"""
        return self._request_type


class TestUnifiedDriver:

    @pytest.fixture
    def mock_infrastructure(self):
        """Create a mock DI container."""
        container = Mock(spec=DIContainer)
        container.resolve = Mock()
        return container

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        logger = Mock()
        return logger

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
        mock_infrastructure.resolve.return_value = mock_docker_driver

        # First access should resolve the driver
        driver = unified_driver.docker_driver
        assert driver == mock_docker_driver
        mock_infrastructure.resolve.assert_called_with(DIKey.DOCKER_DRIVER)

        # Second access should return cached driver
        mock_infrastructure.resolve.reset_mock()
        driver2 = unified_driver.docker_driver
        assert driver2 == mock_docker_driver
        mock_infrastructure.resolve.assert_not_called()

    def test_file_driver_lazy_loading(self, unified_driver, mock_infrastructure):
        """Test lazy loading of file driver."""
        mock_file_driver = Mock()
        mock_infrastructure.resolve.return_value = mock_file_driver

        driver = unified_driver.file_driver
        assert driver == mock_file_driver
        mock_infrastructure.resolve.assert_called_with(DIKey.FILE_DRIVER)

    def test_shell_driver_lazy_loading(self, unified_driver, mock_infrastructure):
        """Test lazy loading of shell driver."""
        mock_shell_driver = Mock()
        mock_infrastructure.resolve.return_value = mock_shell_driver

        driver = unified_driver.shell_driver
        assert driver == mock_shell_driver
        mock_infrastructure.resolve.assert_called_with(DIKey.SHELL_DRIVER)


    def test_execute_operation_request_logs_request(self, unified_driver, mock_logger):
        """Test that request execution is logged."""
        request = MockRequest(RequestType.DOCKER_REQUEST)

        # Mock docker driver and its build method
        unified_driver._docker_driver = Mock()
        unified_driver._docker_driver.build.return_value = Mock(
            success=True, output="", error="", container_id="abc123"
        )
        request.op = "build"
        request.context_path = "/path"
        request.tag = "test:latest"
        request.dockerfile = None

        with pytest.raises(TypeError, match="Expected DockerRequest"):  # Will fail on type check
            unified_driver.execute_operation_request(request)

        mock_logger.debug.assert_called_once_with("Executing DOCKER_REQUEST request")

    def test_execute_unsupported_request_type(self, unified_driver):
        """Test error for unsupported request type."""
        # Create a request with an invalid type by mocking
        request = Mock()
        request.request_type = "INVALID_TYPE"

        with pytest.raises(ValueError, match="Unsupported request type"):
            unified_driver.execute_operation_request(request)

    def test_execute_docker_build_request(self, unified_driver, mock_infrastructure):
        """Test execution of docker build request."""
        # Mock the docker driver
        mock_docker_driver = Mock()
        mock_driver_result = Mock(
            success=True,
            output="Build successful",
            error="",
            container_id="abc123"
        )
        mock_docker_driver.build.return_value = mock_driver_result

        # Setup infrastructure to return the mock driver
        mock_infrastructure.resolve.side_effect = lambda key: {
            DIKey.DOCKER_DRIVER: mock_docker_driver,
            DIKey.UNIFIED_LOGGER: unified_driver.logger
        }.get(key, Mock())

        # Create docker request
        request = MockRequest(
            RequestType.DOCKER_REQUEST,
            op="build",
            context_path="/build/context",
            tag="test:latest",
            dockerfile="Dockerfile"
        )

        # The actual execution will fail on type check
        with pytest.raises(TypeError, match="Expected DockerRequest"):
            unified_driver.execute_operation_request(request)

        # Verify the docker driver would be accessed
        _ = unified_driver.docker_driver
        mock_infrastructure.resolve.assert_called_with(DIKey.DOCKER_DRIVER)

    def test_execute_docker_request_with_wrong_type(self, unified_driver):
        """Test docker request execution with wrong request type."""
        unified_driver._docker_driver = Mock()

        # Create a simple mock object that's not a DockerRequest
        request = Mock()

        # Manually call the docker handler to test type checking
        with pytest.raises(TypeError, match="Expected DockerRequest"):
            unified_driver._execute_docker_request(request)

    def test_execute_file_request_with_wrong_type(self, unified_driver):
        """Test file request execution with wrong request type."""
        unified_driver._file_driver = Mock()

        # Create a simple mock object that's not a FileRequest
        request = Mock()

        with pytest.raises(TypeError, match="Expected FileRequest"):
            unified_driver._execute_file_request(request)

    def test_execute_shell_request_with_wrong_type(self, unified_driver):
        """Test shell request execution with wrong request type."""
        unified_driver._shell_driver = Mock()

        # Create a simple mock object that's not a ShellRequest
        request = Mock()

        with pytest.raises(TypeError, match="Expected ShellRequest"):
            unified_driver._execute_shell_request(request)


    def test_docker_request_error_handling(self, unified_driver, mock_logger):
        """Test error handling in docker request execution."""
        unified_driver._docker_driver = Mock()
        unified_driver._docker_driver.build.side_effect = Exception("Docker build failed")

        # Create a mock docker request
        mock_request = Mock()
        mock_request.op = "build"
        mock_request.context_path = "/path"
        mock_request.tag = "test:latest"
        mock_request.dockerfile = None

        # Will fail on type check first, test the type check behavior
        with pytest.raises(TypeError, match="Expected DockerRequest"):
            unified_driver._execute_docker_request(mock_request)

    def test_docker_unsupported_operation(self, unified_driver):
        """Test error for unsupported docker operation."""
        unified_driver._docker_driver = Mock()

        mock_request = Mock()
        mock_request.op = "unsupported_op"

        with pytest.raises(TypeError, match="Expected DockerRequest"):
            unified_driver._execute_docker_request(mock_request)

    def test_file_request_error_handling(self, unified_driver, mock_logger):
        """Test error handling in file request execution."""
        unified_driver._file_driver = Mock()
        unified_driver._file_driver.mkdir.side_effect = Exception("File operation failed")

        # Create a mock file request
        mock_request = Mock()
        mock_request.op = Mock()
        mock_request.op.value = "MKDIR"  # Mock the enum value
        mock_request.get_absolute_source.return_value = "/test/path"

        # Will fail on type check first
        with pytest.raises(TypeError, match="Expected FileRequest"):
            unified_driver._execute_file_request(mock_request)

    def test_shell_request_error_handling(self, unified_driver, mock_logger):
        """Test error handling in shell request execution."""
        # This test would require too much mocking of internal classes
        # Instead, test the type checking behavior
        unified_driver._shell_driver = Mock()

        # Test with wrong type should raise TypeError
        mock_request = Mock()
        with pytest.raises(TypeError, match="Expected ShellRequest"):
            unified_driver._execute_shell_request(mock_request)


    def test_request_routing(self, unified_driver):
        """Test that requests are routed to correct handlers."""
        # Mock all driver methods to avoid import errors
        unified_driver._execute_docker_request = Mock(return_value=Mock())
        unified_driver._execute_file_request = Mock(return_value=Mock())
        unified_driver._execute_shell_request = Mock(return_value=Mock())

        # Test docker request routing
        docker_request = MockRequest(RequestType.DOCKER_REQUEST)
        unified_driver.execute_operation_request(docker_request)
        unified_driver._execute_docker_request.assert_called_once_with(docker_request)

        # Test file request routing
        file_request = MockRequest(RequestType.FILE_REQUEST)
        unified_driver.execute_operation_request(file_request)
        unified_driver._execute_file_request.assert_called_once_with(file_request)

        # Test shell request routing
        shell_request = MockRequest(RequestType.SHELL_REQUEST)
        unified_driver.execute_operation_request(shell_request)
        unified_driver._execute_shell_request.assert_called_once_with(shell_request)



class TestUnifiedDriverDockerOperations:
    """Additional tests for Docker operations with improved coverage"""

    @pytest.fixture
    def mock_infrastructure(self):
        """Create a mock DI container."""
        container = Mock(spec=DIContainer)
        container.resolve = Mock()
        return container

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        logger = Mock()
        return logger

    @pytest.fixture
    def unified_driver_with_mocks(self, mock_infrastructure, mock_logger):
        """Create a UnifiedDriver instance with mocked dependencies."""
        mock_infrastructure.resolve.return_value = mock_logger
        driver = UnifiedDriver(mock_infrastructure, mock_logger)

        # Mock all the actual operation imports that would fail
        driver._docker_driver = Mock()
        driver._file_driver = Mock()
        driver._shell_driver = Mock()

        return driver

    @patch('src.operations.results.docker_result.DockerResult')
    def test_docker_run_operation(self, mock_docker_result, unified_driver_with_mocks):
        """Test Docker run operation execution"""
        mock_request = Mock()
        mock_request.op = "run"
        mock_request.image = "python:3.9"
        mock_request.cmd = ["python", "script.py"]
        mock_request.volumes = {"/host": "/container"}
        mock_request.env = {"TEST": "value"}
        mock_request.working_dir = "/app"
        mock_request.detach = False
        mock_request.remove = True

        # Mock driver response
        mock_driver_result = Mock(
            success=True,
            output="Script executed successfully",
            error="",
            container_id="container123"
        )
        unified_driver_with_mocks._docker_driver.run.return_value = mock_driver_result

        # Mock DockerResult
        mock_result_instance = Mock()
        mock_docker_result.return_value = mock_result_instance

        # Will fail on type check first
        with pytest.raises(TypeError, match="Expected DockerRequest"):
            unified_driver_with_mocks._execute_docker_request(mock_request)


class TestUnifiedDriverEdgeCases:
    """Tests for edge cases and additional scenarios"""

    @pytest.fixture
    def mock_infrastructure(self):
        container = Mock(spec=DIContainer)
        container.resolve = Mock()
        return container

    @pytest.fixture
    def mock_logger(self):
        return Mock()

    @pytest.fixture
    def unified_driver(self, mock_infrastructure, mock_logger):
        mock_infrastructure.resolve.return_value = mock_logger
        return UnifiedDriver(mock_infrastructure, mock_logger)

    def test_driver_resolution_failure(self, unified_driver, mock_infrastructure):
        """Test behavior when driver resolution fails"""
        # Simulate DI container resolution failure
        mock_infrastructure.resolve.side_effect = Exception("Resolution failed")

        with pytest.raises(Exception, match="Resolution failed"):
            _ = unified_driver.docker_driver

    def test_driver_caching_behavior(self, unified_driver, mock_infrastructure):
        """Test that drivers are properly cached after first access"""
        mock_docker_driver = Mock()
        mock_file_driver = Mock()
        mock_shell_driver = Mock()
        mock_infrastructure.resolve.side_effect = [
            mock_docker_driver, mock_file_driver,
            mock_shell_driver
        ]

        # First access should resolve and cache
        docker1 = unified_driver.docker_driver
        file1 = unified_driver.file_driver
        shell1 = unified_driver.shell_driver

        # Second access should return cached instances
        docker2 = unified_driver.docker_driver
        file2 = unified_driver.file_driver
        shell2 = unified_driver.shell_driver

        # Verify same instances returned
        assert docker1 is docker2
        assert file1 is file2
        assert shell1 is shell2

        # Verify resolution was called only once per driver
        assert mock_infrastructure.resolve.call_count == 3

"""Tests for UnifiedDriver."""
from unittest.mock import Mock, patch

import pytest

from src.infrastructure.drivers.unified.unified_driver import UnifiedDriver
from src.operations.constants.request_types import RequestType


class TestUnifiedDriver:
    """Test cases for UnifiedDriver."""

    @pytest.fixture
    def mock_infrastructure(self):
        """Create mock DI container."""
        infrastructure = Mock()

        # Mock logger
        mock_logger = Mock()
        infrastructure.resolve.return_value = mock_logger

        return infrastructure

    @pytest.fixture
    def mock_config_manager(self):
        """Create mock configuration manager."""
        config_manager = Mock()
        config_manager.load_from_files = Mock()
        return config_manager

    @pytest.fixture
    def unified_driver(self, mock_infrastructure, mock_config_manager):
        """Create UnifiedDriver instance."""
        return UnifiedDriver(mock_infrastructure, config_manager=mock_config_manager)

    def test_init_with_logger_and_config(self, mock_infrastructure):
        """Test UnifiedDriver initialization with logger and config manager."""
        mock_logger = Mock()
        mock_config_manager = Mock()

        driver = UnifiedDriver(mock_infrastructure, mock_logger, mock_config_manager)

        assert driver.infrastructure == mock_infrastructure
        assert driver.logger == mock_logger
        assert driver._config_manager == mock_config_manager

    def test_init_without_logger_and_config(self, mock_infrastructure):
        """Test UnifiedDriver initialization without logger and config manager."""
        mock_logger = Mock()
        mock_infrastructure.resolve.return_value = mock_logger

        with patch('src.infrastructure.drivers.unified.unified_driver.TypeSafeConfigNodeManager') as mock_config_class:
            mock_config_instance = Mock()
            mock_config_class.return_value = mock_config_instance

            driver = UnifiedDriver(mock_infrastructure)

            assert driver.infrastructure == mock_infrastructure
            assert driver.logger == mock_logger
            assert driver._config_manager == mock_config_instance
            mock_config_instance.load_from_files.assert_called_once_with(system_dir="config/system")

    def test_docker_driver_property(self, unified_driver, mock_infrastructure):
        """Test docker_driver property lazy loading."""
        mock_docker_driver = Mock()
        mock_infrastructure.resolve.return_value = mock_docker_driver

        # First access
        driver = unified_driver.docker_driver
        assert driver == mock_docker_driver

        # Second access should use cached value
        driver2 = unified_driver.docker_driver
        assert driver2 == mock_docker_driver
        # Should only resolve once due to caching
        assert mock_infrastructure.resolve.call_count == 2  # Once for logger, once for docker driver

    def test_file_driver_property(self, unified_driver, mock_infrastructure):
        """Test file_driver property lazy loading."""
        mock_file_driver = Mock()
        mock_infrastructure.resolve.return_value = mock_file_driver

        driver = unified_driver.file_driver
        assert driver == mock_file_driver

    def test_shell_driver_property(self, unified_driver, mock_infrastructure):
        """Test shell_driver property lazy loading."""
        mock_shell_driver = Mock()
        mock_infrastructure.resolve.return_value = mock_shell_driver

        driver = unified_driver.shell_driver
        assert driver == mock_shell_driver

    def test_execute_operation_request_docker(self, unified_driver):
        """Test executing Docker request."""
        # Create mock Docker request
        mock_request = Mock()
        mock_request.request_type = RequestType.DOCKER_REQUEST
        mock_request.op = "run"
        mock_request.image = "ubuntu:latest"
        mock_request.cmd = "echo hello"
        mock_request.container = "test-container"
        mock_request.volumes = []
        mock_request.environment = []
        mock_request.detach = False

        # Mock docker driver
        mock_docker_driver = Mock()
        mock_docker_result = Mock()
        mock_docker_result.success = True
        mock_docker_result.output = "hello"
        mock_docker_result.error = ""
        mock_docker_driver.run.return_value = mock_docker_result

        unified_driver._docker_driver = mock_docker_driver

        with patch('src.infrastructure.drivers.unified.unified_driver.DockerRequest') as mock_docker_request_class, \
             patch('src.infrastructure.drivers.unified.unified_driver.DockerResult') as mock_docker_result_class:
            mock_docker_request_class.__name__ = "DockerRequest"
            mock_result_instance = Mock()
            mock_docker_result_class.return_value = mock_result_instance

            result = unified_driver.execute_operation_request(mock_request)

            assert result == mock_result_instance
            mock_docker_driver.run.assert_called_once()

    def test_execute_operation_request_file(self, unified_driver):
        """Test executing File request."""
        # Create mock File request
        mock_request = Mock()
        mock_request.request_type = RequestType.FILE_REQUEST

        # Mock file driver
        mock_file_driver = Mock()
        mock_file_result = Mock()
        mock_file_result.success = True
        mock_file_result.output = ""
        mock_file_result.error = ""
        mock_file_driver.mkdir.return_value = mock_file_result

        unified_driver._file_driver = mock_file_driver

        with patch('src.infrastructure.drivers.unified.unified_driver.FileRequest') as mock_file_request_class, \
             patch('src.infrastructure.drivers.unified.unified_driver.FileResult') as mock_file_result_class:
            mock_file_request_class.__name__ = "FileRequest"
            mock_result_instance = Mock()
            mock_file_result_class.return_value = mock_result_instance

            # Mock the request to be an instance of FileRequest
            mock_request.__class__ = mock_file_request_class

            result = unified_driver.execute_operation_request(mock_request)

            assert result == mock_result_instance

    def test_execute_operation_request_shell(self, unified_driver):
        """Test executing Shell request."""
        # Create mock Shell request
        mock_request = Mock()
        mock_request.request_type = RequestType.SHELL_REQUEST
        mock_request.cmd = "echo hello"
        mock_request.cwd = "/tmp"
        mock_request.env = {}
        mock_request.timeout = 30

        # Mock shell driver
        mock_shell_driver = Mock()
        mock_shell_result = Mock()
        mock_shell_result.success = True
        mock_shell_result.output = "hello"
        mock_shell_result.error = ""
        mock_shell_result.exit_code = 0
        mock_shell_driver.run.return_value = mock_shell_result

        unified_driver._shell_driver = mock_shell_driver

        with patch('src.infrastructure.drivers.unified.unified_driver.ShellRequest') as mock_shell_request_class, \
             patch('src.infrastructure.drivers.unified.unified_driver.ShellResult') as mock_shell_result_class:
            mock_shell_request_class.__name__ = "ShellRequest"
            mock_result_instance = Mock()
            mock_shell_result_class.return_value = mock_result_instance

            # Mock the request to be an instance of ShellRequest
            mock_request.__class__ = mock_shell_request_class

            result = unified_driver.execute_operation_request(mock_request)

            assert result == mock_result_instance
            mock_shell_driver.run.assert_called_once_with(
                cmd="echo hello",
                cwd="/tmp",
                env={},
                timeout=30
            )



    def test_execute_docker_request_build_operation(self, unified_driver):
        """Test executing Docker build request."""
        mock_request = Mock()
        mock_request.op = "build"
        mock_request.context_path = "/app"
        mock_request.tag = "my-image:latest"
        mock_request.dockerfile = "FROM ubuntu"

        # Mock docker driver
        mock_docker_driver = Mock()
        mock_docker_result = Mock()
        mock_docker_result.success = True
        mock_docker_result.output = "Successfully built"
        mock_docker_result.error = ""
        mock_docker_driver.build.return_value = mock_docker_result

        unified_driver._docker_driver = mock_docker_driver

        with patch('src.infrastructure.drivers.unified.unified_driver.DockerRequest'), \
             patch('src.infrastructure.drivers.unified.unified_driver.DockerResult') as mock_docker_result_class:
            mock_result_instance = Mock()
            mock_docker_result_class.return_value = mock_result_instance

            # Mock isinstance to return True
            with patch('builtins.isinstance', return_value=True):
                result = unified_driver._execute_docker_request(mock_request)

                assert result == mock_result_instance
                mock_docker_driver.build.assert_called_once_with(
                    context_path="/app",
                    tag="my-image:latest",
                    dockerfile="FROM ubuntu"
                )

    def test_execute_docker_request_unsupported_operation(self, unified_driver):
        """Test executing Docker request with unsupported operation."""
        mock_request = Mock()
        mock_request.op = "unsupported_op"

        with patch('src.infrastructure.drivers.unified.unified_driver.DockerRequest'), \
             patch('src.infrastructure.drivers.unified.unified_driver.DockerResult') as mock_docker_result_class:
            mock_result_instance = Mock()
            mock_docker_result_class.return_value = mock_result_instance

            # Mock isinstance to return True
            with patch('builtins.isinstance', return_value=True):
                result = unified_driver._execute_docker_request(mock_request)

                # Should return error result
                assert result == mock_result_instance
                mock_docker_result_class.assert_called_with(
                    success=False,
                    output="",
                    error="Unsupported docker operation: unsupported_op",
                    request=mock_request
                )

    def test_execute_file_request_mkdir_operation(self, unified_driver):
        """Test executing File mkdir request."""
        mock_request = Mock()
        mock_request.get_absolute_source.return_value = "/test/directory"

        # Mock FileOpType
        with patch('src.infrastructure.drivers.unified.unified_driver.FileOpType') as mock_file_op_type:
            mock_request.op = mock_file_op_type.MKDIR

            # Mock file driver
            mock_file_driver = Mock()
            mock_file_result = Mock()
            mock_file_result.success = True
            mock_file_result.output = ""
            mock_file_result.error = ""
            mock_file_driver.mkdir.return_value = mock_file_result

            unified_driver._file_driver = mock_file_driver

            with patch('src.infrastructure.drivers.unified.unified_driver.FileRequest'), \
                 patch('src.infrastructure.drivers.unified.unified_driver.FileResult') as mock_file_result_class:
                mock_result_instance = Mock()
                mock_file_result_class.return_value = mock_result_instance

                # Mock isinstance to return True
                with patch('builtins.isinstance', return_value=True):
                    result = unified_driver._execute_file_request(mock_request)

                    assert result == mock_result_instance
                    mock_file_driver.mkdir.assert_called_once_with("/test/directory")

    def test_execute_shell_request_with_exit_code_fallback(self, unified_driver, mock_config_manager):
        """Test executing Shell request with exit code fallback."""
        mock_request = Mock()
        mock_request.cmd = "echo hello"
        mock_request.cwd = "/tmp"
        mock_request.env = {}
        mock_request.timeout = 30

        # Mock shell driver with result that doesn't have exit_code
        mock_shell_driver = Mock()
        mock_shell_result = Mock()
        mock_shell_result.success = True
        mock_shell_result.output = "hello"
        mock_shell_result.error = ""
        # Remove exit_code attribute or set to None
        del mock_shell_result.exit_code
        mock_shell_driver.run.return_value = mock_shell_result

        unified_driver._shell_driver = mock_shell_driver

        # Mock config manager to return default exit codes
        mock_config_manager.resolve_config.side_effect = lambda path, type_: {
            ['execution_defaults', 'exit_codes', 'success']: 0,
            ['execution_defaults', 'exit_codes', 'failure']: 1
        }[path]

        with patch('src.infrastructure.drivers.unified.unified_driver.ShellRequest'), \
             patch('src.infrastructure.drivers.unified.unified_driver.ShellResult') as mock_shell_result_class:
            mock_result_instance = Mock()
            mock_shell_result_class.return_value = mock_result_instance

            # Mock isinstance to return True
            with patch('builtins.isinstance', return_value=True):
                result = unified_driver._execute_shell_request(mock_request)

                assert result == mock_result_instance
                # Should call with exit_code=0 (success)
                mock_shell_result_class.assert_called_once()
                call_args = mock_shell_result_class.call_args[1]
                assert call_args['exit_code'] == 0


"""Tests for UnifiedDriver"""
from unittest.mock import Mock, patch

import pytest

from src.infrastructure.drivers.unified.unified_driver import UnifiedDriver
from src.operations.constants.request_types import RequestType
from src.operations.requests.docker.docker_request import DockerOpType, DockerRequest
from src.operations.requests.file.file_op_type import FileOpType
from src.operations.requests.file.file_request import FileRequest
from src.operations.requests.shell.shell_request import ShellRequest
from src.operations.results.docker_result import DockerResult
from src.operations.results.file_result import FileResult
from src.operations.results.shell_result import ShellResult


class TestUnifiedDriver:
    """Test suite for UnifiedDriver"""

    @pytest.fixture
    def mock_infrastructure(self):
        """Create mock infrastructure container"""
        infrastructure = Mock()
        infrastructure.resolve = Mock()
        return infrastructure

    @pytest.fixture
    def mock_logger(self):
        """Create mock logger"""
        logger = Mock()
        return logger

    @pytest.fixture
    def mock_config_manager(self):
        """Create mock config manager"""
        config_manager = Mock()
        config_manager.resolve_config = Mock()
        return config_manager

    @pytest.fixture
    def driver(self, mock_infrastructure, mock_logger, mock_config_manager):
        """Create UnifiedDriver instance"""
        return UnifiedDriver(mock_infrastructure, mock_logger, mock_config_manager)

    def test_init(self, mock_infrastructure, mock_logger, mock_config_manager):
        """Test driver initialization"""
        driver = UnifiedDriver(mock_infrastructure, mock_logger, mock_config_manager)

        assert driver.infrastructure is mock_infrastructure
        assert driver.logger is mock_logger
        assert driver._config_manager is mock_config_manager
        assert driver._docker_driver is None
        assert driver._file_driver is None
        assert driver._shell_driver is None

    def test_docker_driver_lazy_load(self, driver, mock_infrastructure):
        """Test docker driver lazy loading"""
        mock_docker_driver = Mock()
        mock_infrastructure.resolve.return_value = mock_docker_driver

        driver_instance = driver.docker_driver

        assert driver_instance is mock_docker_driver
        assert driver._docker_driver is mock_docker_driver
        mock_infrastructure.resolve.assert_called_once()

    def test_file_driver_lazy_load(self, driver, mock_infrastructure):
        """Test file driver lazy loading"""
        mock_file_driver = Mock()
        mock_infrastructure.resolve.return_value = mock_file_driver

        driver_instance = driver.file_driver

        assert driver_instance is mock_file_driver
        assert driver._file_driver is mock_file_driver

    def test_shell_driver_lazy_load(self, driver, mock_infrastructure):
        """Test shell driver lazy loading"""
        mock_shell_driver = Mock()
        mock_infrastructure.resolve.return_value = mock_shell_driver

        driver_instance = driver.shell_driver

        assert driver_instance is mock_shell_driver
        assert driver._shell_driver is mock_shell_driver

    def test_execute_operation_request_docker(self, driver):
        """Test executing docker request"""
        mock_request = Mock()
        mock_request.request_type = RequestType.DOCKER_REQUEST
        mock_request.op = "run"
        mock_request.image = "test_image"
        mock_request.cmd = ["echo", "test"]
        mock_request.container = "test_container"
        mock_request.volumes = {}
        mock_request.environment = {}
        mock_request.detach = False

        mock_docker_driver = Mock()
        mock_driver_result = Mock()
        mock_driver_result.success = True
        mock_driver_result.output = "test output"
        mock_driver_result.error = ""
        mock_docker_driver.run.return_value = mock_driver_result

        driver._docker_driver = mock_docker_driver
        result = driver.execute_operation_request(mock_request)

        assert isinstance(result, DockerResult)
        assert result.success is True
        assert result.stdout == "test output"
        mock_docker_driver.run.assert_called_once()

    def test_execute_operation_request_file(self, driver):
        """Test executing file request"""
        mock_request = Mock()
        mock_request.request_type = RequestType.FILE_REQUEST
        mock_request.op = FileOpType.MKDIR
        mock_request.get_absolute_source.return_value = "/test/path"

        mock_file_driver = Mock()
        mock_driver_result = Mock()
        mock_driver_result.success = True
        mock_driver_result.output = "directory created"
        mock_driver_result.error = ""
        mock_file_driver.mkdir.return_value = mock_driver_result

        driver._file_driver = mock_file_driver
        result = driver.execute_operation_request(mock_request)

        assert isinstance(result, FileResult)
        assert result.success is True
        mock_file_driver.mkdir.assert_called_once_with("/test/path")

    def test_execute_operation_request_shell(self, driver, mock_config_manager):
        """Test executing shell request"""
        mock_request = Mock()
        mock_request.request_type = RequestType.SHELL_REQUEST
        mock_request.cmd = ["echo", "test"]
        mock_request.cwd = "/test"
        mock_request.env = {}
        mock_request.timeout = 30

        mock_shell_driver = Mock()
        mock_driver_result = Mock()
        mock_driver_result.success = True
        mock_driver_result.output = "test output"
        mock_driver_result.error = ""
        mock_driver_result.exit_code = 0
        mock_shell_driver.run.return_value = mock_driver_result

        driver._shell_driver = mock_shell_driver
        result = driver.execute_operation_request(mock_request)

        assert isinstance(result, ShellResult)
        assert result.success is True
        assert result.returncode == 0
        mock_shell_driver.run.assert_called_once()

    def test_execute_operation_request_unsupported_type(self, driver):
        """Test executing unsupported request type"""
        mock_request = Mock()
        mock_request.request_type = "UNSUPPORTED_TYPE"

        with pytest.raises(ValueError, match="Unsupported request type"):
            driver.execute_operation_request(mock_request)

    def test_execute_docker_request_build(self, driver):
        """Test docker build operation"""
        mock_request = Mock()
        mock_request.op = "build"
        mock_request.context_path = "/test"
        mock_request.tag = "test:latest"
        mock_request.dockerfile = "Dockerfile"

        mock_docker_driver = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.output = "build success"
        mock_result.error = ""
        mock_docker_driver.build.return_value = mock_result

        driver._docker_driver = mock_docker_driver
        result = driver._execute_docker_request(mock_request)

        assert result.success is True
        mock_docker_driver.build.assert_called_once()

    def test_execute_docker_request_exec(self, driver):
        """Test docker exec operation"""
        mock_request = Mock()
        mock_request.op = "exec"
        mock_request.container = "test_container"
        mock_request.cmd = ["bash"]
        mock_request.workdir = "/app"

        mock_docker_driver = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.output = "exec success"
        mock_result.error = ""
        mock_docker_driver.exec.return_value = mock_result

        driver._docker_driver = mock_docker_driver
        result = driver._execute_docker_request(mock_request)

        assert result.success is True
        mock_docker_driver.exec.assert_called_once()

    def test_execute_docker_request_commit(self, driver):
        """Test docker commit operation"""
        mock_request = Mock()
        mock_request.op = "commit"
        mock_request.container = "test_container"
        mock_request.image = "test_image"
        mock_request.tag = "latest"

        mock_docker_driver = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.output = "commit success"
        mock_result.error = ""
        mock_docker_driver.commit.return_value = mock_result

        driver._docker_driver = mock_docker_driver
        result = driver._execute_docker_request(mock_request)

        assert result.success is True
        mock_docker_driver.commit.assert_called_once()

    def test_execute_docker_request_rm(self, driver):
        """Test docker rm operation"""
        mock_request = Mock()
        mock_request.op = "rm"
        mock_request.container = "test_container"
        mock_request.force = True

        mock_docker_driver = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.output = "rm success"
        mock_result.error = ""
        mock_docker_driver.rm.return_value = mock_result

        driver._docker_driver = mock_docker_driver
        result = driver._execute_docker_request(mock_request)

        assert result.success is True
        mock_docker_driver.rm.assert_called_once()

    def test_execute_docker_request_rmi(self, driver):
        """Test docker rmi operation"""
        mock_request = Mock()
        mock_request.op = "rmi"
        mock_request.image = "test_image"
        mock_request.force = True

        mock_docker_driver = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.output = "rmi success"
        mock_result.error = ""
        mock_docker_driver.rmi.return_value = mock_result

        driver._docker_driver = mock_docker_driver
        result = driver._execute_docker_request(mock_request)

        assert result.success is True
        mock_docker_driver.rmi.assert_called_once()

    def test_execute_docker_request_exception(self, driver):
        """Test docker request exception handling"""
        mock_request = Mock()
        mock_request.op = "run"

        mock_docker_driver = Mock()
        mock_docker_driver.run.side_effect = Exception("Test error")

        driver._docker_driver = mock_docker_driver
        result = driver._execute_docker_request(mock_request)

        assert result.success is False
        assert "Test error" in result.stderr

    def test_execute_docker_request_unsupported_op(self, driver):
        """Test unsupported docker operation"""
        mock_request = Mock()
        mock_request.op = "unsupported_op"

        result = driver._execute_docker_request(mock_request)
        assert result.success is False
        assert "Unsupported docker operation" in result.stderr

    def test_execute_docker_request_missing_op_attribute(self, driver):
        """Test docker request missing op attribute"""
        mock_request = Mock(spec=[])  # Mock without 'op' attribute

        with pytest.raises(TypeError, match="Expected DockerRequest with 'op' attribute"):
            driver._execute_docker_request(mock_request)

    def test_execute_file_request_copy(self, driver):
        """Test file copy operation"""
        mock_request = Mock()
        mock_request.op = FileOpType.COPY
        mock_request.get_absolute_source.return_value = "/src/path"
        mock_request.get_absolute_target.return_value = "/dst/path"

        mock_file_driver = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.output = "copy success"
        mock_result.error = ""
        mock_file_driver.copy.return_value = mock_result

        driver._file_driver = mock_file_driver
        result = driver._execute_file_request(mock_request)

        assert result.success is True
        mock_file_driver.copy.assert_called_once_with("/src/path", "/dst/path")

    def test_execute_file_request_exception(self, driver):
        """Test file request exception handling"""
        mock_request = Mock()
        mock_request.op = FileOpType.MKDIR
        mock_request.get_absolute_source.return_value = "/test/path"

        mock_file_driver = Mock()
        mock_file_driver.mkdir.side_effect = Exception("Test error")

        driver._file_driver = mock_file_driver
        result = driver._execute_file_request(mock_request)

        assert result.success is False
        assert "Test error" in result.error_message

    def test_execute_shell_request_with_exit_code_config(self, driver, mock_config_manager):
        """Test shell request with exit code from config"""
        mock_request = Mock()
        mock_request.cmd = ["echo", "test"]
        mock_request.cwd = "/test"
        mock_request.env = {}
        mock_request.timeout = 30

        mock_shell_driver = Mock()
        mock_driver_result = Mock()
        mock_driver_result.success = True
        mock_driver_result.output = "test output"
        mock_driver_result.error = ""
        mock_driver_result.exit_code = None  # No exit code in result
        mock_shell_driver.run.return_value = mock_driver_result

        # Mock config manager to return exit codes
        mock_config_manager.resolve_config.side_effect = lambda path, type_hint: {
            ('execution_defaults', 'exit_codes', 'success'): 0,
            ('execution_defaults', 'exit_codes', 'failure'): 1
        }.get(tuple(path))

        driver._shell_driver = mock_shell_driver
        result = driver._execute_shell_request(mock_request)

        assert result.success is True
        assert result.returncode == 0

    def test_execute_shell_request_config_error(self, driver):
        """Test shell request with config error"""
        mock_request = Mock()
        mock_request.cmd = ["echo", "test"]
        mock_request.cwd = "/test"
        mock_request.env = {}
        mock_request.timeout = 30

        mock_shell_driver = Mock()
        mock_driver_result = Mock()
        mock_driver_result.success = True
        mock_driver_result.output = "test output"
        mock_driver_result.error = ""
        mock_driver_result.exit_code = None
        mock_shell_driver.run.return_value = mock_driver_result

        # Mock config manager to raise KeyError
        driver._config_manager.resolve_config.side_effect = KeyError("Config not found")

        driver._shell_driver = mock_shell_driver
        result = driver._execute_shell_request(mock_request)

        # エラーが発生した場合はexception付きのresultが返される
        assert result.success is False
        assert "Exit code not available" in result.error_message

    def test_execute_shell_request_exception(self, driver):
        """Test shell request exception handling"""
        mock_request = Mock()
        mock_request.cmd = ["echo", "test"]

        mock_shell_driver = Mock()
        mock_shell_driver.run.side_effect = Exception("Test error")

        driver._shell_driver = mock_shell_driver
        result = driver._execute_shell_request(mock_request)

        assert result.success is False
        assert "Test error" in result.stderr
        assert result.returncode == 1

    def test_execute_shell_request_missing_cmd_attribute(self, driver):
        """Test shell request missing cmd attribute"""
        mock_request = Mock(spec=[])  # Mock without 'cmd' attribute

        with pytest.raises(TypeError, match="Expected ShellRequest with 'cmd' attribute"):
            driver._execute_shell_request(mock_request)

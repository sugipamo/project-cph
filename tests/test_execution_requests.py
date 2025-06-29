"""Tests for execution request implementations."""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from typing import Any, Optional

from src.application.execution_requests import (
    ShellRequest, PythonRequest, DockerRequest, FileRequest,
    DockerOpType, DockerOperationError
)
from src.infrastructure.requests.file.file_op_type import FileOpType
from src.domain.base_request import RequestType
from src.operations.constants.operation_type import OperationType


class TestShellRequest:
    """Test cases for ShellRequest."""

    def test_init(self):
        """Test ShellRequest initialization."""
        error_converter = Mock()
        result_factory = Mock()
        
        request = ShellRequest(
            command="ls -la",
            working_directory="/tmp",
            error_converter=error_converter,
            result_factory=result_factory,
            name="List files",
            timeout=30.0,
            environment={"PATH": "/usr/bin"},
            shell=True,
            retry_config={"max_attempts": 3},
            debug_tag="test"
        )
        
        assert request.command == "ls -la"
        assert request.working_directory == "/tmp"
        assert request.timeout == 30.0
        assert request.environment == {"PATH": "/usr/bin"}
        assert request.shell is True
        assert request.retry_config == {"max_attempts": 3}
        # Note: name and debug_tag are passed to super().__init__ but not stored as attributes
        # This appears to be a limitation of the current implementation

    def test_properties(self):
        """Test ShellRequest properties."""
        request = ShellRequest(
            command="echo test",
            working_directory="/tmp",
            error_converter=Mock(),
            result_factory=Mock(),
            name="test_shell",
            timeout=None,
            environment=None,
            shell=True,
            retry_config=None,
            debug_tag=None
        )
        
        assert request.operation_type == OperationType.SHELL
        assert request.request_type == RequestType.SHELL_REQUEST

    def test_execute_success(self):
        """Test successful shell command execution."""
        error_converter = Mock()
        result_factory = Mock()
        driver = Mock()
        logger = Mock()
        
        # Mock driver response
        driver.execute_command.return_value = {
            'success': True,
            'stdout': 'output',
            'stderr': ''
        }
        
        # Mock result factory
        expected_result = Mock()
        result_factory.create_shell_result.return_value = expected_result
        
        request = ShellRequest(
            command="echo test",
            working_directory="/tmp",
            error_converter=error_converter,
            result_factory=result_factory,
            name="test_shell",
            timeout=None,
            environment=None,
            shell=None,
            retry_config=None,
            debug_tag=None
        )
        
        result = request._execute_core(driver, logger)
        
        # Verify driver was called correctly
        driver.execute_command.assert_called_once_with(
            command="echo test",
            timeout=None,
            environment=None,
            shell=None,
            working_directory="/tmp"
        )
        
        # Verify result factory was called
        result_factory.create_shell_result.assert_called_once_with(
            success=True,
            stdout='output',
            stderr='',
            command="echo test",
            working_directory="/tmp"
        )
        
        assert result == expected_result

    def test_execute_failure(self):
        """Test failed shell command execution."""
        error_converter = Mock()
        result_factory = Mock()
        driver = Mock()
        logger = Mock()
        
        # Mock driver response
        driver.execute_command.return_value = {
            'success': False,
            'stdout': '',
            'stderr': 'command not found',
            'error': Exception('Command failed')
        }
        
        # Mock error converter
        converted_error = "Converted error"
        error_converter.convert_error.return_value = converted_error
        
        # Mock result factory
        expected_result = Mock()
        result_factory.create_shell_result.return_value = expected_result
        
        request = ShellRequest(
            command="invalid_command",
            working_directory="/tmp",
            error_converter=error_converter,
            result_factory=result_factory,
            name="test_shell",
            timeout=None,
            environment=None,
            shell=None,
            retry_config=None,
            debug_tag=None
        )
        
        result = request._execute_core(driver, logger)
        
        # Verify error conversion
        error_converter.convert_error.assert_called_once()
        
        # Verify result factory was called with error
        result_factory.create_shell_result.assert_called_once_with(
            success=False,
            stdout='',
            stderr='command not found',
            error=converted_error,
            command="invalid_command",
            working_directory="/tmp"
        )

    def test_execute_with_retry(self):
        """Test shell command execution with retry logic."""
        error_converter = Mock()
        result_factory = Mock()
        driver = Mock()
        logger = Mock()
        
        # First two attempts fail, third succeeds
        driver.execute_command.side_effect = [
            {'success': False, 'stdout': '', 'stderr': 'error', 'error': Exception('Failed')},
            {'success': False, 'stdout': '', 'stderr': 'error', 'error': Exception('Failed')},
            {'success': True, 'stdout': 'output', 'stderr': ''}
        ]
        
        request = ShellRequest(
            command="flaky_command",
            working_directory="/tmp",
            error_converter=error_converter,
            result_factory=result_factory,
            name="test_shell",
            timeout=None,
            environment=None,
            shell=None,
            retry_config={"max_attempts": 3},
            debug_tag=None
        )
        
        result = request._execute_core(driver, logger)
        
        # Verify driver was called 3 times
        assert driver.execute_command.call_count == 3
        
        # Verify logger warnings for retries
        assert logger.warning.call_count == 2

    def test_execute_exception(self):
        """Test shell command execution with exception."""
        error_converter = Mock()
        result_factory = Mock()
        driver = Mock()
        logger = Mock()
        
        # Mock driver to raise exception
        driver.execute_command.side_effect = RuntimeError("Driver error")
        
        # Mock error converter
        converted_error = "Converted runtime error"
        error_converter.convert_error.return_value = converted_error
        
        request = ShellRequest(
            command="echo test",
            working_directory="/tmp",
            error_converter=error_converter,
            result_factory=result_factory,
            name="test_shell",
            timeout=None,
            environment=None,
            shell=None,
            retry_config=None,
            debug_tag=None
        )
        
        result = request._execute_core(driver, logger)
        
        # Verify error handling
        error_converter.convert_error.assert_called_once()
        result_factory.create_shell_result.assert_called_once()


class TestPythonRequest:
    """Test cases for PythonRequest."""

    def test_init(self):
        """Test PythonRequest initialization."""
        os_provider = Mock()
        python_utils = Mock()
        time_ops = Mock()
        
        request = PythonRequest(
            script_or_code="print('test')",
            is_script_path=False,
            working_directory="/tmp",
            os_provider=os_provider,
            python_utils=python_utils,
            time_ops=time_ops,
            name="Test script",
            timeout=60.0,
            environment={"VAR": "value"},
            python_path="/usr/bin/python",
            debug_tag="test"
        )
        
        assert request.script_or_code == "print('test')"
        assert request.is_script_path is False
        assert request.working_directory == "/tmp"
        assert request.timeout == 60.0
        assert request.environment == {"VAR": "value"}
        assert request.python_path == "/usr/bin/python"

    def test_properties(self):
        """Test PythonRequest properties."""
        request = PythonRequest(
            script_or_code="test.py",
            is_script_path=True,
            working_directory="/tmp",
            os_provider=Mock(),
            python_utils=Mock(),
            time_ops=Mock()
        )
        
        assert request.operation_type == OperationType.PYTHON
        assert request.request_type == RequestType.PYTHON_REQUEST

    def test_execute_success(self):
        """Test successful Python execution."""
        os_provider = Mock()
        python_utils = Mock()
        time_ops = Mock()
        driver = Mock()
        logger = Mock()
        
        # Mock environment
        os_provider.environ = {"PATH": "/usr/bin"}
        python_utils.join_paths.return_value = "/tmp:/usr/lib/python"
        
        # Mock time
        start_time = Mock()
        end_time = Mock()
        time_ops.now.side_effect = [start_time, end_time]
        
        # Mock driver response
        driver.execute_python.return_value = {
            'success': True,
            'output': 'Hello, World!'
        }
        
        request = PythonRequest(
            script_or_code="print('Hello, World!')",
            is_script_path=False,
            working_directory="/tmp",
            os_provider=os_provider,
            python_utils=python_utils,
            time_ops=time_ops
        )
        
        result = request._execute_core(driver, logger)
        
        # Verify execution
        driver.execute_python.assert_called_once()
        call_args = driver.execute_python.call_args[1]
        assert call_args['script_or_code'] == "print('Hello, World!')"
        assert call_args['is_script_path'] is False
        assert call_args['working_directory'] == "/tmp"
        
        # Verify result
        assert result.success is True
        assert result.output == 'Hello, World!'
        assert result.start_time == start_time
        assert result.end_time == end_time

    def test_execute_failure(self):
        """Test failed Python execution."""
        os_provider = Mock()
        python_utils = Mock()
        time_ops = Mock()
        driver = Mock()
        logger = Mock()
        
        os_provider.environ = {}
        time_ops.now.return_value = Mock()
        
        # Mock driver response
        driver.execute_python.return_value = {
            'success': False,
            'error': 'Syntax error'
        }
        
        request = PythonRequest(
            script_or_code="invalid syntax",
            is_script_path=False,
            working_directory="/tmp",
            os_provider=os_provider,
            python_utils=python_utils,
            time_ops=time_ops
        )
        
        result = request._execute_core(driver, logger)
        
        assert result.success is False
        assert result.error == 'Syntax error'

    def test_prepare_environment(self):
        """Test environment preparation."""
        os_provider = Mock()
        python_utils = Mock()
        time_ops = Mock()
        
        # Mock existing environment
        os_provider.environ = {"PATH": "/usr/bin", "PYTHONPATH": "/usr/lib"}
        python_utils.join_paths.return_value = "/usr/lib:/tmp"
        
        request = PythonRequest(
            script_or_code="test.py",
            is_script_path=True,
            working_directory="/tmp",
            os_provider=os_provider,
            python_utils=python_utils,
            time_ops=time_ops,
            environment={"NEW_VAR": "value"}
        )
        
        env = request._prepare_environment()
        
        assert env["PATH"] == "/usr/bin"
        assert env["NEW_VAR"] == "value"
        assert "PYTHONPATH" in env
        python_utils.join_paths.assert_called_once()


class TestDockerRequest:
    """Test cases for DockerRequest."""

    def test_init(self):
        """Test DockerRequest initialization."""
        json_provider = Mock()
        
        request = DockerRequest(
            operation=DockerOpType.BUILD,
            json_provider=json_provider,
            working_directory="/project",
            name="Build image",
            image_name="myapp:latest",
            container_name="myapp-container",
            dockerfile_path="./Dockerfile",
            build_args={"VERSION": "1.0"},
            run_args={"detach": True},
            command=["python", "app.py"],
            environment={"ENV": "prod"},
            volumes={"/host/data": "/data"},
            ports={"8080": "80"},
            network="bridge",
            debug_tag="test"
        )
        
        assert request.operation == DockerOpType.BUILD
        assert request.image_name == "myapp:latest"
        assert request.container_name == "myapp-container"
        assert request.dockerfile_path == "./Dockerfile"
        assert request.build_args == {"VERSION": "1.0"}

    def test_properties(self):
        """Test DockerRequest properties."""
        request = DockerRequest(
            operation=DockerOpType.RUN,
            json_provider=Mock(),
            working_directory="/tmp"
        )
        
        assert request.operation_type == OperationType.DOCKER
        assert request.request_type == RequestType.DOCKER_REQUEST

    def test_execute_build_success(self):
        """Test successful Docker build operation."""
        json_provider = Mock()
        driver = Mock()
        logger = Mock()
        
        json_provider.dumps.return_value = '{"VERSION": "1.0"}'
        
        # Mock driver response
        driver.execute_docker_operation.return_value = {
            'success': True,
            'image_id': 'abc123',
            'output': 'Build complete'
        }
        
        request = DockerRequest(
            operation=DockerOpType.BUILD,
            json_provider=json_provider,
            working_directory="/project",
            image_name="myapp:latest",
            dockerfile_path="./Dockerfile",
            build_args={"VERSION": "1.0"}
        )
        
        result = request._execute_core(driver, logger)
        
        # Verify driver call
        driver.execute_docker_operation.assert_called_once_with('build', {
            'context': '/project',
            'dockerfile': './Dockerfile',
            'tag': 'myapp:latest',
            'buildargs': '{"VERSION": "1.0"}'
        })
        
        assert result.success is True
        assert result.operation == 'BUILD'
        assert result.image_id == 'abc123'

    def test_execute_build_missing_image_name(self):
        """Test Docker build without image name."""
        request = DockerRequest(
            operation=DockerOpType.BUILD,
            json_provider=Mock(),
            working_directory="/project"
        )
        
        with pytest.raises(DockerOperationError, match="Image name is required"):
            request._execute_build(Mock(), Mock())

    @patch('src.application.execution_requests.CompositeRequest')
    @patch('src.application.execution_requests.ShellRequest')
    @patch('src.application.execution_requests.ErrorConverter')
    @patch('src.application.execution_requests.ResultFactory')
    def test_execute_run_success(self, mock_result_factory, mock_error_converter, 
                                  mock_shell_request, mock_composite_request):
        """Test successful Docker run operation."""
        json_provider = Mock()
        driver = Mock()
        logger = Mock()
        
        # Mock composite request execution
        mock_composite_instance = Mock()
        mock_composite_instance.execute_operation.return_value = [
            Mock(success=True),  # pull result
            Mock(success=True)   # run result
        ]
        mock_composite_request.return_value = mock_composite_instance
        
        request = DockerRequest(
            operation=DockerOpType.RUN,
            json_provider=json_provider,
            working_directory="/project",
            image_name="myapp:latest",
            container_name="myapp-container"
        )
        
        result = request._execute_core(driver, logger)
        
        assert result.success is True
        assert result.operation == 'RUN'

    def test_execute_stop_success(self):
        """Test successful Docker stop operation."""
        driver = Mock()
        logger = Mock()
        
        driver.execute_docker_operation.return_value = {
            'success': True
        }
        
        request = DockerRequest(
            operation=DockerOpType.STOP,
            json_provider=Mock(),
            working_directory="/project",
            container_name="myapp-container"
        )
        
        result = request._execute_core(driver, logger)
        
        driver.execute_docker_operation.assert_called_once_with('stop', {
            'container': 'myapp-container'
        })
        
        assert result.success is True
        assert result.operation == 'STOP'

    def test_build_run_command(self):
        """Test Docker run command building."""
        request = DockerRequest(
            operation=DockerOpType.RUN,
            json_provider=Mock(),
            working_directory="/project"
        )
        
        params = {
            'image': 'myapp:latest',
            'name': 'myapp',
            'environment': {'ENV': 'prod', 'DEBUG': 'false'},
            'volumes': {'/host/data': '/app/data'},
            'ports': {'8080': '80'},
            'network': 'custom',
            'command': ['python', 'app.py']
        }
        
        command = request._build_run_command(params)
        
        expected = (
            "docker run --name myapp "
            "-e ENV=prod -e DEBUG=false "
            "-v /host/data:/app/data "
            "-p 8080:80 "
            "--network custom "
            "myapp:latest python app.py"
        )
        
        # Split and compare parts (order of env vars might vary)
        assert "docker run" in command
        assert "--name myapp" in command
        assert "-e ENV=prod" in command
        assert "-e DEBUG=false" in command
        assert "-v /host/data:/app/data" in command
        assert "-p 8080:80" in command
        assert "--network custom" in command
        assert "myapp:latest" in command
        assert command.endswith("python app.py")


class TestFileRequest:
    """Test cases for FileRequest."""

    def test_init(self):
        """Test FileRequest initialization."""
        time_ops = Mock()
        
        request = FileRequest(
            operation=FileOpType.READ,
            path="/tmp/test.txt",
            time_ops=time_ops,
            name="Read test file",
            content="test content",
            destination="/tmp/copy.txt",
            encoding="utf-8",
            allow_failure=True,
            debug_tag="test"
        )
        
        assert request.operation == FileOpType.READ
        assert request.path == "/tmp/test.txt"
        assert request.content == "test content"
        assert request.destination == "/tmp/copy.txt"
        assert request.encoding == "utf-8"
        assert request.allow_failure is True

    def test_properties(self):
        """Test FileRequest properties."""
        request = FileRequest(
            operation=FileOpType.WRITE,
            path="/tmp/test.txt",
            time_ops=Mock()
        )
        
        assert request.operation_type == OperationType.FILE
        assert request.request_type == RequestType.FILE_REQUEST

    def test_execute_read_success(self):
        """Test successful file read operation."""
        time_ops = Mock()
        driver = Mock()
        logger = Mock()
        
        time_ops.now.return_value = Mock()
        driver.read_file.return_value = "file content"
        
        request = FileRequest(
            operation=FileOpType.READ,
            path="/tmp/test.txt",
            time_ops=time_ops,
            encoding="utf-8"
        )
        
        result = request._execute_core(driver, logger)
        
        driver.read_file.assert_called_once_with("/tmp/test.txt", encoding="utf-8")
        assert result.success is True
        assert result.content == "file content"

    def test_execute_write_success(self):
        """Test successful file write operation."""
        time_ops = Mock()
        driver = Mock()
        logger = Mock()
        
        time_ops.now.return_value = Mock()
        
        request = FileRequest(
            operation=FileOpType.WRITE,
            path="/tmp/test.txt",
            time_ops=time_ops,
            content="new content",
            encoding="utf-8"
        )
        
        result = request._execute_core(driver, logger)
        
        driver.write_file.assert_called_once_with(
            "/tmp/test.txt", "new content", encoding="utf-8"
        )
        assert result.success is True
        assert result.exists is True

    def test_execute_write_missing_content(self):
        """Test file write without content."""
        time_ops = Mock()
        driver = Mock()
        logger = Mock()
        
        request = FileRequest(
            operation=FileOpType.WRITE,
            path="/tmp/test.txt",
            time_ops=time_ops
        )
        
        with pytest.raises(ValueError, match="Content is required"):
            request._execute_core(driver, logger)

    def test_execute_exists_check(self):
        """Test file exists check."""
        time_ops = Mock()
        driver = Mock()
        logger = Mock()
        
        time_ops.now.return_value = Mock()
        driver.file_exists.return_value = True
        
        request = FileRequest(
            operation=FileOpType.EXISTS,
            path="/tmp/test.txt",
            time_ops=time_ops
        )
        
        result = request._execute_core(driver, logger)
        
        driver.file_exists.assert_called_once_with("/tmp/test.txt")
        assert result.success is True
        assert result.exists is True

    def test_execute_copy_success(self):
        """Test successful file copy operation."""
        time_ops = Mock()
        driver = Mock()
        logger = Mock()
        
        time_ops.now.return_value = Mock()
        
        request = FileRequest(
            operation=FileOpType.COPY,
            path="/tmp/source.txt",
            destination="/tmp/dest.txt",
            time_ops=time_ops
        )
        
        result = request._execute_core(driver, logger)
        
        driver.copy_file.assert_called_once_with("/tmp/source.txt", "/tmp/dest.txt")
        assert result.success is True
        assert result.metadata['destination'] == "/tmp/dest.txt"

    def test_execute_error_allowed_failure(self):
        """Test file operation error with allowed failure."""
        time_ops = Mock()
        driver = Mock()
        logger = Mock()
        
        time_ops.now.return_value = Mock()
        driver.read_file.side_effect = IOError("File not found")
        
        request = FileRequest(
            operation=FileOpType.READ,
            path="/tmp/missing.txt",
            time_ops=time_ops,
            allow_failure=True
        )
        
        result = request._execute_core(driver, logger)
        
        # Should succeed even though operation failed
        assert result.success is True
        assert result.error_message == "File not found"
        assert isinstance(result.exception, IOError)

    def test_execute_error_not_allowed(self):
        """Test file operation error without allowed failure."""
        time_ops = Mock()
        driver = Mock()
        logger = Mock()
        
        time_ops.now.return_value = Mock()
        driver.read_file.side_effect = IOError("File not found")
        
        request = FileRequest(
            operation=FileOpType.READ,
            path="/tmp/missing.txt",
            time_ops=time_ops,
            allow_failure=False
        )
        
        with pytest.raises(IOError, match="File not found"):
            request._execute_core(driver, logger)

    @patch('src.application.execution_requests.SystemRegistryProvider')
    def test_resolve_driver_with_registry(self, mock_registry_provider):
        """Test driver resolution with registry."""
        time_ops = Mock()
        driver_without_file_ops = Mock(spec=[])  # No file operation methods
        file_driver = Mock()
        
        # Mock registry
        registry_instance = Mock()
        registry_instance.get_driver.return_value = file_driver
        mock_registry_provider.return_value = registry_instance
        
        request = FileRequest(
            operation=FileOpType.READ,
            path="/tmp/test.txt",
            time_ops=time_ops
        )
        
        resolved_driver = request._resolve_driver(driver_without_file_ops)
        
        assert resolved_driver == file_driver
        registry_instance.get_driver.assert_called_once_with('file')

    def test_resolve_driver_with_file_ops(self):
        """Test driver resolution when driver has file operations."""
        time_ops = Mock()
        driver_with_file_ops = Mock(spec=['read_file', 'write_file'])
        
        request = FileRequest(
            operation=FileOpType.READ,
            path="/tmp/test.txt",
            time_ops=time_ops
        )
        
        resolved_driver = request._resolve_driver(driver_with_file_ops)
        
        # Should use the provided driver directly
        assert resolved_driver == driver_with_file_ops
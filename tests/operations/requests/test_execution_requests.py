"""Tests for execution requests module."""
import pytest
from unittest.mock import Mock, patch
from src.application.execution_requests import (
    ShellRequest, PythonRequest, DockerRequest, DockerOpType,
    FileRequest
)
from src.infrastructure.requests.file.file_op_type import FileOpType
from src.operations.constants.operation_type import OperationType
from src.domain.base_request import RequestType


class TestShellRequest:
    """Tests for ShellRequest class."""
    
    @pytest.fixture
    def error_converter(self):
        return Mock()
    
    @pytest.fixture
    def result_factory(self):
        return Mock()
    
    def test_init(self, error_converter, result_factory):
        """Test ShellRequest initialization."""
        request = ShellRequest(
            command="echo test",
            working_directory="/tmp",
            error_converter=error_converter,
            result_factory=result_factory,
            name="test_shell",
            timeout=30.0,
            environment={"VAR": "value"},
            shell=True,
            retry_config={"max_attempts": 3},
            debug_tag="test"
        )
        
        assert request.command == "echo test"
        assert request.working_directory == "/tmp"
        assert request.timeout == 30.0
        assert request.environment == {"VAR": "value"}
        assert request.shell is True
        assert request.retry_config == {"max_attempts": 3}
        assert request.operation_type == OperationType.SHELL
        assert request.request_type == RequestType.SHELL_REQUEST
    
    def test_execute_core_success(self, error_converter, result_factory):
        """Test successful shell execution."""
        mock_driver = Mock()
        mock_driver.execute_command.return_value = {
            'stdout': "output",
            'stderr': "",
            'returncode': 0,
            'success': True
        }
        
        mock_result = Mock()
        result_factory.create_shell_result.return_value = mock_result
        
        request = ShellRequest(
            command="echo test",
            working_directory="/tmp",
            error_converter=error_converter,
            result_factory=result_factory
        )
        
        result = request._execute_core(mock_driver, None)
        
        assert result == mock_result
        mock_driver.execute_command.assert_called_once()
        result_factory.create_shell_result.assert_called_once_with(
            success=True,
            stdout="output",
            stderr="",
            command="echo test",
            working_directory="/tmp"
        )
    
    def test_execute_core_with_retry(self, error_converter, result_factory):
        """Test shell execution with retry."""
        mock_driver = Mock()
        mock_driver.execute_command.side_effect = [
            Exception("First failure"),
            {'stdout': "output", 'stderr': "", 'returncode': 0, 'success': True}
        ]
        
        error_converter.convert_error.return_value = "Converted error"
        mock_result = Mock()
        result_factory.create_shell_result.return_value = mock_result
        
        request = ShellRequest(
            command="echo test",
            working_directory="/tmp",
            error_converter=error_converter,
            result_factory=result_factory,
            retry_config={"max_attempts": 2}
        )
        
        result = request._execute_core(mock_driver, Mock())
        
        assert result == mock_result
        assert mock_driver.execute_command.call_count == 2


class TestPythonRequest:
    """Tests for PythonRequest class."""
    
    @pytest.fixture
    def providers(self):
        return {
            'os_provider': Mock(),
            'python_utils': Mock(),
            'time_ops': Mock()
        }
    
    def test_init(self, providers):
        """Test PythonRequest initialization."""
        request = PythonRequest(
            script_or_code="print('test')",
            is_script_path=False,
            working_directory="/tmp",
            os_provider=providers['os_provider'],
            python_utils=providers['python_utils'],
            time_ops=providers['time_ops'],
            name="test_python",
            timeout=30.0,
            environment={"PYTHONPATH": "/custom"},
            python_path="/usr/bin/python3",
            debug_tag="test"
        )
        
        assert request.script_or_code == "print('test')"
        assert request.is_script_path is False
        assert request.working_directory == "/tmp"
        assert request.timeout == 30.0
        assert request.environment == {"PYTHONPATH": "/custom"}
        assert request.python_path == "/usr/bin/python3"
        assert request.operation_type == OperationType.PYTHON
        assert request.request_type == RequestType.PYTHON_REQUEST
    
    def test_execute_core_success(self, providers):
        """Test successful Python execution."""
        mock_driver = Mock()
        mock_driver.execute_python.return_value = {
            'success': True,
            'output': 'test output'
        }
        
        providers['time_ops'].now.side_effect = [1.0, 2.0, 3.0]  # Need 3 calls: start, end for success, and possible error
        providers['os_provider'].environ = {"PATH": "/usr/bin"}
        providers['python_utils'].join_paths.return_value = "/tmp:/usr/lib"
        
        request = PythonRequest(
            script_or_code="print('test')",
            is_script_path=False,
            working_directory="/tmp",
            **providers
        )
        
        result = request._execute_core(mock_driver, Mock())
        
        assert result.success is True
        assert result.output == 'test output'
        assert result.start_time == 1.0
        assert result.end_time == 2.0
    
    def test_prepare_environment(self, providers):
        """Test environment preparation."""
        providers['os_provider'].environ = {"PATH": "/usr/bin"}
        providers['python_utils'].join_paths.return_value = "/existing:/tmp"
        
        request = PythonRequest(
            script_or_code="test.py",
            is_script_path=True,
            working_directory="/tmp",
            environment={"CUSTOM_VAR": "value"},
            **providers
        )
        
        env = request._prepare_environment()
        
        assert env["PATH"] == "/usr/bin"
        assert env["CUSTOM_VAR"] == "value"
        assert env["PYTHONPATH"] == "/existing:/tmp"


class TestDockerRequest:
    """Tests for DockerRequest class."""
    
    @pytest.fixture
    def time_ops(self):
        return Mock()
    
    def test_init(self, time_ops):
        """Test DockerRequest initialization."""
        json_provider = Mock()
        json_provider.dumps.return_value = '{}'
        request = DockerRequest(
            operation=DockerOpType.BUILD,
            json_provider=json_provider,
            working_directory="/app",
            image_name="test:latest",
            name="test_docker",
            container_name="test_container",
            command="echo test",
            dockerfile_path="./Dockerfile",
            build_args={"ARG": "value"},
            environment={"ENV": "value"},
            volumes={"/host": "/container"},
            ports={"8080": "80"},
            network="bridge",
            debug_tag="test"
        )
        
        assert request.operation == DockerOpType.BUILD
        assert request.image_name == "test:latest"
        assert request.container_name == "test_container"
        assert request.command == "echo test"
        assert request.dockerfile_path == "./Dockerfile"
        assert request.build_args == {"ARG": "value"}
        assert request.environment == {"ENV": "value"}
        assert request.volumes == {"/host": "/container"}
        assert request.ports == {"8080": "80"}
        assert request.network == "bridge"
        assert request.working_directory == "/app"
        assert request.operation_type == OperationType.DOCKER
        assert request.request_type == RequestType.DOCKER_REQUEST
    
    def test_execute_core_build(self, time_ops):
        """Test Docker build operation."""
        time_ops.now.side_effect = [1.0, 2.0]
        
        mock_driver = Mock()
        mock_driver.execute_docker_operation.return_value = {
            'success': True,
            'image_id': 'abc123'
        }
        
        json_provider = Mock()
        json_provider.dumps.return_value = '{}'
        request = DockerRequest(
            operation=DockerOpType.BUILD,
            json_provider=json_provider,
            working_directory="/app",
            image_name="test:latest",
            dockerfile_path="./Dockerfile"
        )
        
        result = request._execute_core(mock_driver, Mock())
        
        assert result.success is True
        assert result.image_id == 'abc123'
        mock_driver.execute_docker_operation.assert_called_once()
    
    def test_execute_core_run(self, time_ops):
        """Test Docker run operation."""
        time_ops.now.side_effect = [1.0, 2.0]
        
        mock_driver = Mock()
        # Mock the execute_command method that ShellRequest will call
        # This needs to return success for both pull and run commands
        mock_driver.execute_command.return_value = {
            'success': True,
            'stdout': 'Command output',
            'stderr': '',
            'error': None
        }
        
        json_provider = Mock()
        json_provider.dumps.return_value = '{}'
        request = DockerRequest(
            operation=DockerOpType.RUN,
            json_provider=json_provider,
            working_directory="/app",
            image_name="test:latest",
            container_name="test_container",
            command="echo test"
        )
        
        # The execute_core method will create a composite request internally
        # which will execute shell commands through the driver
        result = request._execute_core(mock_driver, Mock())
        
        assert result.success is True
        assert result.container_id == 'test_container'
        assert result.output == 'Container started successfully'
        
        # Verify that execute_command was called twice (pull + run)
        assert mock_driver.execute_command.call_count == 2
    
    def test_execute_core_invalid_operation(self, time_ops):
        """Test invalid Docker operation."""
        time_ops.now.side_effect = [1.0, 2.0]
        
        json_provider = Mock()
        json_provider.dumps.return_value = '{}'
        # Create an invalid operation type
        invalid_op = Mock()
        invalid_op.name = "INVALID"
        request = DockerRequest(
            operation=invalid_op,
            json_provider=json_provider,
            working_directory="/app",
            image_name="test:latest"
        )
        
        result = request._execute_core(Mock(), Mock())
        
        assert result.success is False
        assert "Unsupported Docker operation" in result.error


class TestFileRequestAdditional:
    """Additional tests for FileRequest to improve coverage."""
    
    @pytest.fixture
    def time_ops(self):
        mock = Mock()
        mock.now.return_value = 1.0
        return mock
    
    def test_execute_write_no_content(self, time_ops):
        """Test write operation without content."""
        request = FileRequest(
            operation=FileOpType.WRITE,
            path="/test/file.txt",
            time_ops=time_ops,
            content=None
        )
        
        with pytest.raises(ValueError, match="Content is required for write operation"):
            request._execute_write(Mock(), Mock())
    
    def test_execute_copy_no_destination(self, time_ops):
        """Test copy operation without destination."""
        request = FileRequest(
            operation=FileOpType.COPY,
            path="/test/file.txt",
            time_ops=time_ops,
            destination=None
        )
        
        with pytest.raises(ValueError, match="Destination is required for copy operation"):
            request._execute_copy(Mock(), Mock())
    
    def test_execute_move_no_destination(self, time_ops):
        """Test move operation without destination."""
        request = FileRequest(
            operation=FileOpType.MOVE,
            path="/test/file.txt",
            time_ops=time_ops,
            destination=None
        )
        
        with pytest.raises(ValueError, match="Destination is required for move operation"):
            request._execute_move(Mock(), Mock())
    
    def test_handle_file_error_allow_failure(self, time_ops):
        """Test error handling with allow_failure=True."""
        request = FileRequest(
            operation=FileOpType.READ,
            path="/test/file.txt",
            time_ops=time_ops,
            allow_failure=True
        )
        
        error = Exception("Test error")
        result = request._handle_file_error(error, 0.5, Mock())
        
        assert result.success is True  # Marked as success since failure is allowed
        assert result.error_message == "Test error"
        assert result.exception == error
    
    def test_resolve_driver_with_file_methods(self, time_ops):
        """Test driver resolution when driver has file methods."""
        request = FileRequest(
            operation=FileOpType.READ,
            path="/test/file.txt",
            time_ops=time_ops
        )
        
        mock_driver = Mock()
        mock_driver.read_file = Mock()
        
        resolved = request._resolve_driver(mock_driver)
        assert resolved == mock_driver
    
    def test_resolve_driver_from_registry(self, time_ops):
        """Test driver resolution from registry."""
        request = FileRequest(
            operation=FileOpType.READ,
            path="/test/file.txt",
            time_ops=time_ops
        )
        
        # Create a mock driver without file methods
        mock_driver = Mock(spec=[])  # Empty spec means no methods
        mock_file_driver = Mock()
        
        with patch('src.operations.requests.execution_requests.SystemRegistryProvider') as mock_registry:
            mock_registry.return_value.get_driver.return_value = mock_file_driver
            
            resolved = request._resolve_driver(mock_driver)
            assert resolved == mock_file_driver
            mock_registry.return_value.get_driver.assert_called_once_with('file')
    
    def test_execute_rmtree(self, time_ops):
        """Test recursive directory removal."""
        mock_driver = Mock()
        
        request = FileRequest(
            operation=FileOpType.RMTREE,
            path="/test/dir",
            time_ops=time_ops
        )
        
        result = request._execute_rmtree(mock_driver, Mock())
        
        assert result.success is True
        assert result.path == "/test/dir"
        assert result.exists is False
        mock_driver.remove_directory.assert_called_once_with("/test/dir")
    
    def test_execute_touch(self, time_ops):
        """Test file touch operation."""
        mock_driver = Mock()
        
        request = FileRequest(
            operation=FileOpType.TOUCH,
            path="/test/file.txt",
            time_ops=time_ops
        )
        
        result = request._execute_touch(mock_driver, Mock())
        
        assert result.success is True
        assert result.path == "/test/file.txt"
        assert result.exists is True
        mock_driver.touch_file.assert_called_once_with("/test/file.txt")
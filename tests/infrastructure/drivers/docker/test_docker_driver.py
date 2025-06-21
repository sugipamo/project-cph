"""Tests for Docker driver implementation."""
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.infrastructure.drivers.docker.docker_driver import DockerDriver, LocalDockerDriver
from src.infrastructure.drivers.file.local_file_driver import LocalFileDriver
from src.operations.results.shell_result import ShellResult


class TestDockerDriver:
    """Test abstract DockerDriver base class."""


    def test_abstract_methods_exist(self):
        """Test that all required abstract methods are defined."""
        # Verify abstract methods are properly defined
        abstract_methods = {
            'run_container',
            'stop_container',
            'remove_container',
            'exec_in_container',
            'get_logs',
            'build_docker_image',
            'image_ls',
            'image_rm',
            'ps',
            'inspect',
            'cp'
        }

        # Get abstract methods from the class
        driver_abstracts = {name for name, method in DockerDriver.__dict__.items()
                          if getattr(method, '__isabstractmethod__', False)}

        assert driver_abstracts == abstract_methods


class TestLocalDockerDriver:
    """Test LocalDockerDriver implementation."""

    def test_initialization_default(self):
        """Test default initialization of LocalDockerDriver."""
        driver = LocalDockerDriver(file_driver=LocalFileDriver(base_dir=Path('.')))
        assert driver.shell_driver is not None
        assert hasattr(driver.shell_driver, 'execute_command')

    def test_initialization_with_file_driver(self):
        """Test initialization with custom file driver."""
        mock_file_driver = Mock()
        driver = LocalDockerDriver(file_driver=mock_file_driver)
        assert driver.shell_driver is not None

    def test_execute_command_compatibility(self):
        """Test execute_command method for BaseDriver compatibility."""
        driver = LocalDockerDriver(file_driver=LocalFileDriver(base_dir=Path('.')))
        # Should not raise an error - compatibility method
        result = driver.execute_command(Mock())
        assert result is None

    def test_validate_always_true(self):
        """Test that validate always returns True for now."""
        driver = LocalDockerDriver(file_driver=LocalFileDriver(base_dir=Path('.')))
        mock_request = Mock()
        assert driver.validate(mock_request) is True

    @patch('src.infrastructure.drivers.docker.docker_driver.build_docker_run_command')
    @patch('src.infrastructure.drivers.docker.docker_driver.ShellRequest')
    def test_run_container_basic(self, mock_shell_request, mock_build_command):
        """Test basic container run functionality."""
        mock_build_command.return_value = ["docker", "run", "ubuntu"]
        mock_request = Mock()
        mock_result = Mock()
        mock_result.stdout = "Container started"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_request.execute_operation.return_value = mock_result
        mock_shell_request.return_value = mock_request

        driver = LocalDockerDriver(file_driver=LocalFileDriver(base_dir=Path('.')))
        result = driver.run_container("ubuntu", name=None, options={}, show_output=True)

        mock_build_command.assert_called_once_with("ubuntu", None, {})
        mock_shell_request.assert_called_once_with(["docker", "run", "ubuntu"], cwd=".", env={}, inputdata="", timeout=300, debug_tag="docker_run", name="docker_run_request", show_output=True, allow_failure=False)
        assert result == mock_result

    @patch('src.infrastructure.drivers.docker.docker_driver.build_docker_run_command')
    @patch('src.infrastructure.drivers.docker.docker_driver.ShellRequest')
    def test_run_container_with_options(self, mock_shell_request, mock_build_command):
        """Test container run with name and options."""
        mock_build_command.return_value = ["docker", "run", "--name", "test", "ubuntu"]
        mock_request = Mock()
        mock_result = Mock()
        mock_result.stdout = "Container started"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_request.execute_operation.return_value = mock_result
        mock_shell_request.return_value = mock_request

        driver = LocalDockerDriver(file_driver=LocalFileDriver(base_dir=Path('.')))
        options = {"detach": True}
        driver.run_container("ubuntu", name="test", options=options, show_output=False)

        mock_build_command.assert_called_once_with("ubuntu", "test", options)
        mock_shell_request.assert_called_once_with(["docker", "run", "--name", "test", "ubuntu"], cwd=".", env={}, inputdata="", timeout=300, debug_tag="docker_run", name="docker_run_request", show_output=False, allow_failure=False)

    @patch('src.infrastructure.drivers.docker.docker_driver.build_docker_stop_command')
    @patch('src.infrastructure.drivers.docker.docker_driver.ShellRequest')
    def test_stop_container(self, mock_shell_request, mock_build_command):
        """Test container stop functionality."""
        mock_build_command.return_value = ["docker", "stop", "test-container"]
        mock_request = Mock()
        mock_result = Mock()
        mock_result.stdout = "Container stopped"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_request.execute_operation.return_value = mock_result
        mock_shell_request.return_value = mock_request

        driver = LocalDockerDriver(file_driver=LocalFileDriver(base_dir=Path('.')))
        result = driver.stop_container("test-container", timeout=10, show_output=True)

        mock_build_command.assert_called_once_with("test-container", 10)
        mock_shell_request.assert_called_once_with(["docker", "stop", "test-container"],
                                                  cwd=".", env={}, inputdata="", timeout=300,
                                                  debug_tag="docker_run", name="docker_run_request",
                                                  show_output=True, allow_failure=False)
        assert result == mock_result

    @patch('src.infrastructure.drivers.docker.docker_driver.build_docker_remove_command')
    @patch('src.infrastructure.drivers.docker.docker_driver.ShellRequest')
    def test_remove_container(self, mock_shell_request, mock_build_command):
        """Test container removal functionality."""
        mock_build_command.return_value = ["docker", "rm", "test-container"]
        mock_request = Mock()
        mock_result = Mock()
        mock_result.stdout = "Container removed"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_request.execute_operation.return_value = mock_result
        mock_shell_request.return_value = mock_request

        driver = LocalDockerDriver(file_driver=LocalFileDriver(base_dir=Path('.')))
        result = driver.remove_container("test-container")

        mock_build_command.assert_called_once_with("test-container", force=False)
        mock_shell_request.assert_called_once_with(["docker", "rm", "test-container"], show_output=True)
        assert result == mock_result

    @patch('src.infrastructure.drivers.docker.docker_driver.build_docker_remove_command')
    @patch('src.infrastructure.drivers.docker.docker_driver.ShellRequest')
    def test_remove_container_force(self, mock_shell_request, mock_build_command):
        """Test forced container removal."""
        mock_build_command.return_value = ["docker", "rm", "-f", "test-container"]
        mock_request = Mock()
        mock_result = Mock()
        mock_result.stdout = "Container removed"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_request.execute_operation.return_value = mock_result
        mock_shell_request.return_value = mock_request

        driver = LocalDockerDriver(file_driver=LocalFileDriver(base_dir=Path('.')))
        driver.remove_container("test-container", force=True, show_output=False)

        mock_build_command.assert_called_once_with("test-container", force=True)
        mock_shell_request.assert_called_once_with(["docker", "rm", "-f", "test-container"], show_output=False)

    @patch('src.infrastructure.drivers.docker.docker_driver.ShellRequest')
    def test_exec_in_container_list_command(self, mock_shell_request):
        """Test executing command in container with list command."""
        mock_request = Mock()
        mock_result = Mock()
        mock_result.stdout = "Command executed"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_request.execute_operation.return_value = mock_result
        mock_shell_request.return_value = mock_request

        driver = LocalDockerDriver(file_driver=LocalFileDriver(base_dir=Path('.')))
        result = driver.exec_in_container("test-container", ["bash", "-c", "echo hello"])

        expected_cmd = ["docker", "exec", "test-container", "bash", "-c", "echo hello"]
        mock_shell_request.assert_called_once_with(expected_cmd, show_output=True)
        assert result == mock_result

    @patch('src.infrastructure.drivers.docker.docker_driver.ShellRequest')
    @patch('src.infrastructure.drivers.docker.docker_driver.shlex')
    def test_exec_in_container_string_command(self, mock_shlex, mock_shell_request):
        """Test executing command in container with string command."""
        mock_shlex.split.return_value = ["bash", "-c", "echo hello"]
        mock_request = Mock()
        mock_result = Mock()
        mock_result.stdout = "Command executed"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_request.execute_operation.return_value = mock_result
        mock_shell_request.return_value = mock_request

        driver = LocalDockerDriver(file_driver=LocalFileDriver(base_dir=Path('.')))
        driver.exec_in_container("test-container", 'bash -c "echo hello"')

        expected_cmd = ["docker", "exec", "test-container", "bash", "-c", "echo hello"]
        mock_shell_request.assert_called_once_with(expected_cmd, show_output=True)
        mock_shlex.split.assert_called_once_with('bash -c "echo hello"')


    @patch('src.infrastructure.drivers.docker.docker_driver.ShellRequest')
    def test_get_logs(self, mock_shell_request):
        """Test getting container logs."""
        mock_request = Mock()
        mock_result = Mock()
        mock_result.stdout = "Container logs"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_request.execute_operation.return_value = mock_result
        mock_shell_request.return_value = mock_request

        driver = LocalDockerDriver(file_driver=LocalFileDriver(base_dir=Path('.')))
        result = driver.get_logs("test-container", show_output=False)

        expected_cmd = ["docker", "logs", "test-container"]
        mock_shell_request.assert_called_once_with(expected_cmd, show_output=False)
        assert result == mock_result

    @patch('src.infrastructure.drivers.docker.docker_driver.build_docker_build_command')
    @patch('src.infrastructure.drivers.docker.docker_driver.ShellRequest')
    def test_build_docker_image_success(self, mock_shell_request, mock_build_command):
        """Test successful Docker image build."""
        dockerfile_content = "FROM ubuntu\\nRUN echo hello"
        mock_build_command.return_value = ["docker", "build", "-t", "test:latest", "-f", "-", "."]
        mock_request = Mock()
        mock_result = Mock()
        mock_result.stdout = "Image built"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_request.execute_operation.return_value = mock_result
        mock_shell_request.return_value = mock_request

        driver = LocalDockerDriver(file_driver=LocalFileDriver(base_dir=Path('.')))
        result = driver.build_docker_image(dockerfile_content, tag="test:latest", options={}, show_output=True)

        mock_build_command.assert_called_once_with("test:latest", dockerfile_content, {})
        mock_shell_request.assert_called_once_with(
            ["docker", "build", "-t", "test:latest", "-f", "-", "."],
            show_output=True,
            inputdata=dockerfile_content
        )
        assert result == mock_result


    @patch('src.infrastructure.drivers.docker.docker_driver.ShellRequest')
    def test_image_ls(self, mock_shell_request):
        """Test listing Docker images."""
        mock_request = Mock()
        mock_result = Mock()
        mock_result.stdout = "ubuntu\\nalpine"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_request.execute_operation.return_value = mock_result
        mock_shell_request.return_value = mock_request

        driver = LocalDockerDriver(file_driver=LocalFileDriver(base_dir=Path('.')))
        result = driver.image_ls()

        expected_cmd = ["docker", "image", "ls"]
        mock_shell_request.assert_called_once_with(expected_cmd, show_output=True)
        assert result == mock_result

    @patch('src.infrastructure.drivers.docker.docker_driver.ShellRequest')
    def test_image_rm(self, mock_shell_request):
        """Test removing Docker image."""
        mock_request = Mock()
        mock_result = Mock()
        mock_result.stdout = "Image removed"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_request.execute_operation.return_value = mock_result
        mock_shell_request.return_value = mock_request

        driver = LocalDockerDriver(file_driver=LocalFileDriver(base_dir=Path('.')))
        result = driver.image_rm("test:latest", show_output=False)

        expected_cmd = ["docker", "image", "rm", "test:latest"]
        mock_shell_request.assert_called_once_with(expected_cmd, show_output=False)
        assert result == mock_result

    @patch('src.infrastructure.drivers.docker.docker_driver.ShellRequest')
    def test_ps_basic(self, mock_shell_request):
        """Test basic container listing."""
        mock_request = Mock()
        mock_result = Mock()
        mock_result.stdout = "CONTAINER ID   IMAGE"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_request.execute_operation.return_value = mock_result
        mock_shell_request.return_value = mock_request

        driver = LocalDockerDriver(file_driver=LocalFileDriver(base_dir=Path('.')))
        result = driver.ps()

        expected_cmd = ["docker", "ps"]
        mock_shell_request.assert_called_once_with(expected_cmd, show_output=True)
        assert result == mock_result

    @patch('src.infrastructure.drivers.docker.docker_driver.ShellRequest')
    def test_ps_names_only(self, mock_shell_request):
        """Test container listing with names only."""
        mock_request = Mock()
        mock_result = Mock()
        mock_result.stdout = "container1\ncontainer2"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_request.execute_operation.return_value = mock_result
        mock_shell_request.return_value = mock_request

        driver = LocalDockerDriver(file_driver=LocalFileDriver(base_dir=Path('.')))
        result = driver.ps(names_only=True, show_output=False)

        expected_cmd = ["docker", "ps", "-a", "--format", "{{.Names}}"]
        mock_shell_request.assert_called_once_with(expected_cmd, show_output=False)
        # When names_only=True, it returns parsed container names
        assert result == ["container1", "container2"]

    @patch('src.infrastructure.drivers.docker.docker_driver.parse_container_names')
    @patch('src.infrastructure.drivers.docker.docker_driver.ShellRequest')
    def test_ps_names_only_with_parsing(self, mock_shell_request, mock_parse):
        """Test container listing with names parsing."""
        mock_request = Mock()
        mock_result = Mock()
        mock_result.stdout = "container1\\ncontainer2"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_request.execute_operation.return_value = mock_result
        mock_shell_request.return_value = mock_request
        mock_parse.return_value = ["container1", "container2"]

        driver = LocalDockerDriver(file_driver=LocalFileDriver(base_dir=Path('.')))
        driver.ps(names_only=True)

        # Verify the parsing function would be called on the output
        mock_parse.assert_called_once_with("container1\\ncontainer2")

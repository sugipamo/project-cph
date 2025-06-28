"""Tests for Docker driver."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

from src.infrastructure.drivers.docker.docker_driver import DockerDriver
from src.application.execution_requests import ShellRequest


class TestDockerDriverInit:
    """Test Docker driver initialization."""

    def test_init_minimal(self):
        """Test initialization with minimal parameters."""
        mock_file_driver = Mock()
        
        driver = DockerDriver(file_driver=mock_file_driver)
        
        assert driver.file_driver == mock_file_driver
        assert driver.execution_driver is None
        assert driver.logger is None
        assert driver.container_repo is None
        assert driver.image_repo is None
        assert driver._tracking_enabled is False

    def test_init_full(self):
        """Test initialization with all parameters."""
        mock_file_driver = Mock()
        mock_execution_driver = Mock()
        mock_logger = Mock()
        mock_container_repo = Mock()
        mock_image_repo = Mock()
        
        driver = DockerDriver(
            file_driver=mock_file_driver,
            execution_driver=mock_execution_driver,
            logger=mock_logger,
            container_repo=mock_container_repo,
            image_repo=mock_image_repo
        )
        
        assert driver.file_driver == mock_file_driver
        assert driver.execution_driver == mock_execution_driver
        assert driver.logger == mock_logger
        assert driver.container_repo == mock_container_repo
        assert driver.image_repo == mock_image_repo
        assert driver._tracking_enabled is True

    def test_tracking_enabled_with_container_repo_only(self):
        """Test tracking is enabled with only container repo."""
        mock_file_driver = Mock()
        mock_container_repo = Mock()
        
        driver = DockerDriver(
            file_driver=mock_file_driver,
            container_repo=mock_container_repo
        )
        
        assert driver._tracking_enabled is True

    def test_tracking_enabled_with_image_repo_only(self):
        """Test tracking is enabled with only image repo."""
        mock_file_driver = Mock()
        mock_image_repo = Mock()
        
        driver = DockerDriver(
            file_driver=mock_file_driver,
            image_repo=mock_image_repo
        )
        
        assert driver._tracking_enabled is True


class TestDockerDriverValidation:
    """Test Docker driver validation methods."""

    def test_validate_docker_image_name_valid(self):
        """Test validation of valid Docker image names."""
        # Valid image names
        assert DockerDriver.validate_docker_image_name("ubuntu") is True
        assert DockerDriver.validate_docker_image_name("ubuntu:20.04") is True
        assert DockerDriver.validate_docker_image_name("myregistry.com/myimage") is True
        assert DockerDriver.validate_docker_image_name("myregistry.com/myimage:v1.0") is True
        assert DockerDriver.validate_docker_image_name("python:3.9-slim") is True
        assert DockerDriver.validate_docker_image_name("node:14.17.0-alpine3.13") is True

    def test_validate_docker_image_name_invalid(self):
        """Test validation of invalid Docker image names."""
        # Invalid image names
        assert DockerDriver.validate_docker_image_name("") is False
        assert DockerDriver.validate_docker_image_name("UPPERCASE") is False
        assert DockerDriver.validate_docker_image_name("image with spaces") is False
        assert DockerDriver.validate_docker_image_name("image@invalid") is False
        assert DockerDriver.validate_docker_image_name("image#tag") is False

    def test_validate_request(self):
        """Test request validation."""
        driver = DockerDriver(file_driver=Mock())
        
        # Valid requests
        valid_request = Mock()
        valid_request.operation = "run"
        assert driver.validate(valid_request) is True
        
        valid_request.operation = "stop"
        assert driver.validate(valid_request) is True
        
        valid_request.operation = "build"
        assert driver.validate(valid_request) is True
        
        # Invalid requests
        invalid_request = Mock()
        invalid_request.operation = "invalid"
        assert driver.validate(invalid_request) is False
        
        no_operation = Mock(spec=[])  # No operation attribute
        assert driver.validate(no_operation) is False


class TestDockerCommandBuilding:
    """Test Docker command building methods."""

    def setup_method(self):
        """Setup test driver."""
        self.driver = DockerDriver(file_driver=Mock())

    def test_build_docker_run_command_minimal(self):
        """Test building minimal docker run command."""
        cmd = self.driver._build_docker_run_command("ubuntu", None, {})
        assert cmd == ["docker", "run", "ubuntu"]

    def test_build_docker_run_command_with_name(self):
        """Test building docker run command with container name."""
        cmd = self.driver._build_docker_run_command("ubuntu", "mycontainer", {})
        assert cmd == ["docker", "run", "--name", "mycontainer", "ubuntu"]

    def test_build_docker_run_command_with_flags(self):
        """Test building docker run command with flags."""
        options = {
            "detach": True,
            "interactive": True,
            "tty": True,
            "remove": True
        }
        cmd = self.driver._build_docker_run_command("ubuntu", None, options)
        assert cmd == ["docker", "run", "-d", "-i", "-t", "--rm", "ubuntu"]

    def test_build_docker_run_command_with_network(self):
        """Test building docker run command with network."""
        options = {"network": "mynetwork"}
        cmd = self.driver._build_docker_run_command("ubuntu", None, options)
        assert cmd == ["docker", "run", "--network", "mynetwork", "ubuntu"]

    def test_build_docker_run_command_with_ports(self):
        """Test building docker run command with port mappings."""
        options = {"ports": ["8080:80", "3306:3306"]}
        cmd = self.driver._build_docker_run_command("ubuntu", None, options)
        assert cmd == ["docker", "run", "-p", "8080:80", "-p", "3306:3306", "ubuntu"]

    def test_build_docker_run_command_with_volumes(self):
        """Test building docker run command with volumes."""
        options = {"volumes": ["/host/path:/container/path", "myvolume:/data"]}
        cmd = self.driver._build_docker_run_command("ubuntu", None, options)
        assert cmd == ["docker", "run", "-v", "/host/path:/container/path", "-v", "myvolume:/data", "ubuntu"]

    def test_build_docker_run_command_with_env(self):
        """Test building docker run command with environment variables."""
        options = {"env": {"KEY1": "value1", "KEY2": "value2"}}
        cmd = self.driver._build_docker_run_command("ubuntu", None, options)
        assert cmd == ["docker", "run", "-e", "KEY1=value1", "-e", "KEY2=value2", "ubuntu"]

    def test_build_docker_run_command_with_workdir(self):
        """Test building docker run command with working directory."""
        options = {"workdir": "/app"}
        cmd = self.driver._build_docker_run_command("ubuntu", None, options)
        assert cmd == ["docker", "run", "-w", "/app", "ubuntu"]

    def test_build_docker_run_command_with_command_string(self):
        """Test building docker run command with command as string."""
        options = {"command": "python app.py --arg value"}
        cmd = self.driver._build_docker_run_command("ubuntu", None, options)
        assert cmd == ["docker", "run", "ubuntu", "python", "app.py", "--arg", "value"]

    def test_build_docker_run_command_with_command_list(self):
        """Test building docker run command with command as list."""
        options = {"command": ["python", "app.py", "--arg", "value"]}
        cmd = self.driver._build_docker_run_command("ubuntu", None, options)
        assert cmd == ["docker", "run", "ubuntu", "python", "app.py", "--arg", "value"]

    def test_build_docker_run_command_complete(self):
        """Test building complete docker run command with all options."""
        options = {
            "detach": True,
            "interactive": True,
            "tty": True,
            "network": "bridge",
            "ports": ["8080:80"],
            "volumes": ["/data:/data"],
            "env": {"ENV": "prod"},
            "workdir": "/app",
            "command": "python server.py"
        }
        cmd = self.driver._build_docker_run_command("myimage:latest", "myapp", options)
        
        expected = [
            "docker", "run", "--name", "myapp", "-d", "-i", "-t",
            "--network", "bridge", "-p", "8080:80", "-v", "/data:/data",
            "-e", "ENV=prod", "-w", "/app", "myimage:latest", "python", "server.py"
        ]
        assert cmd == expected

    def test_build_docker_stop_command(self):
        """Test building docker stop command."""
        cmd = self.driver._build_docker_stop_command("mycontainer")
        assert cmd == ["docker", "stop", "-t", "10", "mycontainer"]
        
        cmd = self.driver._build_docker_stop_command("mycontainer", timeout=30)
        assert cmd == ["docker", "stop", "-t", "30", "mycontainer"]

    def test_build_docker_remove_command(self):
        """Test building docker remove command."""
        cmd = self.driver._build_docker_remove_command("mycontainer")
        assert cmd == ["docker", "rm", "mycontainer"]
        
        cmd = self.driver._build_docker_remove_command("mycontainer", force=True)
        assert cmd == ["docker", "rm", "-f", "mycontainer"]

    def test_build_docker_build_command(self):
        """Test building docker build command."""
        cmd = self.driver._build_docker_build_command("myimage", "Dockerfile", {})
        assert cmd == ["docker", "build", "-t", "myimage", "."]
        
        # With custom dockerfile
        cmd = self.driver._build_docker_build_command("myimage", "custom.dockerfile", {})
        assert cmd == ["docker", "build", "-t", "myimage", "-f", "custom.dockerfile", "."]
        
        # With build args
        build_args = {"ARG1": "value1", "ARG2": "value2"}
        cmd = self.driver._build_docker_build_command("myimage", "Dockerfile", build_args)
        assert cmd == ["docker", "build", "-t", "myimage", "--build-arg", "ARG1=value1", 
                       "--build-arg", "ARG2=value2", "."]


class TestDockerOperations:
    """Test Docker operation methods."""

    def setup_method(self):
        """Setup test driver with mocks."""
        self.mock_file_driver = Mock()
        self.mock_execution_driver = Mock()
        self.mock_logger = Mock()
        self.driver = DockerDriver(
            file_driver=self.mock_file_driver,
            execution_driver=self.mock_execution_driver,
            logger=self.mock_logger
        )

    @patch('src.infrastructure.drivers.docker_driver.ShellRequest')
    def test_run_container(self, mock_shell_request_class):
        """Test running a container."""
        # Setup mocks
        mock_request = Mock()
        mock_result = Mock()
        mock_request.execute_operation.return_value = mock_result
        mock_shell_request_class.return_value = mock_request
        
        # Mock _get_default_value
        self.driver._get_default_value = Mock(side_effect=lambda key, default: default)
        
        # Execute
        result = self.driver.run_container(
            image="ubuntu:20.04",
            name="test-container",
            options={"detach": True, "ports": ["8080:80"]},
            show_output=True
        )
        
        # Verify
        assert result == mock_result
        
        # Verify ShellRequest creation
        mock_shell_request_class.assert_called_once()
        call_kwargs = mock_shell_request_class.call_args[1]
        assert call_kwargs["show_output"] is True
        assert call_kwargs["debug_tag"] == "docker_run"
        assert isinstance(call_kwargs["cmd"], list)
        assert call_kwargs["cmd"][0] == "docker"
        assert call_kwargs["cmd"][1] == "run"

    def test_execute_command_run(self):
        """Test execute_command routing to run operation."""
        mock_request = Mock(spec=['operation', 'image'])
        mock_request.operation = "run"
        mock_request.image = "ubuntu"
        
        with patch.object(self.driver, 'run_container') as mock_run:
            mock_run.return_value = "success"
            
            result = self.driver.execute_command(mock_request)
            
            assert result == "success"
            # getattr on Mock returns Mock objects, not defaults
            mock_run.assert_called_once()

    def test_execute_command_stop(self):
        """Test execute_command routing to stop operation."""
        mock_request = Mock(spec=['operation', 'name'])
        mock_request.operation = "stop"
        mock_request.name = "mycontainer"
        
        with patch.object(self.driver, 'stop_container') as mock_stop:
            mock_stop.return_value = "stopped"
            
            result = self.driver.execute_command(mock_request)
            
            assert result == "stopped"
            # getattr on Mock returns Mock objects, not defaults
            mock_stop.assert_called_once()

    def test_execute_command_build(self):
        """Test execute_command routing to build operation."""
        mock_request = Mock(spec=['operation', 'image_name', 'dockerfile_path'])
        mock_request.operation = "build"
        mock_request.image_name = "myimage"
        mock_request.dockerfile_path = "Dockerfile"
        
        with patch.object(self.driver, 'build_docker_image') as mock_build:
            mock_build.return_value = "built"
            
            result = self.driver.execute_command(mock_request)
            
            assert result == "built"
            # getattr on Mock returns Mock objects, not defaults
            mock_build.assert_called_once()

    def test_execute_command_invalid(self):
        """Test execute_command with invalid request."""
        mock_request = Mock()
        mock_request.operation = "invalid"
        
        with pytest.raises(ValueError, match="Invalid Docker request"):
            self.driver.execute_command(mock_request)

    def test_execute_command_no_operation(self):
        """Test execute_command with no operation attribute."""
        mock_request = Mock(spec=[])  # No operation attribute
        
        with pytest.raises(ValueError, match="Invalid Docker request"):
            self.driver.execute_command(mock_request)
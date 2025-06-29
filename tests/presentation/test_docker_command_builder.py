"""Tests for docker_command_builder module."""
import pytest
from unittest.mock import Mock, patch

from src.presentation.docker_command_builder import (
    set_config_manager,
    validate_docker_image_name,
    build_docker_run_command,
    build_docker_stop_command,
    build_docker_remove_command,
    build_docker_build_command,
    build_docker_exec_command,
    build_docker_ps_command,
    build_docker_logs_command,
    build_docker_inspect_command,
    build_docker_cp_command,
    _get_docker_option
)


class TestDockerCommandBuilder:
    """Tests for docker command builder functions."""
    
    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock configuration manager."""
        mock = Mock()
        mock.root_node = {"docker_defaults": {"docker_options": {}}}
        return mock
    
    @pytest.fixture(autouse=True)
    def reset_config_manager(self):
        """Reset global config manager before each test."""
        set_config_manager(None)
        yield
        set_config_manager(None)
    
    def test_set_config_manager(self, mock_config_manager):
        """Test setting configuration manager."""
        set_config_manager(mock_config_manager)
        # This should not raise an error now
        from src.presentation.docker_command_builder import _get_config_manager
        assert _get_config_manager() == mock_config_manager
    
    def test_get_config_manager_not_set_raises_error(self):
        """Test accessing config manager when not set raises error."""
        with pytest.raises(RuntimeError, match="Configuration manager not injected"):
            _get_docker_option("test_option", None)
    
    def test_get_docker_option_from_user_options(self, mock_config_manager):
        """Test getting Docker option from user options."""
        set_config_manager(mock_config_manager)
        user_options = {"test_option": "user_value"}
        
        result = _get_docker_option("test_option", user_options)
        
        assert result == "user_value"
        mock_config_manager.resolve_config.assert_not_called()
    
    def test_get_docker_option_from_config(self, mock_config_manager):
        """Test getting Docker option from configuration."""
        set_config_manager(mock_config_manager)
        mock_config_manager.resolve_config.return_value = "config_value"
        
        result = _get_docker_option("test_option", None)
        
        assert result == "config_value"
        mock_config_manager.resolve_config.assert_called_once_with(
            ['docker_defaults', 'docker_options', 'test_option'], bool
        )
    
    def test_get_docker_option_no_root_node_raises_error(self, mock_config_manager):
        """Test getting Docker option when root node is None raises error."""
        mock_config_manager.root_node = None
        set_config_manager(mock_config_manager)
        
        with pytest.raises(KeyError, match="configuration not loaded"):
            _get_docker_option("test_option", None)
    
    def test_validate_docker_image_name_valid(self):
        """Test validation of valid Docker image names."""
        valid_names = [
            "ubuntu",
            "ubuntu:latest",
            "ubuntu:20.04",
            "myregistry.com/ubuntu",
            "myregistry.com/namespace/ubuntu:tag",
            "my-app",  # Simple name with hyphen
            "gcr.io/project/image:v1.0.0"
        ]
        
        for name in valid_names:
            assert validate_docker_image_name(name) is True, f"Expected {name} to be valid"
    
    def test_validate_docker_image_name_invalid(self):
        """Test validation of invalid Docker image names."""
        invalid_names = [
            "",
            "Ubuntu",  # Uppercase not allowed
            "my image",  # Spaces not allowed
            ":tag",  # Missing name
            "image:",  # Missing tag after colon
            "my/image/",  # Trailing slash
            "/image",  # Leading slash
        ]
        
        for name in invalid_names:
            assert validate_docker_image_name(name) is False
    
    def test_build_docker_run_command_basic(self, mock_config_manager):
        """Test building basic docker run command."""
        set_config_manager(mock_config_manager)
        mock_config_manager.resolve_config.return_value = False
        
        cmd = build_docker_run_command("ubuntu:latest", "test-container", {})
        
        assert cmd == ["docker", "run", "--name", "test-container", "ubuntu:latest"]
    
    def test_build_docker_run_command_with_flags(self, mock_config_manager):
        """Test building docker run command with flags."""
        set_config_manager(mock_config_manager)
        
        # Mock config returns for different options
        def mock_resolve(path, type_):
            option = path[-1]
            return {
                "detach": True,
                "interactive": True,
                "tty": True,
                "remove": True
            }.get(option, False)
        
        mock_config_manager.resolve_config.side_effect = mock_resolve
        
        cmd = build_docker_run_command("ubuntu:latest", "test-container", {})
        
        assert "docker" in cmd
        assert "run" in cmd
        assert "--name" in cmd
        assert "test-container" in cmd
        assert "-d" in cmd
        assert "-i" in cmd
        assert "-t" in cmd
        assert "--rm" in cmd
        assert "ubuntu:latest" in cmd
    
    def test_build_docker_run_command_with_ports(self, mock_config_manager):
        """Test building docker run command with port mappings."""
        set_config_manager(mock_config_manager)
        mock_config_manager.resolve_config.return_value = False
        
        options = {"ports": ["8080:80", "3000:3000"]}
        cmd = build_docker_run_command("nginx", "web-server", options)
        
        assert "-p" in cmd
        assert "8080:80" in cmd
        assert "3000:3000" in cmd
    
    def test_build_docker_run_command_with_volumes(self, mock_config_manager):
        """Test building docker run command with volume mounts."""
        set_config_manager(mock_config_manager)
        mock_config_manager.resolve_config.return_value = False
        
        options = {"volumes": ["/host/path:/container/path", "data-volume:/data"]}
        cmd = build_docker_run_command("postgres", "db", options)
        
        assert "-v" in cmd
        assert "/host/path:/container/path" in cmd
        assert "data-volume:/data" in cmd
    
    def test_build_docker_run_command_with_environment(self, mock_config_manager):
        """Test building docker run command with environment variables."""
        set_config_manager(mock_config_manager)
        mock_config_manager.resolve_config.return_value = False
        
        options = {"environment": ["DB_HOST=localhost", "DB_PORT=5432"]}
        cmd = build_docker_run_command("app", "my-app", options)
        
        assert "-e" in cmd
        assert "DB_HOST=localhost" in cmd
        assert "DB_PORT=5432" in cmd
    
    def test_build_docker_run_command_with_misc_options(self, mock_config_manager):
        """Test building docker run command with miscellaneous options."""
        set_config_manager(mock_config_manager)
        mock_config_manager.resolve_config.return_value = False
        
        options = {
            "workdir": "/app",
            "user": "1000:1000",
            "network": "bridge",
            "extra_args": ["--cpus", "2"]
        }
        cmd = build_docker_run_command("app", "my-app", options)
        
        assert "-w" in cmd
        assert "/app" in cmd
        assert "-u" in cmd
        assert "1000:1000" in cmd
        assert "--network" in cmd
        assert "bridge" in cmd
        assert "--cpus" in cmd
        assert "2" in cmd
    
    def test_build_docker_run_command_with_command(self, mock_config_manager):
        """Test building docker run command with container command."""
        set_config_manager(mock_config_manager)
        mock_config_manager.resolve_config.return_value = False
        
        # Test with string command
        options = {"command": "/bin/bash"}
        cmd = build_docker_run_command("ubuntu", "test", options)
        assert "/bin/bash" in cmd
        
        # Test with list command
        options = {"command": ["python", "app.py", "--debug"]}
        cmd = build_docker_run_command("python:3.9", "app", options)
        assert "python" in cmd
        assert "app.py" in cmd
        assert "--debug" in cmd
    
    def test_build_docker_stop_command(self):
        """Test building docker stop command."""
        cmd = build_docker_stop_command("my-container", 10)
        
        assert cmd == ["docker", "stop", "-t", "10", "my-container"]
    
    def test_build_docker_remove_command(self):
        """Test building docker remove command."""
        # Basic remove
        cmd = build_docker_remove_command("my-container", False, False)
        assert cmd == ["docker", "rm", "my-container"]
        
        # Force remove
        cmd = build_docker_remove_command("my-container", force=True, volumes=False)
        assert cmd == ["docker", "rm", "-f", "my-container"]
        
        # Remove with volumes
        cmd = build_docker_remove_command("my-container", force=False, volumes=True)
        assert cmd == ["docker", "rm", "-v", "my-container"]
        
        # Force remove with volumes
        cmd = build_docker_remove_command("my-container", force=True, volumes=True)
        assert cmd == ["docker", "rm", "-f", "-v", "my-container"]
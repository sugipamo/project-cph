"""Tests for Docker Command Builder utilities."""
from unittest.mock import Mock, patch

import pytest

from src.infrastructure.drivers.docker.utils.docker_command_builder import (
    _get_config_manager,
    _get_docker_option,
    build_docker_build_command,
    build_docker_cp_command,
    build_docker_exec_command,
    build_docker_inspect_command,
    build_docker_logs_command,
    build_docker_ps_command,
    build_docker_remove_command,
    build_docker_run_command,
    build_docker_stop_command,
    parse_container_names,
    set_config_manager,
    validate_docker_image_name,
)


class TestDockerCommandBuilder:
    """Test cases for Docker Command Builder utilities."""

    def setup_method(self):
        """Reset global config manager before each test."""
        set_config_manager(None)

    def test_set_config_manager(self):
        """Test setting configuration manager."""
        mock_config = Mock()
        set_config_manager(mock_config)

        assert _get_config_manager() == mock_config


    def test_get_docker_option_from_user_options(self):
        """Test getting Docker option from user-provided options."""
        user_options = {"interactive": False}

        result = _get_docker_option("interactive", user_options)
        assert result is False

    def test_get_docker_option_from_config(self):
        """Test getting Docker option from configuration system."""
        mock_config = Mock()
        mock_config.root_node = Mock()
        mock_config.resolve_config.return_value = True
        set_config_manager(mock_config)

        result = _get_docker_option("interactive", None)
        assert result is True



    def test_validate_docker_image_name_valid(self):
        """Test validating valid Docker image names."""
        valid_names = [
            "ubuntu",
            "ubuntu:latest",
            "registry.com/ubuntu:20.04",
            "my-image",
            "my_image",
            "registry.com/namespace/image:tag-v1.0"
        ]

        for name in valid_names:
            assert validate_docker_image_name(name) is True

    def test_validate_docker_image_name_invalid(self):
        """Test validating invalid Docker image names."""
        invalid_names = [
            "",
            "Ubuntu",  # Capital letters not allowed
            "image::",
            "image name",  # Spaces not allowed
            "image/",
            "/image"
        ]

        for name in invalid_names:
            assert validate_docker_image_name(name) is False

    def test_build_docker_run_command_basic(self):
        """Test building basic docker run command."""
        mock_config = Mock()
        mock_config.root_node = Mock()
        # 設定システムから適切な値を返すよう修正
        mock_config.resolve_config.side_effect = lambda path, dtype: {
            ('docker_defaults', 'docker_options', 'interactive'): True,
            ('docker_defaults', 'docker_options', 'tty'): True,
            ('docker_defaults', 'docker_options', 'remove'): True,
            ('docker_defaults', 'docker_options', 'detach'): False
        }.get(tuple(path), False)
        set_config_manager(mock_config)

        cmd = build_docker_run_command("ubuntu:latest", "test-container", {})

        expected = ["docker", "run", "--name", "test-container", "-i", "-t", "--rm", "ubuntu:latest"]
        assert cmd == expected

    def test_build_docker_run_command_with_name(self):
        """Test building docker run command with container name."""
        mock_config = Mock()
        mock_config.root_node = Mock()
        # 設定システムから適切な値を返すよう修正
        mock_config.resolve_config.side_effect = lambda path, dtype: {
            ('docker_defaults', 'docker_options', 'interactive'): True,
            ('docker_defaults', 'docker_options', 'tty'): True,
            ('docker_defaults', 'docker_options', 'remove'): True,
            ('docker_defaults', 'docker_options', 'detach'): False
        }.get(tuple(path), False)
        set_config_manager(mock_config)

        cmd = build_docker_run_command("ubuntu:latest", "my-container", {})

        expected = ["docker", "run", "--name", "my-container", "-i", "-t", "--rm", "ubuntu:latest"]
        assert cmd == expected

    def test_build_docker_run_command_with_options(self):
        """Test building docker run command with various options."""
        mock_config = Mock()
        mock_config.root_node = Mock()
        mock_config.resolve_config.side_effect = KeyError("Not found")
        set_config_manager(mock_config)

        options = {
            "detach": True,
            "interactive": False,
            "tty": False,
            "remove": False,
            "ports": ["8080:80", "3000:3000"],
            "volumes": ["/host:/container"],
            "environment": ["ENV_VAR=value"],
            "workdir": "/app",
            "user": "1000:1000",
            "network": "bridge",
            "extra_args": ["--cap-add", "SYS_ADMIN"],
            "command": ["bash", "-c", "echo hello"]
        }

        cmd = build_docker_run_command("ubuntu:latest", "test-container", options)

        expected = [
            "docker", "run", "--name", "test-container", "-d",
            "-p", "8080:80", "-p", "3000:3000",
            "-v", "/host:/container",
            "-e", "ENV_VAR=value",
            "-w", "/app",
            "-u", "1000:1000",
            "--network", "bridge",
            "--cap-add", "SYS_ADMIN",
            "ubuntu:latest",
            "bash", "-c", "echo hello"
        ]
        assert cmd == expected

    def test_build_docker_run_command_with_string_command(self):
        """Test building docker run command with string command."""
        mock_config = Mock()
        mock_config.root_node = Mock()
        # 設定システムから適切な値を返すよう修正
        mock_config.resolve_config.side_effect = lambda path, dtype: {
            ('docker_defaults', 'docker_options', 'interactive'): False,
            ('docker_defaults', 'docker_options', 'tty'): False,
            ('docker_defaults', 'docker_options', 'remove'): False,
            ('docker_defaults', 'docker_options', 'detach'): False
        }.get(tuple(path), False)
        set_config_manager(mock_config)

        options = {"command": "bash"}
        cmd = build_docker_run_command("ubuntu:latest", "test-container", options)

        assert cmd[-1] == "bash"

    def test_build_docker_stop_command(self):
        """Test building docker stop command."""
        cmd = build_docker_stop_command("my-container", 10)
        expected = ["docker", "stop", "-t", "10", "my-container"]
        assert cmd == expected

    def test_build_docker_stop_command_with_timeout(self):
        """Test building docker stop command with timeout."""
        cmd = build_docker_stop_command("my-container", 30)
        expected = ["docker", "stop", "-t", "30", "my-container"]
        assert cmd == expected

    def test_build_docker_remove_command(self):
        """Test building docker remove command."""
        cmd = build_docker_remove_command("my-container", force=False, volumes=False)
        expected = ["docker", "rm", "my-container"]
        assert cmd == expected

    def test_build_docker_remove_command_with_flags(self):
        """Test building docker remove command with flags."""
        cmd = build_docker_remove_command("my-container", force=True, volumes=True)
        expected = ["docker", "rm", "-f", "-v", "my-container"]
        assert cmd == expected

    def test_build_docker_build_command_basic(self):
        """Test building basic docker build command."""
        mock_config = Mock()
        mock_config.root_node = Mock()
        mock_config.resolve_config.side_effect = KeyError("Not found")
        set_config_manager(mock_config)

        cmd = build_docker_build_command("latest", "FROM ubuntu", ".", {})
        expected = ["docker", "build", "-t", "latest", "-f", "-", "."]
        assert cmd == expected

    def test_build_docker_build_command_with_tag(self):
        """Test building docker build command with tag."""
        mock_config = Mock()
        mock_config.root_node = Mock()
        mock_config.resolve_config.side_effect = KeyError("Not found")
        set_config_manager(mock_config)

        cmd = build_docker_build_command("my-image:latest", "FROM ubuntu", ".", {})
        expected = ["docker", "build", "-t", "my-image:latest", "-f", "-", "."]
        assert cmd == expected

    def test_build_docker_build_command_with_dockerfile_text(self):
        """Test building docker build command with dockerfile text."""
        mock_config = Mock()
        mock_config.root_node = Mock()
        mock_config.resolve_config.side_effect = KeyError("Not found")
        set_config_manager(mock_config)

        cmd = build_docker_build_command("latest", "FROM ubuntu", ".", {})
        expected = ["docker", "build", "-t", "latest", "-f", "-", "."]
        assert cmd == expected

    def test_build_docker_build_command_with_options(self):
        """Test building docker build command with options."""
        options = {
            "build_args": ["ARG1=value1", "ARG2=value2"],
            "no_cache": True,
            "pull": True,
            "quiet": True
        }

        cmd = build_docker_build_command("test:latest", "FROM ubuntu", "/app", options)

        expected = [
            "docker", "build",
            "-t", "test:latest",
            "--build-arg", "ARG1=value1",
            "--build-arg", "ARG2=value2",
            "--no-cache", "--pull", "-q",
            "-f", "-",
            "/app"
        ]
        assert cmd == expected

    def test_build_docker_ps_command_basic(self):
        """Test building basic docker ps command."""
        cmd = build_docker_ps_command(all=False, filter_params=[], format_string="table")
        expected = ["docker", "ps", "--format", "table"]
        assert cmd == expected

    def test_build_docker_ps_command_with_options(self):
        """Test building docker ps command with options."""
        cmd = build_docker_ps_command(
            all=True,
            filter_params=["status=running", "name=test"],
            format_string="table {{.Names}}\t{{.Status}}"
        )

        expected = [
            "docker", "ps", "-a",
            "--filter", "status=running",
            "--filter", "name=test",
            "--format", "table {{.Names}}\t{{.Status}}"
        ]
        assert cmd == expected

    def test_build_docker_inspect_command_basic(self):
        """Test building basic docker inspect command."""
        cmd = build_docker_inspect_command("my-container", "container", "json")
        expected = ["docker", "inspect", "--type", "container", "--format", "json", "my-container"]
        assert cmd == expected

    def test_build_docker_inspect_command_with_options(self):
        """Test building docker inspect command with options."""
        cmd = build_docker_inspect_command(
            "my-container",
            type_="container",
            format_string="{{.State.Status}}"
        )

        expected = [
            "docker", "inspect",
            "--type", "container",
            "--format", "{{.State.Status}}",
            "my-container"
        ]
        assert cmd == expected

    def test_build_docker_cp_command_to_container(self):
        """Test building docker cp command to container."""
        cmd = build_docker_cp_command("/host/file", "/container/file", "my-container")
        expected = ["docker", "cp", "/host/file", "my-container:/container/file"]
        assert cmd == expected

    def test_build_docker_cp_command_from_container(self):
        """Test building docker cp command from container."""
        cmd = build_docker_cp_command("/container/file", "/host/file", "my-container", to_container=False)
        expected = ["docker", "cp", "my-container:/container/file", "/host/file"]
        assert cmd == expected

    def test_build_docker_exec_command_basic(self):
        """Test building basic docker exec command."""
        cmd = build_docker_exec_command("my-container", "bash", interactive=False, tty=False, user="root", workdir="/")
        expected = ["docker", "exec", "-u", "root", "-w", "/", "my-container", "bash"]
        assert cmd == expected

    def test_build_docker_exec_command_with_options(self):
        """Test building docker exec command with options."""
        cmd = build_docker_exec_command(
            "my-container",
            ["bash", "-c", "echo hello"],
            interactive=True,
            tty=True,
            user="root",
            workdir="/app"
        )

        expected = [
            "docker", "exec", "-i", "-t",
            "-u", "root", "-w", "/app",
            "my-container", "bash", "-c", "echo hello"
        ]
        assert cmd == expected

    def test_build_docker_logs_command_basic(self):
        """Test building basic docker logs command."""
        cmd = build_docker_logs_command("my-container", follow=False, tail=50, since="1970-01-01")
        expected = ["docker", "logs", "--tail", "50", "--since", "1970-01-01", "my-container"]
        assert cmd == expected

    def test_build_docker_logs_command_with_options(self):
        """Test building docker logs command with options."""
        cmd = build_docker_logs_command(
            "my-container",
            follow=True,
            tail=100,
            since="2023-01-01T00:00:00Z"
        )

        expected = [
            "docker", "logs", "-f",
            "--tail", "100",
            "--since", "2023-01-01T00:00:00Z",
            "my-container"
        ]
        assert cmd == expected

    def test_parse_container_names_empty(self):
        """Test parsing empty container names output."""
        result = parse_container_names("")
        assert result == []

    def test_parse_container_names_single(self):
        """Test parsing single container name."""
        output = "my-container"
        result = parse_container_names(output)
        assert result == ["my-container"]

    def test_parse_container_names_multiple(self):
        """Test parsing multiple container names."""
        output = "container1\ncontainer2\ncontainer3"
        result = parse_container_names(output)
        assert result == ["container1", "container2", "container3"]

    def test_parse_container_names_with_whitespace(self):
        """Test parsing container names with whitespace."""
        output = "  container1  \n  container2  \n"
        result = parse_container_names(output)
        assert result == ["container1", "container2"]

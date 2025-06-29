"""Tests for Docker utility functions."""
import pytest
from src.utils.docker_utils import DockerUtils, validate_docker_image_name


class TestDockerUtils:
    """Test cases for DockerUtils class."""

    class TestBuildDockerCmd:
        """Test cases for build_docker_cmd method."""

        def test_build_simple_command(self):
            """Test building a simple Docker command."""
            base_cmd = ["docker", "run"]
            options = {}
            positional_args = ["ubuntu"]
            
            result = DockerUtils.build_docker_cmd(base_cmd, options, positional_args)
            assert result == ["docker", "run", "ubuntu"]

        def test_build_with_short_options(self):
            """Test building command with short options."""
            base_cmd = ["docker", "run"]
            options = {"i": None, "t": None}
            positional_args = ["ubuntu"]
            
            result = DockerUtils.build_docker_cmd(base_cmd, options, positional_args)
            assert result == ["docker", "run", "-i", "-t", "ubuntu"]

        def test_build_with_long_options(self):
            """Test building command with long options."""
            base_cmd = ["docker", "run"]
            options = {"name": "my-container", "rm": None}
            positional_args = ["ubuntu"]
            
            result = DockerUtils.build_docker_cmd(base_cmd, options, positional_args)
            assert result == ["docker", "run", "--name", "my-container", "--rm", "ubuntu"]

        def test_build_with_mixed_options(self):
            """Test building command with mixed short and long options."""
            base_cmd = ["docker", "run"]
            options = {"i": None, "name": "test", "v": "/host:/container"}
            positional_args = ["ubuntu", "bash"]
            
            result = DockerUtils.build_docker_cmd(base_cmd, options, positional_args)
            assert result == ["docker", "run", "-i", "--name", "test", "-v", "/host:/container", "ubuntu", "bash"]

        def test_build_with_numeric_values(self):
            """Test building command with numeric option values."""
            base_cmd = ["docker", "run"]
            options = {"p": 8080, "memory": 512}
            positional_args = ["nginx"]
            
            result = DockerUtils.build_docker_cmd(base_cmd, options, positional_args)
            assert result == ["docker", "run", "-p", "8080", "--memory", "512", "nginx"]

        def test_build_preserves_base_cmd(self):
            """Test that original base_cmd is not modified."""
            base_cmd = ["docker", "run"]
            original_base_cmd = base_cmd.copy()
            options = {"name": "test"}
            positional_args = ["ubuntu"]
            
            DockerUtils.build_docker_cmd(base_cmd, options, positional_args)
            assert base_cmd == original_base_cmd

    class TestParseImageTag:
        """Test cases for parse_image_tag method."""

        def test_parse_with_tag(self):
            """Test parsing image with tag."""
            image, tag = DockerUtils.parse_image_tag("ubuntu:20.04")
            assert image == "ubuntu"
            assert tag == "20.04"

        def test_parse_without_tag(self):
            """Test parsing image without tag."""
            image, tag = DockerUtils.parse_image_tag("ubuntu")
            assert image == "ubuntu"
            assert tag is None

        def test_parse_with_registry(self):
            """Test parsing image with registry."""
            image, tag = DockerUtils.parse_image_tag("docker.io/library/ubuntu:latest")
            assert image == "docker.io/library/ubuntu"
            assert tag == "latest"

        def test_parse_with_port_in_registry(self):
            """Test parsing image with port in registry."""
            image, tag = DockerUtils.parse_image_tag("localhost:5000/myimage:v1.0")
            assert image == "localhost"
            assert tag == "5000/myimage:v1.0"

        def test_parse_with_multiple_colons(self):
            """Test parsing handles only first colon as separator."""
            image, tag = DockerUtils.parse_image_tag("registry:5000/image:tag:extra")
            assert image == "registry"
            assert tag == "5000/image:tag:extra"

        def test_parse_empty_tag(self):
            """Test parsing image with empty tag."""
            image, tag = DockerUtils.parse_image_tag("ubuntu:")
            assert image == "ubuntu"
            assert tag == ""

    class TestFormatContainerName:
        """Test cases for format_container_name method."""

        def test_format_valid_name(self):
            """Test formatting already valid container name."""
            result = DockerUtils.format_container_name("my-container_123")
            assert result == "my-container_123"

        def test_format_name_starting_with_letter(self):
            """Test name starting with letter remains unchanged."""
            result = DockerUtils.format_container_name("container123")
            assert result == "container123"

        def test_format_name_starting_with_number(self):
            """Test name starting with number gets prefix."""
            result = DockerUtils.format_container_name("123container")
            assert result == "container_123container"

        def test_format_name_starting_with_hyphen(self):
            """Test name starting with hyphen gets prefix."""
            result = DockerUtils.format_container_name("-mycontainer")
            assert result == "container_-mycontainer"

        def test_format_name_with_invalid_chars_raises_error(self):
            """Test name with invalid characters raises error."""
            with pytest.raises(ValueError, match="Invalid character"):
                DockerUtils.format_container_name("my container")
            
            with pytest.raises(ValueError, match="Invalid character"):
                DockerUtils.format_container_name("my@container")
            
            with pytest.raises(ValueError, match="Invalid character"):
                DockerUtils.format_container_name("my.container")

        def test_format_empty_name_raises_error(self):
            """Test empty name raises error."""
            with pytest.raises(ValueError, match="Container name cannot be empty"):
                DockerUtils.format_container_name("")

        def test_format_all_invalid_chars_raises_error(self):
            """Test name with all invalid characters raises error."""
            with pytest.raises(ValueError, match="Invalid character"):
                DockerUtils.format_container_name("@#$%")

    class TestValidateImageName:
        """Test cases for validate_image_name method."""

        def test_validate_simple_image(self):
            """Test validating simple image name."""
            assert DockerUtils.validate_image_name("ubuntu") is True
            assert DockerUtils.validate_image_name("nginx") is True

        def test_validate_with_tag(self):
            """Test validating image with tag."""
            assert DockerUtils.validate_image_name("ubuntu:20.04") is True
            assert DockerUtils.validate_image_name("python:3.9-slim") is True

        def test_validate_with_registry(self):
            """Test validating image with registry."""
            assert DockerUtils.validate_image_name("docker.io/library/ubuntu") is True
            assert DockerUtils.validate_image_name("localhost:5000/myimage") is True

        def test_validate_empty_image(self):
            """Test validating empty image name."""
            assert DockerUtils.validate_image_name("") is False

        def test_validate_too_long_image(self):
            """Test validating image name that's too long."""
            long_name = "a" * 129
            assert DockerUtils.validate_image_name(long_name) is False

        def test_validate_with_spaces(self):
            """Test validating image name with spaces."""
            assert DockerUtils.validate_image_name("ubuntu latest") is False

        def test_validate_with_special_chars(self):
            """Test validating image name with special characters."""
            assert DockerUtils.validate_image_name("ubuntu@latest") is False
            assert DockerUtils.validate_image_name("ubuntu#latest") is False
            assert DockerUtils.validate_image_name("ubuntu$latest") is False

        def test_validate_with_allowed_special_chars(self):
            """Test validating image name with allowed special characters."""
            assert DockerUtils.validate_image_name("my_image") is True
            assert DockerUtils.validate_image_name("my-image") is True
            assert DockerUtils.validate_image_name("my.image") is True


class TestValidateDockerImageName:
    """Test cases for backward compatibility function."""

    def test_validate_simple_image(self):
        """Test validating simple image name."""
        assert validate_docker_image_name("ubuntu") is True

    def test_validate_invalid_image(self):
        """Test validating invalid image name."""
        assert validate_docker_image_name("ubuntu latest") is False

    def test_validate_empty_image(self):
        """Test validating empty image name."""
        assert validate_docker_image_name("") is False
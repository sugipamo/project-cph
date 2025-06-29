"""Tests for Docker path operations."""
import pytest
from src.utils.docker_path_ops import DockerPathOperations


class TestDockerPathOperations:
    """Test cases for DockerPathOperations class."""

    class TestShouldBuildCustomDockerImage:
        """Test cases for should_build_custom_docker_image method."""

        def test_custom_ojtools_image(self):
            """Test ojtools prefixed images should be built."""
            assert DockerPathOperations.should_build_custom_docker_image("ojtools") is True
            assert DockerPathOperations.should_build_custom_docker_image("ojtools-python") is True
            assert DockerPathOperations.should_build_custom_docker_image("ojtools:latest") is True

        def test_custom_cph_image(self):
            """Test cph_ prefixed images should be built."""
            assert DockerPathOperations.should_build_custom_docker_image("cph_") is True
            assert DockerPathOperations.should_build_custom_docker_image("cph_python") is True
            assert DockerPathOperations.should_build_custom_docker_image("cph_rust:v1") is True

        def test_registry_images_not_built(self):
            """Test registry images should not be built."""
            assert DockerPathOperations.should_build_custom_docker_image("docker.io/library/python") is False
            assert DockerPathOperations.should_build_custom_docker_image("gcr.io/project/image") is False
            assert DockerPathOperations.should_build_custom_docker_image("quay.io/org/image") is False
            assert DockerPathOperations.should_build_custom_docker_image("ghcr.io/owner/image") is False
            assert DockerPathOperations.should_build_custom_docker_image("registry.hub.docker.com/library/ubuntu") is False

        def test_custom_registry_not_built(self):
            """Test custom registry URLs should not be built."""
            assert DockerPathOperations.should_build_custom_docker_image("myregistry.com/image") is False
            assert DockerPathOperations.should_build_custom_docker_image("192.168.1.1:5000/image") is False

        def test_standard_images_with_tag_not_built(self):
            """Test standard images with tag should not be built."""
            assert DockerPathOperations.should_build_custom_docker_image("python:3.9") is False
            assert DockerPathOperations.should_build_custom_docker_image("ubuntu:20.04") is False
            assert DockerPathOperations.should_build_custom_docker_image("alpine:latest") is False

        def test_simple_image_names_depend_on_content(self):
            """Test simple image names behavior."""
            # Simple names without special chars should not be built
            assert DockerPathOperations.should_build_custom_docker_image("python") is False
            assert DockerPathOperations.should_build_custom_docker_image("ubuntu") is False
            
            # Names with / should be built (unless they're registry images)
            assert DockerPathOperations.should_build_custom_docker_image("user/image") is True
            
            # Images with @ and : (digest format) should not be built
            assert DockerPathOperations.should_build_custom_docker_image("image@sha256:abc123") is False
            
            # Images with @ but no : should be built
            assert DockerPathOperations.should_build_custom_docker_image("image@latest") is True

    class TestConvertPathToDockerMount:
        """Test cases for convert_path_to_docker_mount method."""

        def test_convert_workspace_reference(self):
            """Test converting ./workspace reference."""
            result = DockerPathOperations.convert_path_to_docker_mount(
                "./workspace",
                "/home/user/workspace",
                "/docker/mount"
            )
            assert result == "/docker/mount"

        def test_convert_exact_workspace_path(self):
            """Test converting exact workspace path."""
            result = DockerPathOperations.convert_path_to_docker_mount(
                "/home/user/workspace",
                "/home/user/workspace",
                "/docker/mount"
            )
            assert result == "/docker/mount"

        def test_convert_path_containing_workspace(self):
            """Test converting path containing workspace."""
            result = DockerPathOperations.convert_path_to_docker_mount(
                "/home/user/workspace/subfolder/file.txt",
                "/home/user/workspace",
                "/docker/mount"
            )
            assert result == "/docker/mount/subfolder/file.txt"

        def test_path_not_containing_workspace(self):
            """Test path not containing workspace remains unchanged."""
            result = DockerPathOperations.convert_path_to_docker_mount(
                "/other/path/file.txt",
                "/home/user/workspace",
                "/docker/mount"
            )
            assert result == "/other/path/file.txt"

        def test_relative_path_not_workspace(self):
            """Test relative path that's not ./workspace."""
            result = DockerPathOperations.convert_path_to_docker_mount(
                "./subfolder/file.txt",
                "/home/user/workspace",
                "/docker/mount"
            )
            assert result == "./subfolder/file.txt"

        def test_workspace_in_middle_of_path(self):
            """Test workspace appearing in middle of path."""
            result = DockerPathOperations.convert_path_to_docker_mount(
                "/prefix/home/user/workspace/suffix",
                "/home/user/workspace",
                "/mount"
            )
            assert result == "/prefix/mount/suffix"

    class TestGetDockerMountPathFromConfig:
        """Test cases for get_docker_mount_path_from_config method."""

        def test_language_specific_mount_path(self):
            """Test getting language-specific mount path."""
            env_json = {
                "python": {"mount_path": "/python/workspace"},
                "rust": {"mount_path": "/rust/workspace"}
            }
            result = DockerPathOperations.get_docker_mount_path_from_config(
                env_json, "python", "/default"
            )
            assert result == "/python/workspace"

        def test_global_mount_path(self):
            """Test getting global mount path when no language-specific path."""
            env_json = {
                "mount_path": "/global/workspace",
                "python": {"version": "3.9"}
            }
            result = DockerPathOperations.get_docker_mount_path_from_config(
                env_json, "python", "/default"
            )
            assert result == "/global/workspace"

        def test_default_mount_path(self):
            """Test default mount path when nothing configured."""
            env_json = {
                "python": {"version": "3.9"}
            }
            result = DockerPathOperations.get_docker_mount_path_from_config(
                env_json, "python", "/default"
            )
            assert result == "/default"

        def test_empty_config(self):
            """Test empty config returns default."""
            result = DockerPathOperations.get_docker_mount_path_from_config(
                {}, "python", "/default"
            )
            assert result == "/default"

        def test_none_config(self):
            """Test None config returns default."""
            result = DockerPathOperations.get_docker_mount_path_from_config(
                None, "python", "/default"
            )
            assert result == "/default"

        def test_language_not_in_config(self):
            """Test language not in config falls back to global or default."""
            env_json = {
                "mount_path": "/global",
                "python": {"mount_path": "/python"}
            }
            result = DockerPathOperations.get_docker_mount_path_from_config(
                env_json, "rust", "/default"
            )
            assert result == "/global"

        def test_language_config_not_dict(self):
            """Test language config that's not a dict."""
            env_json = {
                "python": "not-a-dict",
                "mount_path": "/global"
            }
            result = DockerPathOperations.get_docker_mount_path_from_config(
                env_json, "python", "/default"
            )
            assert result == "/global"

        def test_default_mount_path_when_not_provided(self):
            """Test default mount path value when not provided."""
            env_json = {"python": {"version": "3.9"}}
            result = DockerPathOperations.get_docker_mount_path_from_config(
                env_json, "python"
            )
            assert result == "/workspace"  # Default value in function signature
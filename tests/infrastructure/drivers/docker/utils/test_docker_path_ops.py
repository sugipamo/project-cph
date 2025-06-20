"""Tests for DockerPathOperations"""

import pytest

from src.infrastructure.drivers.docker.utils.docker_path_ops import DockerPathOperations


class TestDockerPathOperations:
    """Tests for DockerPathOperations class"""

    def test_should_build_custom_docker_image_ojtools_prefix(self):
        """Test should_build_custom_docker_image returns True for ojtools prefix"""
        assert DockerPathOperations.should_build_custom_docker_image("ojtools/cpp") is True
        assert DockerPathOperations.should_build_custom_docker_image("ojtools-dev:latest") is True

    def test_should_build_custom_docker_image_cph_prefix(self):
        """Test should_build_custom_docker_image returns True for cph_ prefix"""
        assert DockerPathOperations.should_build_custom_docker_image("cph_python:3.9") is True
        assert DockerPathOperations.should_build_custom_docker_image("cph_dev") is True

    def test_should_build_custom_docker_image_registry_urls(self):
        """Test should_build_custom_docker_image returns False for registry URLs"""
        registry_images = [
            "docker.io/library/python:3.9",
            "gcr.io/project/image:latest",
            "registry.hub.docker.com/library/ubuntu",
            "quay.io/user/repo:tag",
            "ghcr.io/owner/image:latest"
        ]

        for image in registry_images:
            assert DockerPathOperations.should_build_custom_docker_image(image) is False

    def test_should_build_custom_docker_image_registry_with_dots(self):
        """Test should_build_custom_docker_image returns False for registry URLs with dots"""
        assert DockerPathOperations.should_build_custom_docker_image("my.registry.com/image:tag") is False
        assert DockerPathOperations.should_build_custom_docker_image("example.org/namespace/image") is False

    def test_should_build_custom_docker_image_standard_images(self):
        """Test should_build_custom_docker_image returns False for standard images"""
        standard_images = [
            "python:3.9",
            "ubuntu:20.04",
            "alpine:latest",
            "node:16"
        ]

        for image in standard_images:
            assert DockerPathOperations.should_build_custom_docker_image(image) is False

    def test_should_build_custom_docker_image_simple_names(self):
        """Test should_build_custom_docker_image returns False for simple names"""
        assert DockerPathOperations.should_build_custom_docker_image("python") is False
        assert DockerPathOperations.should_build_custom_docker_image("ubuntu") is False
        assert DockerPathOperations.should_build_custom_docker_image("alpine") is False

    def test_should_build_custom_docker_image_with_slash(self):
        """Test should_build_custom_docker_image returns True for names with slash but not registry"""
        assert DockerPathOperations.should_build_custom_docker_image("user/custom-image") is True
        assert DockerPathOperations.should_build_custom_docker_image("namespace/project") is True

    def test_should_build_custom_docker_image_with_at_symbol(self):
        """Test should_build_custom_docker_image returns True for names with @ symbol (without colon)"""
        assert DockerPathOperations.should_build_custom_docker_image("custom@digest") is True
        assert DockerPathOperations.should_build_custom_docker_image("myimage@sha256abcd") is True

    def test_should_build_custom_docker_image_at_symbol_with_colon(self):
        """Test should_build_custom_docker_image returns False for @ with colon (standard format)"""
        assert DockerPathOperations.should_build_custom_docker_image("image@sha256:abc123") is False

    def test_convert_path_to_docker_mount_workspace_exact_match(self):
        """Test convert_path_to_docker_mount with exact workspace path match"""
        result = DockerPathOperations.convert_path_to_docker_mount(
            "./workspace", "/host/workspace", "/container/workspace"
        )
        assert result == "/container/workspace"

    def test_convert_path_to_docker_mount_workspace_host_path_match(self):
        """Test convert_path_to_docker_mount with host workspace path match"""
        result = DockerPathOperations.convert_path_to_docker_mount(
            "/host/workspace", "/host/workspace", "/container/workspace"
        )
        assert result == "/container/workspace"

    def test_convert_path_to_docker_mount_subpath_replacement(self):
        """Test convert_path_to_docker_mount with subpath replacement"""
        result = DockerPathOperations.convert_path_to_docker_mount(
            "/host/workspace/subdir", "/host/workspace", "/container/workspace"
        )
        assert result == "/container/workspace/subdir"

    def test_convert_path_to_docker_mount_no_replacement(self):
        """Test convert_path_to_docker_mount returns original path when no match"""
        result = DockerPathOperations.convert_path_to_docker_mount(
            "/other/path", "/host/workspace", "/container/workspace"
        )
        assert result == "/other/path"

    def test_convert_path_to_docker_mount_partial_match_replacement(self):
        """Test convert_path_to_docker_mount replaces partial matches (current behavior)"""
        result = DockerPathOperations.convert_path_to_docker_mount(
            "/host/workspace-other", "/host/workspace", "/container/workspace"
        )
        assert result == "/container/workspace-other"

    def test_get_docker_mount_path_from_config_empty_config(self):
        """Test get_docker_mount_path_from_config with empty config"""
        result = DockerPathOperations.get_docker_mount_path_from_config({}, "python")
        assert result == "/workspace"

    def test_get_docker_mount_path_from_config_none_config(self):
        """Test get_docker_mount_path_from_config with None config"""
        result = DockerPathOperations.get_docker_mount_path_from_config(None, "python")
        assert result == "/workspace"

    def test_get_docker_mount_path_from_config_custom_default(self):
        """Test get_docker_mount_path_from_config with custom default"""
        result = DockerPathOperations.get_docker_mount_path_from_config(
            {}, "python", "/custom/workspace"
        )
        assert result == "/custom/workspace"

    def test_get_docker_mount_path_from_config_language_specific(self):
        """Test get_docker_mount_path_from_config with language-specific config"""
        config = {
            "python": {
                "mount_path": "/app/python"
            }
        }
        result = DockerPathOperations.get_docker_mount_path_from_config(config, "python")
        assert result == "/app/python"

    def test_get_docker_mount_path_from_config_language_not_dict(self):
        """Test get_docker_mount_path_from_config when language config is not dict"""
        config = {
            "python": "simple_string"
        }
        result = DockerPathOperations.get_docker_mount_path_from_config(config, "python")
        assert result == "/workspace"

    def test_get_docker_mount_path_from_config_language_no_mount_path(self):
        """Test get_docker_mount_path_from_config when language config has no mount_path"""
        config = {
            "python": {
                "other_setting": "value"
            }
        }
        result = DockerPathOperations.get_docker_mount_path_from_config(config, "python")
        assert result == "/workspace"

    def test_get_docker_mount_path_from_config_global_mount_path(self):
        """Test get_docker_mount_path_from_config with global mount_path"""
        config = {
            "mount_path": "/global/workspace"
        }
        result = DockerPathOperations.get_docker_mount_path_from_config(config, "python")
        assert result == "/global/workspace"

    def test_get_docker_mount_path_from_config_language_overrides_global(self):
        """Test get_docker_mount_path_from_config where language config overrides global"""
        config = {
            "mount_path": "/global/workspace",
            "python": {
                "mount_path": "/python/workspace"
            }
        }
        result = DockerPathOperations.get_docker_mount_path_from_config(config, "python")
        assert result == "/python/workspace"

    def test_get_docker_mount_path_from_config_nonexistent_language(self):
        """Test get_docker_mount_path_from_config with nonexistent language falls back to global"""
        config = {
            "mount_path": "/global/workspace",
            "java": {
                "mount_path": "/java/workspace"
            }
        }
        result = DockerPathOperations.get_docker_mount_path_from_config(config, "python")
        assert result == "/global/workspace"

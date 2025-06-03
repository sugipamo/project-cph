"""
Tests for Docker path utilities pure functions
"""
import pytest
from src.pure_functions.docker_path_utils_pure import (
    convert_path_to_docker_mount,
    get_docker_mount_path_from_config,
    wrap_command_with_cwd,
    validate_mount_path,
    should_build_custom_docker_image
)


class TestConvertPathToDockerMount:
    """Test path conversion between host and Docker"""
    
    def test_exact_workspace_path(self):
        """Test conversion of exact workspace path"""
        result = convert_path_to_docker_mount("./workspace", "./workspace", "/app")
        assert result == "/app"
        
    def test_workspace_path_without_dot(self):
        """Test conversion of workspace path without dot"""
        result = convert_path_to_docker_mount("/home/user/workspace", "/home/user/workspace", "/app")
        assert result == "/app"
        
    def test_path_containing_workspace(self):
        """Test conversion of path containing workspace"""
        result = convert_path_to_docker_mount("./workspace/test", "./workspace", "/app")
        assert result == "/app/test"
        
    def test_path_not_containing_workspace(self):
        """Test path that doesn't contain workspace"""
        result = convert_path_to_docker_mount("/other/path", "./workspace", "/app")
        assert result == "/other/path"
        
    def test_complex_path_replacement(self):
        """Test complex path replacement"""
        result = convert_path_to_docker_mount(
            "/home/user/workspace/subdir/file",
            "/home/user/workspace",
            "/container/mount"
        )
        assert result == "/container/mount/subdir/file"


class TestGetDockerMountPathFromConfig:
    """Test Docker mount path extraction from config"""
    
    def test_valid_config_with_mount_path(self):
        """Test extraction from valid config"""
        config = {
            "python": {
                "env_types": {
                    "docker": {
                        "mount_path": "/custom/path"
                    }
                }
            }
        }
        result = get_docker_mount_path_from_config(config, "python", "/default")
        assert result == "/custom/path"
        
    def test_missing_mount_path(self):
        """Test with missing mount_path key"""
        config = {
            "python": {
                "env_types": {
                    "docker": {}
                }
            }
        }
        result = get_docker_mount_path_from_config(config, "python", "/default")
        assert result == "/default"
        
    def test_missing_language(self):
        """Test with missing language key"""
        config = {"ruby": {}}
        result = get_docker_mount_path_from_config(config, "python", "/default")
        assert result == "/default"
        
    def test_empty_config(self):
        """Test with empty config"""
        result = get_docker_mount_path_from_config({}, "python", "/default")
        assert result == "/default"
        
    def test_none_config(self):
        """Test with None config"""
        result = get_docker_mount_path_from_config(None, "python", "/default")
        assert result == "/default"


class TestWrapCommandWithCwd:
    """Test command wrapping with cd directive"""
    
    def test_no_cwd(self):
        """Test command without cwd"""
        result = wrap_command_with_cwd("echo hello", None, None, "/app")
        assert result == "echo hello"
        
    def test_simple_cwd(self):
        """Test command with simple cwd"""
        result = wrap_command_with_cwd("echo hello", "/app/test", None, "/app")
        assert result == "bash -c 'cd /app/test && echo hello'"
        
    def test_workspace_cwd_conversion(self):
        """Test command with workspace cwd"""
        result = wrap_command_with_cwd(
            "python main.py",
            "./workspace",
            "./workspace",
            "/app"
        )
        assert result == "bash -c 'cd /app && python main.py'"
        
    def test_complex_command_escaping(self):
        """Test complex command with quotes"""
        result = wrap_command_with_cwd(
            "oj download 'https://example.com'",
            "/app",
            None,
            "/app"
        )
        assert result == "bash -c 'cd /app && oj download 'https://example.com''"


class TestValidateMountPath:
    """Test Docker mount path validation"""
    
    def test_valid_paths(self):
        """Test valid mount paths"""
        valid_paths = [
            "/app",
            "/workspace",
            "/",
            "/usr/local/app",
            "/var/lib/docker/volumes"
        ]
        for path in valid_paths:
            is_valid, error = validate_mount_path(path)
            assert is_valid is True
            assert error is None
            
    def test_empty_path(self):
        """Test empty path"""
        is_valid, error = validate_mount_path("")
        assert is_valid is False
        assert "empty" in error
        
    def test_relative_path(self):
        """Test relative path"""
        is_valid, error = validate_mount_path("app/data")
        assert is_valid is False
        assert "absolute" in error
        
    def test_trailing_slash(self):
        """Test path with trailing slash"""
        is_valid, error = validate_mount_path("/app/")
        assert is_valid is False
        assert "end with /" in error
        
    def test_path_with_dots(self):
        """Test path with parent directory reference"""
        is_valid, error = validate_mount_path("/app/../data")
        assert is_valid is False
        assert ".." in error
        
    def test_path_with_spaces(self):
        """Test path with spaces"""
        is_valid, error = validate_mount_path("/app data")
        assert is_valid is False
        assert " " in str(error)


class TestShouldBuildCustomDockerImage:
    """Test Docker image build determination"""
    
    def test_ojtools_images(self):
        """Test OJ tools images"""
        assert should_build_custom_docker_image("ojtools") is True
        assert should_build_custom_docker_image("ojtools_abc123") is True
        assert should_build_custom_docker_image("ojtools:latest") is True
        
    def test_cph_images(self):
        """Test CPH prefixed images"""
        assert should_build_custom_docker_image("cph_python") is True
        assert should_build_custom_docker_image("cph_rust_builder") is True
        
    def test_standard_images(self):
        """Test standard registry images"""
        assert should_build_custom_docker_image("python:3.9") is False
        assert should_build_custom_docker_image("ubuntu:20.04") is False
        assert should_build_custom_docker_image("alpine") is False
        assert should_build_custom_docker_image("node") is False
        
    def test_registry_images(self):
        """Test images with registry prefix"""
        assert should_build_custom_docker_image("docker.io/python:3.9") is False
        assert should_build_custom_docker_image("gcr.io/project/image") is False
        
    def test_custom_non_cph_images(self):
        """Test custom images without CPH prefix"""
        assert should_build_custom_docker_image("myapp/custom") is True
        assert should_build_custom_docker_image("company/app/image") is True
        
    def test_sha_referenced_images(self):
        """Test images referenced by SHA256"""
        assert should_build_custom_docker_image("image@sha256:abc") is False
        assert should_build_custom_docker_image("ubuntu@sha256:abc123") is False
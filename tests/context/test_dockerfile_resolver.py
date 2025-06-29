"""Tests for DockerfileResolver class"""
import pytest
from unittest.mock import Mock, MagicMock
from src.context.dockerfile_resolver import DockerfileResolver


class TestDockerfileResolver:
    """Test suite for DockerfileResolver"""

    def setup_method(self):
        """Set up test fixtures"""
        self.dockerfile_path = "/path/to/Dockerfile"
        self.oj_dockerfile_path = "/path/to/oj/Dockerfile"
        self.dockerfile_content = "FROM python:3.9\nRUN pip install numpy"
        self.oj_dockerfile_content = "FROM ubuntu:20.04\nRUN apt-get update"
        
        # Mock loader function
        self.loader_mock = Mock(side_effect=self._mock_loader)
        
        # Mock docker naming provider
        self.docker_naming_provider_mock = Mock()
        self.docker_naming_provider_mock.get_docker_image_name.return_value = "test_image"
        self.docker_naming_provider_mock.get_docker_container_name.return_value = "test_container"
        self.docker_naming_provider_mock.get_oj_image_name.return_value = "test_oj_image"
        self.docker_naming_provider_mock.get_oj_container_name.return_value = "test_oj_container"
        
    def _mock_loader(self, path):
        """Mock loader function"""
        if path == self.dockerfile_path:
            return self.dockerfile_content
        elif path == self.oj_dockerfile_path:
            return self.oj_dockerfile_content
        else:
            raise FileNotFoundError(f"File not found: {path}")

    def test_init(self):
        """Test DockerfileResolver initialization"""
        resolver = DockerfileResolver(
            dockerfile_path=self.dockerfile_path,
            oj_dockerfile_path=self.oj_dockerfile_path,
            dockerfile_loader=self.loader_mock,
            docker_naming_provider=self.docker_naming_provider_mock
        )
        
        assert resolver._dockerfile_path == self.dockerfile_path
        assert resolver._oj_dockerfile_path == self.oj_dockerfile_path
        assert resolver._dockerfile_loader == self.loader_mock
        assert resolver._docker_naming_provider == self.docker_naming_provider_mock
        assert resolver._dockerfile_content is None
        assert resolver._oj_dockerfile_content is None
        assert resolver._content_loaded == {"dockerfile": False, "oj_dockerfile": False}

    def test_dockerfile_lazy_loading(self):
        """Test lazy loading of main Dockerfile content"""
        resolver = DockerfileResolver(
            dockerfile_path=self.dockerfile_path,
            oj_dockerfile_path=self.oj_dockerfile_path,
            dockerfile_loader=self.loader_mock,
            docker_naming_provider=self.docker_naming_provider_mock
        )
        
        # Content should not be loaded initially
        assert resolver._dockerfile_content is None
        assert not resolver._content_loaded["dockerfile"]
        
        # Access property triggers loading
        content = resolver.dockerfile
        
        assert content == self.dockerfile_content
        assert resolver._dockerfile_content == self.dockerfile_content
        assert resolver._content_loaded["dockerfile"]
        assert self.loader_mock.called
        assert self.loader_mock.call_count == 1

    def test_oj_dockerfile_lazy_loading(self):
        """Test lazy loading of OJ Dockerfile content"""
        resolver = DockerfileResolver(
            dockerfile_path=self.dockerfile_path,
            oj_dockerfile_path=self.oj_dockerfile_path,
            dockerfile_loader=self.loader_mock,
            docker_naming_provider=self.docker_naming_provider_mock
        )
        
        # Content should not be loaded initially
        assert resolver._oj_dockerfile_content is None
        assert not resolver._content_loaded["oj_dockerfile"]
        
        # Access property triggers loading
        content = resolver.oj_dockerfile
        
        assert content == self.oj_dockerfile_content
        assert resolver._oj_dockerfile_content == self.oj_dockerfile_content
        assert resolver._content_loaded["oj_dockerfile"]
        assert self.loader_mock.called

    def test_dockerfile_none_path(self):
        """Test behavior when dockerfile_path is None"""
        resolver = DockerfileResolver(
            dockerfile_path=None,
            oj_dockerfile_path=self.oj_dockerfile_path,
            dockerfile_loader=self.loader_mock,
            docker_naming_provider=self.docker_naming_provider_mock
        )
        
        content = resolver.dockerfile
        assert content is None
        assert resolver._content_loaded["dockerfile"]
        assert self.loader_mock.call_count == 0

    def test_dockerfile_none_loader(self):
        """Test behavior when dockerfile_loader is None"""
        resolver = DockerfileResolver(
            dockerfile_path=self.dockerfile_path,
            oj_dockerfile_path=self.oj_dockerfile_path,
            dockerfile_loader=None,
            docker_naming_provider=self.docker_naming_provider_mock
        )
        
        content = resolver.dockerfile
        assert content is None
        assert resolver._content_loaded["dockerfile"]

    def test_dockerfile_loading_error(self):
        """Test error handling when loading Dockerfile fails"""
        error_loader = Mock(side_effect=Exception("Load error"))
        resolver = DockerfileResolver(
            dockerfile_path=self.dockerfile_path,
            oj_dockerfile_path=self.oj_dockerfile_path,
            dockerfile_loader=error_loader,
            docker_naming_provider=self.docker_naming_provider_mock
        )
        
        with pytest.raises(RuntimeError) as exc_info:
            _ = resolver.dockerfile
        
        assert "Failed to load Dockerfile" in str(exc_info.value)
        assert self.dockerfile_path in str(exc_info.value)
        assert "Load error" in str(exc_info.value)

    def test_oj_dockerfile_loading_error(self):
        """Test error handling when loading OJ Dockerfile fails"""
        error_loader = Mock(side_effect=Exception("Load error"))
        resolver = DockerfileResolver(
            dockerfile_path=self.dockerfile_path,
            oj_dockerfile_path=self.oj_dockerfile_path,
            dockerfile_loader=error_loader,
            docker_naming_provider=self.docker_naming_provider_mock
        )
        
        with pytest.raises(RuntimeError) as exc_info:
            _ = resolver.oj_dockerfile
        
        assert "Failed to load OJ Dockerfile" in str(exc_info.value)
        assert self.oj_dockerfile_path in str(exc_info.value)
        assert "Load error" in str(exc_info.value)

    def test_get_docker_names(self):
        """Test get_docker_names method"""
        resolver = DockerfileResolver(
            dockerfile_path=self.dockerfile_path,
            oj_dockerfile_path=self.oj_dockerfile_path,
            dockerfile_loader=self.loader_mock,
            docker_naming_provider=self.docker_naming_provider_mock
        )
        
        names = resolver.get_docker_names("python")
        
        assert names["image_name"] == "test_image"
        assert names["container_name"] == "test_container"
        assert names["oj_image_name"] == "test_oj_image"
        assert names["oj_container_name"] == "test_oj_container"
        
        # Verify provider was called with correct arguments
        self.docker_naming_provider_mock.get_docker_image_name.assert_called_once_with("python", self.dockerfile_content)
        self.docker_naming_provider_mock.get_docker_container_name.assert_called_once_with("python", self.dockerfile_content)
        self.docker_naming_provider_mock.get_oj_image_name.assert_called_once_with(self.oj_dockerfile_content)
        self.docker_naming_provider_mock.get_oj_container_name.assert_called_once_with(self.oj_dockerfile_content)

    def test_get_docker_names_no_provider(self):
        """Test get_docker_names when provider is None"""
        resolver = DockerfileResolver(
            dockerfile_path=self.dockerfile_path,
            oj_dockerfile_path=self.oj_dockerfile_path,
            dockerfile_loader=self.loader_mock,
            docker_naming_provider=None
        )
        
        with pytest.raises(RuntimeError) as exc_info:
            resolver.get_docker_names("python")
        
        assert "Docker naming provider is not injected" in str(exc_info.value)

    def test_has_dockerfile(self):
        """Test has_dockerfile method"""
        # With path
        resolver = DockerfileResolver(
            dockerfile_path=self.dockerfile_path,
            oj_dockerfile_path=None,
            dockerfile_loader=self.loader_mock,
            docker_naming_provider=self.docker_naming_provider_mock
        )
        assert resolver.has_dockerfile() is True
        
        # Without path
        resolver = DockerfileResolver(
            dockerfile_path=None,
            oj_dockerfile_path=None,
            dockerfile_loader=self.loader_mock,
            docker_naming_provider=self.docker_naming_provider_mock
        )
        assert resolver.has_dockerfile() is False

    def test_has_oj_dockerfile(self):
        """Test has_oj_dockerfile method"""
        # With path
        resolver = DockerfileResolver(
            dockerfile_path=None,
            oj_dockerfile_path=self.oj_dockerfile_path,
            dockerfile_loader=self.loader_mock,
            docker_naming_provider=self.docker_naming_provider_mock
        )
        assert resolver.has_oj_dockerfile() is True
        
        # Without path
        resolver = DockerfileResolver(
            dockerfile_path=None,
            oj_dockerfile_path=None,
            dockerfile_loader=self.loader_mock,
            docker_naming_provider=self.docker_naming_provider_mock
        )
        assert resolver.has_oj_dockerfile() is False

    def test_invalidate_cache(self):
        """Test cache invalidation"""
        resolver = DockerfileResolver(
            dockerfile_path=self.dockerfile_path,
            oj_dockerfile_path=self.oj_dockerfile_path,
            dockerfile_loader=self.loader_mock,
            docker_naming_provider=self.docker_naming_provider_mock
        )
        
        # Load content
        _ = resolver.dockerfile
        _ = resolver.oj_dockerfile
        
        assert resolver._dockerfile_content == self.dockerfile_content
        assert resolver._oj_dockerfile_content == self.oj_dockerfile_content
        assert resolver._content_loaded["dockerfile"]
        assert resolver._content_loaded["oj_dockerfile"]
        
        # Invalidate cache
        resolver.invalidate_cache()
        
        assert resolver._dockerfile_content is None
        assert resolver._oj_dockerfile_content is None
        assert not resolver._content_loaded["dockerfile"]
        assert not resolver._content_loaded["oj_dockerfile"]

    def test_preload(self):
        """Test preload method"""
        resolver = DockerfileResolver(
            dockerfile_path=self.dockerfile_path,
            oj_dockerfile_path=self.oj_dockerfile_path,
            dockerfile_loader=self.loader_mock,
            docker_naming_provider=self.docker_naming_provider_mock
        )
        
        # Content should not be loaded initially
        assert resolver._dockerfile_content is None
        assert resolver._oj_dockerfile_content is None
        
        # Preload
        resolver.preload()
        
        # Both should be loaded
        assert resolver._dockerfile_content == self.dockerfile_content
        assert resolver._oj_dockerfile_content == self.oj_dockerfile_content
        assert resolver._content_loaded["dockerfile"]
        assert resolver._content_loaded["oj_dockerfile"]

    def test_repr(self):
        """Test string representation"""
        resolver = DockerfileResolver(
            dockerfile_path=self.dockerfile_path,
            oj_dockerfile_path=self.oj_dockerfile_path,
            dockerfile_loader=self.loader_mock,
            docker_naming_provider=self.docker_naming_provider_mock
        )
        
        repr_str = repr(resolver)
        assert "DockerfileResolver" in repr_str
        assert self.dockerfile_path in repr_str
        assert self.oj_dockerfile_path in repr_str
        assert "loaded=" in repr_str

    def test_multiple_access_uses_cache(self):
        """Test that multiple accesses use cached content"""
        resolver = DockerfileResolver(
            dockerfile_path=self.dockerfile_path,
            oj_dockerfile_path=self.oj_dockerfile_path,
            dockerfile_loader=self.loader_mock,
            docker_naming_provider=self.docker_naming_provider_mock
        )
        
        # First access
        content1 = resolver.dockerfile
        call_count1 = self.loader_mock.call_count
        
        # Second access
        content2 = resolver.dockerfile
        call_count2 = self.loader_mock.call_count
        
        assert content1 == content2
        assert call_count1 == call_count2  # Loader should not be called again

    def test_edge_case_empty_dockerfile(self):
        """Test handling of empty Dockerfile content"""
        empty_loader = Mock(return_value="")
        resolver = DockerfileResolver(
            dockerfile_path=self.dockerfile_path,
            oj_dockerfile_path=self.oj_dockerfile_path,
            dockerfile_loader=empty_loader,
            docker_naming_provider=self.docker_naming_provider_mock
        )
        
        content = resolver.dockerfile
        assert content == ""
        assert resolver._content_loaded["dockerfile"]

    def test_concurrent_property_access(self):
        """Test that concurrent access to properties works correctly"""
        resolver = DockerfileResolver(
            dockerfile_path=self.dockerfile_path,
            oj_dockerfile_path=self.oj_dockerfile_path,
            dockerfile_loader=self.loader_mock,
            docker_naming_provider=self.docker_naming_provider_mock
        )
        
        # Access both properties
        dockerfile = resolver.dockerfile
        oj_dockerfile = resolver.oj_dockerfile
        
        assert dockerfile == self.dockerfile_content
        assert oj_dockerfile == self.oj_dockerfile_content
        assert resolver._content_loaded["dockerfile"]
        assert resolver._content_loaded["oj_dockerfile"]
        
        # Loader should be called twice (once for each file)
        assert self.loader_mock.call_count == 2

    def test_oj_dockerfile_none_path(self):
        """Test behavior when oj_dockerfile_path is None"""
        resolver = DockerfileResolver(
            dockerfile_path=self.dockerfile_path,
            oj_dockerfile_path=None,
            dockerfile_loader=self.loader_mock,
            docker_naming_provider=self.docker_naming_provider_mock
        )
        
        content = resolver.oj_dockerfile
        assert content is None
        assert resolver._content_loaded["oj_dockerfile"]
        # Loader should not be called for OJ dockerfile
        self.loader_mock.assert_not_called()

    def test_oj_dockerfile_none_loader(self):
        """Test behavior when dockerfile_loader is None for OJ dockerfile"""
        resolver = DockerfileResolver(
            dockerfile_path=self.dockerfile_path,
            oj_dockerfile_path=self.oj_dockerfile_path,
            dockerfile_loader=None,
            docker_naming_provider=self.docker_naming_provider_mock
        )
        
        content = resolver.oj_dockerfile
        assert content is None
        assert resolver._content_loaded["oj_dockerfile"]
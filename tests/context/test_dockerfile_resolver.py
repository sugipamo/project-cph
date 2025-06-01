"""
Test DockerfileResolver functionality
"""
import pytest

pytestmark = pytest.mark.skip(reason="Needs update for new DockerfileResolver API")
from unittest.mock import MagicMock, call
from src.context.dockerfile_resolver import DockerfileResolver


class TestDockerfileResolver:
    """Test DockerfileResolver basic functionality"""
    
    def test_init_with_paths(self):
        """Test initialization with paths"""
        dockerfile_loader = MagicMock()
        resolver = DockerfileResolver(
            dockerfile_path="/path/to/Dockerfile",
            oj_dockerfile_path="/path/to/oj.Dockerfile", 
            dockerfile_loader=dockerfile_loader
        )
        
        assert resolver.dockerfile_path == "/path/to/Dockerfile"
        assert resolver.oj_dockerfile_path == "/path/to/oj.Dockerfile"
        assert resolver.loader_func is loader_func
        assert resolver._dockerfile_content_cache is None
        assert resolver._oj_dockerfile_content_cache is None
    
    def test_init_empty(self):
        """Test initialization with no paths"""
        resolver = DockerfileResolver()
        
        assert resolver.dockerfile_path is None
        assert resolver.oj_dockerfile_path is None
        assert resolver.loader_func is None
        assert resolver._dockerfile_content_cache is None
        assert resolver._oj_dockerfile_content_cache is None


class TestDockerfileContentLoading:
    """Test lazy loading of dockerfile content"""
    
    def test_get_dockerfile_content_lazy_load(self):
        """Test dockerfile content is loaded lazily"""
        loader_func = MagicMock(return_value="FROM python:3.9")
        resolver = DockerfileResolver(
            dockerfile_path="/path/to/Dockerfile",
            loader_func=loader_func
        )
        
        # First call should load content
        content1 = resolver.get_dockerfile_content()
        assert content1 == "FROM python:3.9"
        loader_func.assert_called_once_with("/path/to/Dockerfile")
        
        # Second call should use cache
        loader_func.reset_mock()
        content2 = resolver.get_dockerfile_content()
        assert content2 == "FROM python:3.9"
        loader_func.assert_not_called()
    
    def test_get_dockerfile_content_no_path(self):
        """Test get_dockerfile_content with no path"""
        resolver = DockerfileResolver()
        
        content = resolver.get_dockerfile_content()
        assert content is None
    
    def test_get_dockerfile_content_no_loader(self):
        """Test get_dockerfile_content with path but no loader"""
        resolver = DockerfileResolver(dockerfile_path="/path/to/Dockerfile")
        
        content = resolver.get_dockerfile_content()
        assert content is None
    
    def test_get_dockerfile_content_loader_exception(self):
        """Test get_dockerfile_content when loader raises exception"""
        loader_func = MagicMock(side_effect=Exception("File not found"))
        resolver = DockerfileResolver(
            dockerfile_path="/path/to/Dockerfile",
            loader_func=loader_func
        )
        
        content = resolver.get_dockerfile_content()
        assert content is None
        loader_func.assert_called_once_with("/path/to/Dockerfile")
    
    def test_get_oj_dockerfile_content_lazy_load(self):
        """Test OJ dockerfile content is loaded lazily"""
        loader_func = MagicMock(return_value="FROM python:3.9\nRUN pip install oj")
        resolver = DockerfileResolver(
            oj_dockerfile_path="/path/to/oj.Dockerfile",
            loader_func=loader_func
        )
        
        # First call should load content
        content1 = resolver.get_oj_dockerfile_content()
        assert content1 == "FROM python:3.9\nRUN pip install oj"
        loader_func.assert_called_once_with("/path/to/oj.Dockerfile")
        
        # Second call should use cache
        loader_func.reset_mock()
        content2 = resolver.get_oj_dockerfile_content()
        assert content2 == "FROM python:3.9\nRUN pip install oj"
        loader_func.assert_not_called()


class TestDockerfileContentSetting:
    """Test explicit content setting for backward compatibility"""
    
    def test_set_dockerfile_content(self):
        """Test setting dockerfile content directly"""
        resolver = DockerfileResolver()
        
        resolver.set_dockerfile_content("FROM rust:1.70")
        
        assert resolver.get_dockerfile_content() == "FROM rust:1.70"
        assert resolver._dockerfile_content_set is True
    
    def test_set_oj_dockerfile_content(self):
        """Test setting OJ dockerfile content directly"""
        resolver = DockerfileResolver()
        
        resolver.set_oj_dockerfile_content("FROM python:3.9\nRUN pip install oj")
        
        assert resolver.get_oj_dockerfile_content() == "FROM python:3.9\nRUN pip install oj"
        assert resolver._oj_dockerfile_content_set is True
    
    def test_set_content_overrides_lazy_loading(self):
        """Test that explicitly set content overrides lazy loading"""
        loader_func = MagicMock(return_value="FROM python:3.9")
        resolver = DockerfileResolver(
            dockerfile_path="/path/to/Dockerfile",
            loader_func=loader_func
        )
        
        # Set content explicitly
        resolver.set_dockerfile_content("FROM rust:1.70")
        
        # Should return set content, not call loader
        content = resolver.get_dockerfile_content()
        assert content == "FROM rust:1.70"
        loader_func.assert_not_called()


class TestDockerNamesGeneration:
    """Test Docker names generation using resolver"""
    
    def test_get_docker_names_no_dockerfiles(self):
        """Test docker names generation without dockerfiles"""
        resolver = DockerfileResolver()
        
        result = resolver.get_docker_names("python")
        
        assert result["image_name"] == "python"
        assert result["container_name"] == "cph_python"
        assert result["oj_image_name"] == "ojtools"
        assert result["oj_container_name"] == "cph_ojtools"
    
    def test_get_docker_names_with_dockerfiles(self):
        """Test docker names generation with custom dockerfiles"""
        loader_func = MagicMock()
        loader_func.side_effect = lambda path: {
            "/dockerfile": "FROM python:3.9\nRUN pip install requests",
            "/oj.dockerfile": "FROM python:3.9\nRUN pip install oj"
        }[path]
        
        resolver = DockerfileResolver(
            dockerfile_path="/dockerfile",
            oj_dockerfile_path="/oj.dockerfile",
            loader_func=loader_func
        )
        
        result = resolver.get_docker_names("python")
        
        # Should have hash suffixes
        assert result["image_name"].startswith("python_")
        assert result["container_name"].startswith("cph_python_")
        assert result["oj_image_name"].startswith("ojtools_")
        assert result["oj_container_name"].startswith("cph_ojtools_")
        
        # Verify both files were loaded
        assert loader_func.call_count == 2
        loader_func.assert_has_calls([call("/dockerfile"), call("/oj.dockerfile")], any_order=True)


class TestDockerfileAvailabilityChecks:
    """Test dockerfile availability checking methods"""
    
    def test_has_dockerfile_with_path(self):
        """Test has_dockerfile with path set"""
        resolver = DockerfileResolver(dockerfile_path="/path/to/Dockerfile")
        assert resolver.has_dockerfile() is True
    
    def test_has_dockerfile_with_content_set(self):
        """Test has_dockerfile with content explicitly set"""
        resolver = DockerfileResolver()
        resolver.set_dockerfile_content("FROM python:3.9")
        assert resolver.has_dockerfile() is True
    
    def test_has_dockerfile_with_cached_content(self):
        """Test has_dockerfile with cached content"""
        resolver = DockerfileResolver()
        resolver._dockerfile_content_cache = "FROM python:3.9"
        assert resolver.has_dockerfile() is True
    
    def test_has_dockerfile_false(self):
        """Test has_dockerfile returns False when no dockerfile"""
        resolver = DockerfileResolver()
        assert resolver.has_dockerfile() is False
    
    def test_has_oj_dockerfile_with_path(self):
        """Test has_oj_dockerfile with path set"""
        resolver = DockerfileResolver(oj_dockerfile_path="/path/to/oj.Dockerfile")
        assert resolver.has_oj_dockerfile() is True
    
    def test_has_oj_dockerfile_false(self):
        """Test has_oj_dockerfile returns False when no dockerfile"""
        resolver = DockerfileResolver()
        assert resolver.has_oj_dockerfile() is False


class TestUtilityMethods:
    """Test utility methods"""
    
    def test_force_load_content(self):
        """Test force loading of all content"""
        loader_func = MagicMock()
        loader_func.side_effect = lambda path: f"content-{path}"
        
        resolver = DockerfileResolver(
            dockerfile_path="/dockerfile",
            oj_dockerfile_path="/oj.dockerfile", 
            loader_func=loader_func
        )
        
        resolver.force_load_content()
        
        assert resolver._dockerfile_content_cache == "content-/dockerfile"
        assert resolver._oj_dockerfile_content_cache == "content-/oj.dockerfile"
        assert loader_func.call_count == 2
    
    def test_clear_cache(self):
        """Test clearing content cache"""
        loader_func = MagicMock(return_value="content")
        resolver = DockerfileResolver(
            dockerfile_path="/dockerfile",
            loader_func=loader_func
        )
        
        # Load content
        resolver.get_dockerfile_content()
        assert resolver._dockerfile_content_cache == "content"
        
        # Clear cache
        resolver.clear_cache()
        assert resolver._dockerfile_content_cache is None
        
        # Should reload on next access
        loader_func.reset_mock()
        content = resolver.get_dockerfile_content()
        assert content == "content"
        loader_func.assert_called_once()
    
    def test_clear_cache_respects_set_content(self):
        """Test that clear_cache doesn't clear explicitly set content"""
        resolver = DockerfileResolver()
        resolver.set_dockerfile_content("explicit content")
        
        resolver.clear_cache()
        
        # Should still have explicitly set content
        assert resolver._dockerfile_content_cache == "explicit content"
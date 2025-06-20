"""Tests for DockerfileResolver class."""
from unittest.mock import Mock, patch

import pytest

from src.context.dockerfile_resolver import DockerfileResolver


class TestDockerfileResolver:
    """Test cases for DockerfileResolver class."""

    def test_init_default_values(self):
        """Test DockerfileResolver initialization with default values."""
        resolver = DockerfileResolver()

        assert resolver._dockerfile_path is None
        assert resolver._oj_dockerfile_path is None
        assert resolver._dockerfile_loader is None
        assert resolver._dockerfile_content is None
        assert resolver._oj_dockerfile_content is None
        assert resolver._content_loaded == {"dockerfile": False, "oj_dockerfile": False}

    def test_init_with_values(self):
        """Test DockerfileResolver initialization with custom values."""
        mock_loader = Mock()
        resolver = DockerfileResolver(
            dockerfile_path="/path/to/dockerfile",
            oj_dockerfile_path="/path/to/oj_dockerfile",
            dockerfile_loader=mock_loader
        )

        assert resolver._dockerfile_path == "/path/to/dockerfile"
        assert resolver._oj_dockerfile_path == "/path/to/oj_dockerfile"
        assert resolver._dockerfile_loader == mock_loader

    def test_dockerfile_property_lazy_loading(self):
        """Test dockerfile property lazy loading mechanism."""
        mock_loader = Mock(return_value="dockerfile content")
        resolver = DockerfileResolver(
            dockerfile_path="/path/to/dockerfile",
            dockerfile_loader=mock_loader
        )

        # First access should trigger loading
        content = resolver.dockerfile

        assert content == "dockerfile content"
        mock_loader.assert_called_once_with("/path/to/dockerfile")
        assert resolver._content_loaded["dockerfile"] is True

        # Second access should use cached value
        content2 = resolver.dockerfile
        assert content2 == "dockerfile content"
        # Should still be called only once
        assert mock_loader.call_count == 1

    def test_dockerfile_property_no_path(self):
        """Test dockerfile property when no path is provided."""
        resolver = DockerfileResolver()

        content = resolver.dockerfile

        assert content is None
        assert resolver._content_loaded["dockerfile"] is True

    def test_dockerfile_property_no_loader(self):
        """Test dockerfile property when no loader is provided."""
        resolver = DockerfileResolver(dockerfile_path="/path/to/dockerfile")

        content = resolver.dockerfile

        assert content is None
        assert resolver._content_loaded["dockerfile"] is True

    def test_dockerfile_property_loader_exception(self):
        """Test dockerfile property when loader raises exception."""
        mock_loader = Mock(side_effect=Exception("File not found"))
        resolver = DockerfileResolver(
            dockerfile_path="/path/to/dockerfile",
            dockerfile_loader=mock_loader
        )

        content = resolver.dockerfile

        assert content is None
        assert resolver._content_loaded["dockerfile"] is True
        mock_loader.assert_called_once_with("/path/to/dockerfile")

    def test_oj_dockerfile_property_lazy_loading(self):
        """Test oj_dockerfile property lazy loading mechanism."""
        mock_loader = Mock(return_value="oj dockerfile content")
        resolver = DockerfileResolver(
            oj_dockerfile_path="/path/to/oj_dockerfile",
            dockerfile_loader=mock_loader
        )

        # First access should trigger loading
        content = resolver.oj_dockerfile

        assert content == "oj dockerfile content"
        mock_loader.assert_called_once_with("/path/to/oj_dockerfile")
        assert resolver._content_loaded["oj_dockerfile"] is True

        # Second access should use cached value
        content2 = resolver.oj_dockerfile
        assert content2 == "oj dockerfile content"
        assert mock_loader.call_count == 1

    def test_oj_dockerfile_property_no_path(self):
        """Test oj_dockerfile property when no path is provided."""
        resolver = DockerfileResolver()

        content = resolver.oj_dockerfile

        assert content is None
        assert resolver._content_loaded["oj_dockerfile"] is True

    def test_oj_dockerfile_property_no_loader(self):
        """Test oj_dockerfile property when no loader is provided."""
        resolver = DockerfileResolver(oj_dockerfile_path="/path/to/oj_dockerfile")

        content = resolver.oj_dockerfile

        assert content is None
        assert resolver._content_loaded["oj_dockerfile"] is True

    def test_oj_dockerfile_property_loader_exception(self):
        """Test oj_dockerfile property when loader raises exception."""
        mock_loader = Mock(side_effect=Exception("File not found"))
        resolver = DockerfileResolver(
            oj_dockerfile_path="/path/to/oj_dockerfile",
            dockerfile_loader=mock_loader
        )

        content = resolver.oj_dockerfile

        assert content is None
        assert resolver._content_loaded["oj_dockerfile"] is True
        mock_loader.assert_called_once_with("/path/to/oj_dockerfile")

    @patch('src.context.dockerfile_resolver.get_docker_image_name')
    @patch('src.context.dockerfile_resolver.get_docker_container_name')
    @patch('src.context.dockerfile_resolver.get_oj_image_name')
    @patch('src.context.dockerfile_resolver.get_oj_container_name')
    def test_get_docker_names(self, mock_oj_container, mock_oj_image, mock_container, mock_image):
        """Test get_docker_names method."""
        mock_image.return_value = "test_image"
        mock_container.return_value = "test_container"
        mock_oj_image.return_value = "oj_test_image"
        mock_oj_container.return_value = "oj_test_container"

        mock_loader = Mock(side_effect=["dockerfile content", "oj dockerfile content"])
        resolver = DockerfileResolver(
            dockerfile_path="/path/to/dockerfile",
            oj_dockerfile_path="/path/to/oj_dockerfile",
            dockerfile_loader=mock_loader
        )

        names = resolver.get_docker_names("python")

        expected_names = {
            "image_name": "test_image",
            "container_name": "test_container",
            "oj_image_name": "oj_test_image",
            "oj_container_name": "oj_test_container"
        }

        assert names == expected_names
        mock_image.assert_called_once_with("python", "dockerfile content")
        mock_container.assert_called_once_with("python", "dockerfile content")
        mock_oj_image.assert_called_once_with("oj dockerfile content")
        mock_oj_container.assert_called_once_with("oj dockerfile content")

    @patch('src.context.dockerfile_resolver.get_docker_image_name')
    @patch('src.context.dockerfile_resolver.get_docker_container_name')
    @patch('src.context.dockerfile_resolver.get_oj_image_name')
    @patch('src.context.dockerfile_resolver.get_oj_container_name')
    def test_get_docker_names_with_none_content(self, mock_oj_container, mock_oj_image, mock_container, mock_image):
        """Test get_docker_names method with None content."""
        mock_image.return_value = "test_image"
        mock_container.return_value = "test_container"
        mock_oj_image.return_value = "oj_test_image"
        mock_oj_container.return_value = "oj_test_container"

        resolver = DockerfileResolver()  # No paths or loader

        names = resolver.get_docker_names("python")

        expected_names = {
            "image_name": "test_image",
            "container_name": "test_container",
            "oj_image_name": "oj_test_image",
            "oj_container_name": "oj_test_container"
        }

        assert names == expected_names
        mock_image.assert_called_once_with("python", None)
        mock_container.assert_called_once_with("python", None)
        mock_oj_image.assert_called_once_with(None)
        mock_oj_container.assert_called_once_with(None)

    def test_invalidate_cache(self):
        """Test invalidate_cache method."""
        mock_loader = Mock(return_value="content")
        resolver = DockerfileResolver(
            dockerfile_path="/path/to/dockerfile",
            oj_dockerfile_path="/path/to/oj_dockerfile",
            dockerfile_loader=mock_loader
        )

        # Load content
        _ = resolver.dockerfile
        _ = resolver.oj_dockerfile

        assert resolver._content_loaded["dockerfile"] is True
        assert resolver._content_loaded["oj_dockerfile"] is True
        assert resolver._dockerfile_content == "content"
        assert resolver._oj_dockerfile_content == "content"

        # Invalidate cache
        resolver.invalidate_cache()

        assert resolver._content_loaded["dockerfile"] is False
        assert resolver._content_loaded["oj_dockerfile"] is False
        assert resolver._dockerfile_content is None
        assert resolver._oj_dockerfile_content is None

    def test_has_dockerfile_true(self):
        """Test has_dockerfile method when path exists."""
        resolver = DockerfileResolver(dockerfile_path="/path/to/dockerfile")

        assert resolver.has_dockerfile() is True

    def test_has_dockerfile_false(self):
        """Test has_dockerfile method when path is None."""
        resolver = DockerfileResolver()

        assert resolver.has_dockerfile() is False

    def test_has_oj_dockerfile_true(self):
        """Test has_oj_dockerfile method when path exists."""
        resolver = DockerfileResolver(oj_dockerfile_path="/path/to/oj_dockerfile")

        assert resolver.has_oj_dockerfile() is True

    def test_has_oj_dockerfile_false(self):
        """Test has_oj_dockerfile method when path is None."""
        resolver = DockerfileResolver()

        assert resolver.has_oj_dockerfile() is False

    def test_preload(self):
        """Test preload method."""
        mock_loader = Mock(side_effect=["dockerfile content", "oj dockerfile content"])
        resolver = DockerfileResolver(
            dockerfile_path="/path/to/dockerfile",
            oj_dockerfile_path="/path/to/oj_dockerfile",
            dockerfile_loader=mock_loader
        )

        # Initially not loaded
        assert resolver._content_loaded["dockerfile"] is False
        assert resolver._content_loaded["oj_dockerfile"] is False

        # Preload
        resolver.preload()

        # Should be loaded now
        assert resolver._content_loaded["dockerfile"] is True
        assert resolver._content_loaded["oj_dockerfile"] is True
        assert resolver._dockerfile_content == "dockerfile content"
        assert resolver._oj_dockerfile_content == "oj dockerfile content"

    def test_preload_partial_paths(self):
        """Test preload method with partial paths."""
        mock_loader = Mock(return_value="dockerfile content")
        resolver = DockerfileResolver(
            dockerfile_path="/path/to/dockerfile",
            # oj_dockerfile_path not set
            dockerfile_loader=mock_loader
        )

        resolver.preload()

        assert resolver._content_loaded["dockerfile"] is True
        assert resolver._content_loaded["oj_dockerfile"] is True
        assert resolver._dockerfile_content == "dockerfile content"
        assert resolver._oj_dockerfile_content is None

    def test_repr(self):
        """Test __repr__ method."""
        resolver = DockerfileResolver(
            dockerfile_path="/path/to/dockerfile",
            oj_dockerfile_path="/path/to/oj_dockerfile"
        )

        repr_str = repr(resolver)

        assert "DockerfileResolver" in repr_str
        assert "/path/to/dockerfile" in repr_str
        assert "/path/to/oj_dockerfile" in repr_str
        assert "loaded={'dockerfile': False, 'oj_dockerfile': False}" in repr_str

    def test_repr_after_loading(self):
        """Test __repr__ method after content is loaded."""
        mock_loader = Mock(return_value="content")
        resolver = DockerfileResolver(
            dockerfile_path="/path/to/dockerfile",
            dockerfile_loader=mock_loader
        )

        # Load content
        _ = resolver.dockerfile

        repr_str = repr(resolver)

        assert "loaded={'dockerfile': True, 'oj_dockerfile': False}" in repr_str

    def test_multiple_load_calls(self):
        """Test that multiple property accesses don't cause redundant loading."""
        call_count = 0

        def mock_loader(path):
            nonlocal call_count
            call_count += 1
            return f"content_{call_count}"

        resolver = DockerfileResolver(
            dockerfile_path="/path/to/dockerfile",
            oj_dockerfile_path="/path/to/oj_dockerfile",
            dockerfile_loader=mock_loader
        )

        # Multiple accesses should only load once each
        content1 = resolver.dockerfile
        content2 = resolver.dockerfile
        content3 = resolver.oj_dockerfile
        content4 = resolver.oj_dockerfile

        assert content1 == "content_1"
        assert content2 == "content_1"  # Same as first call
        assert content3 == "content_2"
        assert content4 == "content_2"  # Same as third call
        assert call_count == 2  # Only called twice total

    def test_load_dockerfile_content_method(self):
        """Test _load_dockerfile_content method directly."""
        mock_loader = Mock(return_value="dockerfile content")
        resolver = DockerfileResolver(
            dockerfile_path="/path/to/dockerfile",
            dockerfile_loader=mock_loader
        )

        # Method should be private, but test it for completeness
        resolver._load_dockerfile_content()

        assert resolver._content_loaded["dockerfile"] is True
        assert resolver._dockerfile_content == "dockerfile content"
        mock_loader.assert_called_once_with("/path/to/dockerfile")

    def test_load_oj_dockerfile_content_method(self):
        """Test _load_oj_dockerfile_content method directly."""
        mock_loader = Mock(return_value="oj dockerfile content")
        resolver = DockerfileResolver(
            oj_dockerfile_path="/path/to/oj_dockerfile",
            dockerfile_loader=mock_loader
        )

        # Method should be private, but test it for completeness
        resolver._load_oj_dockerfile_content()

        assert resolver._content_loaded["oj_dockerfile"] is True
        assert resolver._oj_dockerfile_content == "oj dockerfile content"
        mock_loader.assert_called_once_with("/path/to/oj_dockerfile")

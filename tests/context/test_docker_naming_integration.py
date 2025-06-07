"""
Test Docker naming integration with ExecutionContext
"""
from unittest.mock import MagicMock

import pytest


class TestDockerNamingIntegration:
    """Test Docker naming integration with ExecutionContext"""

    def test_get_docker_names_without_dockerfile(self):
        """Test get_docker_names without custom dockerfile"""
        # Create mock context
        context = MagicMock()
        context.language = "python"
        context._dockerfile_resolver = None

        # Add the method to the mock
        from src.context.execution_context import ExecutionContext
        real_method = ExecutionContext.get_docker_names
        context.get_docker_names = lambda: real_method(context)

        result = context.get_docker_names()

        assert result["image_name"] == "python"
        assert result["container_name"] == "cph_python"
        assert result["oj_image_name"] == "ojtools"
        assert result["oj_container_name"] == "cph_ojtools"

    def test_get_docker_names_with_dockerfile(self):
        """Test get_docker_names with custom dockerfile"""
        # Create mock context
        context = MagicMock()
        context.language = "rust"
        context._dockerfile_resolver = None  # No resolver (fallback mode)

        # Mock dockerfile_resolver to return content
        mock_resolver = MagicMock()
        mock_resolver.dockerfile = "FROM rust:1.70\nRUN cargo install --version"
        mock_resolver.oj_dockerfile = "FROM python:3.9\nRUN pip install online-judge-tools"
        context._dockerfile_resolver = mock_resolver

        # Add the method to the mock
        from src.context.execution_context import ExecutionContext
        real_method = ExecutionContext.get_docker_names
        context.get_docker_names = lambda: real_method(context)

        result = context.get_docker_names()

        # Image names should have hash suffixes, container names should be fixed
        assert result["image_name"].startswith("rust_")
        assert result["container_name"] == "cph_rust"  # Fixed container name
        assert result["oj_image_name"].startswith("ojtools_")
        assert result["oj_container_name"] == "cph_ojtools"  # Fixed container name

    def test_get_docker_names_empty_dockerfile(self):
        """Test get_docker_names with empty dockerfile"""
        # Create mock context
        context = MagicMock()
        context.language = "python"

        # Mock dockerfile_resolver to return empty content
        mock_resolver = MagicMock()
        mock_resolver.dockerfile = ""
        mock_resolver.oj_dockerfile = "   "
        context._dockerfile_resolver = mock_resolver

        # Add the method to the mock
        from src.context.execution_context import ExecutionContext
        real_method = ExecutionContext.get_docker_names
        context.get_docker_names = lambda: real_method(context)

        result = context.get_docker_names()

        # Should use base names without hash
        assert result["image_name"] == "python"
        assert result["container_name"] == "cph_python"
        assert result["oj_image_name"] == "ojtools"
        assert result["oj_container_name"] == "cph_ojtools"

"""
Test Docker naming integration with ExecutionContextAdapter
"""
from unittest.mock import MagicMock

import pytest
from src.configuration.integration.user_input_parser_integration import create_new_execution_context


class TestDockerNamingIntegration:
    """Test Docker naming integration with ExecutionContextAdapter"""

    def test_get_docker_names_without_dockerfile(self):
        """Test get_docker_names without custom dockerfile"""
        # Create new system context
        context = create_new_execution_context(
            command_type="test",
            language="python",
            contest_name="test_contest",
            problem_name="a",
            env_type="local",
            env_json={"python": {"test": "value"}}
        )

        result = context.get_docker_names()

        assert result["image_name"] == "python"
        assert result["container_name"] == "cph_python"
        assert result["oj_image_name"] == "ojtools"
        assert result["oj_container_name"] == "cph_ojtools"

    def test_get_docker_names_with_dockerfile(self):
        """Test get_docker_names with custom dockerfile"""
        # Create new system context
        context = create_new_execution_context(
            command_type="test",
            language="rust",
            contest_name="test_contest",
            problem_name="a",
            env_type="local",
            env_json={"rust": {"test": "value"}}
        )

        # Mock dockerfile_resolver to return content
        mock_resolver = MagicMock()
        mock_resolver.dockerfile = "FROM rust:1.70\nRUN cargo install --version"
        mock_resolver.oj_dockerfile = "FROM python:3.9\nRUN pip install online-judge-tools"
        context.dockerfile_resolver = mock_resolver

        result = context.get_docker_names()

        # Image names should have hash suffixes, container names should be fixed
        assert result["image_name"].startswith("rust_")
        assert result["container_name"] == "cph_rust"  # Fixed container name
        assert result["oj_image_name"].startswith("ojtools_")
        assert result["oj_container_name"] == "cph_ojtools"  # Fixed container name

    def test_get_docker_names_empty_dockerfile(self):
        """Test get_docker_names with empty dockerfile"""
        # Create new system context
        context = create_new_execution_context(
            command_type="test",
            language="python",
            contest_name="test_contest",
            problem_name="a",
            env_type="local",
            env_json={"python": {"test": "value"}}
        )

        # Mock dockerfile_resolver to return empty content
        mock_resolver = MagicMock()
        mock_resolver.dockerfile = ""
        mock_resolver.oj_dockerfile = "   "
        context.dockerfile_resolver = mock_resolver

        result = context.get_docker_names()

        # Should use base names without hash
        assert result["image_name"] == "python"
        assert result["container_name"] == "cph_python"
        assert result["oj_image_name"] == "ojtools"
        assert result["oj_container_name"] == "cph_ojtools"

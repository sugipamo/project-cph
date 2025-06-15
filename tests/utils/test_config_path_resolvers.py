"""Tests for configuration path resolvers."""
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.context.resolver.config_resolver import ConfigNode
from src.utils.config_path_resolvers import (
    get_contest_current_path,
    get_contest_env_path,
    get_contest_temp_path,
    get_contest_template_path,
    get_source_file_name,
    get_test_case_in_path,
    get_test_case_out_path,
    get_test_case_path,
    get_workspace_path,
)


class TestPathResolvers:
    """Test path resolver functions."""

    def create_mock_config_node(self, key: str, value: str):
        """Helper to create mock ConfigNode."""
        node = Mock(spec=ConfigNode)
        node.key = key
        node.value = value
        return node

    @patch('src.utils.config_path_resolvers.resolve_best')
    def test_get_workspace_path_language_specific(self, mock_resolve_best):
        # First call returns the language-specific path
        mock_resolve_best.return_value = self.create_mock_config_node("workspace_path", "/home/user/workspace")

        resolver = Mock(spec=ConfigNode)
        result = get_workspace_path(resolver, "python")

        assert result == Path("/home/user/workspace")
        # Should try language-specific path first
        assert mock_resolve_best.call_args_list[0][0][1] == ["python", "paths", "workspace_path"]

    @patch('src.utils.config_path_resolvers.resolve_best')
    def test_get_workspace_path_fallback_to_shared(self, mock_resolve_best):
        # First two calls return None, third returns shared path
        mock_resolve_best.side_effect = [
            None,
            None,
            self.create_mock_config_node("workspace_path", "/shared/workspace")
        ]

        resolver = Mock(spec=ConfigNode)
        result = get_workspace_path(resolver, "python")

        assert result == Path("/shared/workspace")
        assert mock_resolve_best.call_count == 3

    @patch('src.utils.config_path_resolvers.resolve_best')
    def test_get_workspace_path_not_found(self, mock_resolve_best):
        mock_resolve_best.return_value = None

        resolver = Mock(spec=ConfigNode)
        with pytest.raises(TypeError, match="workspace_pathが設定されていません"):
            get_workspace_path(resolver, "python")

    @patch('src.utils.config_path_resolvers.resolve_best')
    def test_get_contest_current_path(self, mock_resolve_best):
        mock_resolve_best.return_value = self.create_mock_config_node("contest_current_path", "/contest/current")

        resolver = Mock(spec=ConfigNode)
        result = get_contest_current_path(resolver, "cpp")

        assert result == Path("/contest/current")

    @patch('src.utils.config_path_resolvers.resolve_best')
    def test_get_contest_current_path_not_found(self, mock_resolve_best):
        mock_resolve_best.return_value = None

        resolver = Mock(spec=ConfigNode)
        with pytest.raises(TypeError, match="contest_current_pathが設定されていません"):
            get_contest_current_path(resolver, "cpp")

    def test_get_contest_env_path_found(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create contest_env directory
            contest_env_dir = Path(temp_dir) / "contest_env"
            contest_env_dir.mkdir()

            # Change to temp directory
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                result = get_contest_env_path()
                assert result == contest_env_dir
            finally:
                os.chdir(original_cwd)

    def test_get_contest_env_path_found_in_parent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create contest_env in parent
            contest_env_dir = Path(temp_dir) / "contest_env"
            contest_env_dir.mkdir()

            # Create and change to subdirectory
            sub_dir = Path(temp_dir) / "subdir"
            sub_dir.mkdir()

            original_cwd = os.getcwd()
            try:
                os.chdir(sub_dir)
                result = get_contest_env_path()
                assert result == contest_env_dir
            finally:
                os.chdir(original_cwd)

    def test_get_contest_env_path_not_found(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # No contest_env directory
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                with pytest.raises(ValueError, match="contest_env_pathが自動検出できませんでした"):
                    get_contest_env_path()
            finally:
                os.chdir(original_cwd)

    @patch('src.utils.config_path_resolvers.resolve_best')
    def test_get_contest_template_path(self, mock_resolve_best):
        mock_resolve_best.return_value = self.create_mock_config_node("contest_template_path", "/templates/contest")

        resolver = Mock(spec=ConfigNode)
        result = get_contest_template_path(resolver, "java")

        assert result == Path("/templates/contest")

    @patch('src.utils.config_path_resolvers.resolve_best')
    def test_get_contest_template_path_not_found(self, mock_resolve_best):
        mock_resolve_best.return_value = None

        resolver = Mock(spec=ConfigNode)
        with pytest.raises(TypeError, match="contest_template_pathが設定されていません"):
            get_contest_template_path(resolver, "java")

    @patch('src.utils.config_path_resolvers.resolve_best')
    def test_get_contest_temp_path(self, mock_resolve_best):
        mock_resolve_best.return_value = self.create_mock_config_node("contest_temp_path", "/tmp/contest")

        resolver = Mock(spec=ConfigNode)
        result = get_contest_temp_path(resolver, "go")

        assert result == Path("/tmp/contest")

    @patch('src.utils.config_path_resolvers.resolve_best')
    def test_get_contest_temp_path_not_found(self, mock_resolve_best):
        mock_resolve_best.return_value = None

        resolver = Mock(spec=ConfigNode)
        with pytest.raises(TypeError, match="contest_temp_pathが設定されていません"):
            get_contest_temp_path(resolver, "go")

    def test_get_test_case_path(self):
        contest_path = Path("/contest/abc123")
        result = get_test_case_path(contest_path)
        assert result == Path("/contest/abc123/test")

    def test_get_test_case_in_path(self):
        contest_path = Path("/contest/abc123")
        result = get_test_case_in_path(contest_path)
        assert result == Path("/contest/abc123/test/in")

    def test_get_test_case_out_path(self):
        contest_path = Path("/contest/abc123")
        result = get_test_case_out_path(contest_path)
        assert result == Path("/contest/abc123/test/out")

    @patch('src.utils.config_path_resolvers.resolve_best')
    def test_get_source_file_name_language_specific(self, mock_resolve_best):
        mock_resolve_best.return_value = self.create_mock_config_node("source_file_name", "main.py")

        resolver = Mock(spec=ConfigNode)
        result = get_source_file_name(resolver, "python")

        assert result == "main.py"
        assert mock_resolve_best.call_args_list[0][0][1] == ["python", "source_file_name"]

    @patch('src.utils.config_path_resolvers.resolve_best')
    def test_get_source_file_name_shared(self, mock_resolve_best):
        mock_resolve_best.side_effect = [
            None,
            self.create_mock_config_node("source_file_name", "main")
        ]

        resolver = Mock(spec=ConfigNode)
        result = get_source_file_name(resolver, "rust")

        assert result == "main"
        assert mock_resolve_best.call_count == 2

    @patch('src.utils.config_path_resolvers.resolve_best')
    def test_get_source_file_name_not_found(self, mock_resolve_best):
        mock_resolve_best.return_value = None

        resolver = Mock(spec=ConfigNode)
        with pytest.raises(ValueError, match="source_file_nameが設定されていません"):
            get_source_file_name(resolver, "kotlin")

    @patch('src.utils.config_path_resolvers.resolve_best')
    def test_resolve_best_returns_wrong_key(self, mock_resolve_best):
        # Test case where resolve_best returns a node but with wrong key
        wrong_node = Mock(spec=ConfigNode)
        wrong_node.key = "wrong_key"
        wrong_node.value = "/some/path"
        mock_resolve_best.return_value = wrong_node

        resolver = Mock(spec=ConfigNode)
        with pytest.raises(TypeError, match="workspace_pathが設定されていません"):
            get_workspace_path(resolver, "python")

    @patch('src.utils.config_path_resolvers.resolve_best')
    def test_resolve_best_returns_none_value(self, mock_resolve_best):
        # Test case where resolve_best returns a node with None value
        null_node = Mock(spec=ConfigNode)
        null_node.key = "workspace_path"
        null_node.value = None
        mock_resolve_best.return_value = null_node

        resolver = Mock(spec=ConfigNode)
        with pytest.raises(TypeError, match="workspace_pathが設定されていません"):
            get_workspace_path(resolver, "python")

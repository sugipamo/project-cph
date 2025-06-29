"""Tests for path operations utility module."""
import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path
import tempfile
import os

from src.utils.path_operations import PathOperations
from src.operations.path_types import PathOperationResult


class TestPathOperations:
    """Test cases for PathOperations class."""

    def test_init_with_config_provider(self):
        """Test initialization with config provider."""
        config_provider = Mock()
        path_ops = PathOperations(config_provider)
        assert path_ops.config_provider is config_provider

    def test_get_default_workspace_path_success(self):
        """Test getting default workspace path."""
        config_provider = Mock()
        config_provider.resolve_config.return_value = "/default/workspace"
        
        path_ops = PathOperations(config_provider)
        result = path_ops._get_default_workspace_path()
        
        assert result == "/default/workspace"
        config_provider.resolve_config.assert_called_once_with(
            ['filesystem_config', 'default_paths', 'workspace'],
            str
        )

    def test_get_default_workspace_path_no_provider(self):
        """Test getting default workspace path without provider."""
        path_ops = PathOperations(None)
        
        with pytest.raises(ValueError, match="Configuration provider is not injected"):
            path_ops._get_default_workspace_path()

    def test_get_default_workspace_path_key_error(self):
        """Test getting default workspace path with KeyError."""
        config_provider = Mock()
        config_provider.resolve_config.side_effect = KeyError("Not found")
        
        path_ops = PathOperations(config_provider)
        
        with pytest.raises(ValueError, match="No default workspace path configured"):
            path_ops._get_default_workspace_path()

    def test_resolve_path_absolute(self):
        """Test resolving absolute path."""
        path_ops = PathOperations(Mock())
        
        result = path_ops.resolve_path("/base", "/absolute/path", strict=False)
        assert result == os.path.abspath("/absolute/path")

    def test_resolve_path_relative(self):
        """Test resolving relative path."""
        path_ops = PathOperations(Mock())
        
        result = path_ops.resolve_path("/base", "relative/path", strict=False)
        expected = os.path.abspath(os.path.join("/base", "relative/path"))
        assert result == expected

    def test_resolve_path_strict_success(self):
        """Test resolving path with strict mode success."""
        path_ops = PathOperations(Mock())
        
        result = path_ops.resolve_path("/base", "relative/path", strict=True)
        
        assert isinstance(result, PathOperationResult)
        assert result.success is True
        assert result.result == os.path.abspath(os.path.join("/base", "relative/path"))
        assert result.metadata["resolution_method"] == "relative"

    def test_resolve_path_none_base_dir(self):
        """Test resolving path with None base directory."""
        path_ops = PathOperations(Mock())
        
        # Non-strict mode
        with pytest.raises(ValueError, match="Base directory cannot be None"):
            path_ops.resolve_path(None, "path", strict=False)
        
        # Strict mode
        result = path_ops.resolve_path(None, "path", strict=True)
        assert isinstance(result, PathOperationResult)
        assert result.success is False
        assert "Base directory cannot be None" in result.errors

    def test_resolve_path_empty_path(self):
        """Test resolving empty path."""
        path_ops = PathOperations(Mock())
        
        # Non-strict mode
        with pytest.raises(ValueError, match="Path cannot be empty"):
            path_ops.resolve_path("/base", "", strict=False)
        
        # Strict mode
        result = path_ops.resolve_path("/base", "", strict=True)
        assert isinstance(result, PathOperationResult)
        assert result.success is False
        assert "Path cannot be empty" in result.errors

    def test_normalize_path_success(self):
        """Test normalizing path."""
        path_ops = PathOperations(Mock())
        
        result = path_ops.normalize_path("/path/../other/./file", strict=False)
        assert result == os.path.normpath("/path/../other/./file")

    def test_normalize_path_strict(self):
        """Test normalizing path with strict mode."""
        path_ops = PathOperations(Mock())
        
        result = path_ops.normalize_path("/path/../other/./file", strict=True)
        
        assert isinstance(result, PathOperationResult)
        assert result.success is True
        assert result.result == os.path.normpath("/path/../other/./file")
        assert result.metadata["original"] == "/path/../other/./file"

    def test_normalize_path_none(self):
        """Test normalizing None path."""
        path_ops = PathOperations(Mock())
        
        with pytest.raises(ValueError, match="Path parameter cannot be None"):
            path_ops.normalize_path(None, strict=False)

    def test_safe_path_join_success(self):
        """Test safe path joining."""
        path_ops = PathOperations(Mock())
        
        result = path_ops.safe_path_join("/base", "sub", "file.txt", strict=False)
        expected = os.path.normpath(os.path.join("/base", "sub", "file.txt"))
        assert result == expected

    def test_safe_path_join_strict_with_warnings(self):
        """Test safe path joining with warnings."""
        path_ops = PathOperations(Mock())
        
        result = path_ops.safe_path_join("/base", "../dangerous", "file", strict=True)
        
        assert isinstance(result, PathOperationResult)
        assert result.success is True
        assert len(result.warnings) > 0
        assert "Potentially unsafe path component" in result.warnings[0]

    def test_safe_path_join_empty(self):
        """Test safe path joining with no paths."""
        path_ops = PathOperations(Mock())
        
        with pytest.raises(ValueError, match="At least one path must be provided"):
            path_ops.safe_path_join(strict=False)

    def test_safe_path_join_none_path(self):
        """Test safe path joining with None path."""
        path_ops = PathOperations(Mock())
        
        with pytest.raises(ValueError, match="Path at index 1 is None"):
            path_ops.safe_path_join("/base", None, "file", strict=False)

    def test_get_relative_path_success(self):
        """Test getting relative path."""
        path_ops = PathOperations(Mock())
        
        with tempfile.TemporaryDirectory() as tmpdir:
            base = os.path.join(tmpdir, "base")
            target = os.path.join(tmpdir, "base", "sub", "file.txt")
            os.makedirs(os.path.dirname(target), exist_ok=True)
            
            result = path_ops.get_relative_path(target, base, strict=False)
            assert result == os.path.join("sub", "file.txt")

    def test_get_relative_path_not_relative(self):
        """Test getting relative path when not relative."""
        path_ops = PathOperations(Mock())
        
        with pytest.raises(ValueError, match="Cannot compute relative path"):
            path_ops.get_relative_path("/other/path", "/base", strict=False)

    def test_is_subdirectory_true(self):
        """Test checking if path is subdirectory."""
        path_ops = PathOperations(Mock())
        
        result = path_ops.is_subdirectory("/parent/child", "/parent", strict=False)
        assert result is True

    def test_is_subdirectory_false(self):
        """Test checking if path is not subdirectory."""
        path_ops = PathOperations(Mock())
        
        result = path_ops.is_subdirectory("/other", "/parent", strict=False)
        assert result is False

    def test_is_subdirectory_strict(self):
        """Test checking subdirectory with strict mode."""
        path_ops = PathOperations(Mock())
        
        result, operation_result = path_ops.is_subdirectory("/parent/child", "/parent", strict=True)
        
        assert result is True
        assert isinstance(operation_result, PathOperationResult)
        assert operation_result.success is True
        assert operation_result.metadata["is_subdirectory"] is True

    def test_ensure_parent_dir(self):
        """Test ensuring parent directory exists."""
        path_ops = PathOperations(Mock())
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "new_dir", "file.txt")
            
            result = path_ops.ensure_parent_dir(file_path, strict=False)
            
            assert os.path.exists(result)
            assert result == os.path.dirname(file_path)

    def test_get_file_extension(self):
        """Test getting file extension."""
        path_ops = PathOperations(Mock())
        
        result = path_ops.get_file_extension("/path/to/file.txt", strict=False)
        assert result == ".txt"
        
        result = path_ops.get_file_extension("/path/to/file", strict=False)
        assert result == ""

    def test_get_file_extension_strict(self):
        """Test getting file extension with strict mode."""
        path_ops = PathOperations(Mock())
        
        result = path_ops.get_file_extension("/path/to/file.py", strict=True)
        
        assert isinstance(result, PathOperationResult)
        assert result.success is True
        assert result.result == ".py"
        assert result.metadata["stem"] == "file"
        assert result.metadata["name"] == "file.py"

    def test_change_extension_success(self):
        """Test changing file extension."""
        path_ops = PathOperations(Mock())
        
        result = path_ops.change_extension("/path/file.txt", ".py", strict=False)
        assert result == "/path/file.py"
        
        # Without dot prefix
        result = path_ops.change_extension("/path/file.txt", "md", strict=False)
        assert result == "/path/file.md"

    def test_change_extension_no_extension(self):
        """Test changing extension when file has no extension."""
        path_ops = PathOperations(Mock())
        
        with pytest.raises(ValueError, match="has no extension to replace"):
            path_ops.change_extension("/path/file", ".txt", strict=False)

    def test_change_extension_strict(self):
        """Test changing extension with strict mode."""
        path_ops = PathOperations(Mock())
        
        result = path_ops.change_extension("/path/file.cpp", ".h", strict=True)
        
        assert isinstance(result, PathOperationResult)
        assert result.success is True
        assert result.result == "/path/file.h"
        assert result.metadata["original_extension"] == ".cpp"
        assert result.metadata["new_extension"] == ".h"
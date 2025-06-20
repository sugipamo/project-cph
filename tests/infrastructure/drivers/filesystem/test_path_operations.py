"""Tests for PathOperations class"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.configuration.config_manager import TypeSafeConfigNodeManager
from src.infrastructure.drivers.filesystem.path_operations import PathOperations
from src.operations.types.path_types import PathOperationResult


class TestPathOperations:
    """Test PathOperations functionality"""

    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock configuration manager"""
        config_manager = Mock(spec=TypeSafeConfigNodeManager)
        config_manager.resolve_config.return_value = "/default/workspace"
        return config_manager

    @pytest.fixture
    def path_ops(self, mock_config_manager):
        """Create PathOperations instance"""
        return PathOperations(mock_config_manager)

    def test_init(self, mock_config_manager):
        """Test PathOperations initialization"""
        path_ops = PathOperations(mock_config_manager)
        assert path_ops.config_manager == mock_config_manager

    def test_get_default_workspace_path_success(self, path_ops, mock_config_manager):
        """Test successful default workspace path retrieval"""
        mock_config_manager.resolve_config.return_value = "/test/workspace"

        result = path_ops._get_default_workspace_path()

        assert result == "/test/workspace"
        mock_config_manager.resolve_config.assert_called_once_with(
            ['filesystem_config', 'default_paths', 'workspace'],
            str
        )

    def test_get_default_workspace_path_key_error(self, path_ops, mock_config_manager):
        """Test default workspace path with KeyError"""
        mock_config_manager.resolve_config.side_effect = KeyError("Config not found")

        with pytest.raises(ValueError, match="No default workspace path configured"):
            path_ops._get_default_workspace_path()

    def test_resolve_path_absolute(self, path_ops):
        """Test resolving absolute path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = temp_dir
            target_path = "/usr/bin/python"

            result = path_ops.resolve_path(base_dir, target_path)

            assert result == str(Path(target_path).resolve())

    def test_resolve_path_relative(self, path_ops):
        """Test resolving relative path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = temp_dir
            target_path = "subdir/file.txt"

            result = path_ops.resolve_path(base_dir, target_path)

            expected = str((Path(base_dir) / target_path).resolve())
            assert result == expected

    def test_resolve_path_strict_mode_success(self, path_ops):
        """Test resolve_path in strict mode with success"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = temp_dir
            target_path = "test.txt"

            result = path_ops.resolve_path(base_dir, target_path, strict=True)

            assert isinstance(result, PathOperationResult)
            assert result.success is True
            assert result.result == str((Path(base_dir) / target_path).resolve())
            assert result.errors == []

    def test_resolve_path_strict_mode_with_errors(self, path_ops):
        """Test resolve_path in strict mode with validation errors"""
        result = path_ops.resolve_path(None, "", strict=True)

        assert isinstance(result, PathOperationResult)
        assert result.success is False
        assert result.result is None
        assert len(result.errors) > 0
        assert "Base directory cannot be None" in result.errors

    def test_resolve_path_exception_handling(self, path_ops):
        """Test resolve_path exception handling"""
        with pytest.raises(ValueError):
            path_ops.resolve_path(None, "test")

    def test_normalize_path_success(self, path_ops):
        """Test successful path normalization"""
        test_path = "/path/to/../normalized/./file.txt"

        result = path_ops.normalize_path(test_path)

        expected = os.path.normpath(test_path)
        assert result == expected

    def test_normalize_path_strict_mode(self, path_ops):
        """Test normalize_path in strict mode"""
        test_path = "/path/to/../file.txt"

        result = path_ops.normalize_path(test_path, strict=True)

        assert isinstance(result, PathOperationResult)
        assert result.success is True
        assert result.result == os.path.normpath(test_path)
        assert result.metadata["original"] == test_path

    def test_normalize_path_none_error(self, path_ops):
        """Test normalize_path with None input"""
        with pytest.raises(ValueError, match="Path parameter cannot be None"):
            path_ops.normalize_path(None)

    def test_safe_path_join_success(self, path_ops):
        """Test successful path joining"""
        paths = ["dir1", "dir2", "file.txt"]

        result = path_ops.safe_path_join(*paths)

        expected = os.path.normpath(os.path.join(*paths))
        assert result == expected

    def test_safe_path_join_strict_mode(self, path_ops):
        """Test safe_path_join in strict mode"""
        paths = ["dir1", "dir2", "file.txt"]

        result = path_ops.safe_path_join(*paths, strict=True)

        assert isinstance(result, PathOperationResult)
        assert result.success is True
        assert result.result == os.path.normpath(os.path.join(*paths))
        assert result.metadata["input_paths"] == paths

    def test_safe_path_join_with_warnings(self, path_ops):
        """Test safe_path_join with unsafe paths"""
        paths = ["dir1", "../dir2", "file.txt"]

        result = path_ops.safe_path_join(*paths, strict=True)

        assert isinstance(result, PathOperationResult)
        assert result.success is True
        assert len(result.warnings) > 0
        assert "Potentially unsafe path component" in result.warnings[0]

    def test_safe_path_join_no_paths_error(self, path_ops):
        """Test safe_path_join with no paths"""
        with pytest.raises(ValueError, match="At least one path must be provided"):
            path_ops.safe_path_join()

    def test_safe_path_join_none_path_error(self, path_ops):
        """Test safe_path_join with None path"""
        with pytest.raises(ValueError, match="Path at index 0 is None"):
            path_ops.safe_path_join(None, "dir")

    def test_get_relative_path_success(self, path_ops):
        """Test successful relative path calculation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base = temp_dir
            target = os.path.join(temp_dir, "subdir", "file.txt")

            # Create the directory structure
            os.makedirs(os.path.dirname(target), exist_ok=True)

            result = path_ops.get_relative_path(target, base)

            expected = os.path.relpath(target, base)
            assert result == expected

    def test_get_relative_path_strict_mode(self, path_ops):
        """Test get_relative_path in strict mode"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base = temp_dir
            target = os.path.join(temp_dir, "file.txt")

            result = path_ops.get_relative_path(target, base, strict=True)

            assert isinstance(result, PathOperationResult)
            assert result.success is True
            assert result.result == os.path.relpath(target, base)

    def test_get_relative_path_not_relative_error(self, path_ops):
        """Test get_relative_path when paths are not related"""
        with tempfile.TemporaryDirectory() as base_dir, \
             tempfile.TemporaryDirectory() as target_dir, \
             pytest.raises(ValueError, match="Cannot compute relative path"):
            path_ops.get_relative_path(target_dir, base_dir)

    def test_is_subdirectory_true(self, path_ops):
        """Test is_subdirectory when child is subdirectory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = temp_dir
            child = os.path.join(temp_dir, "subdir")
            os.makedirs(child, exist_ok=True)

            result = path_ops.is_subdirectory(child, parent)

            assert result is True

    def test_is_subdirectory_false(self, path_ops):
        """Test is_subdirectory when child is not subdirectory"""
        with tempfile.TemporaryDirectory() as parent, tempfile.TemporaryDirectory() as child:
            result = path_ops.is_subdirectory(child, parent)

            assert result is False

    def test_is_subdirectory_strict_mode(self, path_ops):
        """Test is_subdirectory in strict mode"""
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = temp_dir
            child = os.path.join(temp_dir, "subdir")
            os.makedirs(child, exist_ok=True)

            result, operation_result = path_ops.is_subdirectory(child, parent, strict=True)

            assert result is True
            assert isinstance(operation_result, PathOperationResult)
            assert operation_result.success is True
            assert operation_result.metadata["is_subdirectory"] is True

    def test_ensure_parent_dir_creates_directory(self, path_ops):
        """Test ensure_parent_dir creates parent directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "new_dir", "file.txt")

            result = path_ops.ensure_parent_dir(file_path)

            expected_parent = os.path.dirname(file_path)
            assert result == expected_parent
            assert os.path.isdir(expected_parent)

    def test_ensure_parent_dir_existing_directory(self, path_ops):
        """Test ensure_parent_dir with existing directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "file.txt")

            result = path_ops.ensure_parent_dir(file_path)

            assert result == temp_dir

    def test_ensure_parent_dir_strict_mode(self, path_ops):
        """Test ensure_parent_dir in strict mode"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "new_dir", "file.txt")

            result = path_ops.ensure_parent_dir(file_path, strict=True)

            assert isinstance(result, PathOperationResult)
            assert result.success is True
            assert result.result == os.path.dirname(file_path)

    def test_get_file_extension_success(self, path_ops):
        """Test successful file extension retrieval"""
        file_path = "/path/to/file.txt"

        result = path_ops.get_file_extension(file_path)

        assert result == ".txt"

    def test_get_file_extension_no_extension(self, path_ops):
        """Test get_file_extension with no extension"""
        file_path = "/path/to/file"

        result = path_ops.get_file_extension(file_path)

        assert result == ""

    def test_get_file_extension_strict_mode(self, path_ops):
        """Test get_file_extension in strict mode"""
        file_path = "/path/to/file.py"

        result = path_ops.get_file_extension(file_path, strict=True)

        assert isinstance(result, PathOperationResult)
        assert result.success is True
        assert result.result == ".py"
        assert result.metadata["stem"] == "file"
        assert result.metadata["name"] == "file.py"

    def test_change_extension_success(self, path_ops):
        """Test successful extension change"""
        file_path = "/path/to/file.txt"
        new_extension = ".py"

        result = path_ops.change_extension(file_path, new_extension)

        assert result == "/path/to/file.py"

    def test_change_extension_without_dot(self, path_ops):
        """Test change_extension automatically adds dot"""
        file_path = "/path/to/file.txt"
        new_extension = "py"

        result = path_ops.change_extension(file_path, new_extension)

        assert result == "/path/to/file.py"

    def test_change_extension_no_original_extension(self, path_ops):
        """Test change_extension with file that has no extension"""
        file_path = "/path/to/file"

        with pytest.raises(ValueError, match="has no extension to replace"):
            path_ops.change_extension(file_path, ".txt")

    def test_change_extension_strict_mode(self, path_ops):
        """Test change_extension in strict mode"""
        file_path = "/path/to/file.txt"
        new_extension = ".py"

        result = path_ops.change_extension(file_path, new_extension, strict=True)

        assert isinstance(result, PathOperationResult)
        assert result.success is True
        assert result.result == "/path/to/file.py"
        assert result.metadata["original_extension"] == ".txt"
        assert result.metadata["new_extension"] == ".py"

    def test_exception_handling_in_strict_mode(self, path_ops):
        """Test exception handling in strict mode"""
        with patch('os.path.normpath') as mock_normpath:
            mock_normpath.side_effect = Exception("Test exception")

            result = path_ops.normalize_path("test", strict=True)

            assert isinstance(result, PathOperationResult)
            assert result.success is False
            assert "Test exception" in result.errors
            assert result.metadata["error_type"] == "Exception"

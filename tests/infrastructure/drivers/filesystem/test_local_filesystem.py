"""Tests for local filesystem implementation."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import pytest

from src.infrastructure.drivers.filesystem.local_filesystem import FileSystemError, LocalFileSystem


class TestLocalFileSystem:
    """Test LocalFileSystem implementation."""

    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock config manager for tests."""
        mock_config = Mock()
        mock_config.resolve_config.return_value = 'error'
        return mock_config

    def test_exists_file(self, mock_config_manager):
        fs = LocalFileSystem(mock_config_manager)
        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test")
            assert fs.exists(test_file)

    def test_exists_directory(self, mock_config_manager):
        fs = LocalFileSystem(mock_config_manager)
        with TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "test_dir"
            test_dir.mkdir()
            assert fs.exists(test_dir)

    def test_not_exists(self, mock_config_manager):
        fs = LocalFileSystem(mock_config_manager)
        with TemporaryDirectory() as temp_dir:
            non_existent = Path(temp_dir) / "non_existent.txt"
            assert not fs.exists(non_existent)

    def test_is_file(self, mock_config_manager):
        fs = LocalFileSystem(mock_config_manager)
        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test")
            assert fs.is_file(test_file)

            test_dir = Path(temp_dir) / "test_dir"
            test_dir.mkdir()
            assert not fs.is_file(test_dir)

    def test_is_dir(self, mock_config_manager):
        fs = LocalFileSystem(mock_config_manager)
        with TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "test_dir"
            test_dir.mkdir()
            assert fs.is_dir(test_dir)

            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test")
            assert not fs.is_dir(test_file)

    def test_iterdir_success(self, mock_config_manager):
        fs = LocalFileSystem(mock_config_manager)
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files and directories
            (temp_path / "file1.txt").write_text("content1")
            (temp_path / "file2.txt").write_text("content2")
            (temp_path / "subdir").mkdir()

            contents = fs.iterdir(temp_path)

            # Check that all items are returned
            assert len(contents) == 3
            names = {p.name for p in contents}
            assert names == {"file1.txt", "file2.txt", "subdir"}

    def test_iterdir_empty_directory(self, mock_config_manager):
        fs = LocalFileSystem(mock_config_manager)
        with TemporaryDirectory() as temp_dir:
            empty_dir = Path(temp_dir) / "empty"
            empty_dir.mkdir()

            contents = fs.iterdir(empty_dir)
            assert contents == []

    def test_iterdir_permission_error(self, mock_config_manager):
        fs = LocalFileSystem(mock_config_manager)
        with TemporaryDirectory():
            # Use patch to simulate PermissionError
            mock_path = Mock()
            mock_path.iterdir.side_effect = PermissionError("Access denied")

            # Should raise FileSystemError when permission denied
            with pytest.raises(FileSystemError, match="Failed to list directory contents"):
                fs.iterdir(mock_path)

    def test_iterdir_os_error(self, mock_config_manager):
        fs = LocalFileSystem(mock_config_manager)
        with TemporaryDirectory():
            # Use patch to simulate OSError
            mock_path = Mock()
            mock_path.iterdir.side_effect = OSError("IO error")

            # Should raise FileSystemError when OS error occurs
            with pytest.raises(FileSystemError, match="Failed to list directory contents"):
                fs.iterdir(mock_path)

    def test_mkdir_basic(self, mock_config_manager):
        fs = LocalFileSystem(mock_config_manager)
        with TemporaryDirectory() as temp_dir:
            new_dir = Path(temp_dir) / "new_dir"

            fs.mkdir(new_dir)
            assert new_dir.exists()
            assert new_dir.is_dir()

    def test_mkdir_with_parents(self, mock_config_manager):
        fs = LocalFileSystem(mock_config_manager)
        with TemporaryDirectory() as temp_dir:
            nested_dir = Path(temp_dir) / "parent" / "child" / "grandchild"

            # Without parents=True, this should fail
            with pytest.raises(FileNotFoundError):
                fs.mkdir(nested_dir)

            # With parents=True, this should succeed
            fs.mkdir(nested_dir, parents=True)
            assert nested_dir.exists()
            assert nested_dir.is_dir()

    def test_mkdir_exist_ok(self, mock_config_manager):
        fs = LocalFileSystem(mock_config_manager)
        with TemporaryDirectory() as temp_dir:
            existing_dir = Path(temp_dir) / "existing"
            existing_dir.mkdir()

            # Without exist_ok=True, this should fail
            with pytest.raises(FileExistsError):
                fs.mkdir(existing_dir)

            # With exist_ok=True, this should succeed
            fs.mkdir(existing_dir, exist_ok=True)
            assert existing_dir.exists()

    def test_mkdir_exists_raises(self, mock_config_manager):
        fs = LocalFileSystem(mock_config_manager)
        with TemporaryDirectory() as temp_dir:
            existing_dir = Path(temp_dir) / "existing"
            existing_dir.mkdir()

            # Try to create the same directory without exist_ok
            with pytest.raises(FileExistsError):
                fs.mkdir(existing_dir, exist_ok=False)

    def test_complex_scenario(self, mock_config_manager):
        """Test a complex scenario with multiple operations."""
        fs = LocalFileSystem(mock_config_manager)
        with TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)

            # Create directory structure
            project_dir = base_path / "project"
            fs.mkdir(project_dir)

            src_dir = project_dir / "src"
            fs.mkdir(src_dir)

            test_dir = project_dir / "tests"
            fs.mkdir(test_dir)

            # Create files
            main_file = src_dir / "main.py"
            main_file.write_text("print('Hello')")

            test_file = test_dir / "test_main.py"
            test_file.write_text("import pytest")

            # Verify structure
            assert fs.exists(project_dir)
            assert fs.is_dir(project_dir)

            assert fs.exists(main_file)
            assert fs.is_file(main_file)

            # List directory contents
            project_contents = fs.iterdir(project_dir)
            assert len(project_contents) == 2

            src_contents = fs.iterdir(src_dir)
            assert len(src_contents) == 1
            assert src_contents[0].name == "main.py"

    def test_copy_file_not_implemented(self, mock_config_manager):
        fs = LocalFileSystem(mock_config_manager)
        with pytest.raises(NotImplementedError, match="copy_file is not implemented"):
            fs.copy_file(Path("source"), Path("dest"))

    def test_move_file_not_implemented(self, mock_config_manager):
        fs = LocalFileSystem(mock_config_manager)
        with pytest.raises(NotImplementedError, match="move_file is not implemented"):
            fs.move_file(Path("source"), Path("dest"))

    def test_delete_file_not_implemented(self, mock_config_manager):
        fs = LocalFileSystem(mock_config_manager)
        with pytest.raises(NotImplementedError, match="delete_file is not implemented"):
            fs.delete_file(Path("test.txt"))

    def test_create_directory_not_implemented(self, mock_config_manager):
        fs = LocalFileSystem(mock_config_manager)
        with pytest.raises(NotImplementedError, match="create_directory is not implemented"):
            fs.create_directory(Path("test_dir"))

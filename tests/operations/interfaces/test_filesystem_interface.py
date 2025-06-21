"""Tests for filesystem interface."""
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.operations.interfaces.filesystem_interface import FileSystemInterface


class MockFileSystem(FileSystemInterface):
    """Mock implementation for testing."""

    def __init__(self):
        self.files = set()
        self.dirs = set()

    def exists(self, path: Path) -> bool:
        return path in self.files or path in self.dirs

    def is_file(self, path: Path) -> bool:
        return path in self.files

    def is_dir(self, path: Path) -> bool:
        return path in self.dirs

    def iterdir(self, path: Path) -> list[Path]:
        if not self.is_dir(path):
            raise FileNotFoundError(f"Directory {path} not found")
        return [p for p in self.files | self.dirs if p.parent == path]

    def mkdir(self, path: Path, parents: bool = False, exist_ok: bool = False) -> None:
        if self.exists(path) and not exist_ok:
            raise FileExistsError(f"Directory {path} already exists")
        self.dirs.add(path)

    def copy_file(self, source: Path, destination: Path) -> bool:
        if not self.is_file(source):
            return False
        self.files.add(destination)
        return True

    def move_file(self, source: Path, destination: Path) -> bool:
        if not self.is_file(source):
            return False
        self.files.discard(source)
        self.files.add(destination)
        return True

    def delete_file(self, path: Path) -> bool:
        if not self.is_file(path):
            return False
        self.files.discard(path)
        return True

    def create_directory(self, path: Path) -> bool:
        if self.exists(path):
            return False
        self.dirs.add(path)
        return True


class TestFileSystemInterface:
    """Test filesystem interface implementation."""

    def test_exists_file(self):
        fs = MockFileSystem()
        path = Path("/test/file.txt")
        fs.files.add(path)
        assert fs.exists(path)

    def test_exists_directory(self):
        fs = MockFileSystem()
        path = Path("/test/dir")
        fs.dirs.add(path)
        assert fs.exists(path)

    def test_not_exists(self):
        fs = MockFileSystem()
        path = Path("/nonexistent")
        assert not fs.exists(path)

    def test_is_file(self):
        fs = MockFileSystem()
        path = Path("/test/file.txt")
        fs.files.add(path)
        assert fs.is_file(path)
        assert not fs.is_dir(path)

    def test_is_dir(self):
        fs = MockFileSystem()
        path = Path("/test/dir")
        fs.dirs.add(path)
        assert fs.is_dir(path)
        assert not fs.is_file(path)

    def test_iterdir(self):
        fs = MockFileSystem()
        parent = Path("/test")
        child1 = Path("/test/file1.txt")
        child2 = Path("/test/subdir")

        fs.dirs.add(parent)
        fs.files.add(child1)
        fs.dirs.add(child2)

        contents = fs.iterdir(parent)
        assert child1 in contents
        assert child2 in contents


    def test_mkdir(self):
        fs = MockFileSystem()
        path = Path("/new/dir")
        fs.mkdir(path)
        assert fs.is_dir(path)

    def test_mkdir_exist_ok(self):
        fs = MockFileSystem()
        path = Path("/existing")
        fs.dirs.add(path)
        fs.mkdir(path, exist_ok=True)


    def test_copy_file_success(self):
        fs = MockFileSystem()
        source = Path("/source.txt")
        dest = Path("/dest.txt")
        fs.files.add(source)

        result = fs.copy_file(source, dest)
        assert result
        assert fs.is_file(source)
        assert fs.is_file(dest)

    def test_copy_file_nonexistent(self):
        fs = MockFileSystem()
        source = Path("/nonexistent.txt")
        dest = Path("/dest.txt")

        result = fs.copy_file(source, dest)
        assert not result
        assert not fs.is_file(dest)

    def test_move_file_success(self):
        fs = MockFileSystem()
        source = Path("/source.txt")
        dest = Path("/dest.txt")
        fs.files.add(source)

        result = fs.move_file(source, dest)
        assert result
        assert not fs.is_file(source)
        assert fs.is_file(dest)

    def test_move_file_nonexistent(self):
        fs = MockFileSystem()
        source = Path("/nonexistent.txt")
        dest = Path("/dest.txt")

        result = fs.move_file(source, dest)
        assert not result

    def test_delete_file_success(self):
        fs = MockFileSystem()
        path = Path("/file.txt")
        fs.files.add(path)

        result = fs.delete_file(path)
        assert result
        assert not fs.is_file(path)

    def test_delete_file_nonexistent(self):
        fs = MockFileSystem()
        path = Path("/nonexistent.txt")

        result = fs.delete_file(path)
        assert not result

    def test_create_directory_success(self):
        fs = MockFileSystem()
        path = Path("/new/dir")

        result = fs.create_directory(path)
        assert result
        assert fs.is_dir(path)

    def test_create_directory_exists(self):
        fs = MockFileSystem()
        path = Path("/existing")
        fs.dirs.add(path)

        result = fs.create_directory(path)
        assert not result

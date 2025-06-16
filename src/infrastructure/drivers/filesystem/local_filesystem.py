"""Local file system implementation."""
from pathlib import Path
from typing import List

from src.operations.interfaces.filesystem_interface import FileSystemInterface


class LocalFileSystem(FileSystemInterface):
    """Local file system implementation of FileSystemInterface."""

    def exists(self, path: Path) -> bool:
        """Check if a path exists."""
        return path.exists()

    def is_file(self, path: Path) -> bool:
        """Check if a path is a file."""
        return path.is_file()

    def is_dir(self, path: Path) -> bool:
        """Check if a path is a directory."""
        return path.is_dir()

    def iterdir(self, path: Path) -> List[Path]:
        """List contents of a directory."""
        try:
            return list(path.iterdir())
        except (OSError, PermissionError):
            return []

    def mkdir(self, path: Path, parents: bool = False, exist_ok: bool = False) -> None:
        """Create a directory."""
        path.mkdir(parents=parents, exist_ok=exist_ok)

    def copy_file(self, source: Path, destination: Path) -> bool:
        """Copy a file from source to destination."""
        raise NotImplementedError("copy_file is not implemented")

    def move_file(self, source: Path, destination: Path) -> bool:
        """Move a file from source to destination."""
        raise NotImplementedError("move_file is not implemented")

    def delete_file(self, path: Path) -> bool:
        """Delete a file."""
        raise NotImplementedError("delete_file is not implemented")

    def create_directory(self, path: Path) -> bool:
        """Create a directory."""
        raise NotImplementedError("create_directory is not implemented")

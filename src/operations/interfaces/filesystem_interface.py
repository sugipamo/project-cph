"""File system interface for dependency injection."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List


class FileSystemInterface(ABC):
    """Interface for file system operations."""

    @abstractmethod
    def exists(self, path: Path) -> bool:
        """Check if a path exists."""
        pass

    @abstractmethod
    def is_file(self, path: Path) -> bool:
        """Check if a path is a file."""
        pass

    @abstractmethod
    def is_dir(self, path: Path) -> bool:
        """Check if a path is a directory."""
        pass

    @abstractmethod
    def iterdir(self, path: Path) -> List[Path]:
        """List contents of a directory."""
        pass

    @abstractmethod
    def mkdir(self, path: Path, parents: bool = False, exist_ok: bool = False) -> None:
        """Create a directory."""
        pass

    @abstractmethod
    def copy_file(self, source: Path, destination: Path) -> bool:
        """Copy a file from source to destination.

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            True if copy was successful, False otherwise
        """
        pass

    @abstractmethod
    def move_file(self, source: Path, destination: Path) -> bool:
        """Move a file from source to destination.

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            True if move was successful, False otherwise
        """
        pass

    @abstractmethod
    def delete_file(self, path: Path) -> bool:
        """Delete a file.

        Args:
            path: File path to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        pass

    @abstractmethod
    def create_directory(self, path: Path) -> bool:
        """Create a directory.

        Args:
            path: Directory path to create

        Returns:
            True if creation was successful, False otherwise
        """
        pass

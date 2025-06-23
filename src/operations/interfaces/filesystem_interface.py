"""File system interface for dependency injection."""
from abc import ABC, abstractmethod
from typing import List, Union


class FileSystemInterface(ABC):
    """Interface for file system operations."""

    @abstractmethod
    def exists(self, path: Union[str, object]) -> bool:
        """Check if a path exists."""
        pass

    @abstractmethod
    def is_file(self, path: Union[str, object]) -> bool:
        """Check if a path is a file."""
        pass

    @abstractmethod
    def is_dir(self, path: Union[str, object]) -> bool:
        """Check if a path is a directory."""
        pass

    @abstractmethod
    def iterdir(self, path: Union[str, object]) -> List[Union[str, object]]:
        """List contents of a directory."""
        pass

    @abstractmethod
    def mkdir(self, path: Union[str, object], parents: bool, exist_ok: bool) -> None:
        """Create a directory."""
        pass


    @abstractmethod
    def delete_file(self, path: Union[str, object]) -> bool:
        """Delete a file.

        Args:
            path: File path to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        pass

    @abstractmethod
    def create_directory(self, path: Union[str, object]) -> bool:
        """Create a directory.

        Args:
            path: Directory path to create

        Returns:
            True if creation was successful, False otherwise
        """
        pass

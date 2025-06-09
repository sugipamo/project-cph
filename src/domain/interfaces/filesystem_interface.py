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

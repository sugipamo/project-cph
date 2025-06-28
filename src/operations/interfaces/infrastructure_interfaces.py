"""Consolidated infrastructure-related interfaces."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple


class FileSystemInterface(ABC):
    """Interface for file system operations."""

    @abstractmethod
    def exists(self, path: Path) -> bool:
        """Check if path exists."""
        pass

    @abstractmethod
    def is_file(self, path: Path) -> bool:
        """Check if path is a file."""
        pass

    @abstractmethod
    def is_dir(self, path: Path) -> bool:
        """Check if path is a directory."""
        pass

    @abstractmethod
    def iterdir(self, path: Path) -> Iterator[Path]:
        """Iterate over directory contents."""
        pass

    @abstractmethod
    def mkdir(self, path: Path, parents: bool, exist_ok: bool) -> None:
        """Create directory."""
        pass

    @abstractmethod
    def create_directory(self, path: Path) -> None:
        """Create directory with default settings."""
        pass

    @abstractmethod
    def delete_file(self, path: Path) -> None:
        """Delete a file."""
        pass


class PersistenceInterface(ABC):
    """Interface for persistence operations."""

    @abstractmethod
    def get_connection(self) -> Any:
        """Get database connection."""
        pass

    @abstractmethod
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        pass

    @abstractmethod
    def execute_command(self, command: str, params: Optional[Tuple] = None) -> int:
        """Execute a command and return affected rows."""
        pass

    @abstractmethod
    def begin_transaction(self) -> Any:
        """Begin a new transaction."""
        pass

    @abstractmethod
    def get_repository(self, repository_class: type) -> Any:
        """Get a repository instance."""
        pass


class RepositoryInterface(ABC):
    """Interface for repository pattern operations."""

    @abstractmethod
    def create_entity_record(self, entity: Any) -> Any:
        """Create a new entity record."""
        pass

    @abstractmethod
    def find_by_id(self, entity_id: Any) -> Optional[Any]:
        """Find entity by ID."""
        pass

    @abstractmethod
    def find_all(self) -> List[Any]:
        """Find all entities."""
        pass

    @abstractmethod
    def update(self, entity: Any) -> bool:
        """Update an entity."""
        pass

    @abstractmethod
    def delete(self, entity_id: Any) -> bool:
        """Delete an entity."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Count total entities."""
        pass


class TimeInterface(ABC):
    """Interface for time operations."""

    @abstractmethod
    def current_time(self) -> float:
        """Get current time as timestamp."""
        pass

    @abstractmethod
    def sleep(self, seconds: float) -> None:
        """Sleep for specified seconds."""
        pass
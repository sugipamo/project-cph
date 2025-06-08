"""Persistence interface for domain layer."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class PersistenceInterface(ABC):
    """Abstract interface for persistence operations."""

    @abstractmethod
    def get_connection(self) -> Any:
        """Get a database connection.

        Returns:
            Database connection object
        """

    @abstractmethod
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of result dictionaries
        """

    @abstractmethod
    def execute_command(self, command: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE command.

        Args:
            command: SQL command string
            params: Command parameters

        Returns:
            Number of affected rows or last insert ID
        """

    @abstractmethod
    def begin_transaction(self) -> Any:
        """Begin a database transaction.

        Returns:
            Transaction context manager
        """

    @abstractmethod
    def get_repository(self, repository_class: type) -> Any:
        """Get a repository instance.

        Args:
            repository_class: Repository class to instantiate

        Returns:
            Repository instance
        """


class RepositoryInterface(ABC):
    """Abstract interface for repository operations."""

    @abstractmethod
    def create(self, entity: Dict[str, Any]) -> Any:
        """Create a new entity.

        Args:
            entity: Entity data dictionary

        Returns:
            Created entity ID or object
        """

    @abstractmethod
    def find_by_id(self, entity_id: Any) -> Optional[Dict[str, Any]]:
        """Find entity by ID.

        Args:
            entity_id: Entity identifier

        Returns:
            Entity dictionary if found, None otherwise
        """

    @abstractmethod
    def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """Find all entities with optional pagination.

        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip

        Returns:
            List of entity dictionaries
        """

    @abstractmethod
    def update(self, entity_id: Any, updates: Dict[str, Any]) -> bool:
        """Update an existing entity.

        Args:
            entity_id: Entity identifier
            updates: Dictionary of fields to update

        Returns:
            True if updated, False if not found
        """

    @abstractmethod
    def delete(self, entity_id: Any) -> bool:
        """Delete entity by ID.

        Args:
            entity_id: Entity identifier

        Returns:
            True if deleted, False if not found
        """

    @abstractmethod
    def count(self) -> int:
        """Count total number of entities.

        Returns:
            Total count of entities
        """

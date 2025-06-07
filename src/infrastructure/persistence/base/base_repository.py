"""Base repository interface for data persistence."""
from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseRepository(ABC):
    """Abstract base class for all repositories."""

    @abstractmethod
    def create(self, entity: Any) -> Any:
        """Create a new entity.

        Args:
            entity: The entity to create

        Returns:
            The created entity with ID
        """

    @abstractmethod
    def find_by_id(self, entity_id: Any) -> Optional[Any]:
        """Find entity by ID.

        Args:
            entity_id: The ID to search for

        Returns:
            The entity if found, None otherwise
        """

    @abstractmethod
    def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> list[Any]:
        """Find all entities with optional pagination.

        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip

        Returns:
            List of entities
        """

    @abstractmethod
    def update(self, entity: Any) -> Any:
        """Update an existing entity.

        Args:
            entity: The entity to update

        Returns:
            The updated entity
        """

    @abstractmethod
    def delete(self, entity_id: Any) -> bool:
        """Delete entity by ID.

        Args:
            entity_id: The ID of entity to delete

        Returns:
            True if deleted, False if not found
        """

    def count(self) -> int:
        """Count total number of entities.

        Returns:
            Total count of entities
        """
        return len(self.find_all())

"""Base repository interface for data persistence."""
from typing import Any

from src.domain.interfaces.persistence_interface import RepositoryInterface


class DatabaseRepositoryFoundation(RepositoryInterface):
    """Foundation class for database repositories with common functionality.

    This class provides a foundation for all concrete repository implementations,
    offering common database connection management and basic operations.
    """

    def __init__(self, persistence_manager: Any):
        """Initialize repository with persistence manager.

        Args:
            persistence_manager: Database manager instance
        """
        self.persistence_manager = persistence_manager

    @property
    def connection(self):
        """Get database connection context manager."""
        return self.persistence_manager.get_connection()

    def count(self) -> int:
        """Count total number of entities.

        Returns:
            Total count of entities
        """
        # Default implementation - can be overridden for efficiency
        return len(self.find_all())

    # Note: Concrete repositories must implement the abstract methods from RepositoryInterface:
    # - create(self, entity: Dict[str, Any]) -> Any
    # - find_by_id(self, entity_id: Any) -> Optional[Dict[str, Any]]
    # - find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]
    # - update(self, entity_id: Any, updates: Dict[str, Any]) -> bool
    # - delete(self, entity_id: Any) -> bool



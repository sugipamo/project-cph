"""Base repository interface for data persistence."""
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Dict


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
        pass
    
    @abstractmethod
    def find_by_id(self, entity_id: Any) -> Optional[Any]:
        """Find entity by ID.
        
        Args:
            entity_id: The ID to search for
            
        Returns:
            The entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Any]:
        """Find all entities with optional pagination.
        
        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities
        """
        pass
    
    @abstractmethod
    def update(self, entity: Any) -> Any:
        """Update an existing entity.
        
        Args:
            entity: The entity to update
            
        Returns:
            The updated entity
        """
        pass
    
    @abstractmethod
    def delete(self, entity_id: Any) -> bool:
        """Delete entity by ID.
        
        Args:
            entity_id: The ID of entity to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    def count(self) -> int:
        """Count total number of entities.
        
        Returns:
            Total count of entities
        """
        return len(self.find_all())
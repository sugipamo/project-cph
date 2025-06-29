"""Adapter to bridge DIContainer to DIContainerInterface."""
from typing import Any
from src.operations.interfaces.utility_interfaces import DIContainerInterface
from src.infrastructure.di_container import DIContainer, DIKey


class DIContainerAdapter(DIContainerInterface):
    """Adapter that wraps DIContainer to implement DIContainerInterface."""
    
    def __init__(self, di_container: DIContainer):
        """Initialize with the actual DI container.
        
        Args:
            di_container: The infrastructure DIContainer instance
        """
        self._container = di_container
    
    def resolve(self, key: str) -> Any:
        """Resolve a dependency by string key.
        
        Args:
            key: Dependency identifier as string
            
        Returns:
            Resolved dependency instance
        """
        # Convert string key to DIKey enum if possible
        key_upper = key.upper()
        if key_upper in DIKey.__members__:
            enum_key = DIKey[key_upper]
            return self._container.resolve(enum_key)
        
        # Fall back to direct string resolution
        return self._container.resolve(key)
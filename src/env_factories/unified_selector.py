"""
Unified factory selector

Provides a simplified interface for creating command requests
using the unified factory pattern while maintaining backward compatibility.
"""

from typing import Optional
from .unified_factory import UnifiedCommandRequestFactory
from .command_types import CommandType, get_command_type_from_string
from src.operations.di_container import DIContainer


class UnifiedFactorySelector:
    """
    Simplified factory selector using the unified factory pattern
    
    Replaces the complex RequestFactorySelector with a single factory
    that handles all command types.
    """
    
    def __init__(self):
        self._factory_cache = {}
    
    def get_factory(self, controller, operations: Optional[DIContainer] = None) -> UnifiedCommandRequestFactory:
        """
        Get unified factory instance (cached per controller)
        
        Args:
            controller: Environment resource controller
            operations: DI container (optional, for backward compatibility)
            
        Returns:
            UnifiedCommandRequestFactory instance
        """
        # Use controller as cache key
        cache_key = id(controller)
        
        if cache_key not in self._factory_cache:
            factory = UnifiedCommandRequestFactory(controller)
            self._factory_cache[cache_key] = factory
        
        return self._factory_cache[cache_key]
    
    def get_factory_for_step_type(self, step_type: str, controller, operations: Optional[DIContainer] = None):
        """
        Get factory for specific step type (backward compatibility method)
        
        Args:
            step_type: Command type string (e.g., "shell", "copy", "mkdir")
            controller: Environment resource controller
            operations: DI container (optional)
            
        Returns:
            UnifiedCommandRequestFactory instance
        """
        # Validate step type
        command_type = get_command_type_from_string(step_type)
        if not command_type:
            raise ValueError(f"Unsupported step type: {step_type}")
        
        factory = self.get_factory(controller, operations)
        
        # Verify that the factory supports this command type
        if not factory.supports_command_type(command_type):
            raise ValueError(f"Factory does not support command type: {step_type}")
        
        return factory
    
    def create_request_for_type(self, step_type: str, controller, operations: Optional[DIContainer] = None, **kwargs):
        """
        Directly create request for given type with parameters
        
        Args:
            step_type: Command type string
            controller: Environment resource controller  
            operations: DI container (optional)
            **kwargs: Request parameters
            
        Returns:
            Created request instance
        """
        command_type = get_command_type_from_string(step_type)
        if not command_type:
            raise ValueError(f"Unsupported step type: {step_type}")
        
        factory = self.get_factory(controller, operations)
        return factory.create_request_by_type(command_type, **kwargs)
    
    def get_supported_types(self, controller, operations: Optional[DIContainer] = None) -> list:
        """
        Get list of supported command types
        
        Args:
            controller: Environment resource controller
            operations: DI container (optional)
            
        Returns:
            List of supported CommandType values
        """
        factory = self.get_factory(controller, operations)
        return factory.get_supported_types()
    
    def clear_cache(self):
        """Clear the factory cache"""
        self._factory_cache.clear()


# Backward compatibility: create global instance
_unified_selector = UnifiedFactorySelector()


def get_unified_factory(controller, operations: Optional[DIContainer] = None) -> UnifiedCommandRequestFactory:
    """Get unified factory instance (convenience function)"""
    return _unified_selector.get_factory(controller, operations)


def get_factory_for_step_type(step_type: str, controller, operations: Optional[DIContainer] = None):
    """Get factory for step type (backward compatibility function)"""
    return _unified_selector.get_factory_for_step_type(step_type, controller, operations)
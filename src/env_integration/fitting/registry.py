"""
Provider registry system for dynamic environment provider management
"""
from typing import Dict, Type, Optional, List
import logging

from .core.interfaces import ProviderFactory, ProviderSet


class ProviderRegistry:
    """Registry for managing environment provider factories"""
    
    def __init__(self):
        """Initialize empty registry"""
        self._factories: Dict[str, ProviderFactory] = {}
        self._provider_cache: Dict[str, ProviderSet] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_factory(self, env_type: str, factory: ProviderFactory) -> None:
        """Register a provider factory for an environment type
        
        Args:
            env_type: Environment type identifier (e.g., "docker", "kubernetes")
            factory: Factory instance that can create providers for this environment
        """
        if not factory.supports_env_type(env_type):
            raise ValueError(f"Factory does not support environment type: {env_type}")
        
        self._factories[env_type] = factory
        self.logger.info(f"Registered provider factory for environment type: {env_type}")
    
    def unregister_factory(self, env_type: str) -> None:
        """Unregister a provider factory
        
        Args:
            env_type: Environment type to unregister
        """
        if env_type in self._factories:
            del self._factories[env_type]
            # Clear cached providers for this environment type
            if env_type in self._provider_cache:
                del self._provider_cache[env_type]
            self.logger.info(f"Unregistered provider factory for environment type: {env_type}")
    
    def get_provider_set(self, env_type: str, operations, context) -> ProviderSet:
        """Get or create a provider set for the given environment type
        
        Args:
            env_type: Environment type identifier
            operations: Operations container
            context: Execution context
            
        Returns:
            ProviderSet for the environment type
            
        Raises:
            ValueError: If no factory is registered for the environment type
        """
        if env_type not in self._factories:
            available_types = list(self._factories.keys())
            raise ValueError(
                f"No provider factory registered for environment type: {env_type}. "
                f"Available types: {available_types}"
            )
        
        # Check cache first (but skip for now since operations/context may vary)
        # TODO: Implement smarter caching based on context hash
        
        factory = self._factories[env_type]
        provider_set = factory.create_provider_set(operations, context)
        
        if not provider_set.validate():
            raise ValueError(f"Invalid provider set created for environment type: {env_type}")
        
        # Cache the provider set
        cache_key = self._generate_cache_key(env_type, operations, context)
        self._provider_cache[cache_key] = provider_set
        
        return provider_set
    
    def list_supported_env_types(self) -> List[str]:
        """Get list of supported environment types
        
        Returns:
            List of registered environment type identifiers
        """
        return list(self._factories.keys())
    
    def is_env_type_supported(self, env_type: str) -> bool:
        """Check if an environment type is supported
        
        Args:
            env_type: Environment type to check
            
        Returns:
            True if supported
        """
        return env_type in self._factories
    
    def clear_cache(self) -> None:
        """Clear the provider cache"""
        self._provider_cache.clear()
        self.logger.debug("Cleared provider cache")
    
    def _generate_cache_key(self, env_type: str, operations, context) -> str:
        """Generate cache key for provider set
        
        Args:
            env_type: Environment type
            operations: Operations container
            context: Execution context
            
        Returns:
            Cache key string
        """
        # Simple cache key - could be enhanced with context hashing
        context_hash = getattr(context, 'language', 'unknown')
        return f"{env_type}_{context_hash}"


# Global registry instance
_global_registry = ProviderRegistry()


def get_global_registry() -> ProviderRegistry:
    """Get the global provider registry instance
    
    Returns:
        Global ProviderRegistry instance
    """
    return _global_registry


def register_provider_factory(env_type: str, factory: ProviderFactory) -> None:
    """Convenience function to register a factory with the global registry
    
    Args:
        env_type: Environment type identifier
        factory: Factory instance
    """
    _global_registry.register_factory(env_type, factory)


def get_provider_set(env_type: str, operations, context) -> ProviderSet:
    """Convenience function to get provider set from global registry
    
    Args:
        env_type: Environment type identifier
        operations: Operations container
        context: Execution context
        
    Returns:
        ProviderSet for the environment type
    """
    return _global_registry.get_provider_set(env_type, operations, context)
"""
Registry for environment strategies
"""
from typing import Dict, Optional, List
from .base_strategy import EnvironmentStrategy
from .local_strategy import LocalStrategy
from .docker_strategy import DockerStrategy


class EnvironmentStrategyRegistry:
    """
    Registry for managing environment strategies.
    Provides strategy lookup and configuration.
    """
    
    def __init__(self):
        self._strategies: Dict[str, EnvironmentStrategy] = {}
        self._default_strategy: Optional[str] = None
        self._initialize_default_strategies()
    
    def _initialize_default_strategies(self):
        """Initialize with default strategies"""
        # Create default strategies with configurations
        local_config = {
            'working_directory': '.',
            'default_shell': 'bash',
            'timeout_seconds': 300,
        }
        
        docker_config = {
            'working_directory': '/workspace',
            'mount_path': '/workspace',
            'default_shell': 'bash',
            'timeout_seconds': 300,
        }
        
        # Register strategies
        self.register(LocalStrategy(local_config))
        self.register(DockerStrategy(docker_config))
        
        # Set default
        self._default_strategy = 'local'
    
    def register(self, strategy: EnvironmentStrategy):
        """
        Register an environment strategy.
        
        Args:
            strategy: The strategy to register
        """
        # Register by primary name
        self._strategies[strategy.name] = strategy
        
        # Register by aliases
        for alias in strategy.aliases:
            self._strategies[alias] = strategy
    
    def get_strategy(self, env_type: str) -> Optional[EnvironmentStrategy]:
        """
        Get a strategy by environment type.
        
        Args:
            env_type: The environment type string
            
        Returns:
            The strategy if found, None otherwise
        """
        return self._strategies.get(env_type)
    
    def get_default_strategy(self) -> Optional[EnvironmentStrategy]:
        """
        Get the default strategy.
        
        Returns:
            The default strategy if set
        """
        if self._default_strategy:
            return self._strategies.get(self._default_strategy)
        return None
    
    def set_default_strategy(self, env_type: str):
        """
        Set the default strategy.
        
        Args:
            env_type: The environment type to use as default
        """
        if env_type in self._strategies:
            self._default_strategy = env_type
    
    def get_all_strategies(self) -> List[EnvironmentStrategy]:
        """
        Get all unique strategies.
        
        Returns:
            List of all registered strategies
        """
        # Use dict to remove duplicates
        unique_strategies = {}
        for strategy in self._strategies.values():
            unique_strategies[strategy.name] = strategy
        return list(unique_strategies.values())
    
    def update_strategy_config(self, env_type: str, config: Dict):
        """
        Update configuration for a specific strategy.
        
        Args:
            env_type: The environment type
            config: New configuration to merge
        """
        strategy = self.get_strategy(env_type)
        if strategy:
            strategy._config.update(config)


# Global registry instance
_registry = EnvironmentStrategyRegistry()


def get_strategy(env_type: str) -> Optional[EnvironmentStrategy]:
    """Get an environment strategy from the global registry"""
    return _registry.get_strategy(env_type)


def get_default_strategy() -> Optional[EnvironmentStrategy]:
    """Get the default environment strategy"""
    return _registry.get_default_strategy()


def register_strategy(strategy: EnvironmentStrategy):
    """Register a strategy in the global registry"""
    _registry.register(strategy)


def update_strategy_config(env_type: str, config: Dict):
    """Update configuration for a strategy"""
    _registry.update_strategy_config(env_type, config)
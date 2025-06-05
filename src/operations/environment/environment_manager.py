"""
Environment manager using strategy pattern
"""
from typing import Any, Optional, Dict
from src.operations.base_request import BaseRequest
from src.operations.result.result import OperationResult
from .base_strategy import EnvironmentStrategy
from .strategy_registry import get_strategy, get_default_strategy


class EnvironmentManager:
    """
    Manages environment-specific operations using the strategy pattern.
    Replaces scattered env_type branching with centralized strategy management.
    """
    
    def __init__(self, env_type: Optional[str] = None):
        """
        Initialize environment manager.
        
        Args:
            env_type: Environment type to use, defaults to registry default
        """
        self._env_type = env_type
        self._strategy = self._get_strategy()
    
    def _get_strategy(self) -> EnvironmentStrategy:
        """Get the appropriate strategy based on environment type"""
        if self._env_type:
            strategy = get_strategy(self._env_type)
            if strategy:
                return strategy
        
        # Fall back to default strategy
        default = get_default_strategy()
        if default:
            return default
        
        # This shouldn't happen if registry is properly initialized
        raise ValueError(f"No strategy found for env_type: {self._env_type}")
    
    @property
    def strategy(self) -> EnvironmentStrategy:
        """Get the current environment strategy"""
        return self._strategy
    
    def prepare_environment(self, context: Any) -> OperationResult:
        """
        Prepare the environment for execution.
        
        Args:
            context: Execution context
            
        Returns:
            OperationResult indicating success/failure
        """
        return self._strategy.prepare_environment(context)
    
    def cleanup_environment(self, context: Any) -> OperationResult:
        """
        Clean up the environment after execution.
        
        Args:
            context: Execution context
            
        Returns:
            OperationResult indicating success/failure
        """
        return self._strategy.cleanup_environment(context)
    
    def execute_request(self, request: BaseRequest, driver: Any) -> OperationResult:
        """
        Execute a request using the appropriate environment strategy.
        
        Args:
            request: The request to execute
            driver: The driver to use
            
        Returns:
            OperationResult with execution details
        """
        return self._strategy.execute_request(request, driver)
    
    def should_force_local(self, step_config: Dict[str, Any]) -> bool:
        """
        Check if a step should be forced to run locally.
        
        Args:
            step_config: Step configuration
            
        Returns:
            True if step should run locally
        """
        return self._strategy.should_force_local(step_config)
    
    def get_working_directory(self) -> str:
        """Get the working directory for this environment"""
        return self._strategy.get_working_directory()
    
    def get_timeout(self) -> int:
        """Get the default timeout for this environment"""
        return self._strategy.get_timeout()
    
    def get_shell(self) -> str:
        """Get the default shell for this environment"""
        return self._strategy.get_shell()
    
    @classmethod
    def from_context(cls, context: Any) -> 'EnvironmentManager':
        """
        Create an EnvironmentManager from an execution context.
        
        Args:
            context: Execution context with env_type
            
        Returns:
            EnvironmentManager instance
        """
        env_type = getattr(context, 'env_type', None)
        return cls(env_type)
    
    def switch_strategy(self, env_type: str):
        """
        Switch to a different environment strategy.
        
        Args:
            env_type: New environment type
        """
        strategy = get_strategy(env_type)
        if strategy:
            self._env_type = env_type
            self._strategy = strategy
        else:
            raise ValueError(f"Unknown environment type: {env_type}")
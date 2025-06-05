"""
Base environment strategy for handling environment-specific operations
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from src.operations.base_request import BaseRequest
from src.operations.result.result import OperationResult


class EnvironmentStrategy(ABC):
    """
    Abstract base class for environment strategies.
    Encapsulates environment-specific behavior and operations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the environment strategy.
        
        Args:
            config: Environment-specific configuration
        """
        self._config = config or {}
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The name of this environment strategy"""
        pass
    
    @property
    @abstractmethod
    def aliases(self) -> List[str]:
        """Alternative names for this environment"""
        pass
    
    @abstractmethod
    def prepare_environment(self, context: Any) -> OperationResult:
        """
        Prepare the environment for execution.
        
        Args:
            context: Execution context
            
        Returns:
            OperationResult indicating success/failure
        """
        pass
    
    @abstractmethod
    def cleanup_environment(self, context: Any) -> OperationResult:
        """
        Clean up the environment after execution.
        
        Args:
            context: Execution context
            
        Returns:
            OperationResult indicating success/failure
        """
        pass
    
    @abstractmethod
    def execute_request(self, request: BaseRequest, driver: Any) -> OperationResult:
        """
        Execute a request in this environment.
        
        Args:
            request: The request to execute
            driver: The driver to use for execution
            
        Returns:
            OperationResult with execution details
        """
        pass
    
    @abstractmethod
    def should_force_local(self, step_config: Dict[str, Any]) -> bool:
        """
        Check if a step should be forced to run locally.
        
        Args:
            step_config: Step configuration dictionary
            
        Returns:
            True if the step should run locally regardless of environment
        """
        pass
    
    def get_working_directory(self) -> str:
        """
        Get the working directory for this environment.
        
        Returns:
            Working directory path
        """
        return self._config.get('working_directory', '.')
    
    def get_timeout(self) -> int:
        """
        Get the default timeout for operations in this environment.
        
        Returns:
            Timeout in seconds
        """
        return self._config.get('timeout_seconds', 300)
    
    def get_shell(self) -> str:
        """
        Get the default shell for this environment.
        
        Returns:
            Shell command (e.g., 'bash', 'sh')
        """
        return self._config.get('default_shell', 'bash')
    
    def matches(self, env_type: str) -> bool:
        """
        Check if the given environment type matches this strategy.
        
        Args:
            env_type: Environment type string to check
            
        Returns:
            True if this strategy handles the given environment type
        """
        if env_type == self.name:
            return True
        return env_type in self.aliases
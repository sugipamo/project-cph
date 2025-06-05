"""
Local environment strategy implementation
"""
from typing import Any, Dict, Optional, List
from src.operations.base_request import BaseRequest
from src.operations.result.result import OperationResult
from .base_strategy import EnvironmentStrategy


class LocalStrategy(EnvironmentStrategy):
    """
    Strategy for local environment execution.
    Executes operations directly on the host system.
    """
    
    @property
    def name(self) -> str:
        return "local"
    
    @property
    def aliases(self) -> List[str]:
        return ["host", "native"]
    
    def prepare_environment(self, context: Any) -> OperationResult:
        """
        Prepare local environment (usually a no-op).
        
        Args:
            context: Execution context
            
        Returns:
            OperationResult indicating success
        """
        # Local environment typically doesn't need preparation
        return OperationResult(
            success=True,
            stdout="Local environment ready",
            returncode=0
        )
    
    def cleanup_environment(self, context: Any) -> OperationResult:
        """
        Clean up local environment (usually a no-op).
        
        Args:
            context: Execution context
            
        Returns:
            OperationResult indicating success
        """
        # Local environment typically doesn't need cleanup
        return OperationResult(
            success=True,
            stdout="Local environment cleaned up",
            returncode=0
        )
    
    def execute_request(self, request: BaseRequest, driver: Any) -> OperationResult:
        """
        Execute a request in the local environment.
        
        Args:
            request: The request to execute
            driver: The driver to use for execution
            
        Returns:
            OperationResult with execution details
        """
        # In local environment, just execute the request directly
        return request.execute(driver)
    
    def should_force_local(self, step_config: Dict[str, Any]) -> bool:
        """
        Check if a step should be forced to run locally.
        In local strategy, this is always False since we're already local.
        
        Args:
            step_config: Step configuration dictionary
            
        Returns:
            Always False for local strategy
        """
        return False
    
    def get_driver_type(self, operation_type: str) -> str:
        """
        Get the appropriate driver type for an operation in local environment.
        
        Args:
            operation_type: Type of operation (e.g., 'file', 'shell', 'docker')
            
        Returns:
            Driver type to use
        """
        # Map operation types to local drivers
        driver_mapping = {
            'file': 'file_driver',
            'shell': 'shell_driver',
            'docker': 'docker_driver',
            'python': 'shell_driver',  # Python runs via shell in local
        }
        return driver_mapping.get(operation_type, 'shell_driver')
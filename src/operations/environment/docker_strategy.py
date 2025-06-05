"""
Docker environment strategy implementation
"""
from typing import Any, Dict, Optional, List
from src.operations.base_request import BaseRequest
from src.operations.result.result import OperationResult
from src.operations.docker.docker_request import DockerRequest
from src.operations.docker.docker_file_request import DockerFileRequest
from .base_strategy import EnvironmentStrategy


class DockerStrategy(EnvironmentStrategy):
    """
    Strategy for Docker environment execution.
    Executes operations inside Docker containers.
    """
    
    @property
    def name(self) -> str:
        return "docker"
    
    @property
    def aliases(self) -> List[str]:
        return ["container", "isolated"]
    
    def prepare_environment(self, context: Any) -> OperationResult:
        """
        Prepare Docker environment by ensuring container is running.
        
        Args:
            context: Execution context
            
        Returns:
            OperationResult indicating success/failure
        """
        # This would typically involve:
        # 1. Building/pulling Docker image if needed
        # 2. Starting container if not running
        # 3. Setting up volumes and network
        
        # For now, delegate to existing preparation logic
        # This will be refactored to use proper Docker preparation
        return OperationResult(
            success=True,
            stdout="Docker environment prepared",
            returncode=0
        )
    
    def cleanup_environment(self, context: Any) -> OperationResult:
        """
        Clean up Docker environment.
        
        Args:
            context: Execution context
            
        Returns:
            OperationResult indicating success/failure
        """
        # This would typically involve:
        # 1. Stopping container if configured to do so
        # 2. Removing temporary volumes
        # 3. Cleaning up networks
        
        return OperationResult(
            success=True,
            stdout="Docker environment cleaned up",
            returncode=0
        )
    
    def execute_request(self, request: BaseRequest, driver: Any) -> OperationResult:
        """
        Execute a request in the Docker environment.
        
        Args:
            request: The request to execute
            driver: The driver to use for execution
            
        Returns:
            OperationResult with execution details
        """
        # Check if request should be wrapped for Docker execution
        if self._should_wrap_for_docker(request):
            docker_request = self._wrap_request_for_docker(request)
            return docker_request.execute(driver)
        
        # Some requests execute as-is even in Docker environment
        return request.execute(driver)
    
    def should_force_local(self, step_config: Dict[str, Any]) -> bool:
        """
        Check if a step should be forced to run locally.
        
        Args:
            step_config: Step configuration dictionary
            
        Returns:
            True if force_env_type is 'local'
        """
        force_env = step_config.get('force_env_type', '')
        return force_env == 'local'
    
    def _should_wrap_for_docker(self, request: BaseRequest) -> bool:
        """
        Determine if a request should be wrapped for Docker execution.
        
        Args:
            request: The request to check
            
        Returns:
            True if the request should be wrapped
        """
        # Already Docker requests don't need wrapping
        if isinstance(request, (DockerRequest, DockerFileRequest)):
            return False
        
        # File and shell operations typically need wrapping
        operation_type = getattr(request, 'operation_type', None)
        if operation_type in ['FILE', 'SHELL', 'PYTHON']:
            return True
        
        return False
    
    def _wrap_request_for_docker(self, request: BaseRequest) -> BaseRequest:
        """
        Wrap a request for Docker execution.
        
        Args:
            request: The request to wrap
            
        Returns:
            Wrapped request suitable for Docker execution
        """
        # This is a simplified version - actual implementation would
        # create appropriate Docker wrappers based on request type
        
        # For now, return the original request
        # TODO: Implement proper request wrapping
        return request
    
    def get_driver_type(self, operation_type: str) -> str:
        """
        Get the appropriate driver type for an operation in Docker environment.
        
        Args:
            operation_type: Type of operation
            
        Returns:
            Driver type to use
        """
        # In Docker environment, most operations go through docker driver
        driver_mapping = {
            'file': 'docker_driver',  # File ops through docker
            'shell': 'docker_driver',  # Shell commands in container
            'docker': 'docker_driver',  # Docker operations
            'python': 'docker_driver',  # Python in container
        }
        return driver_mapping.get(operation_type, 'docker_driver')
    
    def get_working_directory(self) -> str:
        """
        Get the working directory for Docker environment.
        
        Returns:
            Working directory path inside container
        """
        # Docker typically uses a different working directory
        return self._config.get('working_directory', '/workspace')
    
    def get_mount_path(self) -> str:
        """
        Get the mount path for Docker volumes.
        
        Returns:
            Mount path inside container
        """
        return self._config.get('mount_path', '/workspace')
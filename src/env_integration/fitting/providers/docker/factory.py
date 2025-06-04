"""
Docker provider factory for creating complete Docker provider sets
"""
from ...core.interfaces import ProviderFactory, ProviderSet
from .inspector import DockerResourceInspector
from .generator import DockerTaskGenerator
from .state import DockerStateManager
from .error_handler import DockerErrorHandler


class DockerProviderFactory(ProviderFactory):
    """Factory for creating Docker-specific provider components"""
    
    def create_provider_set(self, operations, context) -> ProviderSet:
        """Create a complete Docker provider set
        
        Args:
            operations: Operations container
            context: Execution context
            
        Returns:
            Complete ProviderSet for Docker environment
        """
        # Create state manager first as other components may depend on it
        state_manager = DockerStateManager()
        
        # Create inspector
        inspector = DockerResourceInspector(operations)
        
        # Create task generator with dependencies
        generator = DockerTaskGenerator(operations, context, state_manager)
        
        # Create error handler
        error_handler = DockerErrorHandler()
        
        return ProviderSet(
            inspector=inspector,
            generator=generator,
            state_manager=state_manager,
            error_handler=error_handler,
            env_type="docker"
        )
    
    def supports_env_type(self, env_type: str) -> bool:
        """Check if this factory supports the given environment type
        
        Args:
            env_type: Environment type to check
            
        Returns:
            True if env_type is "docker"
        """
        return env_type.lower() == "docker"
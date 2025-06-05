"""
Docker provider factory for creating complete Docker provider sets
"""
from ...core.interfaces import ProviderFactory, ProviderSet
from .inspector import DockerResourceInspector
from .generator import DockerTaskGenerator
from .state import DockerStateManager
from .error_handler import DockerErrorHandler
from ...env_context import create_env_json_context


class DockerProviderFactory(ProviderFactory):
    """Factory for creating Docker-specific provider components"""
    
    def create_provider_set(self, operations, context) -> ProviderSet:
        """Create a complete Docker provider set using env.json configuration
        
        Args:
            operations: Operations container
            context: Execution context
            
        Returns:
            Complete ProviderSet for Docker environment
        """
        # Create env.json based context if not already available
        if not hasattr(context, 'get_docker_mount_path'):
            # Convert legacy context to env.json based context
            language = getattr(context, 'language', 'python')
            env_type = getattr(context, 'env_type', 'docker')
            env_context = create_env_json_context(
                language=language,
                env_type=env_type,
                operations=operations
            )
        else:
            env_context = context
        
        # Create state manager with env.json configuration
        state_manager = DockerStateManager(context=env_context)
        
        # Create inspector
        inspector = DockerResourceInspector(operations)
        
        # Create task generator with env.json context
        generator = DockerTaskGenerator(operations, env_context, state_manager)
        
        # Create error handler with env.json configuration
        error_handler = DockerErrorHandler(context=env_context)
        
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
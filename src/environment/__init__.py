"""
Environment management package - unified interface for environment operations

This package consolidates environment-related functionality previously spread across
env_core, env_factories, env_integration, and env_resource packages.
"""

# Import backward compatibility layer
try:
    # Core environment components
    from ..env_core import Step, StepType, StepContext
    from ..env_core.workflow import GraphBasedWorkflowBuilder, RequestExecutionGraph
    
    # Environment factories
    from ..env_factories import UnifiedFactory, RequestBuilders
    
    # Environment integration
    from ..env_integration import EnvironmentController, EnvironmentService
    
    # Environment resources
    from ..env_resource.file import BaseFileHandler, LocalFileHandler, DockerFileHandler
    from ..env_resource.run import BaseRunHandler, LocalRunHandler, DockerRunHandler
    
    core_exports = [
        'Step', 'StepType', 'StepContext',
        'GraphBasedWorkflowBuilder', 'RequestExecutionGraph',
        'UnifiedFactory', 'RequestBuilders',
        'EnvironmentController', 'EnvironmentService',
        'BaseFileHandler', 'LocalFileHandler', 'DockerFileHandler',
        'BaseRunHandler', 'LocalRunHandler', 'DockerRunHandler'
    ]
except ImportError as e:
    # During migration, some imports may fail
    core_exports = []

__all__ = core_exports
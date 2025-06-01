"""
Environment module - Backward compatibility layer

This module provides backward compatibility by re-exporting classes
from the new modular structure. For new code, prefer importing
directly from the specific modules.
"""

# Core workflow engine
from src.env_core.step import Step, StepType, StepContext
from src.env_core.workflow import GraphBasedWorkflowBuilder, RequestExecutionGraph

# Request factories (modules have been removed)
BaseCommandRequestFactory = None
RequestFactorySelector = None

# Resource management (modules have been removed)
LocalFileHandler = None
DockerFileHandler = None
LocalRunHandler = None
DockerRunHandler = None

# Integration services (modules have been removed)
EnvWorkflowService = None
EnvResourceController = None
RunWorkflowBuilder = None

# Legacy support has been removed
# Use env_core directly for new implementations

__all__ = [
    # Core
    "Step",
    "StepType", 
    "StepContext",
    "GraphBasedWorkflowBuilder",
    "RequestExecutionGraph",
    
    # Factories
    "RequestFactorySelector",
    "BaseCommandRequestFactory",
    
    # Resource handlers
    "LocalFileHandler",
    "DockerFileHandler",
    "LocalRunHandler", 
    "DockerRunHandler",
    
    # Integration services
    "EnvWorkflowService",
    "EnvResourceController",
    "RunWorkflowBuilder"
]
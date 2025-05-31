"""
Environment module - Backward compatibility layer

This module provides backward compatibility by re-exporting classes
from the new modular structure. For new code, prefer importing
directly from the specific modules.
"""

# Core workflow engine
from src.env_core.step import Step, StepType, StepContext
from src.env_core.workflow import GraphBasedWorkflowBuilder, RequestExecutionGraph

# Request factories (avoid circular import)
from src.env_factories.base.factory import BaseCommandRequestFactory
try:
    from src.env_factories.unified_selector import UnifiedFactorySelector as RequestFactorySelector
except ImportError:
    RequestFactorySelector = None

# Resource management
from src.env_resource.file import LocalFileHandler, DockerFileHandler
from src.env_resource.run import LocalRunHandler, DockerRunHandler

# Integration services
from src.env_integration.service import EnvWorkflowService
from src.env_integration.controller import EnvResourceController
from src.env_integration.builder import RunWorkflowBuilder

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
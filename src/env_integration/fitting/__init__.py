"""
Fitting functionality for environment preparation - New pluggable architecture
"""

# Legacy compatibility - maintains existing interface
# Core module removed, using direct imports
from .docker_state_manager import DockerStateManager
from .environment_inspector import EnvironmentInspector  
from .preparation_executor import PreparationExecutor
from .preparation_error_handler import PreparationErrorHandler

__all__ = [
    # Legacy compatibility (existing interfaces)
    "EnvironmentInspector",
    "PreparationExecutor", 
    "DockerStateManager",
    "PreparationErrorHandler"
]
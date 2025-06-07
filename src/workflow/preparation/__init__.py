"""Fitting functionality for environment preparation - New pluggable architecture
"""

# Legacy compatibility - maintains existing interface
# Core module removed, using direct imports
from .docker_state_manager import DockerStateManager
from .environment_inspector import EnvironmentInspector
from .preparation_error_handler import PreparationErrorHandler
from .preparation_executor import PreparationExecutor

__all__ = [
    "DockerStateManager",
    # Legacy compatibility (existing interfaces)
    "EnvironmentInspector",
    "PreparationErrorHandler",
    "PreparationExecutor"
]

"""Fitting functionality for environment preparation - Simplified architecture
"""

# Core preparation components still in use
from .core.preparation_error_handler import PreparationErrorHandler
from .core.state_definitions import WorkflowContext, WorkflowState, validate_file_preparation

# Docker state management (still needed for Docker operations)
from .docker.docker_state_manager import DockerStateManager

# Environment preparation (still needed for Docker setup)
from .execution.environment_inspector import EnvironmentInspector
from .execution.preparation_executor import PreparationExecutor

# File operations (still needed by ProblemWorkspaceService)
from .file.folder_mapping import FolderMapper, create_folder_mapper_from_env

__all__ = [
    "DockerStateManager",
    "EnvironmentInspector",
    "FolderMapper",
    "PreparationErrorHandler",
    "PreparationExecutor",
    "WorkflowContext",
    "WorkflowState",
    "create_folder_mapper_from_env",
    "validate_file_preparation"
]

"""Fitting functionality for environment preparation - New pluggable architecture
"""

# Legacy compatibility - maintains existing interface
# Core module removed, using direct imports
from .command_processor import CommandProcessor, FilePreparationDriver, FilePreparationRequest
from .docker_state_manager import DockerStateManager
from .environment_inspector import EnvironmentInspector
from .folder_mapping import FolderMapper, create_folder_mapper_from_env
from .preparation_error_handler import PreparationErrorHandler
from .preparation_executor import PreparationExecutor

# State management components
from .state_definitions import WorkflowContext, WorkflowState, validate_file_preparation
from .state_manager import StateManager
from .transition_engine import TransitionEngine, TransitionStep

__all__ = [
    "CommandProcessor",
    "DockerStateManager",
    # Legacy compatibility (existing interfaces)
    "EnvironmentInspector",
    "FilePreparationDriver",
    "FilePreparationRequest",
    "FolderMapper",
    "PreparationErrorHandler",
    "PreparationExecutor",
    "StateManager",
    "TransitionEngine",
    "TransitionStep",
    "WorkflowContext",
    # State management
    "WorkflowState",
    "create_folder_mapper_from_env",
    "validate_file_preparation"
]

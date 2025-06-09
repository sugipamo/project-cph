"""Fitting functionality for environment preparation - New pluggable architecture
"""

# Legacy compatibility - maintains existing interface
# Core module removed, using direct imports
from .core.preparation_error_handler import PreparationErrorHandler

# State management components
from .core.state_definitions import WorkflowContext, WorkflowState, validate_file_preparation
from .docker.docker_state_manager import DockerStateManager
from .execution.command_processor import CommandProcessor, FilePreparationDriver, FilePreparationRequest
from .execution.environment_inspector import EnvironmentInspector
from .execution.preparation_executor import PreparationExecutor
from .file.folder_mapping import FolderMapper, create_folder_mapper_from_env
from .state.conditions.condition_evaluator import TransitionStep
from .state.management.state_manager import StateManager
from .state.transition.transition_engine import TransitionEngine

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

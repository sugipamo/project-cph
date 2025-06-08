"""Fitting functionality for environment preparation - New pluggable architecture
"""

# Legacy compatibility - maintains existing interface
# Core module removed, using direct imports
from .docker_state_manager import DockerStateManager
from .environment_inspector import EnvironmentInspector
from .preparation_error_handler import PreparationErrorHandler
from .preparation_executor import PreparationExecutor

# State management components
from .state_definitions import WorkflowState, WorkflowContext, validate_state_transition
from .state_manager import StateManager
from .transition_engine import TransitionEngine, TransitionStep
from .command_processor import CommandProcessor, StateTransitionRequest, StateTransitionDriver
from .folder_mapping import FolderMapper, create_folder_mapper_from_env

__all__ = [
    "DockerStateManager",
    # Legacy compatibility (existing interfaces)
    "EnvironmentInspector",
    "PreparationErrorHandler",
    "PreparationExecutor",
    # State management
    "WorkflowState",
    "WorkflowContext", 
    "validate_state_transition",
    "StateManager",
    "TransitionEngine",
    "TransitionStep",
    "CommandProcessor",
    "StateTransitionRequest",
    "StateTransitionDriver",
    "FolderMapper",
    "create_folder_mapper_from_env"
]

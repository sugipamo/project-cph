"""State management system for workflow transitions."""

from .state_definitions import (
    WorkflowState,
    WorkflowContext, 
    StateDefinition,
    get_state_definition,
    validate_state_transition
)

from .folder_mapping import (
    FolderArea,
    FolderMapper,
    create_folder_mapper_from_env
)

from .transition_engine import (
    TransitionEngine,
    TransitionStep,
    TransitionContext
)

from .state_manager import (
    StateManager
)

__all__ = [
    "WorkflowState",
    "WorkflowContext",
    "StateDefinition", 
    "get_state_definition",
    "validate_state_transition",
    "FolderArea",
    "FolderMapper",
    "create_folder_mapper_from_env",
    "TransitionEngine",
    "TransitionStep", 
    "TransitionContext",
    "StateManager"
]
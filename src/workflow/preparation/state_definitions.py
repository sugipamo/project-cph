"""State definitions for the problem-focused workflow system."""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum


class WorkflowState(Enum):
    """Available workflow states."""
    IDLE = "idle"
    WORKING = "working"


@dataclass
class WorkflowContext:
    """Context information for workflow state."""
    contest_name: Optional[str] = None
    problem_id: Optional[str] = None
    language: Optional[str] = None
    
    def is_valid_working_context(self) -> bool:
        """Check if context is valid for working state."""
        return all([
            self.contest_name,
            self.problem_id, 
            self.language
        ])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "contest_name": self.contest_name,
            "problem_id": self.problem_id,
            "language": self.language
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowContext":
        """Create from dictionary."""
        return cls(
            contest_name=data.get("contest_name"),
            problem_id=data.get("problem_id"),
            language=data.get("language")
        )
    
    def matches(self, other: "WorkflowContext") -> bool:
        """Check if contexts match for transition optimization."""
        return (
            self.contest_name == other.contest_name and
            self.problem_id == other.problem_id and
            self.language == other.language
        )


@dataclass
class StateDefinition:
    """Definition of a workflow state."""
    name: WorkflowState
    description: str
    required_context: bool
    working_directory_type: str
    
    def validate_context(self, context: WorkflowContext) -> bool:
        """Validate if context is appropriate for this state."""
        if self.required_context:
            return context.is_valid_working_context()
        return True


# State definitions
STATE_DEFINITIONS = {
    WorkflowState.IDLE: StateDefinition(
        name=WorkflowState.IDLE,
        description="No active problem work",
        required_context=False,
        working_directory_type="empty_or_irrelevant"
    ),
    WorkflowState.WORKING: StateDefinition(
        name=WorkflowState.WORKING,
        description="Active work on specific problem",
        required_context=True,
        working_directory_type="single_problem_files"
    )
}


def get_state_definition(state: WorkflowState) -> StateDefinition:
    """Get definition for a state."""
    return STATE_DEFINITIONS[state]


def validate_state_transition(
    from_state: WorkflowState,
    to_state: WorkflowState,
    context: WorkflowContext
) -> tuple[bool, str]:
    """Validate if state transition is possible."""
    to_definition = get_state_definition(to_state)
    
    if not to_definition.validate_context(context):
        return False, f"Invalid context for {to_state.value} state"
    
    return True, "Valid transition"
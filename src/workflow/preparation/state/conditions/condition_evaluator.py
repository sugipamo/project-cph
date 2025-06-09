"""Condition evaluation system for state transitions."""
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ...core.state_definitions import WorkflowContext, WorkflowState
from ...file.folder_mapping import FolderMapper


@dataclass
class TransitionStep:
    """Represents a single step in a state transition."""
    name: str
    condition: Optional[str]
    action: Dict[str, Any]
    description: Optional[str] = None


@dataclass
class TransitionContext:
    """Context for executing transitions."""
    current_state: WorkflowState
    current_context: WorkflowContext
    target_state: WorkflowState
    target_context: WorkflowContext
    folder_mapper: FolderMapper
    dry_run: bool = False

    def evaluate_condition(self, condition: str) -> bool:
        """Evaluate a condition string."""
        # Simple condition evaluation
        # Format: "current_state=working AND working_area.has_changes"

        conditions = condition.split(" AND ")
        for cond in conditions:
            cond = cond.strip()

            if not self._evaluate_single_condition(cond):
                return False

        return True

    def _evaluate_single_condition(self, condition: str) -> bool:
        """Evaluate a single condition."""
        if "=" in condition:
            left, right = condition.split("=", 1)
            left = left.strip()
            right = right.strip()

            if left == "current_state":
                return self.current_state.value == right
            if left == "target_state":
                return self.target_state.value == right

        elif condition == "working_area.has_changes" or condition == "working_area.has_files":
            return self.folder_mapper.area_has_files("working_area", self.current_context)
        elif condition.startswith("archive_area.") and condition.endswith(".exists"):
            # Extract contest and problem from condition like "archive_area.abc123.a.exists"
            parts = condition.split(".")
            if len(parts) >= 4:
                contest_name = parts[1]
                problem_name = parts[2]
                archive_context = WorkflowContext(contest_name=contest_name, problem_name=problem_name, language="dummy")
                return self.folder_mapper.area_exists("archive_area", archive_context)
        elif condition == "workspace_area.test.exists":
            test_path = self.folder_mapper.get_area_path("workspace_area", self.current_context) / "test"
            return test_path.exists()
        elif condition == "always":
            return True

        return False


class ConditionEvaluator:
    """Evaluates conditions for state transitions."""

    @staticmethod
    def create_context(
        current_state: WorkflowState,
        current_context: WorkflowContext,
        target_state: WorkflowState,
        target_context: WorkflowContext,
        folder_mapper: FolderMapper,
        dry_run: bool = False
    ) -> TransitionContext:
        """Create a transition context for condition evaluation."""
        return TransitionContext(
            current_state=current_state,
            current_context=current_context,
            target_state=target_state,
            target_context=target_context,
            folder_mapper=folder_mapper,
            dry_run=dry_run
        )

    @staticmethod
    def evaluate(context: TransitionContext, condition: str) -> bool:
        """Evaluate a condition in the given context."""
        return context.evaluate_condition(condition)

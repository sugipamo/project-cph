"""Lightweight transition engine that orchestrates state changes."""
import logging
from typing import List, Tuple

from src.infrastructure.drivers.file.file_driver import FileDriver

from ...core.state_definitions import WorkflowContext, WorkflowState
from ...file.folder_mapping import FolderMapper
from ..actions.file_action_executor import FileActionExecutor
from ..conditions.condition_evaluator import ConditionEvaluator, TransitionContext, TransitionStep


class TransitionEngine:
    """Lightweight transition engine that orchestrates state changes."""

    def __init__(self, folder_mapper: FolderMapper, file_driver: FileDriver):
        """Initialize transition engine with required dependencies."""
        self.folder_mapper = folder_mapper
        self.file_driver = file_driver
        self.action_executor = FileActionExecutor(folder_mapper, file_driver)
        self.logger = logging.getLogger(__name__)

    def execute_transition(
        self,
        current_state: WorkflowState,
        current_context: WorkflowContext,
        target_state: WorkflowState,
        target_context: WorkflowContext,
        transition_steps: List[TransitionStep],
        dry_run: bool = False
    ) -> Tuple[bool, List[str]]:
        """Execute a state transition."""

        # Create transition context for condition evaluation
        context = ConditionEvaluator.create_context(
            current_state=current_state,
            current_context=current_context,
            target_state=target_state,
            target_context=target_context,
            folder_mapper=self.folder_mapper,
            dry_run=dry_run
        )

        # Use provided transition steps
        steps = transition_steps

        results = []

        # Execute each step
        for step in steps:
            try:
                # Check if step should be executed based on condition
                if step.condition and not ConditionEvaluator.evaluate(context, step.condition):
                    results.append(f"⏭️  スキップ: {step.name} ({step.condition})")
                    continue

                # Execute the step action
                success, message = self.action_executor.execute_action(step.action, context)

                if success:
                    results.append(f"✅ {step.name}: {message}")
                else:
                    error_msg = f"❌ {step.name} failed: {message}"
                    results.append(error_msg)
                    self.logger.error(error_msg, exc_info=True)
                    return False, results

            except Exception as e:
                error_msg = f"❌ {step.name} error: {e!s}"
                results.append(error_msg)
                self.logger.error(error_msg, exc_info=True)
                return False, results

        return True, results


# Re-export for backward compatibility
__all__ = ["TransitionContext", "TransitionEngine", "TransitionStep"]

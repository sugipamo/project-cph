"""Transition engine for executing state changes with auto-steps."""
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from src.infrastructure.drivers.file.file_driver import FileDriver

from .folder_mapping import FolderMapper
from .state_definitions import WorkflowContext, WorkflowState


@dataclass
class TransitionStep:
    """Represents a single transition step."""
    name: str
    condition: Optional[str]
    action: Dict[str, Any]
    description: Optional[str] = None

    def should_execute(self, context: "TransitionContext") -> bool:
        """Check if this step should be executed based on condition."""
        if not self.condition:
            return True

        return context.evaluate_condition(self.condition)


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
        elif condition == "exists":
            return True  # Context-dependent, handled by caller

        return False


class TransitionEngine:
    """Engine for executing state transitions."""

    def __init__(self, folder_mapper: FolderMapper, file_driver: FileDriver):
        """Initialize with folder mapper and file driver."""
        self.folder_mapper = folder_mapper
        self.file_driver = file_driver
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
        """Execute a state transition with given steps."""

        context = TransitionContext(
            current_state=current_state,
            current_context=current_context,
            target_state=target_state,
            target_context=target_context,
            folder_mapper=self.folder_mapper,
            dry_run=dry_run
        )

        results = []

        for step in transition_steps:
            try:
                if step.should_execute(context):
                    success, message = self._execute_step(step, context)
                    results.append(f"✓ {step.name}: {message}" if success else f"✗ {step.name}: {message}")

                    if not success:
                        return False, results
                else:
                    results.append(f"⊘ {step.name}: skipped (condition not met)")

            except Exception as e:
                error_msg = f"Error in {step.name}: {e!s}"
                results.append(f"✗ {step.name}: {error_msg}")
                self.logger.error(error_msg, exc_info=True)
                return False, results

        return True, results

    def _execute_step(self, step: TransitionStep, context: TransitionContext) -> Tuple[bool, str]:
        """Execute a single transition step."""
        action = step.action
        action_type = action.get("type")

        if action_type == "archive":
            return self._execute_archive(action, context)
        if action_type == "restore_or_create":
            return self._execute_restore_or_create(action, context)
        if action_type == "move":
            return self._execute_move(action, context)
        if action_type == "cleanup":
            return self._execute_cleanup(action, context)
        return False, f"Unknown action type: {action_type}"

    def _execute_archive(self, action: Dict[str, Any], context: TransitionContext) -> Tuple[bool, str]:
        """Execute archive action."""
        from_area = action.get("from")
        to_area = action.get("to")
        mode = action.get("mode", "move_all")

        # Resolve paths
        if from_area == "working_area":
            from_path = self.folder_mapper.get_area_path("working_area", context.current_context)
        else:
            return False, f"Unknown from area: {from_area}"

        # Parse to_area like "archive_area.{current_contest}.{current_problem}"
        if to_area.startswith("archive_area."):
            # Extract contest and problem context variables
            parts = to_area.split(".")
            if len(parts) >= 3:
                contest_var = parts[1]
                problem_var = parts[2]

                # Resolve variables
                contest_name = self._resolve_variable(contest_var, context)
                problem_name = self._resolve_variable(problem_var, context)

                archive_context = WorkflowContext(
                    contest_name=contest_name,
                    problem_name=problem_name,
                    language=context.current_context.language
                )
                to_path = self.folder_mapper.get_area_path("archive_area", archive_context)
            else:
                return False, f"Invalid archive area format: {to_area}"
        else:
            return False, f"Unknown to area: {to_area}"

        if not from_path.exists():
            return True, f"Source {from_path} does not exist, nothing to archive"

        if not self.folder_mapper.area_has_files("working_area", context.current_context):
            return True, "No files to archive"

        if context.dry_run:
            return True, f"Would archive {from_path} to {to_path}"

        # Execute the archive
        try:
            self.folder_mapper.ensure_area_exists("archive_area", archive_context)

            if mode == "move_all":
                # Move all files from working area to archive
                for item in from_path.iterdir():
                    dest = to_path / item.name
                    if item.is_file():
                        if dest.exists():
                            self.file_driver.remove(dest)
                        self.file_driver.move(item, dest)
                    elif item.is_dir():
                        if dest.exists():
                            self.file_driver.rmtree(dest)
                        self.file_driver.move(item, dest)

                return True, f"Archived {from_path} to {to_path}"
            return False, f"Unknown archive mode: {mode}"

        except Exception as e:
            return False, f"Archive failed: {e!s}"

    def _execute_restore_or_create(self, action: Dict[str, Any], context: TransitionContext) -> Tuple[bool, str]:
        """Execute restore_or_create action."""
        to_area = action.get("to")
        source_priority = action.get("source_priority", [])

        if to_area != "working_area":
            return False, f"Unknown to area: {to_area}"

        to_path = self.folder_mapper.get_area_path("working_area", context.target_context)

        # Try sources in priority order
        for source in source_priority:
            from_area = source.get("from")
            condition = source.get("condition", "always")
            source.get("priority", 999)
            description = source.get("description", "")

            # Check condition
            if condition == "exists":
                if from_area.startswith("archive_area."):
                    # Check if archive exists for target context
                    if not self.folder_mapper.area_exists("archive_area", context.target_context):
                        continue
                elif from_area == "template_area" and not self.folder_mapper.area_exists("template_area", context.target_context):
                    continue
            elif condition != "always" and not context.evaluate_condition(condition):
                continue

            # Try to restore from this source
            if from_area.startswith("archive_area."):
                from_path = self.folder_mapper.get_area_path("archive_area", context.target_context)
            elif from_area == "template_area":
                from_path = self.folder_mapper.get_area_path("template_area", context.target_context)
            else:
                continue

            if from_path.exists() and any(from_path.iterdir()):
                if context.dry_run:
                    return True, f"Would restore from {from_path} ({description})"

                # Execute the restore
                try:
                    self.folder_mapper.ensure_area_exists("working_area", context.target_context)

                    # Copy all files from source to working area
                    for item in from_path.iterdir():
                        dest = to_path / item.name
                        if item.is_file():
                            self.file_driver.copy(item, dest)
                        elif item.is_dir():
                            if dest.exists():
                                self.file_driver.rmtree(dest)
                            self.file_driver.copytree(item, dest)

                    return True, f"Restored from {from_path} ({description})"

                except Exception as e:
                    return False, f"Restore failed: {e!s}"

        return False, "No valid source found for restore"

    def _execute_move(self, action: Dict[str, Any], context: TransitionContext) -> Tuple[bool, str]:
        """Execute move action."""
        from_spec = action.get("from")
        to_spec = action.get("to")

        # Handle workspace.test -> working_area.test
        if from_spec == "workspace_area.test" and to_spec == "working_area.test":
            from_path = self.folder_mapper.get_area_path("workspace_area", context.current_context) / "test"
            to_path = self.folder_mapper.get_area_path("working_area", context.target_context) / "test"

            if not from_path.exists():
                return True, "Source test directory does not exist, nothing to move"

            if context.dry_run:
                return True, f"Would move {from_path} to {to_path}"

            try:
                if to_path.exists():
                    self.file_driver.rmtree(to_path)
                self.file_driver.move(from_path, to_path)
                return True, f"Moved {from_path} to {to_path}"

            except Exception as e:
                return False, f"Move failed: {e!s}"

        return False, f"Unknown move specification: {from_spec} -> {to_spec}"

    def _execute_cleanup(self, action: Dict[str, Any], context: TransitionContext) -> Tuple[bool, str]:
        """Execute cleanup action."""
        target = action.get("target")

        if target == "working_area":
            target_path = self.folder_mapper.get_area_path("working_area", context.current_context)

            if not target_path.exists():
                return True, "Working area does not exist, nothing to clean"

            if context.dry_run:
                return True, f"Would clean {target_path}"

            try:
                # Remove all contents but keep the directory
                for item in target_path.iterdir():
                    if item.is_file():
                        self.file_driver.remove(item)
                    elif item.is_dir():
                        self.file_driver.rmtree(item)

                return True, f"Cleaned {target_path}"

            except Exception as e:
                return False, f"Cleanup failed: {e!s}"

        return False, f"Unknown cleanup target: {target}"

    def _resolve_variable(self, variable: str, context: TransitionContext) -> str:
        """Resolve a variable like {current_contest} or {contest_name}."""
        if variable.startswith("{") and variable.endswith("}"):
            var_name = variable[1:-1]

            if var_name == "current_contest":
                return context.current_context.contest_name or ""
            if var_name == "current_problem":
                return context.current_context.problem_name or ""
            if var_name == "contest_name":
                return context.target_context.contest_name or ""
            if var_name == "problem_name":
                return context.target_context.problem_name or ""

        return variable

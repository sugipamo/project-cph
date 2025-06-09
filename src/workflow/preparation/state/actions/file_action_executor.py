"""File action execution system for state transitions."""
import logging
from typing import Any, Dict, Tuple

from src.infrastructure.drivers.file.file_driver import FileDriver

from ...core.state_definitions import WorkflowContext
from ...file.folder_mapping import FolderMapper
from ..conditions.condition_evaluator import TransitionContext


class FileActionExecutor:
    """Executes file operations for state transitions."""

    def __init__(self, folder_mapper: FolderMapper, file_driver: FileDriver):
        """Initialize with folder mapper and file driver."""
        self.folder_mapper = folder_mapper
        self.file_driver = file_driver
        self.logger = logging.getLogger(__name__)

    def execute_action(self, action: Dict[str, Any], context: TransitionContext) -> Tuple[bool, str]:
        """Execute a single file action."""
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
            mode = source.get("mode", "copy_all")

            if from_area.startswith("archive_area."):
                # Extract contest and problem from archive area
                parts = from_area.split(".")
                if len(parts) >= 3:
                    contest_var = parts[1]
                    problem_var = parts[2]

                    # Resolve variables
                    contest_name = self._resolve_variable(contest_var, context)
                    problem_name = self._resolve_variable(problem_var, context)

                    archive_context = WorkflowContext(
                        contest_name=contest_name,
                        problem_name=problem_name,
                        language=context.target_context.language
                    )
                    from_path = self.folder_mapper.get_area_path("archive_area", archive_context)

                    if from_path.exists() and self.folder_mapper.area_has_files("archive_area", archive_context):
                        if context.dry_run:
                            return True, f"Would restore from {from_path} to {to_path}"

                        try:
                            self.folder_mapper.ensure_area_exists("working_area", context.target_context)

                            if mode == "copy_all":
                                for item in from_path.iterdir():
                                    dest = to_path / item.name
                                    if item.is_file():
                                        if dest.exists():
                                            self.file_driver.remove(dest)
                                        self.file_driver.copy(item, dest)
                                    elif item.is_dir():
                                        if dest.exists():
                                            self.file_driver.rmtree(dest)
                                        self.file_driver.copytree(item, dest)

                                return True, f"Restored from {from_path} to {to_path}"

                        except Exception as e:
                            self.logger.warning(f"Failed to restore from {from_path}: {e}")
                            # Try next source
                            continue

            elif from_area == "template_area":
                from_path = self.folder_mapper.get_area_path("template_area", context.target_context)

                if from_path.exists():
                    if context.dry_run:
                        return True, f"Would create from template {from_path} to {to_path}"

                    try:
                        self.folder_mapper.ensure_area_exists("working_area", context.target_context)

                        if mode == "copy_all":
                            for item in from_path.iterdir():
                                dest = to_path / item.name
                                if item.is_file():
                                    if not dest.exists():  # Don't overwrite existing files from template
                                        self.file_driver.copy(item, dest)
                                elif item.is_dir() and not dest.exists():
                                    self.file_driver.copytree(item, dest)

                            return True, f"Created from template {from_path} to {to_path}"

                    except Exception as e:
                        self.logger.warning(f"Failed to create from template {from_path}: {e}")
                        continue

        return False, "No suitable source found for restore_or_create"

    def _execute_move(self, action: Dict[str, Any], context: TransitionContext) -> Tuple[bool, str]:
        """Execute move action."""
        from_area = action.get("from")
        to_area = action.get("to")
        file_pattern = action.get("files", "*")

        if from_area == "workspace_area":
            from_path = self.folder_mapper.get_area_path("workspace_area", context.current_context)
        else:
            return False, f"Unknown from area: {from_area}"

        if to_area == "working_area":
            to_path = self.folder_mapper.get_area_path("working_area", context.target_context)
        else:
            return False, f"Unknown to area: {to_area}"

        if context.dry_run:
            return True, f"Would move files {file_pattern} from {from_path} to {to_path}"

        try:
            self.folder_mapper.ensure_area_exists("working_area", context.target_context)

            moved_count = 0
            if file_pattern == "*":
                # Move all files
                for item in from_path.iterdir():
                    dest = to_path / item.name
                    if item.is_file():
                        if dest.exists():
                            self.file_driver.remove(dest)
                        self.file_driver.move(item, dest)
                        moved_count += 1
                    elif item.is_dir():
                        if dest.exists():
                            self.file_driver.rmtree(dest)
                        self.file_driver.move(item, dest)
                        moved_count += 1
            else:
                # Move specific pattern (basic implementation)
                for item in from_path.glob(file_pattern):
                    dest = to_path / item.name
                    if item.is_file():
                        if dest.exists():
                            self.file_driver.remove(dest)
                        self.file_driver.move(item, dest)
                        moved_count += 1

            return True, f"Moved {moved_count} items from {from_path} to {to_path}"

        except Exception as e:
            return False, f"Move failed: {e!s}"

    def _execute_cleanup(self, action: Dict[str, Any], context: TransitionContext) -> Tuple[bool, str]:
        """Execute cleanup action."""
        area = action.get("area")

        if area == "working_area":
            area_path = self.folder_mapper.get_area_path("working_area", context.current_context)
        else:
            return False, f"Unknown cleanup area: {area}"

        if not area_path.exists():
            return True, f"Area {area_path} does not exist, nothing to clean"

        if context.dry_run:
            return True, f"Would clean {area_path}"

        try:
            # Remove all contents but keep the directory
            for item in area_path.iterdir():
                if item.is_file():
                    self.file_driver.remove(item)
                elif item.is_dir():
                    self.file_driver.rmtree(item)

            return True, f"Cleaned {area_path}"

        except Exception as e:
            return False, f"Cleanup failed: {e!s}"

    def _resolve_variable(self, variable: str, context: TransitionContext) -> str:
        """Resolve a variable in the context."""
        if variable.startswith("{") and variable.endswith("}"):
            var_name = variable[1:-1]
            if var_name == "current_contest":
                return context.current_context.contest_name
            if var_name == "current_problem":
                return context.current_context.problem_name
            if var_name == "target_contest":
                return context.target_context.contest_name
            if var_name == "target_problem":
                return context.target_context.problem_name
        return variable

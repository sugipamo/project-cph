"""Problem workspace management service - simplified replacement for complex state system."""
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Tuple

from src.domain.interfaces.logger_interface import LoggerInterface
from src.infrastructure.drivers.file.file_driver import FileDriver
from src.infrastructure.persistence.sqlite.repositories.file_preparation_repository import FilePreparationRepository


@dataclass
class WorkspaceInfo:
    """Current workspace information."""
    is_working: bool
    current_contest: Optional[str] = None
    current_problem: Optional[str] = None
    current_language: Optional[str] = None
    workspace_files_count: int = 0


@dataclass
class SwitchResult:
    """Result of switching to a problem workspace."""
    success: bool
    message: str
    files_moved: int = 0
    workspace_info: Optional[WorkspaceInfo] = None


@dataclass
class ArchiveResult:
    """Result of archiving current work."""
    success: bool
    message: str
    archived_files: int = 0
    archive_path: Optional[Path] = None


@dataclass
class RestoreResult:
    """Result of restoring workspace."""
    success: bool
    message: str
    restored_files: int = 0
    source_type: str = ""  # "archive" or "template"


class ProblemWorkspaceService:
    """Service for managing problem workspace transitions and file operations.

    Replaces the complex StateManager/TransitionEngine/StepBuilder system
    with a simple, direct service approach.
    """

    def __init__(
        self,
        file_driver: FileDriver,
        repository: FilePreparationRepository,
        logger: LoggerInterface,
        base_paths: dict,
        file_preparation_service: Optional[Any] = None
    ):
        """Initialize the workspace service.

        Args:
            file_driver: File driver for file operations
            repository: Repository for tracking operations
            logger: Logger for logging operations
            base_paths: Dictionary with paths like:
                - contest_current_path: Current working directory
                - contest_stock_path: Archive storage directory
                - contest_template_path: Template directory
                - workspace_path: Temporary workspace directory
            file_preparation_service: Optional service for file operations integration
        """
        self.file_driver = file_driver
        self.repository = repository
        self.logger = logger
        self.base_paths = base_paths
        self.file_preparation_service = file_preparation_service

    def switch_to_problem(
        self,
        contest: str,
        problem: str,
        language: str,
        force: bool = False
    ) -> SwitchResult:
        """Switch to working on a specific problem.

        This is the main entry point that replaces the complex state transition system.

        Args:
            contest: Contest name (e.g. "abc300")
            problem: Problem name (e.g. "a")
            language: Language name (e.g. "python")
            force: Force switch even if already working on this problem

        Returns:
            SwitchResult with success status and details
        """
        current_info = self.get_current_workspace_info()

        # Check if already working on this problem
        if not force and current_info.is_working and (current_info.current_contest == contest and
            current_info.current_problem == problem and
            current_info.current_language == language):
            return SwitchResult(
                success=True,
                message=f"Already working on {contest}/{problem} in {language}",
                workspace_info=current_info
            )

        try:
            total_files_moved = 0

            # Step 1: Archive current work if any exists and we know what it is
            if current_info.is_working and current_info.current_contest and current_info.current_problem:
                archive_result = self.archive_current_work()
                if not archive_result.success:
                    return SwitchResult(
                        success=False,
                        message=f"Failed to archive current work: {archive_result.message}"
                    )
                self.logger.info(f"Archived current work: {archive_result.message}")
            elif current_info.is_working:
                # Files exist but we don't know what problem they're for - just clear them
                self.logger.warning("Current workspace has files but no problem information - clearing without archiving")
                contest_current_path = Path(self.base_paths["contest_current_path"])
                if self.file_driver.exists(contest_current_path):
                    self.file_driver.rmtree(contest_current_path)

            # Step 2: Restore or create workspace for target problem
            restore_result = self.restore_or_create_workspace(contest, problem, language)
            if not restore_result.success:
                return SwitchResult(
                    success=False,
                    message=f"Failed to setup workspace: {restore_result.message}"
                )

            total_files_moved += restore_result.restored_files

            # Step 3: Move test files from workspace to current
            if self.file_preparation_service:
                # Use pattern-based file preparation service
                success, message, file_count = self.file_preparation_service.move_files_by_patterns(
                    "move_test_files", language, contest, problem,
                    self.base_paths.get("workspace_path", ""),
                    self.base_paths["contest_current_path"],
                    self.base_paths.get("contest_stock_path", ""),
                    force
                )
                if success:
                    total_files_moved += file_count
                    self.logger.info(f"Test files moved: {message}")
            else:
                # Fallback to internal implementation
                move_result = self._move_test_files(contest, problem, language)
                if move_result[0]:  # success
                    total_files_moved += move_result[2]  # file_count
                    self.logger.info(f"Test files moved: {move_result[1]}")

            # Step 4: Update workspace info
            new_info = WorkspaceInfo(
                is_working=True,
                current_contest=contest,
                current_problem=problem,
                current_language=language,
                workspace_files_count=total_files_moved
            )

            self._save_workspace_info(new_info)

            message = f"Successfully switched to {contest}/{problem} ({language})"
            if restore_result.source_type:
                message += f" from {restore_result.source_type}"

            return SwitchResult(
                success=True,
                message=message,
                files_moved=total_files_moved,
                workspace_info=new_info
            )

        except Exception as e:
            error_msg = f"Failed to switch to {contest}/{problem}: {e!s}"
            self.logger.error(error_msg)
            return SwitchResult(success=False, message=error_msg)

    def archive_current_work(self) -> ArchiveResult:
        """Archive current working files to contest_stock."""
        current_info = self.get_current_workspace_info()

        if not current_info.is_working:
            return ArchiveResult(
                success=True,
                message="No current work to archive"
            )

        try:
            contest_current_path = Path(self.base_paths["contest_current_path"])
            archive_base_path = Path(self.base_paths["contest_stock_path"])

            archive_path = (archive_base_path /
                          current_info.current_contest /
                          current_info.current_problem)

            if not self.file_driver.exists(contest_current_path):
                return ArchiveResult(
                    success=True,
                    message="No files to archive",
                    archive_path=archive_path
                )

            # Ensure archive directory exists
            if not self.file_driver.exists(archive_path.parent):
                self.file_driver.makedirs(archive_path.parent, exist_ok=True)

            # Remove existing archive if it exists
            if self.file_driver.exists(archive_path):
                self.file_driver.rmtree(archive_path)

            # Copy current work to archive
            self.file_driver.copytree(contest_current_path, archive_path)

            # Count archived files
            archived_files = self._count_files_in_directory(archive_path)

            message = f"Archived {archived_files} files for {current_info.current_contest}/{current_info.current_problem}"
            self.logger.info(message)

            return ArchiveResult(
                success=True,
                message=message,
                archived_files=archived_files,
                archive_path=archive_path
            )

        except Exception as e:
            error_msg = f"Failed to archive current work: {e!s}"
            self.logger.error(error_msg)
            return ArchiveResult(success=False, message=error_msg)

    def restore_or_create_workspace(
        self,
        contest: str,
        problem: str,
        language: str
    ) -> RestoreResult:
        """Restore workspace from archive or create from template."""
        try:
            contest_current_path = Path(self.base_paths["contest_current_path"])
            archive_path = Path(self.base_paths["contest_stock_path"]) / contest / problem
            template_path = Path(self.base_paths["contest_template_path"]) / language

            # Clear current workspace
            if self.file_driver.exists(contest_current_path):
                self.file_driver.rmtree(contest_current_path)

            # Try to restore from archive first
            if self.file_driver.exists(archive_path):
                self.file_driver.copytree(archive_path, contest_current_path)
                restored_files = self._count_files_in_directory(contest_current_path)

                # Create workspace directory for oj operations if configured
                workspace_path = self.base_paths.get("workspace_path", "")
                if workspace_path:
                    workspace_dir = Path(workspace_path)
                    self.file_driver.makedirs(workspace_dir, exist_ok=True)

                message = f"Restored {restored_files} files from archive"
                self.logger.info(message)

                return RestoreResult(
                    success=True,
                    message=message,
                    restored_files=restored_files,
                    source_type="archive"
                )

            # Create from template if no archive exists
            if self.file_driver.exists(template_path):
                self.file_driver.copytree(template_path, contest_current_path)
                created_files = self._count_files_in_directory(contest_current_path)

                # Create workspace directory for oj operations if configured
                workspace_path = self.base_paths.get("workspace_path", "")
                if workspace_path:
                    workspace_dir = Path(workspace_path)
                    self.file_driver.makedirs(workspace_dir, exist_ok=True)

                message = f"Created {created_files} files from template"
                self.logger.info(message)

                return RestoreResult(
                    success=True,
                    message=message,
                    restored_files=created_files,
                    source_type="template"
                )

            # Create empty workspace if no template exists
            self.file_driver.makedirs(contest_current_path, exist_ok=True)

            # Create workspace directory for oj operations if configured
            workspace_path = self.base_paths.get("workspace_path", "")
            if workspace_path:
                workspace_dir = Path(workspace_path)
                self.file_driver.makedirs(workspace_dir, exist_ok=True)

            message = "Created empty workspace (no template available)"
            self.logger.warning(message)

            return RestoreResult(
                success=True,
                message=message,
                restored_files=0,
                source_type="empty"
            )

        except Exception as e:
            error_msg = f"Failed to restore/create workspace: {e!s}"
            self.logger.error(error_msg)
            return RestoreResult(success=False, message=error_msg)

    def get_current_workspace_info(self) -> WorkspaceInfo:
        """Get information about the current workspace state."""
        try:
            # Try to load from repository/file
            info = self._load_workspace_info()
            if info:
                return info

            # Fallback: check if contest_current exists and has files
            contest_current_path = Path(self.base_paths["contest_current_path"])
            if self.file_driver.exists(contest_current_path):
                file_count = self._count_files_in_directory(contest_current_path)
                return WorkspaceInfo(
                    is_working=file_count > 0,
                    workspace_files_count=file_count
                )

            return WorkspaceInfo(is_working=False)

        except Exception as e:
            self.logger.error(f"Failed to get workspace info: {e!s}")
            return WorkspaceInfo(is_working=False)

    def cleanup_workspace(self, language: str, contest: str, problem: str) -> Tuple[bool, str]:
        """Clean up workspace after operations (wrapper for existing functionality)."""
        workspace_path = self.base_paths.get("workspace_path", "")
        if not workspace_path:
            return True, "No workspace path configured"

        # Use existing FilePreparationService if available
        if self.file_preparation_service:
            return self.file_preparation_service.cleanup_workspace_test(
                language, contest, problem, workspace_path
            )

        # Fallback to internal implementation
        try:
            workspace_test_dir = Path(workspace_path) / "test"
            if self.file_driver.exists(workspace_test_dir):
                self.file_driver.rmtree(workspace_test_dir)
                message = f"Cleaned up workspace test directory: {workspace_test_dir}"
                self.logger.info(message)
                return True, message
            return True, "No workspace to clean up"
        except Exception as e:
            error_msg = f"Failed to cleanup workspace: {e!s}"
            self.logger.error(error_msg)
            return False, error_msg

    def _move_test_files(self, contest: str, problem: str, language: str) -> Tuple[bool, str, int]:
        """Move test files from workspace to contest_current (internal helper)."""
        workspace_path = self.base_paths.get("workspace_path", "")
        contest_current_path = self.base_paths["contest_current_path"]

        if not workspace_path:
            return True, "No workspace path configured", 0

        source_test_dir = Path(workspace_path) / "test"
        dest_test_dir = Path(contest_current_path) / "test"

        try:
            if not self.file_driver.exists(source_test_dir):
                return True, "No test files to move", 0

            # Remove existing destination
            if self.file_driver.exists(dest_test_dir):
                self.file_driver.rmtree(dest_test_dir)

            # Move test directory
            self.file_driver.move(source_test_dir, dest_test_dir)

            # Count moved files
            file_count = self._count_files_in_directory(dest_test_dir)

            return True, f"Moved {file_count} test files", file_count

        except Exception as e:
            return False, f"Failed to move test files: {e!s}", 0

    def _count_files_in_directory(self, directory: Path) -> int:
        """Count files recursively in a directory."""
        try:
            if not self.file_driver.exists(directory):
                return 0

            count = 0
            for item in self.file_driver.list_files_recursive(directory):
                if self.file_driver.is_file(item):
                    count += 1
            return count

        except Exception:
            return 0

    def _save_workspace_info(self, info: WorkspaceInfo) -> None:
        """Save workspace info to persistent storage."""
        # This could save to repository or a simple JSON file
        # For now, we'll use the repository system
        try:
            if info.is_working:
                self.repository.record_operation(
                    info.current_language or "",
                    info.current_contest or "",
                    info.current_problem or "",
                    "workspace_switch",
                    "",
                    "",
                    info.workspace_files_count,
                    True,
                    "Workspace switched"
                )
        except Exception as e:
            self.logger.error(f"Failed to save workspace info: {e!s}")

    def _load_workspace_info(self) -> Optional[WorkspaceInfo]:
        """Load workspace info from persistent storage."""
        # This could load from repository or a simple JSON file
        # For now, return None to use fallback detection
        return None

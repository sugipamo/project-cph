"""Service for handling file preparation operations like test file movements."""

from pathlib import Path
from typing import List, Tuple

from src.domain.constants.operation_type import DirectoryName, WorkspaceOperationType
from src.domain.interfaces.logger_interface import LoggerInterface
from src.infrastructure.config.json_config_loader import JsonConfigLoader
from src.infrastructure.drivers.file.file_driver import FileDriver

from .file_pattern_service import FilePatternService


class FilePreparationService:
    """Service for managing file preparation operations."""

    def __init__(self, file_driver: FileDriver, repository, logger: LoggerInterface, config_loader: JsonConfigLoader, file_pattern_service: FilePatternService):
        """Initialize with file driver, repository, logger and config loader.

        Args:
            file_driver: File driver for file operations
            repository: Repository for operation tracking
            logger: Logger for logging operations
            config_loader: Configuration loader for accessing constants
            file_pattern_service: File pattern service for pattern-based operations
        """
        self.file_driver = file_driver
        self.repository = repository
        self.logger = logger
        self.config_loader = config_loader
        self.file_pattern_service = file_pattern_service

    def _check_operation_already_done(
        self,
        language_name: str,
        contest_name: str,
        problem_name: str,
        operation_name: str,
        force: bool
    ) -> Tuple[bool, str]:
        """Check if operation was already completed.

        Args:
            language_name: Programming language name
            contest_name: Contest identifier
            problem_name: Problem identifier
            operation_name: Name of the operation
            force: Whether to force re-execution

        Returns:
            Tuple of (already_done, message)
        """
        if force:
            return False, ""

        if self.repository.has_successful_operation(language_name, contest_name, problem_name, operation_name):
            return True, f"{operation_name} already completed"

        return False, ""

    def move_files_by_patterns(
        self,
        operation_name: str,
        language_name: str,
        contest_name: str,
        problem_name: str,
        workspace_path: str,
        contest_current_path: str,
        contest_stock_path: str = ""
    ) -> Tuple[bool, str, int]:
        """Move files based on pattern configuration.

        Args:
            operation_name: Name of the operation to execute
            language_name: Programming language name
            contest_name: Contest identifier
            problem_name: Problem identifier
            workspace_path: Path to workspace directory
            contest_current_path: Path to contest_current directory
            contest_stock_path: Path to contest_stock directory

        Returns:
            Tuple of (success, message, file_count)
        """
        # Check if operation was already completed
        already_done, message = self._check_operation_already_done(
            language_name, contest_name, problem_name, operation_name, False
        )
        if already_done:
            return True, message, 0

        # Prepare context for pattern service
        context = {
            "workspace_path": workspace_path,
            "contest_current_path": contest_current_path,
            "contest_stock_path": contest_stock_path,
            "language": language_name
        }

        try:
            # Execute pattern-based file operations
            result = self.file_pattern_service.execute_with_fallback(operation_name, context)

            # Record the operation if successful
            if result.success:
                self.repository.record_operation(
                    language_name, contest_name, problem_name, operation_name,
                    workspace_path, contest_current_path, result.files_processed, True
                )

            return result.success, result.message, result.files_processed

        except Exception as e:
            error_message = f"Pattern-based operation failed: {e}"
            self.logger.error(error_message)

            # Record the failed operation
            self.repository.record_operation(
                language_name, contest_name, problem_name, operation_name,
                workspace_path, contest_current_path, 0, False, str(e)
            )

            return False, error_message, 0



    def get_pattern_diagnosis(self, language_name: str) -> dict:
        """Get configuration diagnosis for pattern-based operations.

        Args:
            language_name: Programming language name

        Returns:
            Dictionary with diagnosis information
        """

        try:
            return self.file_pattern_service.diagnose_config_issues(language_name)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Diagnosis failed: {e}"
            }





    def cleanup_workspace_test(
        self,
        language_name: str,
        contest_name: str,
        problem_name: str,
        workspace_path: str
    ) -> Tuple[bool, str]:
        """Clean up workspace test directory after moving files.

        Args:
            language_name: Programming language name
            contest_name: Contest identifier
            problem_name: Problem identifier
            workspace_path: Path to workspace directory

        Returns:
            Tuple of (success, message)
        """
        workspace_test_dir = Path(workspace_path) / DirectoryName.TEST.value

        try:
            if self.file_driver.exists(workspace_test_dir):
                self.file_driver.rmtree(workspace_test_dir)
                message = f"Cleaned up workspace test directory: {workspace_test_dir}"
                self.logger.info(message)

                # Record cleanup operation
                self.repository.record_operation(
                    language_name, contest_name, problem_name, WorkspaceOperationType.CLEANUP_WORKSPACE.value,
                    str(workspace_test_dir), "", 0, True
                )

                return True, message
            message = f"Workspace test directory does not exist: {workspace_test_dir}"
            self.logger.info(message)
            return True, message

        except Exception as e:
            error_message = f"Failed to cleanup workspace test directory: {e!s}"
            self.logger.error(error_message)

            # Record failed cleanup
            self.repository.record_operation(
                language_name, contest_name, problem_name, WorkspaceOperationType.CLEANUP_WORKSPACE.value,
                str(workspace_test_dir), "", 0, False, error_message
            )

            return False, error_message

    def get_operation_history(
        self,
        language_name: str,
        contest_name: str,
        problem_name: str
    ) -> List[dict]:
        """Get file preparation operation history for a contest context.

        Args:
            language_name: Programming language name
            contest_name: Contest identifier
            problem_name: Problem identifier

        Returns:
            List of operation records
        """
        return self.repository.get_operations_by_context(
            language_name, contest_name, problem_name
        )

    def _count_files_recursively(self, directory: Path) -> int:
        """Count all files recursively in a directory.

        Args:
            directory: Directory to count files in

        Returns:
            Number of files found
        """
        count = 0
        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    count += 1
        except Exception as e:
            self.logger.warning(f"Error counting files in {directory}: {e}")
        return count

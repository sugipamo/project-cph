"""Service for handling file preparation operations like test file movements."""

from pathlib import Path
from typing import List, Tuple

from src.domain.constants.operation_type import DirectoryName, WorkspaceOperationType
from src.domain.interfaces.logger_interface import LoggerInterface
from src.infrastructure.config.json_config_loader import JsonConfigLoader
from src.infrastructure.drivers.file.file_driver import FileDriver
from src.infrastructure.persistence.sqlite.repositories.file_preparation_repository import FilePreparationRepository


class FilePreparationService:
    """Service for managing file preparation operations."""

    def __init__(self, file_driver: FileDriver, repository: FilePreparationRepository, logger: LoggerInterface, config_loader: JsonConfigLoader):
        """Initialize with file driver, repository, logger and config loader.

        Args:
            file_driver: File driver for file operations
            repository: Repository for tracking operations
            logger: Logger for logging operations
            config_loader: Configuration loader for accessing constants
        """
        self.file_driver = file_driver
        self.repository = repository
        self.logger = logger
        self.config_loader = config_loader

    def move_test_files(
        self,
        language_name: str,
        contest_name: str,
        problem_name: str,
        workspace_path: str,
        contest_current_path: str,
        force: bool = False
    ) -> Tuple[bool, str, int]:
        """Move test files from workspace/test to contest_current/test.

        Args:
            language_name: Programming language name
            contest_name: Contest identifier
            problem_name: Problem identifier
            workspace_path: Path to workspace directory
            contest_current_path: Path to contest_current directory
            force: Force move even if already done

        Returns:
            Tuple of (success, message, file_count)
        """
        # Check if operation was already completed
        operation_type = WorkspaceOperationType.MOVE_TEST_FILES.value
        already_done, done_message = self._check_operation_already_done(
            language_name, contest_name, problem_name, operation_type, force
        )
        if already_done:
            message = self.config_loader.get_message('test_files_already_moved')
            return True, message, 0

        test_dir_name = DirectoryName.TEST.value
        source_test_dir = Path(workspace_path) / test_dir_name
        dest_test_dir = Path(contest_current_path) / test_dir_name

        # Validate source directory exists
        is_valid, validation_message = self._validate_test_file_operation(
            source_test_dir, operation_type
        )
        if not is_valid:
            self.logger.info(validation_message)
            no_source_message = self.config_loader.get_message('no_source_directory')
            self._record_operation_result(
                language_name, contest_name, problem_name, operation_type,
                source_test_dir, dest_test_dir, 0, True, no_source_message
            )
            return True, validation_message, 0

        # Perform the file move operation
        success, message, file_count = self._perform_test_file_move(
            source_test_dir, dest_test_dir
        )

        # Record the operation result
        self._record_operation_result(
            language_name, contest_name, problem_name, operation_type,
            source_test_dir, dest_test_dir, file_count, success,
            message if not success else ""
        )

        return success, message, file_count

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
            force: Whether to force execution even if already done

        Returns:
            Tuple of (already_done, message)
        """
        if not force and self.repository.has_successful_operation(
            language_name, contest_name, problem_name, operation_name
        ):
            return True, f"{operation_name} already completed"
        return False, ""

    def _validate_test_file_operation(self, source_path: Path, operation_name: str) -> Tuple[bool, str]:
        """Validate preconditions for test file operations.

        Args:
            source_path: Source directory path
            operation_name: Name of the operation for error messages

        Returns:
            Tuple of (is_valid, message)
        """
        if not self.file_driver.exists(source_path):
            return False, f"Source directory does not exist: {source_path}"
        return True, ""

    def _perform_test_file_move(
        self,
        source_path: Path,
        dest_path: Path
    ) -> Tuple[bool, str, int]:
        """Perform the actual file move operation.

        Args:
            source_path: Source directory path
            dest_path: Destination directory path

        Returns:
            Tuple of (success, message, file_count)
        """
        try:
            # Ensure destination directory exists using file driver
            if not self.file_driver.exists(dest_path.parent):
                self.file_driver.makedirs(dest_path.parent, exist_ok=True)

            # Remove existing destination if it exists
            if self.file_driver.exists(dest_path):
                self.file_driver.rmtree(dest_path)
                self.logger.info(f"Removed existing destination: {dest_path}")

            # Move the entire test directory
            self.file_driver.move(source_path, dest_path)

            # Count files that were moved
            file_count = self._count_files_recursively(dest_path)

            message = f"Moved {file_count} test files from {source_path} to {dest_path}"
            self.logger.info(message)

            return True, message, file_count

        except Exception as e:
            error_message = f"Failed to move test files: {e!s}"
            self.logger.error(error_message)
            return False, error_message, 0

    def _record_operation_result(
        self,
        language_name: str,
        contest_name: str,
        problem_name: str,
        operation_name: str,
        source_path: Path,
        dest_path: Path,
        file_count: int,
        success: bool,
        message: str = ""
    ) -> None:
        """Record operation result in repository.

        Args:
            language_name: Programming language name
            contest_name: Contest identifier
            problem_name: Problem identifier
            operation_name: Name of the operation
            source_path: Source directory path
            dest_path: Destination directory path
            file_count: Number of files processed
            success: Whether operation succeeded
            message: Error message if operation failed
        """
        self.repository.record_operation(
            language_name, contest_name, problem_name, operation_name,
            str(source_path), str(dest_path), file_count, success, message
        )

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

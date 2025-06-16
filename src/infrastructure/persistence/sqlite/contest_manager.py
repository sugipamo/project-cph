"""Contest management system for handling contest_current backup and state detection."""
import os
from typing import Dict, List, Optional

from src.operations.requests.file.file_op_type import FileOpType
from src.operations.requests.file.file_request import FileRequest

from .system_config_loader import SystemConfigLoader


class ContestManager:
    """Manages contest state detection and backup operations."""

    def __init__(self, container, env_json: Dict):
        """Initialize contest manager with DI container and environment configuration."""
        self.container = container
        self.config_loader = SystemConfigLoader(container)
        self._file_driver = None
        self._env_json = env_json

    @property
    def env_json(self) -> Dict:
        """Lazy load env_json from config loader with shared config."""
        if not self._env_json:
            try:
                # Load shared env.json directly to ensure we have shared paths
                import json

                from src.operations.requests.file.file_op_type import FileOpType
                from src.operations.requests.file.file_request import FileRequest

                shared_path = "contest_env/shared/env.json"
                req = FileRequest(FileOpType.READ, shared_path)
                result = req.execute_operation(driver=self.file_driver)

                if result.success:
                    shared_config = json.loads(result.content)
                    self._env_json = shared_config
                else:
                    self._env_json = {}

            except Exception as e:
                print(f"Warning: Failed to load shared env.json: {e}")
                self._env_json = {}
        return self._env_json

    @property
    def file_driver(self):
        """Lazy load file driver."""
        if self._file_driver is None:
            from src.infrastructure.di_container import DIKey
            self._file_driver = self.container.resolve(DIKey.FILE_DRIVER)
        return self._file_driver

    @property
    def files_repo(self):
        """Lazy load contest current files repository."""
        if not hasattr(self, '_files_repo'):
            try:
                self._files_repo = self.container.resolve("contest_current_files_repository")
            except ValueError:
                # If repository not available, use None (simpler approach)
                self._files_repo = None
        return self._files_repo

    def get_current_contest_state(self) -> Dict[str, Optional[str]]:
        """Get current contest state from SQLite with fallback for NULL values.

        Returns:
            Dictionary with language_name, contest_name, problem_name
        """
        # Get current context
        current_context = self.config_loader.get_current_context()

        # Apply fallback logic for NULL values
        language = current_context.get("language")
        contest_name = current_context.get("contest_name")
        problem_name = current_context.get("problem_name")

        # If any value is NULL, get latest non-NULL from history
        if language is None:
            language = self._get_latest_non_null_value("language")
        if contest_name is None:
            contest_name = self._get_latest_non_null_value("contest_name")
        if problem_name is None:
            problem_name = self._get_latest_non_null_value("problem_name")

        return {
            "language_name": language,
            "contest_name": contest_name,
            "problem_name": problem_name
        }

    def _get_latest_non_null_value(self, key: str) -> Optional[str]:
        """Get latest non-NULL value for a specific key from SQLite history.

        Args:
            key: Configuration key (language, contest_name, problem_name)

        Returns:
            Latest non-NULL value or None if no non-NULL value found
        """
        try:
            from src.infrastructure.di_container import DIKey

            # Query operations repository for historical data
            operations_repo = self.container.resolve(DIKey.OPERATION_REPOSITORY)

            # Get all operations ordered by timestamp desc
            operations = operations_repo.find_all()

            for operation in operations:
                value = getattr(operation, key, None)
                if value is not None:
                    return value

        except Exception as e:
            # If operations repository fails, try system config
            print(f"Warning: Failed to get historical data: {e}")

        # Fallback: check system config for any stored value
        try:
            user_configs = self.config_loader.config_repo.get_user_specified_configs()
            return user_configs.get(key)
        except Exception:
            return None

    def needs_backup(self, new_language: str, new_contest: str, new_problem: str) -> bool:
        """Check if contest_current needs to be backed up.

        Args:
            new_language: User-specified language
            new_contest: User-specified contest name
            new_problem: User-specified problem name

        Returns:
            True if backup is needed (current state differs from new state)
        """
        current_state = self.get_current_contest_state()

        current_language = current_state.get("language_name")
        current_contest = current_state.get("contest_name")
        current_problem = current_state.get("problem_name")

        # If any of the current values differ from new values, backup is needed
        return (current_language != new_language or
                current_contest != new_contest or
                current_problem != new_problem)

    def backup_contest_current(self, current_state: Dict[str, Optional[str]]) -> bool:
        """Backup contest_current to contest_stock.

        Args:
            current_state: Current contest state with language_name, contest_name, problem_name

        Returns:
            True if backup successful, False otherwise
        """
        language = current_state.get("language_name")
        contest = current_state.get("contest_name")
        problem = current_state.get("problem_name")

        # Skip backup if essential information is missing
        if not all([language, contest, problem]):
            return False

        try:
            # Get paths from env.json
            shared_config = self.env_json.get("shared", {})
            paths = shared_config.get("paths", {})

            contest_current_path = paths.get("contest_current_path", "./contest_current")
            contest_stock_path_template = paths.get("contest_stock_path",
                                                   "./contest_stock/{language_name}/{contest_name}/{problem_name}")

            # Resolve contest_stock path
            contest_stock_path = contest_stock_path_template.format(
                language_name=language,
                contest_name=contest,
                problem_name=problem
            )


            # Check if contest_current exists and has content
            if not self._directory_has_content(contest_current_path):
                return True  # Nothing to backup

            # Create contest_stock directory
            self._ensure_directory_exists(contest_stock_path)

            # Move all files from contest_current to contest_stock
            success = self._move_directory_contents(contest_current_path, contest_stock_path)

            return success

        except Exception as e:
            print(f"Error during backup: {e}")
            return False

    def _directory_has_content(self, directory_path: str) -> bool:
        """Check if directory exists and has content."""
        try:
            req = FileRequest(FileOpType.EXISTS, directory_path)
            result = req.execute_operation(driver=self.file_driver)


            # For now, assume directory has content if it exists
            # TODO: Implement proper directory listing
            return result.exists

        except Exception as e:
            print(f"Debug: Exception checking directory content: {e}")
            return False

    def _ensure_directory_exists(self, directory_path: str) -> bool:
        """Ensure directory exists, create if necessary."""
        try:
            req = FileRequest(FileOpType.MKDIR, directory_path)
            result = req.execute_operation(driver=self.file_driver)
            return result.success
        except Exception:
            return False

    def _move_directory_contents(self, source_path: str, dest_path: str) -> bool:
        """Move all contents from source directory to destination directory."""
        try:
            # Use os.listdir to get directory contents
            items = os.listdir(source_path)

            # Move each file/directory
            for item in items:
                source_item = os.path.join(source_path, item)
                dest_item = os.path.join(dest_path, item)

                # Use move operation
                req = FileRequest(FileOpType.MOVE, source_item, dst_path=dest_item)
                move_result = req.execute_operation(driver=self.file_driver)

                if not move_result.success:
                    return False

            return True

        except Exception as e:
            print(f"Error moving directory contents: {e}")
            return False

    def _clear_contest_current(self, contest_current_path: str) -> bool:
        """Clear contest_current directory."""
        try:
            # Use os.listdir to avoid missing FileOpType.LIST
            if os.path.exists(contest_current_path):
                items = os.listdir(contest_current_path)

                for item in items:
                    item_path = os.path.join(contest_current_path, item)

                    # Remove file or directory
                    if os.path.isdir(item_path):
                        req = FileRequest(FileOpType.RMTREE, item_path)
                    else:
                        req = FileRequest(FileOpType.REMOVE, item_path)

                    result = req.execute_operation(driver=self.file_driver)
                    if not result.success:
                        return False

            return True

        except Exception:
            return False

    def _copy_directory_contents(self, source_path: str, dest_path: str) -> bool:
        """Copy all contents from source directory to destination directory."""
        try:
            # Ensure destination directory exists
            self._ensure_directory_exists(dest_path)

            # Use os.listdir to get directory contents
            items = os.listdir(source_path)

            # Copy each file/directory
            for item in items:
                source_item = os.path.join(source_path, item)
                dest_item = os.path.join(dest_path, item)

                # Use copy operation (preserves structure)
                if os.path.isdir(source_item):
                    req = FileRequest(FileOpType.COPYTREE, source_item, dst_path=dest_item)
                else:
                    req = FileRequest(FileOpType.COPY, source_item, dst_path=dest_item)

                copy_result = req.execute_operation(driver=self.file_driver)

                if not copy_result.success:
                    return False

            return True

        except Exception as e:
            print(f"Error copying directory contents: {e}")
            return False

    def _copy_template_structure(self, template_path: str, dest_path: str,
                                language: str, contest: str, problem: str) -> bool:
        """Copy template structure to destination, preserving directory structure and tracking files."""
        try:
            # Ensure destination directory exists
            self._ensure_directory_exists(dest_path)

            # Track files to be added to SQLite
            tracked_files = []

            # Copy template structure recursively
            success = self._copy_template_recursive(template_path, dest_path, "",
                                                  language, contest, problem, tracked_files)

            if success and tracked_files and self.files_repo:
                # Track all files in SQLite if repository is available
                self.files_repo.track_multiple_files(tracked_files)

            return success

        except Exception as e:
            print(f"Error copying template structure: {e}")
            return False

    def _copy_template_recursive(self, source_dir: str, dest_dir: str, relative_path: str,
                               language: str, contest: str, problem: str,
                               tracked_files: List) -> bool:
        """Recursively copy template files while tracking structure."""
        try:
            items = os.listdir(source_dir)

            for item in items:
                source_item = os.path.join(source_dir, item)
                dest_item = os.path.join(dest_dir, item)
                item_relative_path = os.path.join(relative_path, item) if relative_path else item

                if os.path.isdir(source_item):
                    # Create directory and recurse
                    self._ensure_directory_exists(dest_item)
                    if not self._copy_template_recursive(source_item, dest_item, item_relative_path,
                                                       language, contest, problem, tracked_files):
                        return False
                else:
                    # Copy file
                    req = FileRequest(FileOpType.COPY, source_item, dst_path=dest_item)
                    result = req.execute_operation(driver=self.file_driver)

                    if not result.success:
                        return False

                    # Track file for SQLite
                    tracked_files.append((
                        language, contest, problem,
                        item_relative_path,  # relative path in contest_current
                        'template',          # source type
                        source_item          # original source path
                    ))

            return True

        except Exception:
            return False

    def _track_files_from_stock(self, stock_path: str, current_path: str,
                              language: str, contest: str, problem: str) -> bool:
        """Track files copied from stock to contest_current."""
        try:
            tracked_files = []

            # Recursively track all files
            self._track_files_recursive(stock_path, current_path, "",
                                      language, contest, problem, tracked_files)

            if tracked_files and self.files_repo:
                # Clear previous tracking and add new if repository is available
                self.files_repo.clear_contest_tracking(language, contest, problem)
                self.files_repo.track_multiple_files(tracked_files)

            return True

        except Exception:
            return False

    def _track_files_recursive(self, source_dir: str, dest_dir: str, relative_path: str,
                             language: str, contest: str, problem: str,
                             tracked_files: List) -> None:
        """Recursively track files from source to destination."""
        try:
            items = os.listdir(dest_dir)  # Use destination as it now contains the files

            for item in items:
                dest_item = os.path.join(dest_dir, item)
                item_relative_path = os.path.join(relative_path, item) if relative_path else item

                if os.path.isdir(dest_item):
                    # Recurse into directory
                    source_subdir = os.path.join(source_dir, item)
                    self._track_files_recursive(source_subdir, dest_item, item_relative_path,
                                              language, contest, problem, tracked_files)
                else:
                    # Track file
                    source_item = os.path.join(source_dir, item)
                    tracked_files.append((
                        language, contest, problem,
                        item_relative_path,  # relative path in contest_current
                        'stock',             # source type
                        source_item          # original source path
                    ))

        except Exception:
            pass

    def handle_contest_change(self, new_language: str, new_contest: str, new_problem: str) -> bool:
        """Handle contest change with backup if needed.

        Args:
            new_language: User-specified language
            new_contest: User-specified contest name
            new_problem: User-specified problem name

        Returns:
            True if handling successful, False otherwise
        """
        try:
            # Check if backup is needed
            if self.needs_backup(new_language, new_contest, new_problem):
                # Get current state for backup
                current_state = self.get_current_contest_state()

                # Perform backup
                backup_success = self.backup_contest_current(current_state)

                if backup_success:
                    print("📦 Backed up contest_current to contest_stock")
                    print(f"   From: {current_state.get('language_name')} {current_state.get('contest_name')} {current_state.get('problem_name')}")
                    print(f"   To: {new_language} {new_contest} {new_problem}")
                else:
                    print("⚠️ Failed to backup contest_current")
                    return False

            return True

        except Exception as e:
            print(f"Error handling contest change: {e}")
            return False

    def restore_from_contest_stock(self, language: str, contest: str, problem: str) -> bool:
        """Restore contest_current from contest_stock if available.

        Args:
            language: Programming language
            contest: Contest name
            problem: Problem name

        Returns:
            True if restoration successful, False if no stock available
        """
        try:
            # Get paths from env.json
            shared_config = self.env_json.get("shared", {})
            paths = shared_config.get("paths", {})

            contest_current_path = paths.get("contest_current_path", "./contest_current")
            contest_stock_path_template = paths.get("contest_stock_path",
                                                   "./contest_stock/{language_name}/{contest_name}/{problem_name}")

            # Resolve contest_stock path
            contest_stock_path = contest_stock_path_template.format(
                language_name=language,
                contest_name=contest,
                problem_name=problem
            )

            # Check if contest_stock directory exists and has content
            if not self._directory_has_content(contest_stock_path):
                return False

            # Clear current contest_current directory
            self._clear_contest_current(contest_current_path)

            # Copy all files from contest_stock to contest_current
            success = self._copy_directory_contents(contest_stock_path, contest_current_path)

            if success and self.files_repo:
                # Track all copied files in SQLite if repository is available
                self._track_files_from_stock(contest_stock_path, contest_current_path,
                                           language, contest, problem)
                # print(f"📁 Restored from contest_stock: {language} {contest} {problem}")

            return success

        except Exception as e:
            print(f"Error restoring from contest_stock: {e}")
            return False

    def initialize_from_template(self, language: str, contest: str, problem: str) -> bool:
        """Initialize contest_current from contest_template.

        Args:
            language: Programming language
            contest: Contest name
            problem: Problem name

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Get paths from env.json
            shared_config = self.env_json.get("shared", {})
            paths = shared_config.get("paths", {})

            contest_current_path = paths.get("contest_current_path", "./contest_current")
            contest_template_path = paths.get("contest_template_path", "./contest_template")

            # Language-specific template path
            template_language_path = os.path.join(contest_template_path, language)

            # Check if template exists
            if not self._directory_has_content(template_language_path):
                print(f"Warning: No template found for language {language}")
                return False

            # Clear current contest_current directory
            self._clear_contest_current(contest_current_path)

            # Copy template structure to contest_current, preserving structure
            success = self._copy_template_structure(template_language_path, contest_current_path,
                                                  language, contest, problem)

            if success:
                print(f"📋 Initialized from template: {language} {contest} {problem}")

            return success

        except Exception as e:
            print(f"Error initializing from template: {e}")
            return False

    def initialize_contest_current(self, language: str, contest: str, problem: str) -> bool:
        """Initialize contest_current with priority: stock -> template.

        Args:
            language: Programming language
            contest: Contest name
            problem: Problem name

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Try to restore from contest_stock first
            if self.restore_from_contest_stock(language, contest, problem):
                return True

            # Fall back to template initialization
            return self.initialize_from_template(language, contest, problem)

        except Exception as e:
            print(f"Error initializing contest_current: {e}")
            return False

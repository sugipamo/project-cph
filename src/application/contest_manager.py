"""Contest management system for handling contest_current backup and state detection."""
from typing import Dict, List, Optional
from src.infrastructure.requests.file.file_op_type import FileOpType
from src.operations.results.__init__ import FileRequest
from tests.system_config_loader import SystemConfigLoader
from src.infrastructure.di_container import DIKey

class ContestManager:
    """Manages contest state detection and backup operations."""

    def __init__(self, container, env_json: Dict):
        """Initialize contest manager with DI container and environment configuration."""
        self.container = container
        self.config_loader = SystemConfigLoader(container)
        self._file_driver = None
        self._env_json = env_json
        self._logger = None
        self._os_provider = None
        self._json_provider = None

    @property
    def env_json(self) -> Dict:
        """Lazy load env_json from config loader with shared config."""
        if not self._env_json:
            shared_path = 'contest_env/shared/env.json'
            req = FileRequest(op=FileOpType.READ, path=shared_path, content=None, dst_path=None, debug_tag='load_shared_env', name='load_shared_env_json')
            result = req.execute_operation(driver=self.file_driver, logger=self.logger)
            if result.success:
                shared_config = self.json_provider.loads(result.content)
                self._env_json = shared_config
            else:
                if not result.error_message:
                    raise RuntimeError(f'Failed to load shared env.json from {shared_path}: No error message provided by file operation')
                raise RuntimeError(f'Failed to load shared env.json from {shared_path}: {result.error_message}')
        return self._env_json

    @property
    def file_driver(self):
        """Lazy load file driver."""
        if self._file_driver is None:
            self._file_driver = self.container.resolve(DIKey.FILE_DRIVER)
        return self._file_driver

    @property
    def logger(self):
        """Lazy load logger."""
        if self._logger is None:
            try:
                self._logger = self.container.resolve(DIKey.UNIFIED_LOGGER)
            except ValueError:

                class DummyLogger:

                    def warning(self, msg):
                        pass

                    def error(self, msg):
                        pass

                    def info(self, msg):
                        pass

                    def debug(self, msg):
                        pass
                self._logger = DummyLogger()
        return self._logger

    @property
    def os_provider(self):
        """Lazy load OS provider."""
        if self._os_provider is None:
            self._os_provider = self.container.resolve(DIKey.OS_PROVIDER)
        return self._os_provider

    @property
    def json_provider(self):
        """Lazy load JSON provider."""
        if self._json_provider is None:
            self._json_provider = self.container.resolve(DIKey.JSON_PROVIDER)
        return self._json_provider

    @property
    def files_repo(self):
        """Lazy load contest current files repository."""
        if not hasattr(self, '_files_repo'):
            self._files_repo = self.container.resolve('contest_current_files_repository')
        return self._files_repo

    def get_current_contest_state(self) -> Dict[str, Optional[str]]:
        """Get current contest state from SQLite with fallback for NULL values.

        Returns:
            Dictionary with language_name, contest_name, problem_name
        """
        current_context = self.config_loader.get_current_context()
        language = current_context['language']
        contest_name = current_context['contest_name']
        problem_name = current_context['problem_name']
        if language is None:
            language = self._get_latest_non_null_value('language')
        if contest_name is None:
            contest_name = self._get_latest_non_null_value('contest_name')
        if problem_name is None:
            problem_name = self._get_latest_non_null_value('problem_name')
        return {'language_name': language, 'contest_name': contest_name, 'problem_name': problem_name}

    def _get_latest_non_null_value(self, key: str) -> Optional[str]:
        """Get latest non-NULL value for a specific key from SQLite history.

        Args:
            key: Configuration key (language, contest_name, problem_name)

        Returns:
            Latest non-NULL value or None if no non-NULL value found
        """
        operations_repo = self.container.resolve(DIKey.OPERATION_REPOSITORY)
        operations = operations_repo.find_all()
        for operation in operations:
            if hasattr(operation, key):
                value = getattr(operation, key)
            else:
                value = None
            if value is not None:
                return value
        user_configs = self.config_loader.config_repo.get_user_specified_configs()
        if key in user_configs:
            return user_configs[key]
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
        current_language = current_state['language_name']
        current_contest = current_state['contest_name']
        current_problem = current_state['problem_name']
        if current_language != new_language:
            return True
        if current_contest != new_contest:
            return True
        return current_problem != new_problem

    def backup_contest_current(self, current_state: Dict[str, Optional[str]]) -> bool:
        """Backup contest_current to contest_stock.

        Args:
            current_state: Current contest state with language_name, contest_name, problem_name

        Returns:
            True if backup successful, False otherwise
        """
        language = current_state['language_name']
        contest = current_state['contest_name']
        problem = current_state['problem_name']
        if not all([language, contest, problem]):
            return False
        try:
            shared_config = self.env_json['shared']
            paths = shared_config['paths']
            contest_current_path = paths['contest_current_path']
            contest_stock_path_template = paths['contest_stock_path']
            contest_stock_path = contest_stock_path_template.format(language_name=language, contest_name=contest, problem_name=problem)
            if not self._directory_has_content(contest_current_path):
                return True
            self._ensure_directory_exists(contest_stock_path)
            success = self._move_directory_contents(contest_current_path, contest_stock_path)
            return success
        except Exception as e:
            self.logger.error(f'Error during backup: {e}')
            raise RuntimeError(f'Backup operation failed: {e}') from e

    def _directory_has_content(self, directory_path: str) -> bool:
        """Check if directory exists and has content."""
        try:
            req = FileRequest(op=FileOpType.EXISTS, path=directory_path, content=None, dst_path=None, debug_tag='check_directory_content', name='check_directory_exists')
            result = req.execute_operation(driver=self.file_driver, logger=self.logger)
            return result.exists
        except Exception as e:
            self.logger.debug(f'Exception checking directory content: {e}')
            raise RuntimeError(f'Failed to check directory content: {e}') from e

    def _ensure_directory_exists(self, directory_path: str) -> bool:
        """Ensure directory exists, create if necessary."""
        try:
            req = FileRequest(op=FileOpType.MKDIR, path=directory_path, content=None, dst_path=None, debug_tag='ensure_directory', name='create_directory')
            result = req.execute_operation(driver=self.file_driver, logger=self.logger)
            return result.success
        except Exception as e:
            raise RuntimeError(f"Failed to ensure directory exists '{directory_path}': {e}") from e

    def _move_directory_contents(self, source_path: str, dest_path: str) -> bool:
        """Move all contents from source directory to destination directory."""
        try:
            items = self.os_provider.listdir(source_path)
            for item in items:
                source_item = self.os_provider.path_join(source_path, item)
                dest_item = self.os_provider.path_join(dest_path, item)
                req = FileRequest(op=FileOpType.MOVE, path=source_item, content=None, dst_path=dest_item, debug_tag='move_directory_item', name='move_contest_file')
                move_result = req.execute_operation(driver=self.file_driver, logger=self.logger)
                if not move_result.success:
                    return False
            return True
        except Exception as e:
            self.logger.error(f'Error moving directory contents: {e}')
            raise RuntimeError(f'Failed to move directory contents: {e}') from e

    def _clear_contest_current(self, contest_current_path: str) -> bool:
        """Clear contest_current directory."""
        try:
            if self.os_provider.exists(contest_current_path):
                items = self.os_provider.listdir(contest_current_path)
                for item in items:
                    item_path = self.os_provider.path_join(contest_current_path, item)
                    if self.os_provider.isdir(item_path):
                        req = FileRequest(op=FileOpType.RMTREE, path=item_path, content=None, dst_path=None, debug_tag='clear_directory', name='remove_directory_tree')
                    else:
                        req = FileRequest(op=FileOpType.REMOVE, path=item_path, content=None, dst_path=None, debug_tag='clear_file', name='remove_file')
                    result = req.execute_operation(driver=self.file_driver, logger=self.logger)
                    if not result.success:
                        return False
            return True
        except Exception as e:
            self.logger.error(f'Error clearing contest_current directory: {e}')
            raise RuntimeError(f'Failed to clear contest_current directory: {e}') from e

    def _copy_directory_contents(self, source_path: str, dest_path: str) -> bool:
        """Copy all contents from source directory to destination directory."""
        try:
            self._ensure_directory_exists(dest_path)
            items = self.os_provider.listdir(source_path)
            for item in items:
                source_item = self.os_provider.path_join(source_path, item)
                dest_item = self.os_provider.path_join(dest_path, item)
                if self.os_provider.isdir(source_item):
                    req = FileRequest(op=FileOpType.COPYTREE, path=source_item, content=None, dst_path=dest_item, debug_tag='copy_directory_tree', name='copy_template_directory')
                else:
                    req = FileRequest(op=FileOpType.COPY, path=source_item, content=None, dst_path=dest_item, debug_tag='copy_file', name='copy_template_file')
                copy_result = req.execute_operation(driver=self.file_driver, logger=self.logger)
                if not copy_result.success:
                    return False
            return True
        except Exception as e:
            self.logger.error(f'Error copying directory contents: {e}')
            raise RuntimeError(f'Failed to copy directory contents: {e}') from e

    def _copy_template_structure(self, template_path: str, dest_path: str, language: str, contest: str, problem: str) -> bool:
        """Copy template structure to destination, preserving directory structure and tracking files."""
        try:
            self._ensure_directory_exists(dest_path)
            tracked_files = []
            success = self._copy_template_recursive(template_path, dest_path, '', language, contest, problem, tracked_files)
            if success and tracked_files and self.files_repo:
                self.files_repo.track_multiple_files(tracked_files)
            return success
        except Exception as e:
            self.logger.error(f'Error copying template structure: {e}')
            raise RuntimeError(f'Failed to copy template structure: {e}') from e

    def _copy_template_recursive(self, source_dir: str, dest_dir: str, relative_path: str, language: str, contest: str, problem: str, tracked_files: List) -> bool:
        """Recursively copy template files while tracking structure."""
        try:
            items = self.os_provider.listdir(source_dir)
            for item in items:
                source_item = self.os_provider.path_join(source_dir, item)
                dest_item = self.os_provider.path_join(dest_dir, item)
                if relative_path:
                    item_relative_path = self.os_provider.path_join(relative_path, item)
                else:
                    item_relative_path = item
                if self.os_provider.isdir(source_item):
                    self._ensure_directory_exists(dest_item)
                    if not self._copy_template_recursive(source_item, dest_item, item_relative_path, language, contest, problem, tracked_files):
                        return False
                else:
                    req = FileRequest(op=FileOpType.COPY, path=source_item, content=None, dst_path=dest_item, debug_tag='copy_template_recursive', name='copy_template_recursive_file')
                    result = req.execute_operation(driver=self.file_driver, logger=self.logger)
                    if not result.success:
                        return False
                    tracked_files.append((language, contest, problem, item_relative_path, 'template', source_item))
            return True
        except Exception as e:
            raise RuntimeError(f'Failed to copy template files recursively: {e}') from e

    def _track_files_from_stock(self, stock_path: str, current_path: str, language: str, contest: str, problem: str) -> bool:
        """Track files copied from stock to contest_current."""
        try:
            tracked_files = []
            self._track_files_recursive(stock_path, current_path, '', language, contest, problem, tracked_files)
            if tracked_files and self.files_repo:
                self.files_repo.clear_contest_tracking(language, contest, problem)
                self.files_repo.track_multiple_files(tracked_files)
            return True
        except Exception as e:
            raise RuntimeError(f'Failed to track files from stock: {e}') from e

    def _track_files_recursive(self, source_dir: str, dest_dir: str, relative_path: str, language: str, contest: str, problem: str, tracked_files: List) -> None:
        """Recursively track files from source to destination."""
        try:
            items = self.os_provider.listdir(dest_dir)
            for item in items:
                dest_item = self.os_provider.path_join(dest_dir, item)
                if relative_path:
                    item_relative_path = self.os_provider.path_join(relative_path, item)
                else:
                    item_relative_path = item
                if self.os_provider.isdir(dest_item):
                    source_subdir = self.os_provider.path_join(source_dir, item)
                    self._track_files_recursive(source_subdir, dest_item, item_relative_path, language, contest, problem, tracked_files)
                else:
                    source_item = self.os_provider.path_join(source_dir, item)
                    tracked_files.append((language, contest, problem, item_relative_path, 'stock', source_item))
        except Exception as e:
            raise RuntimeError(f'Failed to track files recursively: {e}') from e

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
            if self.needs_backup(new_language, new_contest, new_problem):
                current_state = self.get_current_contest_state()
                backup_success = self.backup_contest_current(current_state)
                if backup_success:
                    self.logger.info('📦 Backed up contest_current to contest_stock')
                    self.logger.info(f'   From: {current_state['language_name']} {current_state['contest_name']} {current_state['problem_name']}')
                    self.logger.info(f'   To: {new_language} {new_contest} {new_problem}')
                else:
                    self.logger.warning('Failed to backup contest_current')
                    return False
            return True
        except Exception as e:
            self.logger.error(f'Error handling contest change: {e}')
            raise RuntimeError(f'Failed to handle contest change: {e}') from e

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
            shared_config = self.env_json['shared']
            paths = shared_config['paths']
            contest_current_path = paths['contest_current_path']
            contest_stock_path_template = paths['contest_stock_path']
            contest_stock_path = contest_stock_path_template.format(language_name=language, contest_name=contest, problem_name=problem)
            if not self._directory_has_content(contest_stock_path):
                return False
            self._clear_contest_current(contest_current_path)
            success = self._copy_directory_contents(contest_stock_path, contest_current_path)
            if success and self.files_repo:
                self._track_files_from_stock(contest_stock_path, contest_current_path, language, contest, problem)
            return success
        except Exception as e:
            self.logger.error(f'Error restoring from contest_stock: {e}')
            raise RuntimeError(f'Failed to restore from contest_stock: {e}') from e

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
            shared_config = self.env_json['shared']
            paths = shared_config['paths']
            contest_current_path = paths['contest_current_path']
            contest_template_path = paths['contest_template_path']
            template_language_path = self.os_provider.path_join(contest_template_path, language)
            if not self._directory_has_content(template_language_path):
                self.logger.warning(f'No template found for language {language}')
                return False
            self._clear_contest_current(contest_current_path)
            success = self._copy_template_structure(template_language_path, contest_current_path, language, contest, problem)
            if success:
                self.logger.info(f'📋 Initialized from template: {language} {contest} {problem}')
            return success
        except Exception as e:
            self.logger.error(f'Error initializing from template: {e}')
            raise RuntimeError(f'Failed to initialize from template: {e}') from e

    def initialize_contest_current(self, language: str, contest: str, problem: str) -> bool:
        """Initialize contest_current with priority: stock -> template.

        Args:
            language: Programming language
            contest: Contest name
            problem: Problem name

        Returns:
            True if initialization successful, False otherwise

        Raises:
            RuntimeError: If initialization fails for both stock and template
        """
        if self.restore_from_contest_stock(language, contest, problem):
            return True
        template_success = self.initialize_from_template(language, contest, problem)
        if not template_success:
            raise RuntimeError(f'Failed to initialize contest_current for {language} {contest} {problem}: both stock and template initialization failed')
        return template_success
"""Tests for ContestManager."""
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.infrastructure.persistence.sqlite.contest_manager import ContestManager


class TestContestManager:
    """Test cases for ContestManager."""

    @pytest.fixture
    def mock_container(self):
        """Create mock DI container."""
        container = Mock()
        return container

    @pytest.fixture
    def env_json(self):
        """Sample environment configuration."""
        return {
            "shared": {
                "paths": {
                    "contest_current_path": "/contest_current",
                    "contest_stock_path": "/contest_stock/{language_name}/{contest_name}/{problem_name}",
                    "contest_template_path": "/contest_template"
                }
            }
        }

    @pytest.fixture
    def contest_manager(self, mock_container, env_json):
        """Create ContestManager instance."""
        return ContestManager(mock_container, env_json)

    def test_init(self, mock_container, env_json):
        """Test ContestManager initialization."""
        manager = ContestManager(mock_container, env_json)

        assert manager.container == mock_container
        assert manager._env_json == env_json
        assert manager._file_driver is None
        assert manager._logger is None

    def test_env_json_property(self, contest_manager, env_json):
        """Test env_json property returns stored config."""
        assert contest_manager.env_json == env_json

    def test_env_json_property_loads_from_file_when_none(self, mock_container):
        """Test env_json property loads from file when not provided."""
        # Create manager without env_json
        manager = ContestManager(mock_container, None)

        # Mock file driver and json provider
        mock_file_driver = Mock()
        mock_json_provider = Mock()
        mock_file_result = Mock()
        mock_file_result.success = True
        mock_file_result.content = '{"shared": {"test": "data"}}'

        # Configure mocks
        mock_container.resolve.side_effect = lambda key: {
            "DIKey.FILE_DRIVER": mock_file_driver,
            "DIKey.JSON_PROVIDER": mock_json_provider
        }.get(str(key))

        mock_json_provider.loads.return_value = {"shared": {"test": "data"}}

        # Mock FileRequest execution
        with patch('src.infrastructure.persistence.sqlite.contest_manager.FileRequest') as mock_file_request:
            mock_request_instance = Mock()
            mock_file_request.return_value = mock_request_instance
            mock_request_instance.execute_operation.return_value = mock_file_result

            # Access property to trigger loading
            result = manager.env_json

            assert result == {"shared": {"test": "data"}}

    def test_file_driver_property(self, contest_manager, mock_container):
        """Test file_driver property lazy loading."""
        mock_file_driver = Mock()
        mock_container.resolve.return_value = mock_file_driver

        # First access
        driver = contest_manager.file_driver
        assert driver == mock_file_driver

        # Second access should use cached value
        driver2 = contest_manager.file_driver
        assert driver2 == mock_file_driver
        assert mock_container.resolve.call_count == 1

    def test_logger_property(self, contest_manager, mock_container):
        """Test logger property lazy loading."""
        mock_logger = Mock()
        mock_container.resolve.return_value = mock_logger

        logger = contest_manager.logger
        assert logger == mock_logger

    def test_logger_property_fallback_when_not_available(self, contest_manager, mock_container):
        """Test logger property fallback when DI fails."""
        mock_container.resolve.side_effect = ValueError("Logger not found")

        logger = contest_manager.logger

        # Should create dummy logger
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'debug')

    def test_os_provider_property(self, contest_manager, mock_container):
        """Test os_provider property lazy loading."""
        mock_os_provider = Mock()
        mock_container.resolve.return_value = mock_os_provider

        provider = contest_manager.os_provider
        assert provider == mock_os_provider

    def test_json_provider_property(self, contest_manager, mock_container):
        """Test json_provider property lazy loading."""
        mock_json_provider = Mock()
        mock_container.resolve.return_value = mock_json_provider

        provider = contest_manager.json_provider
        assert provider == mock_json_provider

    def test_files_repo_property(self, contest_manager, mock_container):
        """Test files_repo property lazy loading."""
        mock_files_repo = Mock()
        mock_container.resolve.return_value = mock_files_repo

        repo = contest_manager.files_repo
        assert repo == mock_files_repo

    def test_get_current_contest_state(self, contest_manager):
        """Test getting current contest state."""
        # Mock config loader
        mock_config_loader = Mock()
        contest_manager.config_loader = mock_config_loader

        mock_config_loader.get_current_context.return_value = {
            "language": "python",
            "contest_name": "abc123",
            "problem_name": "A"
        }

        state = contest_manager.get_current_contest_state()

        assert state == {
            "language_name": "python",
            "contest_name": "abc123",
            "problem_name": "A"
        }

    def test_get_current_contest_state_with_null_values(self, contest_manager):
        """Test getting current contest state with null values."""
        # Mock config loader
        mock_config_loader = Mock()
        contest_manager.config_loader = mock_config_loader

        mock_config_loader.get_current_context.return_value = {
            "language": None,
            "contest_name": "abc123",
            "problem_name": None
        }

        # Mock _get_latest_non_null_value method
        contest_manager._get_latest_non_null_value = Mock()
        contest_manager._get_latest_non_null_value.side_effect = lambda key: {
            "language": "python",
            "problem_name": "B"
        }.get(key)

        state = contest_manager.get_current_contest_state()

        assert state == {
            "language_name": "python",
            "contest_name": "abc123",
            "problem_name": "B"
        }

    def test_needs_backup_true(self, contest_manager):
        """Test needs_backup returns True when state differs."""
        contest_manager.get_current_contest_state = Mock(return_value={
            "language_name": "python",
            "contest_name": "abc123",
            "problem_name": "A"
        })

        result = contest_manager.needs_backup("cpp", "def456", "B")
        assert result is True

    def test_needs_backup_false(self, contest_manager):
        """Test needs_backup returns False when state is same."""
        contest_manager.get_current_contest_state = Mock(return_value={
            "language_name": "python",
            "contest_name": "abc123",
            "problem_name": "A"
        })

        result = contest_manager.needs_backup("python", "abc123", "A")
        assert result is False

    def test_backup_contest_current_success(self, contest_manager):
        """Test successful backup of contest_current."""
        current_state = {
            "language_name": "python",
            "contest_name": "abc123",
            "problem_name": "A"
        }

        # Mock methods
        contest_manager._directory_has_content = Mock(return_value=True)
        contest_manager._ensure_directory_exists = Mock(return_value=True)
        contest_manager._move_directory_contents = Mock(return_value=True)

        result = contest_manager.backup_contest_current(current_state)
        assert result is True

    def test_backup_contest_current_missing_info(self, contest_manager):
        """Test backup skips when essential info is missing."""
        current_state = {
            "language_name": None,
            "contest_name": "abc123",
            "problem_name": "A"
        }

        result = contest_manager.backup_contest_current(current_state)
        assert result is False

    def test_backup_contest_current_no_content(self, contest_manager):
        """Test backup when directory has no content."""
        current_state = {
            "language_name": "python",
            "contest_name": "abc123",
            "problem_name": "A"
        }

        contest_manager._directory_has_content = Mock(return_value=False)

        result = contest_manager.backup_contest_current(current_state)
        assert result is True

    def test_handle_contest_change_with_backup(self, contest_manager):
        """Test handling contest change that requires backup."""
        # Mock methods
        contest_manager.needs_backup = Mock(return_value=True)
        contest_manager.get_current_contest_state = Mock(return_value={
            "language_name": "python",
            "contest_name": "abc123",
            "problem_name": "A"
        })
        contest_manager.backup_contest_current = Mock(return_value=True)
        contest_manager.logger = Mock()

        result = contest_manager.handle_contest_change("cpp", "def456", "B")
        assert result is True

    def test_handle_contest_change_no_backup_needed(self, contest_manager):
        """Test handling contest change that doesn't need backup."""
        contest_manager.needs_backup = Mock(return_value=False)

        result = contest_manager.handle_contest_change("python", "abc123", "A")
        assert result is True

    def test_restore_from_contest_stock_success(self, contest_manager):
        """Test successful restoration from contest_stock."""
        # Mock methods
        contest_manager._directory_has_content = Mock(return_value=True)
        contest_manager._clear_contest_current = Mock(return_value=True)
        contest_manager._copy_directory_contents = Mock(return_value=True)
        contest_manager._track_files_from_stock = Mock(return_value=True)
        contest_manager.files_repo = Mock()

        result = contest_manager.restore_from_contest_stock("python", "abc123", "A")
        assert result is True

    def test_restore_from_contest_stock_no_stock(self, contest_manager):
        """Test restoration when no stock available."""
        contest_manager._directory_has_content = Mock(return_value=False)

        result = contest_manager.restore_from_contest_stock("python", "abc123", "A")
        assert result is False

    def test_initialize_from_template_success(self, contest_manager):
        """Test successful initialization from template."""
        # Mock methods
        contest_manager._directory_has_content = Mock(return_value=True)
        contest_manager._clear_contest_current = Mock(return_value=True)
        contest_manager._copy_template_structure = Mock(return_value=True)
        contest_manager.os_provider = Mock()
        contest_manager.os_provider.path_join.return_value = "/contest_template/python"
        contest_manager.logger = Mock()

        result = contest_manager.initialize_from_template("python", "abc123", "A")
        assert result is True

    def test_initialize_from_template_no_template(self, contest_manager):
        """Test initialization when no template available."""
        contest_manager._directory_has_content = Mock(return_value=False)
        contest_manager.os_provider = Mock()
        contest_manager.os_provider.path_join.return_value = "/contest_template/python"
        contest_manager.logger = Mock()

        result = contest_manager.initialize_from_template("python", "abc123", "A")
        assert result is False

    def test_initialize_contest_current_from_stock(self, contest_manager):
        """Test initialize_contest_current using stock."""
        contest_manager.restore_from_contest_stock = Mock(return_value=True)

        result = contest_manager.initialize_contest_current("python", "abc123", "A")
        assert result is True

    def test_initialize_contest_current_from_template(self, contest_manager):
        """Test initialize_contest_current using template."""
        contest_manager.restore_from_contest_stock = Mock(return_value=False)
        contest_manager.initialize_from_template = Mock(return_value=True)

        result = contest_manager.initialize_contest_current("python", "abc123", "A")
        assert result is True

    def test_initialize_contest_current_failure(self, contest_manager):
        """Test initialize_contest_current when both stock and template fail."""
        contest_manager.restore_from_contest_stock = Mock(return_value=False)
        contest_manager.initialize_from_template = Mock(return_value=False)

        with pytest.raises(RuntimeError, match="both stock and template initialization failed"):
            contest_manager.initialize_contest_current("python", "abc123", "A")

    def test_directory_has_content(self, contest_manager):
        """Test _directory_has_content method."""
        # Mock file driver and request
        mock_file_driver = Mock()
        mock_result = Mock()
        mock_result.exists = True

        contest_manager.file_driver = mock_file_driver

        with patch('src.infrastructure.persistence.sqlite.contest_manager.FileRequest') as mock_file_request:
            mock_request_instance = Mock()
            mock_file_request.return_value = mock_request_instance
            mock_request_instance.execute_operation.return_value = mock_result

            result = contest_manager._directory_has_content("/test/path")
            assert result is True

    def test_ensure_directory_exists(self, contest_manager):
        """Test _ensure_directory_exists method."""
        # Mock file driver and request
        mock_file_driver = Mock()
        mock_result = Mock()
        mock_result.success = True

        contest_manager.file_driver = mock_file_driver

        with patch('src.infrastructure.persistence.sqlite.contest_manager.FileRequest') as mock_file_request:
            mock_request_instance = Mock()
            mock_file_request.return_value = mock_request_instance
            mock_request_instance.execute_operation.return_value = mock_result

            result = contest_manager._ensure_directory_exists("/test/path")
            assert result is True

    def test_move_directory_contents(self, contest_manager):
        """Test _move_directory_contents method."""
        # Mock OS provider and file operations
        mock_os_provider = Mock()
        mock_os_provider.listdir.return_value = ["file1.txt", "file2.txt"]
        mock_os_provider.path_join.side_effect = lambda *args: "/".join(args)

        contest_manager.os_provider = mock_os_provider
        contest_manager.file_driver = Mock()

        with patch('src.infrastructure.persistence.sqlite.contest_manager.FileRequest') as mock_file_request:
            mock_request_instance = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_request_instance.execute_operation.return_value = mock_result
            mock_file_request.return_value = mock_request_instance

            result = contest_manager._move_directory_contents("/source", "/dest")
            assert result is True
            assert mock_file_request.call_count == 2  # Two files moved

    def test_clear_contest_current(self, contest_manager):
        """Test _clear_contest_current method."""
        # Mock OS provider
        mock_os_provider = Mock()
        mock_os_provider.exists.return_value = True
        mock_os_provider.listdir.return_value = ["file1.txt", "dir1"]
        mock_os_provider.path_join.side_effect = lambda *args: "/".join(args)
        mock_os_provider.isdir.side_effect = lambda path: path.endswith("dir1")

        contest_manager.os_provider = mock_os_provider
        contest_manager.file_driver = Mock()

        with patch('src.infrastructure.persistence.sqlite.contest_manager.FileRequest') as mock_file_request:
            mock_request_instance = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_request_instance.execute_operation.return_value = mock_result
            mock_file_request.return_value = mock_request_instance

            result = contest_manager._clear_contest_current("/contest_current")
            assert result is True

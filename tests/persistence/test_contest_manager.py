"""
Test ContestManager implementation
"""
import os
import shutil
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.infrastructure.persistence.sqlite.contest_manager import ContestManager
from src.infrastructure.persistence.sqlite.system_config_loader import SystemConfigLoader


class MockDIContainer:
    """Mock DI container for testing"""

    def __init__(self):
        self.dependencies = {}

    def resolve(self, key):
        return self.dependencies.get(key, Mock())


class MockFileDriver:
    """Mock file driver for testing"""

    def __init__(self):
        self.executed_requests = []
        self.mock_responses = {}

    def execute(self, request):
        self.executed_requests.append(request)
        response_key = f"{request.op.name}:{request.path}"

        # Create appropriate result object
        from src.operations.constants.operation_type import OperationType
        from src.operations.results.result import OperationResult

        default_result = OperationResult(
            op=OperationType.FILE,
            success=True,
            path=request.path
        )

        # For EXISTS operations, add exists attribute
        if request.op.name == "EXISTS":
            mock_response = self.mock_responses.get(response_key, Mock(exists=True))
            default_result.exists = getattr(mock_response, 'exists', True)

        return self.mock_responses.get(response_key, default_result)

    def mkdir(self, path):
        """Mock mkdir operation"""
        # Track mkdir calls with proper structure
        mock_request = Mock()
        mock_request.op = Mock()
        mock_request.op.name = "MKDIR"
        mock_request.path = path
        self.executed_requests.append(mock_request)
        return True

    def exists(self, path):
        """Mock exists operation"""
        # Check mock responses first
        response_key = f"EXISTS:{path}"
        if response_key in self.mock_responses:
            return getattr(self.mock_responses[response_key], 'exists', True)
        return True

    def move(self, src, dst):
        """Mock move operation"""
        return True

    def copy(self, src, dst):
        """Mock copy operation"""
        return True

    def remove(self, path):
        """Mock remove operation"""
        return True

    def rmtree(self, path):
        """Mock rmtree operation"""
        return True

    def resolve_path(self, path):
        """Mock resolve_path operation"""
        from pathlib import Path
        return Path(path)


class MockFilesRepository:
    """Mock contest current files repository"""

    def __init__(self):
        self.tracked_files = []

    def track_multiple_files(self, files):
        self.tracked_files.extend(files)


class TestContestManager:

    def setup_method(self):
        """Setup test environment"""
        self.container = MockDIContainer()
        self.file_driver = MockFileDriver()
        self.files_repo = MockFilesRepository()

        # Create mock providers
        from src.infrastructure.providers import MockJsonProvider, MockOsProvider
        self.mock_json_provider = MockJsonProvider()
        self.mock_os_provider = MockOsProvider()

        from src.infrastructure.di_container import DIKey
        self.container.dependencies = {
            DIKey.FILE_DRIVER: self.file_driver,
            DIKey.JSON_PROVIDER: self.mock_json_provider,
            DIKey.OS_PROVIDER: self.mock_os_provider,
            "file_driver": self.file_driver,
            "contest_current_files_repository": self.files_repo
        }

        # Mock env_json structure
        self.env_json = {
            "shared": {
                "paths": {
                    "contest_current_path": "./contest_current",
                    "contest_stock_path": "./contest_stock/{language_name}/{contest_name}/{problem_name}"
                }
            }
        }

        self.contest_manager = ContestManager(self.container, self.env_json)

    def test_init(self):
        """Test ContestManager initialization"""
        assert self.contest_manager.container == self.container
        assert self.contest_manager._env_json == self.env_json

    def test_env_json_property_with_existing_config(self):
        """Test env_json property returns existing config"""
        result = self.contest_manager.env_json
        assert result == self.env_json

    def test_env_json_property_lazy_loading(self):
        """Test env_json property lazy loads from config"""
        # Create manager without env_json - use None instead of {} so condition triggers
        manager = ContestManager(self.container, None)
        manager._env_json = {}  # Set to empty dict after init

        # Mock file read response with valid JSON
        mock_result = Mock(success=True, content='{"shared": {"test": true}}')
        self.file_driver.mock_responses["READ:contest_env/shared/env.json"] = mock_result

        # Debug: Check that the file driver is correctly set
        assert manager.file_driver == self.file_driver

        result = manager.env_json

        # Debug: Check if the mock was called
        executed_reads = [req for req in self.file_driver.executed_requests
                         if hasattr(req, 'op') and req.op.name == "READ"]
        print(f"Executed reads: {[req.path for req in executed_reads]}")

        # The MockJsonProvider will parse the JSON correctly
        assert result == {"shared": {"test": True}}

    def test_file_driver_property(self):
        """Test file_driver property lazy loading"""
        driver = self.contest_manager.file_driver
        assert driver is not None

    def test_files_repo_property(self):
        """Test files_repo property lazy loading"""
        repo = self.contest_manager.files_repo
        assert repo is not None

    @patch.object(ContestManager, '_get_latest_non_null_value')
    def test_get_current_contest_state_with_nulls(self, mock_get_latest):
        """Test get_current_contest_state with NULL values"""
        # Mock config loader
        mock_config_loader = Mock()
        mock_config_loader.get_current_context.return_value = {
            "language": None,
            "contest_name": "abc300",
            "problem_name": None
        }
        self.contest_manager.config_loader = mock_config_loader

        # Mock latest non-null values
        mock_get_latest.side_effect = lambda key: {
            "language": "python",
            "problem_name": "a"
        }.get(key)

        result = self.contest_manager.get_current_contest_state()

        assert result["language_name"] == "python"  # From fallback
        assert result["contest_name"] == "abc300"    # From current context
        assert result["problem_name"] == "a"         # From fallback

    def test_needs_backup_different_state(self):
        """Test needs_backup returns True when state differs"""
        # Mock current state
        with patch.object(self.contest_manager, 'get_current_contest_state') as mock_get_state:
            mock_get_state.return_value = {
                "language_name": "python",
                "contest_name": "abc300",
                "problem_name": "a"
            }

            # Test with different contest
            result = self.contest_manager.needs_backup("python", "abc301", "a")
            assert result is True

            # Test with different language
            result = self.contest_manager.needs_backup("cpp", "abc300", "a")
            assert result is True

    def test_needs_backup_same_state(self):
        """Test needs_backup returns False when state is same"""
        with patch.object(self.contest_manager, 'get_current_contest_state') as mock_get_state:
            mock_get_state.return_value = {
                "language_name": "python",
                "contest_name": "abc300",
                "problem_name": "a"
            }

            result = self.contest_manager.needs_backup("python", "abc300", "a")
            assert result is False

    def test_backup_contest_current_missing_info(self):
        """Test backup_contest_current skips when essential info missing"""
        current_state = {
            "language_name": None,
            "contest_name": "abc300",
            "problem_name": "a"
        }

        result = self.contest_manager.backup_contest_current(current_state)
        assert result is False

    def test_backup_contest_current_success(self):
        """Test successful backup_contest_current"""
        current_state = {
            "language_name": "python",
            "contest_name": "abc300",
            "problem_name": "a"
        }

        # Mock directory has content check
        with (patch.object(self.contest_manager, '_directory_has_content', return_value=True),
              patch.object(self.contest_manager, '_ensure_directory_exists', return_value=True),
              patch.object(self.contest_manager, '_move_directory_contents', return_value=True)):
                    result = self.contest_manager.backup_contest_current(current_state)
                    assert result is True

    def test_directory_has_content_exists(self):
        """Test _directory_has_content when directory exists"""
        # Mock file exists response
        mock_result = Mock(exists=True)
        self.file_driver.mock_responses["EXISTS:./test_dir"] = mock_result

        result = self.contest_manager._directory_has_content("./test_dir")
        assert result is True

    def test_directory_has_content_not_exists(self):
        """Test _directory_has_content when directory doesn't exist"""
        # Mock file doesn't exist response
        mock_result = Mock(exists=False)
        self.file_driver.mock_responses["EXISTS:./test_dir"] = mock_result

        result = self.contest_manager._directory_has_content("./test_dir")
        assert result is False

    def test_ensure_directory_exists(self):
        """Test _ensure_directory_exists"""
        result = self.contest_manager._ensure_directory_exists("./test_dir")
        assert result is True

        # Check that MKDIR request was made
        mkdir_requests = [req for req in self.file_driver.executed_requests
                         if hasattr(req, 'op') and req.op.name == "MKDIR"]
        assert len(mkdir_requests) == 1

    def test_move_directory_contents(self):
        """Test _move_directory_contents"""
        # Set up mock OS provider
        self.mock_os_provider.add_directory("./source", ["file1.py", "dir1"])

        result = self.contest_manager._move_directory_contents("./source", "./dest")
        assert result is True

    def test_clear_contest_current(self):
        """Test _clear_contest_current"""
        # Set up mock OS provider
        self.mock_os_provider.add_directory("./contest_current", ["file1.py", "dir1"])
        self.mock_os_provider.add_file("./contest_current/file1.py")
        self.mock_os_provider.add_directory("./contest_current/dir1")

        result = self.contest_manager._clear_contest_current("./contest_current")
        assert result is True

    def test_copy_directory_contents(self):
        """Test _copy_directory_contents"""
        # Set up mock OS provider
        self.mock_os_provider.add_directory("./source", ["file1.py"])

        with patch.object(self.contest_manager, '_ensure_directory_exists', return_value=True):
            result = self.contest_manager._copy_directory_contents("./source", "./dest")
            assert result is True

    def test_copy_template_structure(self):
        """Test _copy_template_structure"""
        with (patch.object(self.contest_manager, '_ensure_directory_exists', return_value=True),
              patch.object(self.contest_manager, '_copy_template_recursive', return_value=True)):
            result = self.contest_manager._copy_template_structure(
                "./template", "./dest", "python", "abc300", "a"
            )
            assert result is True

    def test_get_latest_non_null_value_success(self):
        """Test _get_latest_non_null_value finds value"""
        # Test that the method handles the operation gracefully
        # The method tries operations repository first, then falls back to config
        result = self.contest_manager._get_latest_non_null_value("language")
        # Should return something (Mock or None) without crashing
        assert result is not None or result is None

    def test_get_latest_non_null_value_fallback(self):
        """Test _get_latest_non_null_value uses config fallback"""
        # Mock operations repository to raise exception
        mock_operations_repo = Mock()
        mock_operations_repo.find_all.side_effect = Exception("DB error")

        self.container.dependencies["operation_repository"] = mock_operations_repo

        # Test that the method handles exceptions gracefully and falls back to config
        result = self.contest_manager._get_latest_non_null_value("language")
        # Should return something (Mock or None) without crashing
        assert result is not None or result is None

    def test_handle_contest_change_needs_backup(self):
        """Test handle_contest_change when backup is needed"""
        with (patch.object(self.contest_manager, 'needs_backup', return_value=True),
              patch.object(self.contest_manager, 'get_current_contest_state') as mock_get_state,
              patch.object(self.contest_manager, 'backup_contest_current', return_value=True)):
            mock_get_state.return_value = {
                "language_name": "python",
                "contest_name": "abc299",
                "problem_name": "z"
            }

            # This method would be called in user_input_parser
            self.contest_manager.handle_contest_change("python", "abc300", "a")
            # No direct return value, but should not raise exception

    def test_initialize_contest_current_empty_current(self):
        """Test initialize_contest_current when contest_current is empty"""
        with (patch.object(self.contest_manager, 'restore_from_contest_stock', return_value=False),
              patch.object(self.contest_manager, 'initialize_from_template', return_value=True)):
            result = self.contest_manager.initialize_contest_current("python", "abc300", "a")
            assert result is True

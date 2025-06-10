"""Tests for refactored FilePreparationService helper methods."""
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.workflow.preparation.file.file_preparation_service import FilePreparationService
from tests.base.mock_logger import MockLogger


class TestFilePreparationServiceHelpers:
    """Test the helper methods of FilePreparationService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_file_driver = Mock()
        self.mock_repository = Mock()
        self.mock_logger = MockLogger()
        self.mock_config_loader = Mock()

        self.service = FilePreparationService(
            self.mock_file_driver,
            self.mock_repository,
            self.mock_logger,
            self.mock_config_loader
        )

    def test_check_operation_already_done_when_force_false_and_operation_exists(self):
        """Test check when operation already done and force is False."""
        # Arrange
        self.mock_repository.has_successful_operation.return_value = True

        # Act
        already_done, message = self.service._check_operation_already_done(
            "python", "abc300", "a", "move_test_files", False
        )

        # Assert
        assert already_done is True
        assert message == "move_test_files already completed"
        self.mock_repository.has_successful_operation.assert_called_once_with(
            "python", "abc300", "a", "move_test_files"
        )

    def test_check_operation_already_done_when_force_true(self):
        """Test check when force is True."""
        # Arrange
        self.mock_repository.has_successful_operation.return_value = True

        # Act
        already_done, message = self.service._check_operation_already_done(
            "python", "abc300", "a", "move_test_files", True
        )

        # Assert
        assert already_done is False
        assert message == ""

    def test_check_operation_already_done_when_operation_not_exists(self):
        """Test check when operation does not exist."""
        # Arrange
        self.mock_repository.has_successful_operation.return_value = False

        # Act
        already_done, message = self.service._check_operation_already_done(
            "python", "abc300", "a", "move_test_files", False
        )

        # Assert
        assert already_done is False
        assert message == ""

    def test_validate_test_file_operation_when_source_exists(self):
        """Test validation when source path exists."""
        # Arrange
        source_path = Path("/workspace/test")
        self.mock_file_driver.exists.return_value = True

        # Act
        is_valid, message = self.service._validate_test_file_operation(
            source_path, "move_test_files"
        )

        # Assert
        assert is_valid is True
        assert message == ""
        self.mock_file_driver.exists.assert_called_once_with(source_path)

    def test_validate_test_file_operation_when_source_not_exists(self):
        """Test validation when source path does not exist."""
        # Arrange
        source_path = Path("/workspace/test")
        self.mock_file_driver.exists.return_value = False

        # Act
        is_valid, message = self.service._validate_test_file_operation(
            source_path, "move_test_files"
        )

        # Assert
        assert is_valid is False
        assert message == "Source directory does not exist: /workspace/test"
        self.mock_file_driver.exists.assert_called_once_with(source_path)

    def test_perform_test_file_move_success(self):
        """Test successful file move operation."""
        # Arrange
        source_path = Path("/workspace/test")
        dest_path = Path("/contest_current/test")

        # Mock file driver methods
        self.mock_file_driver.exists.side_effect = lambda p: p != dest_path and p != dest_path.parent
        self.mock_file_driver.makedirs.return_value = None
        self.mock_file_driver.move.return_value = None

        # Mock _count_files_recursively to return 5
        self.service._count_files_recursively = Mock(return_value=5)

        # Act
        success, message, file_count = self.service._perform_test_file_move(
            source_path, dest_path
        )

        # Assert
        assert success is True
        assert "Moved 5 test files" in message
        assert file_count == 5

        # Verify calls
        self.mock_file_driver.move.assert_called_once_with(source_path, dest_path)
        self.service._count_files_recursively.assert_called_once_with(dest_path)

    def test_perform_test_file_move_with_existing_destination(self):
        """Test file move when destination already exists."""
        # Arrange
        source_path = Path("/workspace/test")
        dest_path = Path("/contest_current/test")

        # Mock: parent exists, destination exists
        self.mock_file_driver.exists.side_effect = lambda p: p == dest_path.parent or p == dest_path
        self.mock_file_driver.rmtree.return_value = None
        self.mock_file_driver.move.return_value = None

        self.service._count_files_recursively = Mock(return_value=3)

        # Act
        success, message, file_count = self.service._perform_test_file_move(
            source_path, dest_path
        )

        # Assert
        assert success is True
        assert file_count == 3

        # Verify destination was removed before move
        self.mock_file_driver.rmtree.assert_called_once_with(dest_path)
        self.mock_file_driver.move.assert_called_once_with(source_path, dest_path)

    def test_perform_test_file_move_failure(self):
        """Test file move operation failure."""
        # Arrange
        source_path = Path("/workspace/test")
        dest_path = Path("/contest_current/test")

        self.mock_file_driver.exists.return_value = False
        self.mock_file_driver.makedirs.return_value = None
        self.mock_file_driver.move.side_effect = Exception("Move failed")

        # Act
        success, message, file_count = self.service._perform_test_file_move(
            source_path, dest_path
        )

        # Assert
        assert success is False
        assert "Failed to move test files: Move failed" in message
        assert file_count == 0

    def test_record_operation_result_success(self):
        """Test recording successful operation result."""
        # Arrange
        source_path = Path("/workspace/test")
        dest_path = Path("/contest_current/test")

        # Act
        self.service._record_operation_result(
            "python", "abc300", "a", "move_test_files",
            source_path, dest_path, 5, True, ""
        )

        # Assert
        self.mock_repository.record_operation.assert_called_once_with(
            "python", "abc300", "a", "move_test_files",
            str(source_path), str(dest_path), 5, True, ""
        )

    def test_record_operation_result_failure(self):
        """Test recording failed operation result."""
        # Arrange
        source_path = Path("/workspace/test")
        dest_path = Path("/contest_current/test")
        error_message = "Operation failed"

        # Act
        self.service._record_operation_result(
            "python", "abc300", "a", "move_test_files",
            source_path, dest_path, 0, False, error_message
        )

        # Assert
        self.mock_repository.record_operation.assert_called_once_with(
            "python", "abc300", "a", "move_test_files",
            str(source_path), str(dest_path), 0, False, error_message
        )


class TestMoveTestFilesRefactored:
    """Test the refactored move_test_files method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_file_driver = Mock()
        self.mock_repository = Mock()
        self.mock_logger = MockLogger()
        self.mock_config_loader = Mock()

        self.service = FilePreparationService(
            self.mock_file_driver,
            self.mock_repository,
            self.mock_logger,
            self.mock_config_loader
        )

    def test_move_test_files_already_done(self):
        """Test move_test_files when operation already completed."""
        # Arrange
        self.mock_repository.has_successful_operation.return_value = True
        self.mock_config_loader.get_message.return_value = "Test files already moved"

        # Act
        success, message, file_count = self.service.move_test_files(
            "python", "abc300", "a", "/workspace", "/contest_current", False
        )

        # Assert
        assert success is True
        assert message == "Test files already moved"
        assert file_count == 0

    def test_move_test_files_source_not_exists(self):
        """Test move_test_files when source directory does not exist."""
        # Arrange
        self.mock_repository.has_successful_operation.return_value = False
        self.mock_file_driver.exists.return_value = False
        self.mock_config_loader.get_message.return_value = "No source directory"

        # Act
        success, message, file_count = self.service.move_test_files(
            "python", "abc300", "a", "/workspace", "/contest_current", False
        )

        # Assert
        assert success is True
        assert "Source directory does not exist" in message
        assert file_count == 0

        # Verify operation was recorded
        self.mock_repository.record_operation.assert_called_once()

    def test_move_test_files_successful_move(self):
        """Test successful move_test_files operation."""
        # Arrange
        self.mock_repository.has_successful_operation.return_value = False

        # Mock file driver for validation and move operations
        self.mock_file_driver.exists.side_effect = lambda p: str(p).endswith("/test") and "workspace" in str(p)
        self.mock_file_driver.makedirs.return_value = None
        self.mock_file_driver.move.return_value = None

        # Mock count method
        self.service._count_files_recursively = Mock(return_value=7)

        # Act
        success, message, file_count = self.service.move_test_files(
            "python", "abc300", "a", "/workspace", "/contest_current", False
        )

        # Assert
        assert success is True
        assert "Moved 7 test files" in message
        assert file_count == 7

        # Verify operation was recorded
        self.mock_repository.record_operation.assert_called_once()
        args = self.mock_repository.record_operation.call_args[0]
        assert args[4] == "/workspace/test"  # source_path
        assert args[5] == "/contest_current/test"  # dest_path
        assert args[6] == 7  # file_count
        assert args[7] is True  # success

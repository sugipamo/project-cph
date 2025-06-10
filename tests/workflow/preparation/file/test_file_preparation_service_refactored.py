"""Tests for refactored FilePreparationService helper methods."""
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.workflow.preparation.file.file_preparation_service import FilePreparationService
from src.workflow.preparation.file.file_pattern_service import FilePatternService, FileOperationResult
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


class TestFilePatternIntegration:
    """Test FilePreparationService integration with FilePatternService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_file_driver = Mock()
        self.mock_repository = Mock()
        self.mock_logger = MockLogger()
        self.mock_config_loader = Mock()
        self.mock_pattern_service = Mock(spec=FilePatternService)

        self.service = FilePreparationService(
            self.mock_file_driver,
            self.mock_repository,
            self.mock_logger,
            self.mock_config_loader,
            self.mock_pattern_service
        )

    def test_move_files_by_patterns_feature_disabled(self):
        """Test move_files_by_patterns when feature is disabled."""
        # Arrange
        self.mock_config_loader.get_shared_config.return_value = {
            "feature_flags": {"use_file_patterns": False}
        }
        self.mock_repository.has_successful_operation.return_value = False
        self.mock_file_driver.exists.return_value = True
        self.mock_file_driver.makedirs.return_value = None
        self.mock_file_driver.move.return_value = None
        self.service._count_files_recursively = Mock(return_value=3)

        # Act
        success, message, file_count = self.service.move_files_by_patterns(
            "move_test_files", "cpp", "abc300", "a", 
            "/workspace", "/contest_current", "/contest_stock", False
        )

        # Assert - should fall back to legacy implementation
        assert success is True
        assert file_count == 3
        self.mock_pattern_service.execute_with_fallback.assert_not_called()

    def test_move_files_by_patterns_no_pattern_service(self):
        """Test move_files_by_patterns when pattern service is not available."""
        # Arrange
        service_without_patterns = FilePreparationService(
            self.mock_file_driver,
            self.mock_repository,
            self.mock_logger,
            self.mock_config_loader,
            None  # No pattern service
        )
        
        self.mock_repository.has_successful_operation.return_value = False
        self.mock_file_driver.exists.return_value = True
        self.mock_file_driver.makedirs.return_value = None
        self.mock_file_driver.move.return_value = None
        service_without_patterns._count_files_recursively = Mock(return_value=2)

        # Act
        success, message, file_count = service_without_patterns.move_files_by_patterns(
            "move_test_files", "cpp", "abc300", "a",
            "/workspace", "/contest_current", "/contest_stock", False
        )

        # Assert - should fall back to legacy implementation
        assert success is True
        assert file_count == 2
        self.mock_logger.has_warning("FilePatternService not available")

    def test_move_files_by_patterns_feature_enabled_success(self):
        """Test move_files_by_patterns when feature is enabled and successful."""
        # Arrange
        self.mock_config_loader.get_shared_config.return_value = {
            "feature_flags": {"use_file_patterns": True}
        }
        self.mock_repository.has_successful_operation.return_value = False
        
        # Mock successful pattern service result
        pattern_result = FileOperationResult(
            success=True,
            message="Pattern operation successful",
            files_processed=5,
            files_failed=0,
            error_details=[],
            operation_log=["Pattern operation completed"]
        )
        self.mock_pattern_service.execute_with_fallback.return_value = pattern_result

        # Act
        success, message, file_count = self.service.move_files_by_patterns(
            "move_test_files", "cpp", "abc300", "a",
            "/workspace", "/contest_current", "/contest_stock", False
        )

        # Assert
        assert success is True
        assert message == "Pattern operation successful"
        assert file_count == 5

        # Verify pattern service was called with correct context
        expected_context = {
            "workspace_path": "/workspace",
            "contest_current_path": "/contest_current",
            "contest_stock_path": "/contest_stock",
            "language": "cpp"
        }
        self.mock_pattern_service.execute_with_fallback.assert_called_once_with(
            "move_test_files", expected_context
        )

        # Verify operation was recorded
        self.mock_repository.record_operation.assert_called_once()

    def test_move_files_by_patterns_feature_enabled_failure(self):
        """Test move_files_by_patterns when pattern service fails."""
        # Arrange
        self.mock_config_loader.get_shared_config.return_value = {
            "feature_flags": {"use_file_patterns": True}
        }
        self.mock_repository.has_successful_operation.return_value = False

        # Mock failed pattern service result
        pattern_result = FileOperationResult(
            success=False,
            message="Pattern resolution failed",
            files_processed=2,
            files_failed=3,
            error_details=[
                {"file": "test1.txt", "error": "Permission denied"},
                {"file": "test2.txt", "error": "File not found"}
            ],
            operation_log=["Pattern operation failed"]
        )
        self.mock_pattern_service.execute_with_fallback.return_value = pattern_result

        # Act
        success, message, file_count = self.service.move_files_by_patterns(
            "move_test_files", "cpp", "abc300", "a",
            "/workspace", "/contest_current", "/contest_stock", False
        )

        # Assert
        assert success is False
        assert message == "Pattern resolution failed"
        assert file_count == 2

        # Verify operation was recorded with failure details
        self.mock_repository.record_operation.assert_called_once()
        args = self.mock_repository.record_operation.call_args[0]
        assert args[6] == 2  # files_processed
        assert args[7] is False  # success
        assert "test1.txt: Permission denied" in args[8]  # error message

    def test_move_files_by_patterns_already_done(self):
        """Test move_files_by_patterns when operation already completed."""
        # Arrange
        self.mock_config_loader.get_shared_config.return_value = {
            "feature_flags": {"use_file_patterns": True}
        }
        self.mock_repository.has_successful_operation.return_value = True

        # Act
        success, message, file_count = self.service.move_files_by_patterns(
            "move_test_files", "cpp", "abc300", "a",
            "/workspace", "/contest_current", "/contest_stock", False
        )

        # Assert
        assert success is True
        assert "already completed" in message
        assert file_count == 0
        self.mock_pattern_service.execute_with_fallback.assert_not_called()

    def test_move_files_by_patterns_exception_handling(self):
        """Test move_files_by_patterns exception handling."""
        # Arrange
        self.mock_config_loader.get_shared_config.return_value = {
            "feature_flags": {"use_file_patterns": True}
        }
        self.mock_repository.has_successful_operation.return_value = False
        self.mock_pattern_service.execute_with_fallback.side_effect = Exception("Unexpected error")

        # Act
        success, message, file_count = self.service.move_files_by_patterns(
            "move_test_files", "cpp", "abc300", "a",
            "/workspace", "/contest_current", "/contest_stock", False
        )

        # Assert
        assert success is False
        assert "Pattern-based operation failed: Unexpected error" in message
        assert file_count == 0

        # Verify error was logged and recorded
        self.mock_logger.has_error("Pattern-based operation failed")
        self.mock_repository.record_operation.assert_called_once()

    def test_get_pattern_diagnosis_service_available(self):
        """Test get_pattern_diagnosis when service is available."""
        # Arrange
        expected_diagnosis = {
            "language": "cpp",
            "config_status": "valid",
            "issues": [],
            "suggestions": []
        }
        self.mock_pattern_service.diagnose_config_issues.return_value = expected_diagnosis

        # Act
        result = self.service.get_pattern_diagnosis("cpp")

        # Assert
        assert result == expected_diagnosis
        self.mock_pattern_service.diagnose_config_issues.assert_called_once_with("cpp")

    def test_get_pattern_diagnosis_service_unavailable(self):
        """Test get_pattern_diagnosis when service is unavailable."""
        # Arrange
        service_without_patterns = FilePreparationService(
            self.mock_file_driver,
            self.mock_repository,
            self.mock_logger,
            self.mock_config_loader,
            None  # No pattern service
        )

        # Act
        result = service_without_patterns.get_pattern_diagnosis("cpp")

        # Assert
        assert result["status"] == "unavailable"
        assert "FilePatternService not initialized" in result["message"]

    def test_get_pattern_diagnosis_exception_handling(self):
        """Test get_pattern_diagnosis exception handling."""
        # Arrange
        self.mock_pattern_service.diagnose_config_issues.side_effect = Exception("Diagnosis failed")

        # Act
        result = self.service.get_pattern_diagnosis("cpp")

        # Assert
        assert result["status"] == "error"
        assert "Diagnosis failed: Diagnosis failed" in result["message"]

    def test_is_file_patterns_enabled_true(self):
        """Test _is_file_patterns_enabled when feature is enabled."""
        # Arrange
        self.mock_config_loader.get_shared_config.return_value = {
            "feature_flags": {"use_file_patterns": True}
        }

        # Act
        result = self.service._is_file_patterns_enabled()

        # Assert
        assert result is True

    def test_is_file_patterns_enabled_false(self):
        """Test _is_file_patterns_enabled when feature is disabled."""
        # Arrange
        self.mock_config_loader.get_shared_config.return_value = {
            "feature_flags": {"use_file_patterns": False}
        }

        # Act
        result = self.service._is_file_patterns_enabled()

        # Assert
        assert result is False

    def test_is_file_patterns_enabled_missing_config(self):
        """Test _is_file_patterns_enabled with missing configuration."""
        # Arrange
        self.mock_config_loader.get_shared_config.return_value = {}

        # Act
        result = self.service._is_file_patterns_enabled()

        # Assert
        assert result is False

    def test_is_file_patterns_enabled_exception(self):
        """Test _is_file_patterns_enabled exception handling."""
        # Arrange
        self.mock_config_loader.get_shared_config.side_effect = Exception("Config error")

        # Act
        result = self.service._is_file_patterns_enabled()

        # Assert
        assert result is False
        self.mock_logger.has_warning("Failed to check file patterns feature flag")

"""Tests for refactored FilePreparationService helper methods."""
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.workflow.preparation.file.file_pattern_service import FileOperationResult, FilePatternService
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
        self.mock_file_pattern_service = Mock(spec=FilePatternService)

        self.service = FilePreparationService(
            self.mock_file_driver,
            self.mock_repository,
            self.mock_logger,
            self.mock_config_loader,
            self.mock_file_pattern_service
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


class TestMoveFilesByPatterns:
    """Test move_files_by_patterns method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_file_driver = Mock()
        self.mock_repository = Mock()
        self.mock_logger = MockLogger()
        self.mock_config_loader = Mock()
        self.mock_file_pattern_service = Mock(spec=FilePatternService)

        self.service = FilePreparationService(
            self.mock_file_driver,
            self.mock_repository,
            self.mock_logger,
            self.mock_config_loader,
            self.mock_file_pattern_service
        )

    def test_move_files_by_patterns_success(self):
        """Test successful pattern-based file operation."""
        # Arrange
        self.mock_repository.has_successful_operation.return_value = False

        result = FileOperationResult(
            success=True,
            message="Files moved successfully",
            files_processed=5,
            files_failed=0,
            error_details=[],
            operation_log=["File1 moved", "File2 moved"]
        )
        self.mock_file_pattern_service.execute_with_fallback.return_value = result

        # Act
        success, message, file_count = self.service.move_files_by_patterns(
            "move_test_files",
            "python", "abc300", "a",
            "/workspace", "/contest_current", "/contest_stock"
        )

        # Assert
        assert success is True
        assert message == "Files moved successfully"
        assert file_count == 5

    def test_move_files_by_patterns_already_done(self):
        """Test when operation already completed."""
        # Arrange
        self.mock_repository.has_successful_operation.return_value = True

        # Act
        success, message, file_count = self.service.move_files_by_patterns(
            "move_test_files",
            "python", "abc300", "a",
            "/workspace", "/contest_current", "/contest_stock"
        )

        # Assert
        assert success is True
        assert message == "move_test_files already completed"
        assert file_count == 0

    def test_move_files_by_patterns_pattern_service_error(self):
        """Test when pattern service raises an exception."""
        # Arrange
        self.mock_repository.has_successful_operation.return_value = False
        self.mock_file_pattern_service.execute_with_fallback.side_effect = Exception("Pattern error")

        # Act
        success, message, file_count = self.service.move_files_by_patterns(
            "move_test_files",
            "python", "abc300", "a",
            "/workspace", "/contest_current", "/contest_stock"
        )

        # Assert
        assert success is False
        assert "Pattern-based operation failed: Pattern error" in message
        assert file_count == 0


class TestFilePatternIntegration:
    """Test file pattern integration methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_file_driver = Mock()
        self.mock_repository = Mock()
        self.mock_logger = MockLogger()
        self.mock_config_loader = Mock()
        self.mock_file_pattern_service = Mock(spec=FilePatternService)

        self.service = FilePreparationService(
            self.mock_file_driver,
            self.mock_repository,
            self.mock_logger,
            self.mock_config_loader,
            self.mock_file_pattern_service
        )

    def test_get_pattern_diagnosis_success(self):
        """Test successful pattern diagnosis."""
        # Arrange
        expected_diagnosis = {
            "status": "healthy",
            "patterns": ["*.txt", "*.in"],
            "operations": ["move_test_files"]
        }
        self.mock_file_pattern_service.diagnose_config_issues.return_value = expected_diagnosis

        # Act
        result = self.service.get_pattern_diagnosis("python")

        # Assert
        assert result == expected_diagnosis
        self.mock_file_pattern_service.diagnose_config_issues.assert_called_once_with("python")

    def test_get_pattern_diagnosis_exception(self):
        """Test pattern diagnosis when exception occurs."""
        # Arrange
        self.mock_file_pattern_service.diagnose_config_issues.side_effect = Exception("Diagnosis error")

        # Act
        result = self.service.get_pattern_diagnosis("python")

        # Assert
        assert result["status"] == "error"
        assert "Diagnosis failed: Diagnosis error" in result["message"]


class TestOperationHistory:
    """Test operation history methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_file_driver = Mock()
        self.mock_repository = Mock()
        self.mock_logger = MockLogger()
        self.mock_config_loader = Mock()
        self.mock_file_pattern_service = Mock(spec=FilePatternService)

        self.service = FilePreparationService(
            self.mock_file_driver,
            self.mock_repository,
            self.mock_logger,
            self.mock_config_loader,
            self.mock_file_pattern_service
        )

    def test_get_operation_history(self):
        """Test getting operation history."""
        # Arrange
        expected_history = [
            {"operation": "move_test_files", "timestamp": "2023-01-01", "success": True},
            {"operation": "cleanup_workspace", "timestamp": "2023-01-02", "success": True}
        ]
        self.mock_repository.get_operations_by_context.return_value = expected_history

        # Act
        result = self.service.get_operation_history("python", "abc300", "a")

        # Assert
        assert result == expected_history
        self.mock_repository.get_operations_by_context.assert_called_once_with(
            "python", "abc300", "a"
        )

"""Tests for operation type constants."""
import pytest

from src.operations.constants.operation_type import (
    DirectoryName,
    FileOperationType,
    FilePattern,
    OperationType,
    PreparationAction,
)


class TestOperationType:
    """Tests for OperationType enum."""

    def test_operation_type_values(self):
        """Test that OperationType has expected values."""
        assert OperationType.SHELL
        assert OperationType.SHELL_INTERACTIVE
        assert OperationType.FILE
        assert OperationType.DOCKER
        assert OperationType.COMPOSITE
        assert OperationType.PYTHON
        # assert OperationType.FILE_PREPARATION  # Removed
        assert OperationType.STATE_SHOW
        assert OperationType.LOCAL_WORKSPACE

    def test_operation_type_auto_values(self):
        """Test that auto() generates unique values."""
        values = [op.value for op in OperationType]
        assert len(values) == len(set(values))  # All values should be unique


# class TestWorkspaceOperationType:
#     """Tests for WorkspaceOperationType enum."""
#
#     def test_workspace_operation_values(self):
#         """Test workspace operation type string values."""
#         assert WorkspaceOperationType.WORKSPACE_SWITCH.value == "workspace_switch"
#         assert WorkspaceOperationType.MOVE_TEST_FILES.value == "move_test_files"
#         assert WorkspaceOperationType.CLEANUP_WORKSPACE.value == "cleanup_workspace"
#         assert WorkspaceOperationType.ARCHIVE_CURRENT.value == "archive_current"
#
#     def test_workspace_operation_count(self):
#         """Test expected number of workspace operations."""
#         assert len(WorkspaceOperationType) == 4


class TestFileOperationType:
    """Tests for FileOperationType enum."""

    def test_file_operation_values(self):
        """Test file operation type string values."""
        assert FileOperationType.MKDIR.value == "mkdir"
        assert FileOperationType.TOUCH.value == "touch"
        assert FileOperationType.COPY.value == "copy"
        assert FileOperationType.MOVE.value == "move"
        assert FileOperationType.REMOVE.value == "remove"
        assert FileOperationType.READ.value == "read"
        assert FileOperationType.WRITE.value == "write"
        assert FileOperationType.EXISTS.value == "exists"

    def test_file_operation_count(self):
        """Test expected number of file operations."""
        assert len(FileOperationType) == 8


class TestDirectoryName:
    """Tests for DirectoryName enum."""

    def test_directory_name_values(self):
        """Test directory name string values."""
        assert DirectoryName.TEST.value == "test"
        assert DirectoryName.TEMPLATE.value == "template"
        assert DirectoryName.STOCK.value == "stock"
        assert DirectoryName.CURRENT.value == "current"
        assert DirectoryName.WORKSPACE.value == "workspace"
        assert DirectoryName.CONTEST_ENV.value == "contest_env"

    def test_directory_name_count(self):
        """Test expected number of directory names."""
        assert len(DirectoryName) == 6


class TestFilePattern:
    """Tests for FilePattern enum."""

    def test_file_pattern_values(self):
        """Test file pattern string values."""
        assert FilePattern.TEST_INPUT_PATTERN.value == "sample-*.in"
        assert FilePattern.TEST_OUTPUT_PATTERN.value == "sample-*.out"
        assert FilePattern.TEST_INPUT_EXTENSION.value == ".in"
        assert FilePattern.TEST_OUTPUT_EXTENSION.value == ".out"
        assert FilePattern.CONFIG_FILE.value == "env.json"
        assert FilePattern.DOCKERFILE.value == "Dockerfile"

    def test_file_pattern_count(self):
        """Test expected number of file patterns."""
        assert len(FilePattern) == 6


class TestPreparationAction:
    """Tests for PreparationAction enum."""

    def test_preparation_action_values(self):
        """Test preparation action string values."""
        assert PreparationAction.REMOVE_STOPPED_CONTAINER.value == "remove_stopped_container"
        assert PreparationAction.RUN_NEW_CONTAINER.value == "run_new_container"
        assert PreparationAction.CREATE_DIRECTORY.value == "create_directory"
        assert PreparationAction.BUILD_OR_PULL_IMAGE.value == "build_or_pull_image"

    def test_preparation_action_count(self):
        """Test expected number of preparation actions."""
        assert len(PreparationAction) == 4


class TestConstantIntegration:
    """Integration tests for constants across enums."""

    def test_no_duplicate_values_across_enums(self):
        """Test that string values don't conflict across different enums."""
        # workspace_values = {op.value for op in WorkspaceOperationType}
        file_values = {op.value for op in FileOperationType}
        directory_values = {op.value for op in DirectoryName}
        {op.value for op in FilePattern}
        {op.value for op in PreparationAction}

        # Check for overlaps between different categories
        # assert not workspace_values & file_values
        # assert not workspace_values & directory_values
        assert not file_values & directory_values

    def test_enum_accessibility(self):
        """Test that all enums can be imported and accessed correctly."""
        # Test that we can access enum members
        # assert hasattr(WorkspaceOperationType, 'MOVE_TEST_FILES')
        assert hasattr(FileOperationType, 'COPY')
        assert hasattr(DirectoryName, 'TEST')
        assert hasattr(FilePattern, 'CONFIG_FILE')
        assert hasattr(PreparationAction, 'CREATE_DIRECTORY')

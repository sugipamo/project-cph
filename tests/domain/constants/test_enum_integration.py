"""Integration tests for enum constants migration."""
import pytest

from src.domain.constants.operation_type import (
    DirectoryName,
    FileOperationType,
    FilePattern,
    PreparationAction,
)
from src.infrastructure.config.json_config_loader import JsonConfigLoader


class TestEnumIntegration:
    """Integration tests for enum constants with JsonConfigLoader compatibility."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config_loader = JsonConfigLoader("./contest_env")

    def test_directory_name_enum_matches_config_loader(self):
        """Test that DirectoryName enum values match JsonConfigLoader results."""
        assert DirectoryName.TEST.value == self.config_loader.get_directory_name('test')
        assert DirectoryName.TEMPLATE.value == self.config_loader.get_directory_name('template')
        assert DirectoryName.STOCK.value == self.config_loader.get_directory_name('stock')
        assert DirectoryName.CURRENT.value == self.config_loader.get_directory_name('current')
        assert DirectoryName.WORKSPACE.value == self.config_loader.get_directory_name('workspace')
        assert DirectoryName.CONTEST_ENV.value == self.config_loader.get_directory_name('contest_env')

    # def test_workspace_operation_enum_matches_config_loader(self):
    #     """Test that WorkspaceOperationType enum values match JsonConfigLoader results."""
    #     assert WorkspaceOperationType.WORKSPACE_SWITCH.value == self.config_loader.get_operation_type('workspace_switch')
    #     assert WorkspaceOperationType.MOVE_TEST_FILES.value == self.config_loader.get_operation_type('move_test_files')
    #     assert WorkspaceOperationType.CLEANUP_WORKSPACE.value == self.config_loader.get_operation_type('cleanup_workspace')
    #     assert WorkspaceOperationType.ARCHIVE_CURRENT.value == self.config_loader.get_operation_type('archive_current')

    def test_file_operation_enum_consistency(self):
        """Test that FileOperationType enum has consistent values."""
        expected_operations = {
            'mkdir', 'touch', 'copy', 'move', 'remove', 'read', 'write', 'exists'
        }
        actual_operations = {op.value for op in FileOperationType}
        assert actual_operations == expected_operations

    def test_file_pattern_enum_consistency(self):
        """Test that FilePattern enum has expected patterns."""
        assert FilePattern.TEST_INPUT_PATTERN.value == "sample-*.in"
        assert FilePattern.TEST_OUTPUT_PATTERN.value == "sample-*.out"
        assert FilePattern.TEST_INPUT_EXTENSION.value == ".in"
        assert FilePattern.TEST_OUTPUT_EXTENSION.value == ".out"
        assert FilePattern.CONFIG_FILE.value == "env.json"
        assert FilePattern.DOCKERFILE.value == "Dockerfile"

    def test_preparation_action_enum_consistency(self):
        """Test that PreparationAction enum has expected actions."""
        expected_actions = {
            'remove_stopped_container',
            'run_new_container',
            'create_directory',
            'build_or_pull_image'
        }
        actual_actions = {action.value for action in PreparationAction}
        assert actual_actions == expected_actions

    def test_enum_values_are_strings(self):
        """Test that all enum values are strings for compatibility."""
        for directory in DirectoryName:
            assert isinstance(directory.value, str)

        # for operation in WorkspaceOperationType:
        #     assert isinstance(operation.value, str)

        for file_op in FileOperationType:
            assert isinstance(file_op.value, str)

        for pattern in FilePattern:
            assert isinstance(pattern.value, str)

        for action in PreparationAction:
            assert isinstance(action.value, str)

    def test_enum_access_performance(self):
        """Test that enum access is efficient compared to config loader."""
        import time

        # Test enum access speed (should be very fast)
        start_time = time.time()
        for _ in range(1000):
            _ = DirectoryName.TEST.value
            # _ = WorkspaceOperationType.MOVE_TEST_FILES.value
        enum_time = time.time() - start_time

        # Test config loader access speed
        start_time = time.time()
        for _ in range(1000):
            _ = self.config_loader.get_directory_name('test')
            # _ = self.config_loader.get_operation_type('move_test_files')  # WorkspaceOperationType removed
        config_time = time.time() - start_time

        # Enum access should be faster (though both should be quite fast)
        assert enum_time < config_time * 2  # Allow some margin for test variability

    def test_backward_compatibility(self):
        """Test that deprecated methods still work for backward compatibility."""
        # These should still work even though they're deprecated
        assert self.config_loader.get_directory_name('test') == 'test'
        # assert self.config_loader.get_operation_type('move_test_files') == 'move_test_files'  # WorkspaceOperationType removed

        # Test fallback behavior for unknown keys
        assert self.config_loader.get_directory_name('unknown_dir') == 'unknown_dir'
        # assert self.config_loader.get_operation_type('unknown_op') == 'unknown_op'  # WorkspaceOperationType removed

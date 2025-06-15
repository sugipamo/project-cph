"""Tests for file operations resource extraction."""
from unittest.mock import Mock

import pytest

from src.workflow.builder.resource_analysis.file_operations import (
    _extract_copy_resources,
    _extract_move_resources,
    _extract_remove_resources,
    _extract_rmtree_resources,
    _extract_touch_resources,
    extract_file_operation_resources,
)
from src.workflow.builder.resource_analysis.resource_types import ResourceInfo
from src.workflow.step.step import Step, StepType


class TestExtractFileOperationResources:
    """Test main file operation resource extraction function."""

    def test_touch_step(self):
        step = Step(type=StepType.TOUCH, cmd=["output.txt"])
        resources = extract_file_operation_resources(step)

        assert resources.creates_files == {"output.txt"}
        assert resources.creates_dirs == set()
        assert resources.reads_files == set()
        assert resources.requires_dirs == {"."}

    def test_copy_step(self):
        step = Step(type=StepType.COPY, cmd=["source.txt", "dest.txt"])
        resources = extract_file_operation_resources(step)

        assert resources.creates_files == {"dest.txt"}
        assert resources.creates_dirs == set()
        assert resources.reads_files == {"source.txt"}
        assert resources.requires_dirs == {"."}

    def test_move_step(self):
        step = Step(type=StepType.MOVE, cmd=["old.txt", "new.txt"])
        resources = extract_file_operation_resources(step)

        assert resources.creates_files == {"new.txt"}
        assert resources.creates_dirs == set()
        assert resources.reads_files == {"old.txt"}
        assert resources.requires_dirs == {"."}

    def test_remove_step(self):
        step = Step(type=StepType.REMOVE, cmd=["target.txt"])
        resources = extract_file_operation_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == set()
        assert resources.reads_files == {"target.txt"}
        assert resources.requires_dirs == set()

    def test_rmtree_step(self):
        step = Step(type=StepType.RMTREE, cmd=["target_dir"])
        resources = extract_file_operation_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == set()
        assert resources.reads_files == {"target_dir"}
        assert resources.requires_dirs == set()

    def test_unsupported_step_type(self):
        step = Step(type=StepType.SHELL, cmd=["echo", "hello"])
        resources = extract_file_operation_resources(step)

        # Should return empty ResourceInfo
        assert resources == ResourceInfo.empty()


class TestTouchResources:
    """Test TOUCH step resource extraction."""

    def test_touch_simple_file(self):
        step = Step(type=StepType.TOUCH, cmd=["file.txt"])
        resources = _extract_touch_resources(step)

        assert resources.creates_files == {"file.txt"}
        assert resources.creates_dirs == set()
        assert resources.reads_files == set()
        assert resources.requires_dirs == {"."}

    def test_touch_nested_file(self):
        step = Step(type=StepType.TOUCH, cmd=["dir1/dir2/file.txt"])
        resources = _extract_touch_resources(step)

        assert resources.creates_files == {"dir1/dir2/file.txt"}
        assert resources.creates_dirs == set()
        assert resources.reads_files == set()
        assert resources.requires_dirs == {"dir1/dir2"}

    def test_touch_root_file(self):
        step = Step(type=StepType.TOUCH, cmd=["/absolute/path/file.txt"])
        resources = _extract_touch_resources(step)

        assert resources.creates_files == {"/absolute/path/file.txt"}
        assert resources.creates_dirs == set()
        assert resources.reads_files == set()
        assert resources.requires_dirs == {"/absolute/path"}



class TestCopyResources:
    """Test COPY step resource extraction."""

    def test_copy_simple_files(self):
        step = Step(type=StepType.COPY, cmd=["source.txt", "dest.txt"])
        resources = _extract_copy_resources(step)

        assert resources.creates_files == {"dest.txt"}
        assert resources.creates_dirs == set()
        assert resources.reads_files == {"source.txt"}
        assert resources.requires_dirs == {"."}

    def test_copy_nested_paths(self):
        step = Step(type=StepType.COPY, cmd=["src/input.txt", "output/result.txt"])
        resources = _extract_copy_resources(step)

        assert resources.creates_files == {"output/result.txt"}
        assert resources.creates_dirs == set()
        assert resources.reads_files == {"src/input.txt"}
        assert resources.requires_dirs == {"output"}

    def test_copy_absolute_paths(self):
        step = Step(type=StepType.COPY, cmd=["/tmp/source.txt", "/opt/dest.txt"])
        resources = _extract_copy_resources(step)

        assert resources.creates_files == {"/opt/dest.txt"}
        assert resources.creates_dirs == set()
        assert resources.reads_files == {"/tmp/source.txt"}
        assert resources.requires_dirs == {"/opt"}



class TestMoveResources:
    """Test MOVE step resource extraction."""

    def test_move_simple_files(self):
        step = Step(type=StepType.MOVE, cmd=["old.txt", "new.txt"])
        resources = _extract_move_resources(step)

        assert resources.creates_files == {"new.txt"}
        assert resources.creates_dirs == set()
        assert resources.reads_files == {"old.txt"}
        assert resources.requires_dirs == {"."}

    def test_move_nested_paths(self):
        step = Step(type=StepType.MOVE, cmd=["temp/file.txt", "final/moved.txt"])
        resources = _extract_move_resources(step)

        assert resources.creates_files == {"final/moved.txt"}
        assert resources.creates_dirs == set()
        assert resources.reads_files == {"temp/file.txt"}
        assert resources.requires_dirs == {"final"}

    def test_move_cross_directory(self):
        step = Step(type=StepType.MOVE, cmd=["dir1/file.txt", "dir2/file.txt"])
        resources = _extract_move_resources(step)

        assert resources.creates_files == {"dir2/file.txt"}
        assert resources.creates_dirs == set()
        assert resources.reads_files == {"dir1/file.txt"}
        assert resources.requires_dirs == {"dir2"}



class TestRemoveResources:
    """Test REMOVE step resource extraction."""

    def test_remove_simple_file(self):
        step = Step(type=StepType.REMOVE, cmd=["target.txt"])
        resources = _extract_remove_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == set()
        assert resources.reads_files == {"target.txt"}
        assert resources.requires_dirs == set()

    def test_remove_nested_file(self):
        step = Step(type=StepType.REMOVE, cmd=["dir/subdir/file.txt"])
        resources = _extract_remove_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == set()
        assert resources.reads_files == {"dir/subdir/file.txt"}
        assert resources.requires_dirs == set()

    def test_remove_absolute_path(self):
        step = Step(type=StepType.REMOVE, cmd=["/tmp/unwanted.txt"])
        resources = _extract_remove_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == set()
        assert resources.reads_files == {"/tmp/unwanted.txt"}
        assert resources.requires_dirs == set()



class TestRmtreeResources:
    """Test RMTREE step resource extraction."""

    def test_rmtree_simple_dir(self):
        step = Step(type=StepType.RMTREE, cmd=["target_dir"])
        resources = _extract_rmtree_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == set()
        assert resources.reads_files == {"target_dir"}
        assert resources.requires_dirs == set()

    def test_rmtree_nested_dir(self):
        step = Step(type=StepType.RMTREE, cmd=["parent/child/grandchild"])
        resources = _extract_rmtree_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == set()
        assert resources.reads_files == {"parent/child/grandchild"}
        assert resources.requires_dirs == set()

    def test_rmtree_absolute_path(self):
        step = Step(type=StepType.RMTREE, cmd=["/tmp/temp_dir"])
        resources = _extract_rmtree_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == set()
        assert resources.reads_files == {"/tmp/temp_dir"}
        assert resources.requires_dirs == set()



class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_file_paths(self):
        step = Step(type=StepType.TOUCH, cmd=[""])
        resources = _extract_touch_resources(step)

        assert resources.creates_files == {""}
        assert resources.creates_dirs == set()
        assert resources.reads_files == set()
        assert resources.requires_dirs == {"."}

    def test_current_directory_paths(self):
        step = Step(type=StepType.TOUCH, cmd=["./file.txt"])
        resources = _extract_touch_resources(step)

        assert resources.creates_files == {"./file.txt"}
        assert resources.creates_dirs == set()
        assert resources.reads_files == set()
        assert resources.requires_dirs == {"."}

    def test_parent_directory_paths(self):
        step = Step(type=StepType.TOUCH, cmd=["../file.txt"])
        resources = _extract_touch_resources(step)

        assert resources.creates_files == {"../file.txt"}
        assert resources.creates_dirs == set()
        assert resources.reads_files == set()
        assert resources.requires_dirs == {".."}

    def test_copy_same_source_dest(self):
        step = Step(type=StepType.COPY, cmd=["file.txt", "file.txt"])
        resources = _extract_copy_resources(step)

        assert resources.creates_files == {"file.txt"}
        assert resources.creates_dirs == set()
        assert resources.reads_files == {"file.txt"}
        assert resources.requires_dirs == {"."}

    def test_move_same_source_dest(self):
        step = Step(type=StepType.MOVE, cmd=["file.txt", "file.txt"])
        resources = _extract_move_resources(step)

        assert resources.creates_files == {"file.txt"}
        assert resources.creates_dirs == set()
        assert resources.reads_files == {"file.txt"}
        assert resources.requires_dirs == {"."}

    def test_multiple_file_operations_sequence(self):
        # Test a sequence of operations to ensure they work together
        touch_step = Step(type=StepType.TOUCH, cmd=["temp.txt"])
        copy_step = Step(type=StepType.COPY, cmd=["temp.txt", "backup.txt"])
        move_step = Step(type=StepType.MOVE, cmd=["backup.txt", "final.txt"])
        remove_step = Step(type=StepType.REMOVE, cmd=["temp.txt"])

        touch_resources = extract_file_operation_resources(touch_step)
        copy_resources = extract_file_operation_resources(copy_step)
        move_resources = extract_file_operation_resources(move_step)
        remove_resources = extract_file_operation_resources(remove_step)

        # Verify each step's resources
        assert touch_resources.creates_files == {"temp.txt"}
        assert copy_resources.creates_files == {"backup.txt"}
        assert copy_resources.reads_files == {"temp.txt"}
        assert move_resources.creates_files == {"final.txt"}
        assert move_resources.reads_files == {"backup.txt"}
        assert remove_resources.reads_files == {"temp.txt"}

        # Merge all resources to see the overall effect
        total_resources = touch_resources.merge(copy_resources).merge(move_resources).merge(remove_resources)

        assert total_resources.creates_files == {"temp.txt", "backup.txt", "final.txt"}
        assert total_resources.reads_files == {"temp.txt", "backup.txt"}

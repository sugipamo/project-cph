"""Tests for directory operations resource extraction."""
import pytest

from src.workflow.builder.resource_analysis.directory_operations import (
    _extract_mkdir_resources,
    _extract_movetree_resources,
    extract_directory_operation_resources,
)
from src.workflow.builder.resource_analysis.resource_types import ResourceInfo
from src.workflow.step.step import Step, StepType


class TestExtractDirectoryOperationResources:
    """Test main directory operation resource extraction function."""

    def test_mkdir_step(self):
        step = Step(type=StepType.MKDIR, cmd=["new_directory"])
        resources = extract_directory_operation_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == {"new_directory"}
        assert resources.reads_files == set()
        assert resources.requires_dirs == set()

    def test_movetree_step(self):
        step = Step(type=StepType.MOVETREE, cmd=["source_dir", "dest_dir"])
        resources = extract_directory_operation_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == {"dest_dir"}
        assert resources.reads_files == {"source_dir"}
        assert resources.requires_dirs == set()

    def test_unsupported_step_type(self):
        step = Step(type=StepType.SHELL, cmd=["echo", "hello"])
        resources = extract_directory_operation_resources(step)

        # Should return empty ResourceInfo
        assert resources == ResourceInfo.empty()

    def test_file_operation_step_returns_empty(self):
        # File operations should return empty when passed to directory function
        step = Step(type=StepType.TOUCH, cmd=["file.txt"])
        resources = extract_directory_operation_resources(step)

        assert resources == ResourceInfo.empty()


class TestMkdirResources:
    """Test MKDIR step resource extraction."""

    def test_mkdir_simple_directory(self):
        step = Step(type=StepType.MKDIR, cmd=["simple_dir"])
        resources = _extract_mkdir_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == {"simple_dir"}
        assert resources.reads_files == set()
        assert resources.requires_dirs == set()

    def test_mkdir_nested_directory(self):
        step = Step(type=StepType.MKDIR, cmd=["parent/child/grandchild"])
        resources = _extract_mkdir_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == {"parent/child/grandchild"}
        assert resources.reads_files == set()
        assert resources.requires_dirs == set()

    def test_mkdir_absolute_path(self):
        step = Step(type=StepType.MKDIR, cmd=["/tmp/absolute_dir"])
        resources = _extract_mkdir_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == {"/tmp/absolute_dir"}
        assert resources.reads_files == set()
        assert resources.requires_dirs == set()

    def test_mkdir_current_directory_reference(self):
        step = Step(type=StepType.MKDIR, cmd=["./current_dir"])
        resources = _extract_mkdir_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == {"./current_dir"}
        assert resources.reads_files == set()
        assert resources.requires_dirs == set()

    def test_mkdir_parent_directory_reference(self):
        step = Step(type=StepType.MKDIR, cmd=["../parent_dir"])
        resources = _extract_mkdir_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == {"../parent_dir"}
        assert resources.reads_files == set()
        assert resources.requires_dirs == set()


    def test_mkdir_empty_string_path(self):
        step = Step(type=StepType.MKDIR, cmd=[""])
        resources = _extract_mkdir_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == {""}
        assert resources.reads_files == set()
        assert resources.requires_dirs == set()

    def test_mkdir_with_spaces_in_name(self):
        step = Step(type=StepType.MKDIR, cmd=["directory with spaces"])
        resources = _extract_mkdir_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == {"directory with spaces"}
        assert resources.reads_files == set()
        assert resources.requires_dirs == set()


class TestMovetreeResources:
    """Test MOVETREE step resource extraction."""

    def test_movetree_simple_directories(self):
        step = Step(type=StepType.MOVETREE, cmd=["old_dir", "new_dir"])
        resources = _extract_movetree_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == {"new_dir"}
        assert resources.reads_files == {"old_dir"}
        assert resources.requires_dirs == set()

    def test_movetree_nested_directories(self):
        step = Step(type=StepType.MOVETREE, cmd=["src/project", "backup/project"])
        resources = _extract_movetree_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == {"backup/project"}
        assert resources.reads_files == {"src/project"}
        assert resources.requires_dirs == set()

    def test_movetree_absolute_paths(self):
        step = Step(type=StepType.MOVETREE, cmd=["/tmp/source", "/opt/destination"])
        resources = _extract_movetree_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == {"/opt/destination"}
        assert resources.reads_files == {"/tmp/source"}
        assert resources.requires_dirs == set()

    def test_movetree_cross_directory_move(self):
        step = Step(type=StepType.MOVETREE, cmd=["project/old_location", "archive/new_location"])
        resources = _extract_movetree_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == {"archive/new_location"}
        assert resources.reads_files == {"project/old_location"}
        assert resources.requires_dirs == set()

    def test_movetree_same_source_dest(self):
        step = Step(type=StepType.MOVETREE, cmd=["directory", "directory"])
        resources = _extract_movetree_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == {"directory"}
        assert resources.reads_files == {"directory"}
        assert resources.requires_dirs == set()


    def test_movetree_empty_string_paths(self):
        step = Step(type=StepType.MOVETREE, cmd=["", ""])
        resources = _extract_movetree_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == {""}
        assert resources.reads_files == {""}
        assert resources.requires_dirs == set()

    def test_movetree_with_spaces_in_names(self):
        step = Step(type=StepType.MOVETREE, cmd=["old directory", "new directory"])
        resources = _extract_movetree_resources(step)

        assert resources.creates_files == set()
        assert resources.creates_dirs == {"new directory"}
        assert resources.reads_files == {"old directory"}
        assert resources.requires_dirs == set()


class TestComplexScenarios:
    """Test complex scenarios and edge cases."""

    def test_multiple_directory_operations_sequence(self):
        # Test a sequence of directory operations
        mkdir_step = Step(type=StepType.MKDIR, cmd=["workspace"])
        mkdir_nested_step = Step(type=StepType.MKDIR, cmd=["workspace/project"])
        movetree_step = Step(type=StepType.MOVETREE, cmd=["workspace", "backup"])

        mkdir_resources = extract_directory_operation_resources(mkdir_step)
        mkdir_nested_resources = extract_directory_operation_resources(mkdir_nested_step)
        movetree_resources = extract_directory_operation_resources(movetree_step)

        # Verify each step's resources
        assert mkdir_resources.creates_dirs == {"workspace"}
        assert mkdir_nested_resources.creates_dirs == {"workspace/project"}
        assert movetree_resources.creates_dirs == {"backup"}
        assert movetree_resources.reads_files == {"workspace"}

        # Merge all resources to see the overall effect
        total_resources = mkdir_resources.merge(mkdir_nested_resources).merge(movetree_resources)

        assert total_resources.creates_dirs == {"workspace", "workspace/project", "backup"}
        assert total_resources.reads_files == {"workspace"}
        assert total_resources.creates_files == set()
        assert total_resources.requires_dirs == set()

    def test_directory_operations_with_relative_paths(self):
        # Test various relative path patterns
        relative_paths = [
            "./current",
            "../parent",
            "../../grandparent",
            "./nested/deep/path",
            "../sibling/path"
        ]

        for path in relative_paths:
            mkdir_step = Step(type=StepType.MKDIR, cmd=[path])
            resources = extract_directory_operation_resources(mkdir_step)

            assert resources.creates_dirs == {path}
            assert resources.creates_files == set()
            assert resources.reads_files == set()
            assert resources.requires_dirs == set()

    def test_directory_operations_with_special_characters(self):
        # Test directory names with special characters
        special_names = [
            "dir-with-dashes",
            "dir_with_underscores",
            "dir.with.dots",
            "dir with spaces",
            "dir@with#special$chars"
        ]

        for name in special_names:
            mkdir_step = Step(type=StepType.MKDIR, cmd=[name])
            resources = extract_directory_operation_resources(mkdir_step)

            assert resources.creates_dirs == {name}
            assert resources.creates_files == set()
            assert resources.reads_files == set()
            assert resources.requires_dirs == set()

    def test_mixed_operation_types(self):
        # Ensure directory operations don't interfere with other step types
        non_directory_steps = [
            Step(type=StepType.SHELL, cmd=["echo", "hello"]),
            Step(type=StepType.TOUCH, cmd=["file.txt"]),
            Step(type=StepType.COPY, cmd=["src.txt", "dest.txt"]),
            Step(type=StepType.DOCKER_RUN, cmd=["python", "script.py"])
        ]

        for step in non_directory_steps:
            resources = extract_directory_operation_resources(step)
            assert resources == ResourceInfo.empty()

    def test_directory_operation_edge_cases(self):
        # Test various edge cases
        edge_cases = [
            # Multiple command arguments (should only use first for mkdir)
            Step(type=StepType.MKDIR, cmd=["dir1", "dir2", "dir3"]),
            # Empty path
            Step(type=StepType.MKDIR, cmd=[""]),
            # Root directory
            Step(type=StepType.MKDIR, cmd=["/"]),
            # Current directory
            Step(type=StepType.MKDIR, cmd=["."]),
            # Parent directory
            Step(type=StepType.MKDIR, cmd=[".."]),
        ]

        expected_dirs = ["dir1", "", "/", ".", ".."]

        for step, expected_dir in zip(edge_cases, expected_dirs):
            resources = extract_directory_operation_resources(step)
            assert resources.creates_dirs == {expected_dir}
            assert resources.creates_files == set()
            assert resources.reads_files == set()
            assert resources.requires_dirs == set()

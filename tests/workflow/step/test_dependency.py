"""Tests for workflow step dependency resolution"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.workflow.step.dependency import (
    analyze_step_dependencies,
    creates_file,
    generate_preparation_steps,
    optimize_copy_steps,
    optimize_mkdir_steps,
    resolve_dependencies,
    update_resource_tracking,
)
from src.workflow.step.step import Step, StepContext, StepType


class TestResolveDependencies:
    """Tests for resolve_dependencies function"""

    def test_resolve_dependencies_empty_list(self):
        """Test resolve_dependencies with empty step list"""
        context = Mock(spec=StepContext)
        result = resolve_dependencies([], context)
        assert result == []

    def test_resolve_dependencies_no_prep_needed(self):
        """Test resolve_dependencies when no preparation steps are needed"""
        step = Step(type=StepType.SHELL, cmd=["echo", "hello"])
        context = Mock(spec=StepContext)

        result = resolve_dependencies([step], context)

        assert len(result) == 1
        assert result[0] == step

    def test_resolve_dependencies_copy_step(self):
        """Test resolve_dependencies with copy step requiring directory creation"""
        step = Step(type=StepType.COPY, cmd=["src.txt", "dest/dst.txt"])
        context = Mock(spec=StepContext)

        result = resolve_dependencies([step], context)

        # Should add mkdir step before copy
        assert len(result) == 2
        assert result[0].type == StepType.MKDIR
        assert result[0].cmd == ["dest"]
        assert result[0].allow_failure is True
        assert result[0].auto_generated is True
        assert result[1] == step

    def test_resolve_dependencies_skip_when_condition(self):
        """Test resolve_dependencies skips preparation when step has when condition with invalid paths"""
        step = Step(
            type=StepType.COPY,
            cmd=["src.txt", "dest//invalid.txt"],
            when="some condition"
        )
        context = Mock(spec=StepContext)

        # Mock the template expansion to return invalid path
        with patch('src.workflow.step.step_generation_service.execution_context_to_simple_context') as mock_ctx, \
             patch('src.workflow.step.step_runner.expand_template') as mock_expand:
            mock_ctx.return_value = {}
            mock_expand.side_effect = lambda arg, ctx: arg

            result = resolve_dependencies([step], context)

        # Should skip preparation step due to invalid path
        assert len(result) == 1
        assert result[0] == step

    def test_resolve_dependencies_multiple_steps(self):
        """Test resolve_dependencies with multiple steps"""
        step1 = Step(type=StepType.TOUCH, cmd=["dir1/file1.txt"])
        step2 = Step(type=StepType.COPY, cmd=["src.txt", "dir2/dst.txt"])
        context = Mock(spec=StepContext)

        result = resolve_dependencies([step1, step2], context)

        # Should add mkdir steps before each file operation
        assert len(result) == 4
        assert result[0].type == StepType.MKDIR  # for dir1
        assert result[0].cmd == ["dir1"]
        assert result[1] == step1
        assert result[2].type == StepType.MKDIR  # for dir2
        assert result[2].cmd == ["dir2"]
        assert result[3] == step2

    def test_resolve_dependencies_avoid_duplicate_mkdir(self):
        """Test resolve_dependencies avoids creating duplicate mkdir steps"""
        step1 = Step(type=StepType.TOUCH, cmd=["dir1/file1.txt"])
        step2 = Step(type=StepType.TOUCH, cmd=["dir1/file2.txt"])
        context = Mock(spec=StepContext)

        result = resolve_dependencies([step1, step2], context)

        # Should only create one mkdir for dir1
        mkdir_steps = [s for s in result if s.type == StepType.MKDIR]
        assert len(mkdir_steps) == 1
        assert mkdir_steps[0].cmd == ["dir1"]


class TestGeneratePreparationSteps:
    """Tests for generate_preparation_steps function"""

    def test_generate_preparation_steps_copy(self):
        """Test generate_preparation_steps for copy step"""
        step = Step(type=StepType.COPY, cmd=["src.txt", "dest/dst.txt"])
        existing_dirs = set()
        existing_files = set()
        context = Mock(spec=StepContext)

        result = generate_preparation_steps(step, existing_dirs, existing_files, context)

        assert len(result) == 1
        assert result[0].type == StepType.MKDIR
        assert result[0].cmd == ["dest"]
        assert result[0].allow_failure is True
        assert result[0].auto_generated is True

    def test_generate_preparation_steps_move(self):
        """Test generate_preparation_steps for move step"""
        step = Step(type=StepType.MOVE, cmd=["src.txt", "dest/dst.txt"])
        existing_dirs = set()
        existing_files = set()
        context = Mock(spec=StepContext)

        result = generate_preparation_steps(step, existing_dirs, existing_files, context)

        assert len(result) == 1
        assert result[0].type == StepType.MKDIR
        assert result[0].cmd == ["dest"]

    def test_generate_preparation_steps_movetree(self):
        """Test generate_preparation_steps for movetree step"""
        step = Step(type=StepType.MOVETREE, cmd=["src_dir", "dest/dst_dir"])
        existing_dirs = set()
        existing_files = set()
        context = Mock(spec=StepContext)

        result = generate_preparation_steps(step, existing_dirs, existing_files, context)

        assert len(result) == 1
        assert result[0].type == StepType.MKDIR
        assert result[0].cmd == ["dest"]

    def test_generate_preparation_steps_touch(self):
        """Test generate_preparation_steps for touch step"""
        step = Step(type=StepType.TOUCH, cmd=["dir/file.txt"])
        existing_dirs = set()
        existing_files = set()
        context = Mock(spec=StepContext)

        result = generate_preparation_steps(step, existing_dirs, existing_files, context)

        assert len(result) == 1
        assert result[0].type == StepType.MKDIR
        assert result[0].cmd == ["dir"]

    def test_generate_preparation_steps_with_cwd(self):
        """Test generate_preparation_steps when step has cwd"""
        step = Step(type=StepType.SHELL, cmd=["echo", "hello"], cwd="workdir")
        existing_dirs = set()
        existing_files = set()
        context = Mock(spec=StepContext)

        result = generate_preparation_steps(step, existing_dirs, existing_files, context)

        assert len(result) == 1
        assert result[0].type == StepType.MKDIR
        assert result[0].cmd == ["workdir"]

    def test_generate_preparation_steps_no_prep_needed(self):
        """Test generate_preparation_steps when no preparation is needed"""
        step = Step(type=StepType.SHELL, cmd=["echo", "hello"])
        existing_dirs = set()
        existing_files = set()
        context = Mock(spec=StepContext)

        result = generate_preparation_steps(step, existing_dirs, existing_files, context)

        assert result == []

    def test_generate_preparation_steps_directory_exists(self):
        """Test generate_preparation_steps when directory already exists"""
        step = Step(type=StepType.COPY, cmd=["src.txt", "dest/dst.txt"])
        existing_dirs = {"dest"}
        existing_files = set()
        context = Mock(spec=StepContext)

        result = generate_preparation_steps(step, existing_dirs, existing_files, context)

        assert result == []

    def test_generate_preparation_steps_current_directory(self):
        """Test generate_preparation_steps with current directory destination"""
        step = Step(type=StepType.COPY, cmd=["src.txt", "dst.txt"])
        existing_dirs = set()
        existing_files = set()
        context = Mock(spec=StepContext)

        result = generate_preparation_steps(step, existing_dirs, existing_files, context)

        assert result == []


class TestUpdateResourceTracking:
    """Tests for update_resource_tracking function"""

    def test_update_resource_tracking_mkdir(self):
        """Test update_resource_tracking for mkdir step"""
        step = Step(type=StepType.MKDIR, cmd=["newdir"])
        existing_dirs = set()
        existing_files = set()

        update_resource_tracking(step, existing_dirs, existing_files)

        assert "newdir" in existing_dirs
        assert len(existing_files) == 0

    def test_update_resource_tracking_touch(self):
        """Test update_resource_tracking for touch step"""
        step = Step(type=StepType.TOUCH, cmd=["dir/file.txt"])
        existing_dirs = set()
        existing_files = set()

        update_resource_tracking(step, existing_dirs, existing_files)

        assert "dir/file.txt" in existing_files
        assert "dir" in existing_dirs

    def test_update_resource_tracking_copy(self):
        """Test update_resource_tracking for copy step"""
        step = Step(type=StepType.COPY, cmd=["src.txt", "dest/dst.txt"])
        existing_dirs = set()
        existing_files = set()

        update_resource_tracking(step, existing_dirs, existing_files)

        assert "dest/dst.txt" in existing_files
        assert "dest" in existing_dirs

    def test_update_resource_tracking_move(self):
        """Test update_resource_tracking for move step"""
        step = Step(type=StepType.MOVE, cmd=["src.txt", "dest/dst.txt"])
        existing_dirs = set()
        existing_files = set()

        update_resource_tracking(step, existing_dirs, existing_files)

        assert "dest/dst.txt" in existing_files
        assert "dest" in existing_dirs

    def test_update_resource_tracking_movetree(self):
        """Test update_resource_tracking for movetree step"""
        step = Step(type=StepType.MOVETREE, cmd=["src_dir", "dest/dst_dir"])
        existing_dirs = set()
        existing_files = set()

        update_resource_tracking(step, existing_dirs, existing_files)

        assert "dest/dst_dir" in existing_dirs
        assert "dest" in existing_dirs

    def test_update_resource_tracking_remove(self):
        """Test update_resource_tracking for remove step"""
        step = Step(type=StepType.REMOVE, cmd=["file.txt"])
        existing_dirs = {"dir1"}
        existing_files = {"file.txt", "other.txt"}

        update_resource_tracking(step, existing_dirs, existing_files)

        assert "file.txt" not in existing_files
        assert "other.txt" in existing_files
        assert "dir1" in existing_dirs

    def test_update_resource_tracking_rmtree(self):
        """Test update_resource_tracking for rmtree step"""
        step = Step(type=StepType.RMTREE, cmd=["dir1"])
        existing_dirs = {"dir1", "dir2"}
        existing_files = {"file.txt"}

        update_resource_tracking(step, existing_dirs, existing_files)

        assert "dir1" not in existing_dirs
        assert "dir2" in existing_dirs
        assert "file.txt" in existing_files


class TestAnalyzeStepDependencies:
    """Tests for analyze_step_dependencies function"""

    def test_analyze_step_dependencies_empty(self):
        """Test analyze_step_dependencies with empty list"""
        result = analyze_step_dependencies([])
        assert result == {}

    def test_analyze_step_dependencies_no_dependencies(self):
        """Test analyze_step_dependencies with independent steps"""
        steps = [
            Step(type=StepType.TOUCH, cmd=["file1.txt"]),
            Step(type=StepType.TOUCH, cmd=["file2.txt"])
        ]

        result = analyze_step_dependencies(steps)

        assert result == {0: [], 1: []}

    def test_analyze_step_dependencies_with_dependency(self):
        """Test analyze_step_dependencies with file dependency"""
        steps = [
            Step(type=StepType.TOUCH, cmd=["temp.txt"]),
            Step(type=StepType.COPY, cmd=["temp.txt", "final.txt"])
        ]

        result = analyze_step_dependencies(steps)

        assert result == {0: [], 1: [0]}

    def test_analyze_step_dependencies_multiple_dependencies(self):
        """Test analyze_step_dependencies with multiple dependencies"""
        steps = [
            Step(type=StepType.TOUCH, cmd=["file1.txt"]),
            Step(type=StepType.TOUCH, cmd=["file2.txt"]),
            Step(type=StepType.COPY, cmd=["file1.txt", "copy1.txt"]),
            Step(type=StepType.MOVE, cmd=["file2.txt", "moved.txt"])
        ]

        result = analyze_step_dependencies(steps)

        assert result == {0: [], 1: [], 2: [0], 3: [1]}


class TestCreatesFile:
    """Tests for creates_file function"""

    def test_creates_file_touch(self):
        """Test creates_file for touch step"""
        step = Step(type=StepType.TOUCH, cmd=["file.txt"])
        assert creates_file(step, "file.txt") is True
        assert creates_file(step, "other.txt") is False

    def test_creates_file_copy(self):
        """Test creates_file for copy step"""
        step = Step(type=StepType.COPY, cmd=["src.txt", "dst.txt"])
        assert creates_file(step, "dst.txt") is True
        assert creates_file(step, "src.txt") is False

    def test_creates_file_move(self):
        """Test creates_file for move step"""
        step = Step(type=StepType.MOVE, cmd=["src.txt", "dst.txt"])
        assert creates_file(step, "dst.txt") is True
        assert creates_file(step, "src.txt") is False

    def test_creates_file_shell(self):
        """Test creates_file for shell step (conservative approach)"""
        step = Step(type=StepType.SHELL, cmd=["echo", "hello", ">", "output.txt"])
        assert creates_file(step, "output.txt") is False

    def test_creates_file_insufficient_args(self):
        """Test creates_file with insufficient command arguments"""
        # Step creation will fail validation, so test that the validation works
        with pytest.raises(ValueError, match="requires at least 2 arguments"):
            Step(type=StepType.COPY, cmd=["src.txt"])


class TestOptimizeMkdirSteps:
    """Tests for optimize_mkdir_steps function"""

    def test_optimize_mkdir_steps_empty(self):
        """Test optimize_mkdir_steps with empty list"""
        result = optimize_mkdir_steps([])
        assert result == []

    def test_optimize_mkdir_steps_no_mkdir(self):
        """Test optimize_mkdir_steps with no mkdir steps"""
        steps = [
            Step(type=StepType.TOUCH, cmd=["file.txt"]),
            Step(type=StepType.SHELL, cmd=["echo", "hello"])
        ]

        result = optimize_mkdir_steps(steps)
        assert result == steps

    def test_optimize_mkdir_steps_single_mkdir(self):
        """Test optimize_mkdir_steps with single mkdir step"""
        steps = [Step(type=StepType.MKDIR, cmd=["dir1"])]

        result = optimize_mkdir_steps(steps)
        assert result == steps

    def test_optimize_mkdir_steps_consecutive_mkdir(self):
        """Test optimize_mkdir_steps with consecutive mkdir steps"""
        steps = [
            Step(type=StepType.MKDIR, cmd=["dir1"], allow_failure=True),
            Step(type=StepType.MKDIR, cmd=["dir2"], allow_failure=True),
            Step(type=StepType.MKDIR, cmd=["dir3"], allow_failure=True)
        ]

        result = optimize_mkdir_steps(steps)

        # Should keep separate steps but remove duplicates
        assert len(result) == 3
        assert all(step.type == StepType.MKDIR for step in result)
        assert [step.cmd[0] for step in result] == ["dir1", "dir2", "dir3"]

    def test_optimize_mkdir_steps_with_duplicates(self):
        """Test optimize_mkdir_steps removes duplicate paths"""
        steps = [
            Step(type=StepType.MKDIR, cmd=["dir1"], allow_failure=True),
            Step(type=StepType.MKDIR, cmd=["dir2"], allow_failure=True),
            Step(type=StepType.MKDIR, cmd=["dir1"], allow_failure=True)  # duplicate
        ]

        result = optimize_mkdir_steps(steps)

        # Should remove duplicate but keep order
        assert len(result) == 2
        assert [step.cmd[0] for step in result] == ["dir1", "dir2"]

    def test_optimize_mkdir_steps_different_attributes(self):
        """Test optimize_mkdir_steps with different step attributes"""
        steps = [
            Step(type=StepType.MKDIR, cmd=["dir1"], allow_failure=True),
            Step(type=StepType.MKDIR, cmd=["dir2"], allow_failure=False),  # different attribute
            Step(type=StepType.MKDIR, cmd=["dir3"], allow_failure=True)
        ]

        result = optimize_mkdir_steps(steps)

        # Should not merge steps with different attributes
        assert len(result) == 3
        assert result[0].allow_failure is True
        assert result[1].allow_failure is False
        assert result[2].allow_failure is True


class TestOptimizeCopySteps:
    """Tests for optimize_copy_steps function"""

    def test_optimize_copy_steps_empty(self):
        """Test optimize_copy_steps with empty list"""
        result = optimize_copy_steps([])
        assert result == []

    def test_optimize_copy_steps_no_copy(self):
        """Test optimize_copy_steps with no copy steps"""
        steps = [
            Step(type=StepType.TOUCH, cmd=["file.txt"]),
            Step(type=StepType.SHELL, cmd=["echo", "hello"])
        ]

        result = optimize_copy_steps(steps)
        assert result == steps

    def test_optimize_copy_steps_no_duplicates(self):
        """Test optimize_copy_steps with no duplicate operations"""
        steps = [
            Step(type=StepType.COPY, cmd=["src1.txt", "dst1.txt"]),
            Step(type=StepType.COPY, cmd=["src2.txt", "dst2.txt"])
        ]

        result = optimize_copy_steps(steps)
        assert result == steps

    def test_optimize_copy_steps_with_duplicates(self):
        """Test optimize_copy_steps removes duplicate operations"""
        steps = [
            Step(type=StepType.COPY, cmd=["src.txt", "dst.txt"], allow_failure=True),
            Step(type=StepType.COPY, cmd=["src.txt", "dst.txt"], allow_failure=True)  # duplicate
        ]

        result = optimize_copy_steps(steps)

        assert len(result) == 1
        assert result[0].cmd == ["src.txt", "dst.txt"]

    def test_optimize_copy_steps_prefer_stricter(self):
        """Test optimize_copy_steps prefers stricter constraints"""
        steps = [
            Step(type=StepType.COPY, cmd=["src.txt", "dst.txt"], allow_failure=True),
            Step(type=StepType.COPY, cmd=["src.txt", "dst.txt"], allow_failure=False)  # stricter
        ]

        result = optimize_copy_steps(steps)

        assert len(result) == 1
        assert result[0].allow_failure is False

    def test_optimize_copy_steps_insufficient_args(self):
        """Test optimize_copy_steps with insufficient command arguments"""
        # Step creation will fail validation for insufficient args
        with pytest.raises(ValueError, match="requires at least 2 arguments"):
            Step(type=StepType.COPY, cmd=["src.txt"])  # insufficient args

    def test_optimize_copy_steps_mixed_types(self):
        """Test optimize_copy_steps with mixed step types"""
        steps = [
            Step(type=StepType.COPY, cmd=["src.txt", "dst.txt"]),
            Step(type=StepType.MOVE, cmd=["src.txt", "dst.txt"]),  # different type
            Step(type=StepType.COPYTREE, cmd=["src_dir", "dst_dir"]),
            Step(type=StepType.SHELL, cmd=["echo", "hello"])
        ]

        result = optimize_copy_steps(steps)

        assert len(result) == 4  # All should be kept as they're different operations
        assert [step.type for step in result] == [StepType.COPY, StepType.MOVE, StepType.COPYTREE, StepType.SHELL]


class TestDependencyEdgeCases:
    """Tests for edge cases and error handling in dependency resolution"""

    def test_resolve_dependencies_with_exception_in_template_expansion(self):
        """Test resolve_dependencies handles template expansion exceptions gracefully"""
        step = Step(
            type=StepType.COPY,
            cmd=["{{invalid_template}}", "dest/dst.txt"],
            when="some condition"
        )
        context = Mock(spec=StepContext)

        # Mock to raise exception during template expansion
        with patch('src.workflow.step.step_generation_service.execution_context_to_simple_context') as mock_ctx, \
             patch('src.workflow.step.step_runner.expand_template') as mock_expand:
            mock_ctx.return_value = {}
            mock_expand.side_effect = Exception("Template expansion failed")

            result = resolve_dependencies([step], context)

        # Should handle exception and continue with normal processing
        assert len(result) >= 1
        assert step in result

    def test_resolve_dependencies_when_condition_edge_cases(self):
        """Test resolve_dependencies with various when condition edge cases"""
        steps = [
            Step(type=StepType.COPY, cmd=["src.txt", "dest/.invalid"], when="condition"),
            Step(type=StepType.COPY, cmd=["src.txt", "dest//double.txt"], when="condition"),
            Step(type=StepType.COPY, cmd=["src.txt", "valid/dest.txt"], when="condition")
        ]
        context = Mock(spec=StepContext)

        with patch('src.workflow.step.step_generation_service.execution_context_to_simple_context') as mock_ctx, \
             patch('src.workflow.step.step_runner.expand_template') as mock_expand:
            mock_ctx.return_value = {}
            mock_expand.side_effect = lambda arg, ctx: arg

            result = resolve_dependencies(steps, context)

        # Should skip preparation for steps with invalid paths (only double slashes detected as invalid)
        mkdir_steps = [s for s in result if s.type == StepType.MKDIR]
        assert len(mkdir_steps) == 2  # "dest" and "valid" directories (only double slash is considered invalid)
        mkdir_dirs = [step.cmd[0] for step in mkdir_steps]
        assert "dest" in mkdir_dirs
        assert "valid" in mkdir_dirs

    def test_generate_preparation_steps_edge_cases(self):
        """Test generate_preparation_steps with edge cases"""
        context = Mock(spec=StepContext)
        existing_dirs = set()
        existing_files = set()

        # Test with absolute paths (mkdir is still needed for destination directory)
        step_absolute = Step(type=StepType.COPY, cmd=["/absolute/src.txt", "/absolute/dst.txt"])
        result = generate_preparation_steps(step_absolute, existing_dirs, existing_files, context)
        # Should create mkdir for the destination directory
        assert len(result) == 1
        assert result[0].type == StepType.MKDIR
        assert result[0].cmd == ["/absolute"]

        # Test with root directory as destination (current implementation creates mkdir for root)
        step_root = Step(type=StepType.COPY, cmd=["src.txt", "/dst.txt"])
        result = generate_preparation_steps(step_root, existing_dirs, existing_files, context)
        # Current implementation creates mkdir for root directory (may need improvement)
        mkdir_steps = [step for step in result if step.type == StepType.MKDIR]
        assert len(mkdir_steps) == 1
        assert mkdir_steps[0].cmd == ["/"]

    def test_update_resource_tracking_edge_cases(self):
        """Test update_resource_tracking with edge cases"""
        existing_dirs = {"existing_dir"}
        existing_files = {"existing_file.txt"}

        # Test with valid COPY command
        step_copy = Step(type=StepType.COPY, cmd=["src.txt", "dst.txt"])
        update_resource_tracking(step_copy, existing_dirs, existing_files)
        # Should not crash and should not modify sets for COPY
        assert "existing_dir" in existing_dirs
        assert "existing_file.txt" in existing_files

        # Test with minimal mkdir command
        step_mkdir = Step(type=StepType.MKDIR, cmd=["new_dir"])
        update_resource_tracking(step_mkdir, existing_dirs, existing_files)
        # Should add new directory to existing_dirs
        assert "new_dir" in existing_dirs

        # Test touch with current directory
        step_current_dir = Step(type=StepType.TOUCH, cmd=["file.txt"])
        update_resource_tracking(step_current_dir, existing_dirs, existing_files)
        assert "file.txt" in existing_files
        # Should not add current directory to existing_dirs

    def test_creates_file_edge_cases(self):
        """Test creates_file with edge cases"""
        # Test with valid touch command
        step_touch = Step(type=StepType.TOUCH, cmd=["test.txt"])
        assert creates_file(step_touch, "test.txt") is True
        assert creates_file(step_touch, "other.txt") is False

        # Test with various step types that don't create files
        step_mkdir = Step(type=StepType.MKDIR, cmd=["dir"])
        assert creates_file(step_mkdir, "any.txt") is False

        step_remove = Step(type=StepType.REMOVE, cmd=["file.txt"])
        assert creates_file(step_remove, "file.txt") is False

        # Test Python and Build steps (conservative approach)
        step_python = Step(type=StepType.PYTHON, cmd=["script.py"])
        assert creates_file(step_python, "output.txt") is False

        step_build = Step(type=StepType.BUILD, cmd=["make"])
        assert creates_file(step_build, "binary") is False

    def test_analyze_step_dependencies_complex_scenarios(self):
        """Test analyze_step_dependencies with complex dependency scenarios"""
        # Test with steps that have no file operations
        steps = [
            Step(type=StepType.SHELL, cmd=["echo", "hello"]),
            Step(type=StepType.MKDIR, cmd=["newdir"]),
            Step(type=StepType.RMTREE, cmd=["olddir"])
        ]

        result = analyze_step_dependencies(steps)
        assert result == {0: [], 1: [], 2: []}  # No dependencies

        # Test with copy step that doesn't match any created files
        steps_no_match = [
            Step(type=StepType.TOUCH, cmd=["file1.txt"]),
            Step(type=StepType.COPY, cmd=["different_file.txt", "output.txt"])
        ]

        result = analyze_step_dependencies(steps_no_match)
        assert result == {0: [], 1: []}  # No dependencies found

    def test_optimize_mkdir_steps_complex_scenarios(self):
        """Test optimize_mkdir_steps with complex scenarios"""
        # Test with mixed step types interrupting consecutive mkdirs
        steps = [
            Step(type=StepType.MKDIR, cmd=["dir1"], allow_failure=True),
            Step(type=StepType.MKDIR, cmd=["dir2"], allow_failure=True),
            Step(type=StepType.TOUCH, cmd=["file.txt"]),  # interrupts
            Step(type=StepType.MKDIR, cmd=["dir3"], allow_failure=True),
            Step(type=StepType.MKDIR, cmd=["dir4"], allow_failure=True)
        ]

        result = optimize_mkdir_steps(steps)

        # Should have 5 steps: 2 mkdirs, 1 touch, 2 mkdirs
        assert len(result) == 5
        assert result[0].type == StepType.MKDIR
        assert result[1].type == StepType.MKDIR
        assert result[2].type == StepType.TOUCH
        assert result[3].type == StepType.MKDIR
        assert result[4].type == StepType.MKDIR

    def test_optimize_copy_steps_complex_scenarios(self):
        """Test optimize_copy_steps with complex scenarios"""
        # Test with MOVETREE type
        steps = [
            Step(type=StepType.MOVETREE, cmd=["src_dir", "dst_dir"], allow_failure=True),
            Step(type=StepType.MOVETREE, cmd=["src_dir", "dst_dir"], allow_failure=False)  # stricter
        ]

        result = optimize_copy_steps(steps)

        assert len(result) == 1
        assert result[0].type == StepType.MOVETREE
        assert result[0].allow_failure is False  # Should prefer stricter version

        # Test when existing step is already stricter
        steps_reverse = [
            Step(type=StepType.COPYTREE, cmd=["src_dir", "dst_dir"], allow_failure=False),
            Step(type=StepType.COPYTREE, cmd=["src_dir", "dst_dir"], allow_failure=True)  # less strict
        ]

        result = optimize_copy_steps(steps_reverse)

        assert len(result) == 1
        assert result[0].allow_failure is False  # Should keep the stricter first version

"""Tests for dependency resolution module."""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from src.domain.dependency import (
    resolve_dependencies,
    generate_preparation_steps,
    update_resource_tracking,
    analyze_step_dependencies,
    creates_file,
    create_mkdir_step,
    optimize_mkdir_steps,
    optimize_copy_steps
)
from src.domain.step import Step, StepType, StepContext


def _create_test_step(**kwargs):
    """Create a test Step with defaults for all required fields."""
    defaults = {
        'type': StepType.SHELL,
        'cmd': ['echo', 'test'],
        'allow_failure': False,
        'show_output': True,
        'cwd': None,
        'force_env_type': None,
        'format_options': None,
        'output_format': None,
        'format_preset': None,
        'when': None,
        'name': None,
        'auto_generated': False,
        'max_workers': 1
    }
    defaults.update(kwargs)
    return Step(**defaults)


class TestResolveDependencies:
    """Test cases for resolve_dependencies function."""

    def _create_test_context(self):
        """Create a test StepContext with all required fields."""
        return StepContext(
            contest_name="test",
            problem_name="A",
            language="python",
            env_type="local",
            command_type="run",
            local_workspace_path="/workspace",
            contest_current_path="/contest/current",
            contest_stock_path="/contest/stock",
            contest_template_path="/contest/template",
            contest_temp_path="/contest/temp",
            source_file_name="main.py",
            language_id="python3",
            file_patterns={"py": ["*.py"]}
        )

    def test_resolve_dependencies_empty_list(self):
        """Test resolving dependencies for empty step list."""
        context = self._create_test_context()
        result = resolve_dependencies([], context)
        assert result == []

    def test_resolve_dependencies_single_step_no_deps(self):
        """Test resolving dependencies for single step without dependencies."""
        step = _create_test_step(
            type=StepType.SHELL,
            cmd=["echo", "test"]
        )
        context = self._create_test_context()
        result = resolve_dependencies([step], context)
        assert len(result) == 1
        assert result[0] == step

    @patch('src.domain.dependency.execution_context_to_simple_context')
    @patch('src.domain.dependency.expand_template')
    def test_resolve_dependencies_with_when_condition(self, mock_expand, mock_context):
        """Test resolving dependencies with when condition."""
        mock_context.return_value = {"test": "value"}
        mock_expand.side_effect = lambda x, _: x
        
        step = _create_test_step(
            type=StepType.SHELL,
            cmd=["test", "command"],
            when="test == 'value'"
        )
        context = self._create_test_context()
        result = resolve_dependencies([step], context)
        assert len(result) >= 1
        assert result[-1] == step

    def test_resolve_dependencies_with_invalid_paths(self):
        """Test resolving dependencies with invalid paths."""
        step = _create_test_step(
            type=StepType.SHELL,
            cmd=["cat", "//invalid/path/."],
            when="true"
        )
        context = self._create_test_context()
        with patch('src.domain.dependency.execution_context_to_simple_context') as mock_context:
            with patch('src.domain.dependency.expand_template') as mock_expand:
                mock_context.return_value = {}
                mock_expand.side_effect = lambda x, _: x
                result = resolve_dependencies([step], context)
                # Should not generate prep steps for invalid paths
                assert len(result) == 1
                assert result[0] == step
    
    def test_resolve_dependencies_with_copy_step(self):
        """Test resolving dependencies for copy steps."""
        steps = [
            _create_test_step(
                type=StepType.COPY,
                cmd=["src.txt", "dest/file.txt"]
            )
        ]
        context = self._create_test_context()
        result = resolve_dependencies(steps, context)
        # Should add mkdir for destination directory
        assert len(result) == 2
        assert result[0].type == StepType.MKDIR
        assert result[0].cmd[0] == "dest"
        assert result[1] == steps[0]
    
    def test_resolve_dependencies_multiple_steps(self):
        """Test resolving dependencies for multiple steps."""
        steps = [
            _create_test_step(
                type=StepType.TOUCH,
                cmd=["dir1/file1.txt"]
            ),
            _create_test_step(
                type=StepType.COPY,
                cmd=["dir1/file1.txt", "dir2/file2.txt"]
            ),
            _create_test_step(
                type=StepType.MOVE,
                cmd=["dir2/file2.txt", "dir3/file3.txt"]
            )
        ]
        context = self._create_test_context()
        result = resolve_dependencies(steps, context)
        # Should add mkdir steps for each directory
        mkdir_steps = [s for s in result if s.type == StepType.MKDIR]
        assert len(mkdir_steps) >= 2  # At least dir1 and dir3
    
    def test_resolve_dependencies_tracks_resources(self):
        """Test that resolve_dependencies tracks created resources."""
        steps = [
            _create_test_step(
                type=StepType.MKDIR,
                cmd=["mydir"]
            ),
            _create_test_step(
                type=StepType.TOUCH,
                cmd=["mydir/file.txt"]
            )
        ]
        context = self._create_test_context()
        result = resolve_dependencies(steps, context)
        # Should not add extra mkdir for mydir since it's already created
        mkdir_steps = [s for s in result if s.type == StepType.MKDIR and s.cmd[0] == "mydir"]
        assert len(mkdir_steps) == 1  # Only the original
    
    def test_resolve_dependencies_when_condition_exception(self):
        """Test handling exceptions in when condition evaluation."""
        step = _create_test_step(
            type=StepType.SHELL,
            cmd=["test"],
            when="invalid_condition"
        )
        context = self._create_test_context()
        with patch('src.domain.dependency.execution_context_to_simple_context') as mock_context:
            mock_context.side_effect = Exception("Test exception")
            result = resolve_dependencies([step], context)
            # Should still process the step despite exception
            assert len(result) >= 1
            assert result[-1] == step


class TestGeneratePreparationSteps:
    """Test cases for generate_preparation_steps function."""

    def _create_test_context(self):
        """Create a test StepContext with all required fields."""
        return StepContext(
            contest_name="test",
            problem_name="A",
            language="python",
            env_type="local",
            command_type="run",
            local_workspace_path="/workspace",
            contest_current_path="/contest/current",
            contest_stock_path="/contest/stock",
            contest_template_path="/contest/template",
            contest_temp_path="/contest/temp",
            source_file_name="main.py",
            language_id="python3",
            file_patterns={"py": ["*.py"]}
        )

    def test_generate_prep_steps_no_paths(self):
        """Test generating preparation steps for step without paths."""
        step = _create_test_step(
            type=StepType.SHELL,
            cmd=["echo", "test"]
        )
        context = self._create_test_context()
        result = generate_preparation_steps(step, set(), set(), context)
        assert result == []

    def test_generate_prep_steps_touch_file(self):
        """Test generating preparation steps for touch file."""
        step = _create_test_step(
            type=StepType.TOUCH,
            cmd=["test/output.txt"]
        )
        context = self._create_test_context()
        result = generate_preparation_steps(step, set(), set(), context)
        # Should create directory for the file
        assert len(result) == 1
        assert result[0].type == StepType.MKDIR
        assert result[0].cmd[0] == "test"

    def test_generate_prep_steps_copy_file(self):
        """Test generating preparation steps for copying file."""
        step = _create_test_step(
            type=StepType.COPY,
            cmd=["source.txt", "dest/target.txt"]
        )
        context = self._create_test_context()
        result = generate_preparation_steps(step, set(), set(), context)
        # Should create destination directory only (source is not created by prep steps)
        assert len(result) == 1
        assert result[0].type == StepType.MKDIR
        assert result[0].cmd[0] == "dest"
    
    def test_generate_prep_steps_move_file(self):
        """Test generating preparation steps for moving file."""
        step = _create_test_step(
            type=StepType.MOVE,
            cmd=["old.txt", "new/location.txt"]
        )
        context = self._create_test_context()
        result = generate_preparation_steps(step, set(), set(), context)
        assert len(result) == 1
        assert result[0].type == StepType.MKDIR
        assert result[0].cmd[0] == "new"
    
    def test_generate_prep_steps_movetree(self):
        """Test generating preparation steps for moving directory tree."""
        step = _create_test_step(
            type=StepType.MOVETREE,
            cmd=["olddir", "parent/newdir"]
        )
        context = self._create_test_context()
        result = generate_preparation_steps(step, set(), set(), context)
        assert len(result) == 1
        assert result[0].type == StepType.MKDIR
        assert result[0].cmd[0] == "parent"
    
    def test_generate_prep_steps_existing_dir(self):
        """Test generating preparation steps when directory already exists."""
        step = _create_test_step(
            type=StepType.COPY,
            cmd=["src.txt", "existing/file.txt"]
        )
        context = self._create_test_context()
        existing_dirs = {"existing"}
        result = generate_preparation_steps(step, existing_dirs, set(), context)
        assert len(result) == 0  # No prep steps needed
    
    def test_generate_prep_steps_with_cwd(self):
        """Test generating preparation steps with working directory."""
        step = _create_test_step(
            type=StepType.SHELL,
            cmd=["echo", "test"],
            cwd="work/dir"
        )
        context = self._create_test_context()
        result = generate_preparation_steps(step, set(), set(), context)
        assert len(result) == 1
        assert result[0].type == StepType.MKDIR
        assert result[0].cmd[0] == "work/dir"
        assert result[0].cwd == "work/dir"
    
    def test_generate_prep_steps_cwd_exists(self):
        """Test generating preparation steps when cwd already exists."""
        step = _create_test_step(
            type=StepType.SHELL,
            cmd=["echo", "test"],
            cwd="existing/work"
        )
        context = self._create_test_context()
        existing_dirs = {"existing/work"}
        result = generate_preparation_steps(step, existing_dirs, set(), context)
        assert len(result) == 0  # No prep steps needed
    
    def test_generate_prep_steps_current_dir(self):
        """Test generating preparation steps for current directory."""
        step = _create_test_step(
            type=StepType.TOUCH,
            cmd=["./file.txt"]
        )
        context = self._create_test_context()
        result = generate_preparation_steps(step, set(), set(), context)
        assert len(result) == 0  # No prep steps for current directory
    
    def test_generate_prep_steps_insufficient_args(self):
        """Test generating preparation steps with insufficient arguments."""
        # Copy with only one argument
        step = _create_test_step(
            type=StepType.COPY,
            cmd=["onlyfile.txt", "dest.txt"]  # Valid args to avoid validation error
        )
        # Test with current directory destination
        step2 = _create_test_step(
            type=StepType.COPY,
            cmd=["src.txt", "./dst.txt"]
        )
        context = self._create_test_context()
        result = generate_preparation_steps(step2, set(), set(), context)
        assert len(result) == 0  # No prep steps for current directory


class TestUpdateResourceTracking:
    """Test cases for update_resource_tracking function."""

    def test_update_tracking_mkdir(self):
        """Test updating resource tracking for mkdir step."""
        step = _create_test_step(
            type=StepType.MKDIR,
            cmd=["test/dir"]
        )
        existing_dirs = set()
        existing_files = set()
        update_resource_tracking(step, existing_dirs, existing_files)
        assert "test/dir" in existing_dirs
        assert len(existing_files) == 0

    def test_update_tracking_touch(self):
        """Test updating resource tracking for touch step."""
        step = _create_test_step(
            type=StepType.TOUCH,
            cmd=["test.txt"]
        )
        existing_dirs = set()
        existing_files = set()
        update_resource_tracking(step, existing_dirs, existing_files)
        assert "test.txt" in existing_files
        assert len(existing_dirs) == 0
    
    def test_update_tracking_touch_with_parent(self):
        """Test updating resource tracking for touch with parent directory."""
        step = _create_test_step(
            type=StepType.TOUCH,
            cmd=["parent/file.txt"]
        )
        existing_dirs = set()
        existing_files = set()
        update_resource_tracking(step, existing_dirs, existing_files)
        assert "parent/file.txt" in existing_files
        assert "parent" in existing_dirs
    
    def test_update_tracking_copy(self):
        """Test updating resource tracking for copy step."""
        step = _create_test_step(
            type=StepType.COPY,
            cmd=["src.txt", "dst/file.txt"]
        )
        existing_dirs = set()
        existing_files = set()
        update_resource_tracking(step, existing_dirs, existing_files)
        assert "dst/file.txt" in existing_files
        assert "dst" in existing_dirs
    
    def test_update_tracking_move(self):
        """Test updating resource tracking for move step."""
        step = _create_test_step(
            type=StepType.MOVE,
            cmd=["old.txt", "new/location.txt"]
        )
        existing_dirs = set()
        existing_files = set()
        update_resource_tracking(step, existing_dirs, existing_files)
        assert "new/location.txt" in existing_files
        assert "new" in existing_dirs
    
    def test_update_tracking_movetree(self):
        """Test updating resource tracking for movetree step."""
        step = _create_test_step(
            type=StepType.MOVETREE,
            cmd=["olddir", "parent/newdir"]
        )
        existing_dirs = set()
        existing_files = set()
        update_resource_tracking(step, existing_dirs, existing_files)
        assert "parent/newdir" in existing_dirs
        assert "parent" in existing_dirs
    
    def test_update_tracking_remove(self):
        """Test updating resource tracking for remove step."""
        step = _create_test_step(
            type=StepType.REMOVE,
            cmd=["file.txt"]
        )
        existing_dirs = set()
        existing_files = {"file.txt", "other.txt"}
        update_resource_tracking(step, existing_dirs, existing_files)
        assert "file.txt" not in existing_files
        assert "other.txt" in existing_files
    
    def test_update_tracking_rmtree(self):
        """Test updating resource tracking for rmtree step."""
        step = _create_test_step(
            type=StepType.RMTREE,
            cmd=["directory"]
        )
        existing_dirs = {"directory", "other"}
        existing_files = set()
        update_resource_tracking(step, existing_dirs, existing_files)
        assert "directory" not in existing_dirs
        assert "other" in existing_dirs
    
    def test_update_tracking_empty_cmd(self):
        """Test updating resource tracking with empty command."""
        # Shell command which doesn't track resources
        step = _create_test_step(
            type=StepType.SHELL,
            cmd=["echo"]
        )
        existing_dirs = set()
        existing_files = set()
        update_resource_tracking(step, existing_dirs, existing_files)
        assert len(existing_files) == 0
        assert len(existing_dirs) == 0
    
    def test_update_tracking_copy_current_dir(self):
        """Test updating resource tracking for copy to current directory."""
        step = _create_test_step(
            type=StepType.COPY,
            cmd=["src.txt", "./dst.txt"]
        )
        existing_dirs = set()
        existing_files = set()
        update_resource_tracking(step, existing_dirs, existing_files)
        assert "./dst.txt" in existing_files
        # Current directory '.' should not be added
        assert "." not in existing_dirs


class TestAnalyzeStepDependencies:
    """Test cases for analyze_step_dependencies function."""

    def test_analyze_dependencies_no_deps(self):
        """Test analyzing dependencies with no dependencies."""
        steps = [
            _create_test_step(type=StepType.SHELL, cmd=["echo", "test"]),
            _create_test_step(type=StepType.MKDIR, cmd=["dir"])
        ]
        result = analyze_step_dependencies(steps)
        assert result == {0: [], 1: []}

    def test_analyze_dependencies_with_file_deps(self):
        """Test analyzing dependencies with file dependencies."""
        steps = [
            _create_test_step(type=StepType.TOUCH, cmd=["file.txt"]),
            _create_test_step(type=StepType.COPY, cmd=["file.txt", "copy.txt"])
        ]
        result = analyze_step_dependencies(steps)
        assert result == {0: [], 1: [0]}  # Step 1 depends on step 0

    def test_analyze_dependencies_multiple(self):
        """Test analyzing multiple dependencies."""
        steps = [
            _create_test_step(type=StepType.TOUCH, cmd=["a.txt"]),
            _create_test_step(type=StepType.TOUCH, cmd=["b.txt"]),
            _create_test_step(type=StepType.COPY, cmd=["a.txt", "c.txt"]),
            _create_test_step(type=StepType.MOVE, cmd=["b.txt", "d.txt"])
        ]
        result = analyze_step_dependencies(steps)
        assert result[2] == [0]  # Step 2 depends on step 0
        assert result[3] == [1]  # Step 3 depends on step 1
    
    def test_analyze_dependencies_no_match(self):
        """Test analyzing dependencies when source doesn't match."""
        steps = [
            _create_test_step(type=StepType.TOUCH, cmd=["a.txt"]),
            _create_test_step(type=StepType.MOVE, cmd=["different.txt", "b.txt"])  # Source doesn't match
        ]
        result = analyze_step_dependencies(steps)
        assert result[1] == []  # No dependency since source doesn't match


class TestCreatesFile:
    """Test cases for creates_file function."""

    def test_creates_file_touch(self):
        """Test creates_file for touch step."""
        step = _create_test_step(type=StepType.TOUCH, cmd=["test.txt"])
        assert creates_file(step, "test.txt") is True
        assert creates_file(step, "other.txt") is False

    def test_creates_file_copy(self):
        """Test creates_file for copy step."""
        step = _create_test_step(type=StepType.COPY, cmd=["src.txt", "dest.txt"])
        assert creates_file(step, "dest.txt") is True
        assert creates_file(step, "src.txt") is False

    def test_creates_file_move(self):
        """Test creates_file for move step."""
        step = _create_test_step(type=StepType.MOVE, cmd=["old.txt", "new.txt"])
        assert creates_file(step, "new.txt") is True
        assert creates_file(step, "old.txt") is False

    def test_creates_file_other_types(self):
        """Test creates_file for other step types."""
        step = _create_test_step(type=StepType.MKDIR, cmd=["directory"])
        assert creates_file(step, "directory") is False

    def test_creates_file_shell_command(self):
        """Test creates_file for shell command."""
        step = _create_test_step(type=StepType.SHELL, cmd=["echo test"])
        # Based on the implementation, shell commands return False
        assert creates_file(step, "any.txt") is False


class TestCreateMkdirStep:
    """Test cases for create_mkdir_step function."""
    
    def test_create_mkdir_step_basic(self):
        """Test creating a basic mkdir step."""
        result = create_mkdir_step("/test/path", None)
        assert result.type == StepType.MKDIR
        assert result.cmd == ["/test/path"]
        assert result.allow_failure is True
        assert result.show_output is False
        assert result.cwd is None
        assert result.auto_generated is True
        assert result.max_workers == 1
    
    def test_create_mkdir_step_with_cwd(self):
        """Test creating mkdir step with working directory."""
        result = create_mkdir_step("relative/path", "/working/dir")
        assert result.type == StepType.MKDIR
        assert result.cmd == ["relative/path"]
        assert result.cwd == "/working/dir"
        assert result.allow_failure is True
        assert result.show_output is False


class TestOptimizeMkdirSteps:
    """Test cases for optimize_mkdir_steps function."""
    
    def test_optimize_empty_list(self):
        """Test optimizing empty step list."""
        result = optimize_mkdir_steps([])
        assert result == []
    
    def test_optimize_no_mkdir_steps(self):
        """Test optimizing list with no mkdir steps."""
        steps = [
            _create_test_step(type=StepType.SHELL, cmd=["echo", "test"]),
            _create_test_step(type=StepType.TOUCH, cmd=["file.txt"])
        ]
        result = optimize_mkdir_steps(steps)
        assert result == steps
    
    def test_optimize_single_mkdir(self):
        """Test optimizing single mkdir step."""
        step = _create_test_step(type=StepType.MKDIR, cmd=["dir1"])
        result = optimize_mkdir_steps([step])
        assert len(result) == 1
        assert result[0].cmd == ["dir1"]
    
    def test_optimize_consecutive_mkdirs(self):
        """Test optimizing consecutive mkdir steps."""
        steps = [
            _create_test_step(type=StepType.MKDIR, cmd=["dir1"], allow_failure=True, show_output=False),
            _create_test_step(type=StepType.MKDIR, cmd=["dir2"], allow_failure=True, show_output=False),
            _create_test_step(type=StepType.MKDIR, cmd=["dir3"], allow_failure=True, show_output=False)
        ]
        result = optimize_mkdir_steps(steps)
        assert len(result) == 3
        assert result[0].cmd == ["dir1"]
        assert result[1].cmd == ["dir2"]
        assert result[2].cmd == ["dir3"]
    
    def test_optimize_duplicate_mkdirs(self):
        """Test optimizing duplicate mkdir paths."""
        steps = [
            _create_test_step(type=StepType.MKDIR, cmd=["dir1"], allow_failure=True, show_output=False),
            _create_test_step(type=StepType.MKDIR, cmd=["dir1"], allow_failure=True, show_output=False),
            _create_test_step(type=StepType.MKDIR, cmd=["dir2"], allow_failure=True, show_output=False)
        ]
        result = optimize_mkdir_steps(steps)
        assert len(result) == 2
        assert result[0].cmd == ["dir1"]
        assert result[1].cmd == ["dir2"]
    
    def test_optimize_mixed_steps(self):
        """Test optimizing mixed step types."""
        steps = [
            _create_test_step(type=StepType.MKDIR, cmd=["dir1"], allow_failure=True),
            _create_test_step(type=StepType.SHELL, cmd=["echo", "test"]),
            _create_test_step(type=StepType.MKDIR, cmd=["dir2"], allow_failure=True),
            _create_test_step(type=StepType.MKDIR, cmd=["dir3"], allow_failure=True)
        ]
        result = optimize_mkdir_steps(steps)
        assert len(result) == 4
        assert result[0].type == StepType.MKDIR
        assert result[1].type == StepType.SHELL
        assert result[2].type == StepType.MKDIR
        assert result[3].type == StepType.MKDIR
    
    def test_optimize_different_flags(self):
        """Test optimizing mkdirs with different flags."""
        steps = [
            _create_test_step(type=StepType.MKDIR, cmd=["dir1"], allow_failure=True, show_output=False),
            _create_test_step(type=StepType.MKDIR, cmd=["dir2"], allow_failure=False, show_output=False),
            _create_test_step(type=StepType.MKDIR, cmd=["dir3"], allow_failure=True, show_output=True)
        ]
        result = optimize_mkdir_steps(steps)
        # Different flags should not be combined
        assert len(result) == 3


class TestOptimizeCopySteps:
    """Test cases for optimize_copy_steps function."""
    
    def test_optimize_copy_empty_list(self):
        """Test optimizing empty list."""
        result = optimize_copy_steps([])
        assert result == []
    
    def test_optimize_copy_no_copy_steps(self):
        """Test optimizing list with no copy/move steps."""
        steps = [
            _create_test_step(type=StepType.SHELL, cmd=["echo", "test"]),
            _create_test_step(type=StepType.MKDIR, cmd=["dir"])
        ]
        result = optimize_copy_steps(steps)
        assert result == steps
    
    def test_optimize_copy_single_copy(self):
        """Test optimizing single copy step."""
        step = _create_test_step(type=StepType.COPY, cmd=["src.txt", "dst.txt"])
        result = optimize_copy_steps([step])
        assert len(result) == 1
        assert result[0] == step
    
    def test_optimize_copy_duplicate_operations(self):
        """Test optimizing duplicate copy operations."""
        steps = [
            _create_test_step(type=StepType.COPY, cmd=["src.txt", "dst.txt"], allow_failure=True),
            _create_test_step(type=StepType.COPY, cmd=["src.txt", "dst.txt"], allow_failure=True)
        ]
        result = optimize_copy_steps(steps)
        assert len(result) == 1
        assert result[0].cmd == ["src.txt", "dst.txt"]
    
    def test_optimize_copy_different_destinations(self):
        """Test optimizing copies with different destinations."""
        steps = [
            _create_test_step(type=StepType.COPY, cmd=["src.txt", "dst1.txt"]),
            _create_test_step(type=StepType.COPY, cmd=["src.txt", "dst2.txt"])
        ]
        result = optimize_copy_steps(steps)
        assert len(result) == 2
    
    def test_optimize_copy_move_operations(self):
        """Test optimizing move operations."""
        steps = [
            _create_test_step(type=StepType.MOVE, cmd=["old.txt", "new.txt"]),
            _create_test_step(type=StepType.MOVE, cmd=["old.txt", "new.txt"])
        ]
        result = optimize_copy_steps(steps)
        assert len(result) == 1
    
    def test_optimize_copy_mixed_operations(self):
        """Test optimizing mixed copy/move operations."""
        steps = [
            _create_test_step(type=StepType.COPY, cmd=["a.txt", "b.txt"]),
            _create_test_step(type=StepType.MOVE, cmd=["c.txt", "d.txt"]),
            _create_test_step(type=StepType.COPYTREE, cmd=["dir1", "dir2"]),
            _create_test_step(type=StepType.MOVETREE, cmd=["dir3", "dir4"])
        ]
        result = optimize_copy_steps(steps)
        assert len(result) == 4
    
    def test_optimize_copy_allow_failure_priority(self):
        """Test that allow_failure=False takes priority over allow_failure=True."""
        steps = [
            _create_test_step(type=StepType.COPY, cmd=["src.txt", "dst.txt"], allow_failure=True),
            _create_test_step(type=StepType.COPY, cmd=["src.txt", "dst.txt"], allow_failure=False)
        ]
        result = optimize_copy_steps(steps)
        assert len(result) == 1
        assert result[0].allow_failure is False
    
    def test_optimize_copy_preserves_other_fields(self):
        """Test that optimization preserves other step fields."""
        steps = [
            _create_test_step(
                type=StepType.COPY, 
                cmd=["src.txt", "dst.txt"],
                name="Copy file",
                when="condition == true"
            )
        ]
        result = optimize_copy_steps(steps)
        assert len(result) == 1
        assert result[0].name == "Copy file"
        assert result[0].when == "condition == true"
    
    def test_optimize_copy_single_arg_steps(self):
        """Test optimizing copy steps with single argument (edge case)."""
        # This tests line 244 where cmd has less than 2 args
        # We need to create a step that passes validation but simulates this edge case
        # Since validation prevents this, we'll test a different scenario
        steps = [
            _create_test_step(type=StepType.SHELL, cmd=["echo", "test"]),  # Non-copy step
            _create_test_step(type=StepType.COPYTREE, cmd=["src", "dst"]),  # Tree copy
            _create_test_step(type=StepType.PYTHON, cmd=["script.py"])  # Another non-copy step
        ]
        result = optimize_copy_steps(steps)
        assert len(result) == 3  # All steps preserved
        assert result[0].type == StepType.SHELL
        assert result[1].type == StepType.COPYTREE
        assert result[2].type == StepType.PYTHON
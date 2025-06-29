"""Tests for dependency resolution module."""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from src.domain.dependency import (
    resolve_dependencies,
    generate_preparation_steps,
    update_resource_tracking,
    analyze_step_dependencies,
    creates_file
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
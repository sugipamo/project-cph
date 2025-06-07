"""
Comprehensive tests for src/env_core/step/core.py
Tests all core step generation functions
"""
from unittest.mock import Mock

import pytest

from src.workflow.step.core import (
    create_step_from_json,
    format_template,
    generate_steps_from_json,
    optimize_step_sequence,
    validate_single_step,
    validate_step_sequence,
)
from src.workflow.step.step import Step, StepContext, StepGenerationResult, StepType


class TestGenerateStepsFromJson:
    """Tests for generate_steps_from_json function"""

    def setup_method(self):
        """Setup test fixtures"""
        self.context = StepContext(
            contest_name="abc300",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="test",
            workspace_path="/workspace",
            contest_current_path="/contest_current"
        )

    def test_generate_steps_from_empty_list(self):
        """Test generation from empty JSON list"""
        result = generate_steps_from_json([], self.context)

        assert isinstance(result, StepGenerationResult)
        assert result.steps == []
        assert result.errors == []
        assert result.warnings == []
        assert result.is_success

    def test_generate_steps_from_valid_json(self):
        """Test generation from valid JSON steps"""
        json_steps = [
            {
                "type": "shell",
                "cmd": ["echo", "hello"]
            },
            {
                "type": "mkdir",
                "cmd": ["/test/path"],
                "allow_failure": True
            }
        ]

        result = generate_steps_from_json(json_steps, self.context)

        assert result.is_success
        assert len(result.steps) == 2
        assert result.steps[0].type == StepType.SHELL
        assert result.steps[0].cmd == ["echo", "hello"]
        assert result.steps[1].type == StepType.MKDIR
        assert result.steps[1].allow_failure is True

    def test_generate_steps_with_invalid_step(self):
        """Test generation with invalid step in the list"""
        json_steps = [
            {
                "type": "shell",
                "cmd": ["echo", "hello"]
            },
            {
                "type": "invalid_type",
                "cmd": ["test"]
            },
            {
                "type": "mkdir",
                "cmd": ["/test/path"]
            }
        ]

        result = generate_steps_from_json(json_steps, self.context)

        assert not result.is_success
        assert len(result.steps) == 2  # Valid steps still generated
        assert len(result.errors) == 1
        assert "Step 1:" in result.errors[0]
        assert "Unknown step type: invalid_type" in result.errors[0]

    def test_generate_steps_with_missing_type(self):
        """Test generation with step missing type field"""
        json_steps = [
            {
                "cmd": ["echo", "hello"]  # Missing type
            }
        ]

        result = generate_steps_from_json(json_steps, self.context)

        assert not result.is_success
        assert len(result.steps) == 0
        assert len(result.errors) == 1
        assert "Step must have 'type' field" in result.errors[0]

    def test_generate_steps_with_unexpected_exception(self):
        """Test handling of unexpected exceptions during step creation"""
        # Create a mock context that raises an unexpected exception
        mock_context = Mock()
        mock_context.to_format_dict.side_effect = RuntimeError("Unexpected error")

        json_steps = [
            {
                "type": "shell",
                "cmd": ["echo", "{contest_name}"]
            }
        ]

        result = generate_steps_from_json(json_steps, mock_context)

        assert not result.is_success
        assert len(result.errors) == 1
        assert "Unexpected error - Unexpected error" in result.errors[0]


class TestCreateStepFromJson:
    """Tests for create_step_from_json function"""

    def setup_method(self):
        """Setup test fixtures"""
        self.context = StepContext(
            contest_name="abc300",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="test",
            workspace_path="/workspace",
            contest_current_path="/contest_current"
        )

    def test_create_basic_shell_step(self):
        """Test creation of basic shell step"""
        json_step = {
            "type": "shell",
            "cmd": ["echo", "hello"]
        }

        step = create_step_from_json(json_step, self.context)

        assert step.type == StepType.SHELL
        assert step.cmd == ["echo", "hello"]
        assert step.allow_failure is False
        assert step.show_output is False
        assert step.cwd is None
        assert step.force_env_type is None

    def test_create_step_with_all_options(self):
        """Test creation of step with all optional fields"""
        json_step = {
            "type": "python",
            "cmd": ["python3", "main.py"],
            "allow_failure": True,
            "show_output": True,
            "cwd": "/workspace/{contest_name}",
            "force_env_type": "docker"
        }

        step = create_step_from_json(json_step, self.context)

        assert step.type == StepType.PYTHON
        assert step.cmd == ["python3", "main.py"]
        assert step.allow_failure is True
        assert step.show_output is True
        assert step.cwd == "/workspace/abc300"
        assert step.force_env_type == "docker"

    def test_create_step_with_template_formatting(self):
        """Test step creation with template string formatting"""
        json_step = {
            "type": "copy",
            "cmd": ["{contest_template_path}/main.py", "{workspace_path}/{problem_name}.py"]
        }

        context = StepContext(
            contest_name="abc300",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="test",
            workspace_path="/workspace",
            contest_current_path="/contest_current",
            contest_template_path="/template"
        )

        step = create_step_from_json(json_step, context)

        assert step.type == StepType.COPY
        assert step.cmd == ["/template/main.py", "/workspace/a.py"]

    def test_create_step_missing_type(self):
        """Test error handling for missing type field"""
        json_step = {
            "cmd": ["echo", "hello"]
        }

        with pytest.raises(ValueError, match="Step must have 'type' field"):
            create_step_from_json(json_step, self.context)

    def test_create_step_invalid_type(self):
        """Test error handling for invalid step type"""
        json_step = {
            "type": "invalid_type",
            "cmd": ["echo", "hello"]
        }

        with pytest.raises(ValueError, match="Unknown step type: invalid_type"):
            create_step_from_json(json_step, self.context)

    def test_create_step_non_list_cmd(self):
        """Test error handling for non-list cmd field"""
        json_step = {
            "type": "shell",
            "cmd": "echo hello"  # Should be list, not string
        }

        with pytest.raises(ValueError, match="Step 'cmd' must be a list"):
            create_step_from_json(json_step, self.context)

    def test_create_step_missing_cmd(self):
        """Test step creation with missing cmd field (should raise ValueError due to empty cmd)"""
        json_step = {
            "type": "shell"
            # Missing cmd field
        }

        # This should raise ValueError because Step.__post_init__ validates empty cmd
        with pytest.raises(ValueError, match="Step .* must have non-empty cmd"):
            create_step_from_json(json_step, self.context)


class TestFormatTemplate:
    """Tests for format_template function"""

    def setup_method(self):
        """Setup test fixtures"""
        self.context = StepContext(
            contest_name="abc300",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="test",
            workspace_path="/workspace",
            contest_current_path="/contest_current"
        )

    def test_format_string_template(self):
        """Test formatting of string with placeholders"""
        template = "Hello {contest_name} problem {problem_name}"
        result = format_template(template, self.context)

        assert result == "Hello abc300 problem a"

    def test_format_template_with_multiple_same_placeholder(self):
        """Test formatting with multiple instances of same placeholder"""
        template = "{contest_name}/{contest_name}/file.txt"
        result = format_template(template, self.context)

        assert result == "abc300/abc300/file.txt"

    def test_format_template_no_placeholders(self):
        """Test formatting string without placeholders"""
        template = "simple string"
        result = format_template(template, self.context)

        assert result == "simple string"

    def test_format_template_non_string_input(self):
        """Test formatting non-string inputs"""
        # Integer
        result = format_template(123, self.context)
        assert result == "123"

        # None
        result = format_template(None, self.context)
        assert result == ""

        # Boolean
        result = format_template(True, self.context)
        assert result == "True"

    def test_format_template_unknown_placeholder(self):
        """Test formatting with unknown placeholders (should remain unchanged)"""
        template = "Hello {unknown_field} and {contest_name}"
        result = format_template(template, self.context)

        assert result == "Hello {unknown_field} and abc300"

    def test_format_template_empty_string(self):
        """Test formatting empty string"""
        result = format_template("", self.context)
        assert result == ""

    def test_format_template_with_optional_fields(self):
        """Test formatting with optional context fields"""
        context = StepContext(
            contest_name="abc300",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="test",
            workspace_path="/workspace",
            contest_current_path="/contest_current",
            contest_template_path="/template",
            source_file_name="main.py",
            language_id="py3"
        )

        template = "{contest_template_path}/{source_file_name} for {language_id}"
        result = format_template(template, context)

        assert result == "/template/main.py for py3"


class TestValidateStepSequence:
    """Tests for validate_step_sequence function"""

    def test_validate_empty_sequence(self):
        """Test validation of empty step sequence"""
        errors = validate_step_sequence([])
        assert errors == []

    def test_validate_valid_sequence(self):
        """Test validation of valid step sequence"""
        steps = [
            Step(type=StepType.SHELL, cmd=["echo", "hello"]),
            Step(type=StepType.MKDIR, cmd=["/test/path"]),
            Step(type=StepType.COPY, cmd=["src.txt", "dst.txt"])
        ]

        errors = validate_step_sequence(steps)
        assert errors == []

    def test_validate_sequence_with_invalid_steps(self):
        """Test validation with steps that have validation errors at the core level"""
        # Since Step.__post_init__ validates, we need to create steps that pass
        # __post_init__ but fail the core validation logic
        steps = [
            Step(type=StepType.SHELL, cmd=["echo", "hello"]),  # Valid
            Step(type=StepType.COPY, cmd=["src", ""]),         # Invalid: empty dst path
            Step(type=StepType.SHELL, cmd=[""]),               # Invalid: empty command
        ]

        errors = validate_step_sequence(steps)

        assert len(errors) == 2
        assert "Step 1 (copy):" in errors[0]
        assert "Source and destination paths cannot be empty" in errors[0]
        assert "Step 2 (shell):" in errors[1]
        assert "Command cannot be empty" in errors[1]


class TestValidateSingleStep:
    """Tests for validate_single_step function"""

    def test_validate_empty_command(self):
        """Test validation of step with empty command element"""
        step = Step(type=StepType.SHELL, cmd=[""])  # Empty string as command
        errors = validate_single_step(step)

        assert len(errors) == 1
        assert "Command cannot be empty" in errors[0]

    def test_validate_empty_cmd_list_using_mock(self):
        """Test validation for empty cmd list using mock to bypass Step.__post_init__"""
        from unittest.mock import Mock

        # Create mock step that bypasses __post_init__ validation
        mock_step = Mock()
        mock_step.cmd = []
        mock_step.type = StepType.SHELL

        errors = validate_single_step(mock_step)

        assert len(errors) == 1
        assert "Command cannot be empty" in errors[0]

    def test_validate_copy_move_steps(self):
        """Test validation of COPY/MOVE/MOVETREE steps"""
        # Valid copy step
        step = Step(type=StepType.COPY, cmd=["src.txt", "dst.txt"])
        errors = validate_single_step(step)
        assert errors == []

        # Invalid copy step cannot be created due to Step.__post_init__ validation
        # So we test validation logic for valid steps with empty paths
        step = Step(type=StepType.COPY, cmd=["", "dst.txt"])
        errors = validate_single_step(step)
        assert len(errors) == 1
        assert "Source and destination paths cannot be empty" in errors[0]

        # Invalid move step (empty destination path)
        step = Step(type=StepType.MOVE, cmd=["src.txt", ""])
        errors = validate_single_step(step)
        assert len(errors) == 1
        assert "Source and destination paths cannot be empty" in errors[0]

    def test_validate_file_operation_steps(self):
        """Test validation of file operation steps (MKDIR, TOUCH, REMOVE, RMTREE)"""
        # Valid mkdir step
        step = Step(type=StepType.MKDIR, cmd=["/test/path"])
        errors = validate_single_step(step)
        assert errors == []

        # Invalid mkdir step cannot be created with empty cmd due to Step.__post_init__
        # So we test with empty path string instead
        step = Step(type=StepType.MKDIR, cmd=[""])
        errors = validate_single_step(step)
        assert len(errors) == 1
        assert "Path cannot be empty" in errors[0]

        # Invalid rmtree step (empty path)
        step = Step(type=StepType.RMTREE, cmd=[""])
        errors = validate_single_step(step)
        assert len(errors) == 1
        assert "Path cannot be empty" in errors[0]

    def test_validate_execution_steps(self):
        """Test validation of execution steps (SHELL, PYTHON, OJ, TEST, BUILD)"""
        # Valid shell step
        step = Step(type=StepType.SHELL, cmd=["echo", "hello"])
        errors = validate_single_step(step)
        assert errors == []

        # Invalid python step (empty command)
        step = Step(type=StepType.PYTHON, cmd=[""])
        errors = validate_single_step(step)
        assert len(errors) == 1
        assert "Command cannot be empty" in errors[0]

        # Valid test step with arguments
        step = Step(type=StepType.TEST, cmd=["pytest", "-v"])
        errors = validate_single_step(step)
        assert errors == []

    def test_validate_docker_steps(self):
        """Test validation of Docker-specific steps"""
        # Valid docker exec step
        step = Step(type=StepType.DOCKER_EXEC, cmd=["container", "echo", "hello"])
        errors = validate_single_step(step)
        assert errors == []

        # Valid docker cp step
        step = Step(type=StepType.DOCKER_CP, cmd=["src.txt", "dst.txt"])
        errors = validate_single_step(step)
        assert errors == []

        # Valid docker run step
        step = Step(type=StepType.DOCKER_RUN, cmd=["ubuntu:latest"])
        errors = validate_single_step(step)
        assert errors == []


class TestOptimizeStepSequence:
    """Tests for optimize_step_sequence function"""

    def test_optimize_empty_sequence(self):
        """Test optimization of empty sequence"""
        optimized = optimize_step_sequence([])
        assert optimized == []

    def test_optimize_no_mkdir_steps(self):
        """Test optimization when no MKDIR steps are present"""
        steps = [
            Step(type=StepType.SHELL, cmd=["echo", "hello"]),
            Step(type=StepType.COPY, cmd=["src.txt", "dst.txt"])
        ]

        optimized = optimize_step_sequence(steps)
        assert optimized == steps

    def test_optimize_single_mkdir_step(self):
        """Test optimization with single MKDIR step"""
        steps = [
            Step(type=StepType.MKDIR, cmd=["/test/path"])
        ]

        optimized = optimize_step_sequence(steps)
        assert len(optimized) == 1
        assert optimized[0].type == StepType.MKDIR
        assert optimized[0].cmd == ["/test/path"]

    def test_optimize_consecutive_mkdir_steps(self):
        """Test optimization of consecutive MKDIR steps"""
        steps = [
            Step(type=StepType.MKDIR, cmd=["/path1"]),
            Step(type=StepType.MKDIR, cmd=["/path2"]),
            Step(type=StepType.MKDIR, cmd=["/path3"])
        ]

        optimized = optimize_step_sequence(steps)

        assert len(optimized) == 3
        for i, step in enumerate(optimized):
            assert step.type == StepType.MKDIR
            assert step.cmd == [f"/path{i+1}"]

    def test_optimize_duplicate_mkdir_paths(self):
        """Test optimization removes duplicate MKDIR paths"""
        steps = [
            Step(type=StepType.MKDIR, cmd=["/path1"]),
            Step(type=StepType.MKDIR, cmd=["/path2"]),
            Step(type=StepType.MKDIR, cmd=["/path1"])  # Duplicate
        ]

        optimized = optimize_step_sequence(steps)

        assert len(optimized) == 2
        assert optimized[0].cmd == ["/path1"]
        assert optimized[1].cmd == ["/path2"]

    def test_optimize_mkdir_with_different_options(self):
        """Test optimization preserves options from first MKDIR step"""
        steps = [
            Step(type=StepType.MKDIR, cmd=["/path1"], allow_failure=True, show_output=True),
            Step(type=StepType.MKDIR, cmd=["/path2"], allow_failure=False, show_output=False)
        ]

        optimized = optimize_step_sequence(steps)

        assert len(optimized) == 2
        # Should preserve options from first step
        assert optimized[0].allow_failure is True
        assert optimized[0].show_output is True
        assert optimized[1].allow_failure is True  # Inherited from first
        assert optimized[1].show_output is True   # Inherited from first

    def test_optimize_mixed_step_sequence(self):
        """Test optimization of mixed step sequence with MKDIR and other steps"""
        steps = [
            Step(type=StepType.SHELL, cmd=["echo", "start"]),
            Step(type=StepType.MKDIR, cmd=["/path1"]),
            Step(type=StepType.MKDIR, cmd=["/path2"]),
            Step(type=StepType.COPY, cmd=["src.txt", "dst.txt"]),
            Step(type=StepType.MKDIR, cmd=["/path3"]),
            Step(type=StepType.SHELL, cmd=["echo", "end"])
        ]

        optimized = optimize_step_sequence(steps)

        assert len(optimized) == 6
        assert optimized[0].type == StepType.SHELL
        assert optimized[1].type == StepType.MKDIR
        assert optimized[1].cmd == ["/path1"]
        assert optimized[2].type == StepType.MKDIR
        assert optimized[2].cmd == ["/path2"]
        assert optimized[3].type == StepType.COPY
        assert optimized[4].type == StepType.MKDIR
        assert optimized[4].cmd == ["/path3"]
        assert optimized[5].type == StepType.SHELL

    def test_optimize_preserves_step_order(self):
        """Test that optimization preserves relative order of non-MKDIR steps"""
        steps = [
            Step(type=StepType.SHELL, cmd=["echo", "1"]),
            Step(type=StepType.MKDIR, cmd=["/path1"]),
            Step(type=StepType.SHELL, cmd=["echo", "2"]),
            Step(type=StepType.MKDIR, cmd=["/path2"]),
            Step(type=StepType.SHELL, cmd=["echo", "3"])
        ]

        optimized = optimize_step_sequence(steps)

        assert len(optimized) == 5
        shell_steps = [s for s in optimized if s.type == StepType.SHELL]
        assert len(shell_steps) == 3
        assert shell_steps[0].cmd == ["echo", "1"]
        assert shell_steps[1].cmd == ["echo", "2"]
        assert shell_steps[2].cmd == ["echo", "3"]


class TestIntegration:
    """Integration tests combining multiple core functions"""

    def test_full_workflow_from_json_to_optimized_steps(self):
        """Test complete workflow from JSON to optimized steps"""
        context = StepContext(
            contest_name="abc300",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="test",
            workspace_path="/workspace",
            contest_current_path="/contest_current"
        )

        json_steps = [
            {
                "type": "mkdir",
                "cmd": ["{workspace_path}/temp"]
            },
            {
                "type": "mkdir",
                "cmd": ["{workspace_path}/output"]
            },
            {
                "type": "mkdir",
                "cmd": ["{workspace_path}/temp"]  # Duplicate
            },
            {
                "type": "copy",
                "cmd": ["template.py", "{workspace_path}/main.py"]
            },
            {
                "type": "shell",
                "cmd": ["python3", "{workspace_path}/main.py"]
            }
        ]

        # Generate steps from JSON
        result = generate_steps_from_json(json_steps, context)
        assert result.is_success
        assert len(result.steps) == 5

        # Validate step sequence
        errors = validate_step_sequence(result.steps)
        assert errors == []

        # Optimize step sequence
        optimized = optimize_step_sequence(result.steps)

        # Should have only 2 unique mkdir steps + copy + shell = 4 steps total
        assert len(optimized) == 4
        mkdir_steps = [s for s in optimized if s.type == StepType.MKDIR]
        assert len(mkdir_steps) == 2
        assert mkdir_steps[0].cmd == ["/workspace/temp"]
        assert mkdir_steps[1].cmd == ["/workspace/output"]

    def test_error_handling_in_complete_workflow(self):
        """Test error handling throughout complete workflow"""
        context = StepContext(
            contest_name="abc300",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="test",
            workspace_path="/workspace",
            contest_current_path="/contest_current"
        )

        json_steps = [
            {
                "type": "shell",
                "cmd": ["echo", "hello"]
            },
            {
                "type": "invalid_type",  # This will cause an error
                "cmd": ["test"]
            },
            {
                "type": "copy",
                "cmd": ["src", ""]       # This would be invalid when validated due to empty dst
            }
        ]

        # Generate steps from JSON (should handle invalid_type error)
        result = generate_steps_from_json(json_steps, context)
        assert not result.is_success
        assert len(result.steps) == 2  # Valid steps still created
        assert len(result.errors) == 1
        assert "Unknown step type: invalid_type" in result.errors[0]

        # Validate the generated steps (should find copy step error for empty path)
        errors = validate_step_sequence(result.steps)
        assert len(errors) == 1
        assert "copy" in errors[0]
        assert "Source and destination paths cannot be empty" in errors[0]

"""Tests for workflow step generation service"""
import unittest
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

from src.configuration.config_manager import TypedExecutionConfiguration
from src.workflow.step.step import Step, StepContext, StepGenerationResult, StepType
from src.workflow.step.step_generation_service import (
    create_step_context_from_execution_context,
    create_step_from_json,
    execution_context_to_simple_context,
    expand_file_patterns,
    format_template,
    generate_steps_from_json,
    optimize_step_sequence,
    validate_single_step,
    validate_step_sequence,
)
from src.workflow.step.step_runner import ExecutionContext


class TestStepGenerationService(unittest.TestCase):
    """Test cases for step generation service functions"""

    def setUp(self):
        """Set up test environment"""
        # Mock TypedExecutionConfiguration
        self.typed_context = Mock(spec=TypedExecutionConfiguration)
        self.typed_context.contest_name = "test_contest"
        self.typed_context.problem_name = "test_problem"
        self.typed_context.language = "python3"
        self.typed_context.env_type = "local"
        self.typed_context.command_type = "build"
        self.typed_context.local_workspace_path = "/workspace"
        self.typed_context.contest_current_path = "/contest"
        self.typed_context.contest_stock_path = "/stock"
        self.typed_context.contest_template_path = "/template"
        self.typed_context.contest_temp_path = "/temp"
        self.typed_context.source_file_name = "main.py"
        self.typed_context.language_id = "python3"
        self.typed_context.file_patterns = {"src": ["*.py"], "test": ["test_*.py"]}
        self.typed_context.run_command = "python3 main.py"

        # Mock legacy ExecutionContext
        self.legacy_context = Mock()
        self.legacy_context.contest_name = "test_contest"
        self.legacy_context.problem_name = "test_problem"
        self.legacy_context.language = "python3"
        self.legacy_context.env_type = "local"
        self.legacy_context.command_type = "build"
        self.legacy_context.local_workspace_path = "/workspace"
        self.legacy_context.contest_current_path = "/contest"
        self.legacy_context.contest_stock_path = "/stock"
        self.legacy_context.contest_template_path = "/template"
        self.legacy_context.contest_temp_path = "/temp"
        self.legacy_context.source_file_name = "main.py"
        self.legacy_context.language_id = "python3"
        self.legacy_context.run_command = "python3 main.py"
        self.legacy_context.file_patterns = {"src": ["*.py"]}
        self.legacy_context.env_json = {
            "python3": {
                "file_patterns": {"src": ["*.py"]},
                "run_command": "python3 main.py"
            }
        }
        # Prevent accessing config.runtime_config path
        del self.legacy_context.config

    def test_create_step_context_from_execution_context_typed(self):
        """Test creating StepContext from TypedExecutionConfiguration"""
        result = create_step_context_from_execution_context(self.typed_context)

        self.assertIsInstance(result, StepContext)
        self.assertEqual(result.contest_name, "test_contest")
        self.assertEqual(result.problem_name, "test_problem")
        self.assertEqual(result.language, "python3")
        self.assertEqual(result.file_patterns, {"src": ["*.py"], "test": ["test_*.py"]})

    def test_create_step_context_from_execution_context_legacy(self):
        """Test creating StepContext from legacy ExecutionContext"""
        result = create_step_context_from_execution_context(self.legacy_context)

        self.assertIsInstance(result, StepContext)
        self.assertEqual(result.contest_name, "test_contest")
        self.assertEqual(result.problem_name, "test_problem")
        self.assertEqual(result.language, "python3")


    def test_execution_context_to_simple_context_typed(self):
        """Test converting TypedExecutionConfiguration to ExecutionContext"""
        result = execution_context_to_simple_context(self.typed_context)

        self.assertIsInstance(result, ExecutionContext)
        self.assertEqual(result.contest_name, "test_contest")
        self.assertEqual(result.problem_name, "test_problem")
        self.assertEqual(result.language, "python3")
        self.assertEqual(result.run_command, "python3 main.py")

    def test_execution_context_to_simple_context_legacy(self):
        """Test converting legacy ExecutionContext to ExecutionContext"""
        result = execution_context_to_simple_context(self.legacy_context)

        self.assertIsInstance(result, ExecutionContext)
        self.assertEqual(result.contest_name, "test_contest")
        self.assertEqual(result.run_command, "python3 main.py")

    @patch('src.workflow.step.step_generation_service.run_steps')
    def test_generate_steps_from_json(self, mock_run_steps):
        """Test generating steps from JSON configuration"""
        # Mock step results
        mock_result = Mock()
        mock_result.success = True
        mock_result.skipped = False
        mock_result.error_message = None
        mock_result.step = Mock(spec=Step)
        mock_run_steps.return_value = [mock_result]

        json_steps = [{"type": "mkdir", "cmd": ["test_dir"]}]

        result = generate_steps_from_json(json_steps, self.typed_context)

        self.assertIsInstance(result, StepGenerationResult)
        self.assertEqual(len(result.steps), 1)
        self.assertEqual(len(result.errors), 0)

    @patch('src.workflow.step.step_generation_service.run_steps')
    def test_generate_steps_from_json_with_errors(self, mock_run_steps):
        """Test generating steps with errors"""
        # Mock step result with error
        mock_result = Mock()
        mock_result.success = False
        mock_result.error_message = "Test error"
        mock_result.step = Mock(spec=Step)
        mock_run_steps.return_value = [mock_result]

        json_steps = [{"type": "invalid", "cmd": []}]

        result = generate_steps_from_json(json_steps, self.typed_context)

        self.assertEqual(len(result.errors), 1)
        self.assertIn("Test error", result.errors[0])

    @patch('src.workflow.step.step_generation_service.create_step_simple')
    def test_create_step_from_json(self, mock_create_step):
        """Test creating single step from JSON"""
        mock_step = Mock(spec=Step)
        mock_create_step.return_value = mock_step

        json_step = {"type": "mkdir", "cmd": ["test_dir"]}

        result = create_step_from_json(json_step, self.typed_context)

        self.assertEqual(result, mock_step)
        mock_create_step.assert_called_once()

    @patch('src.workflow.step.step_generation_service.expand_template')
    def test_format_template(self, mock_expand_template):
        """Test template formatting"""
        mock_expand_template.return_value = "formatted_template"

        result = format_template("test_{problem_name}", self.typed_context)

        self.assertEqual(result, "formatted_template")
        mock_expand_template.assert_called_once()


    def test_expand_file_patterns_typed(self):
        """Test expanding file patterns with TypedExecutionConfiguration"""
        self.typed_context.resolve_formatted_string = Mock(return_value="expanded_pattern")

        result = expand_file_patterns("pattern_{src}", self.typed_context, None)

        self.assertEqual(result, "expanded_pattern")
        self.typed_context.resolve_formatted_string.assert_called_once_with("pattern_{src}")


    @patch('src.workflow.step.step_generation_service.expand_template')
    @patch('src.workflow.step.step_generation_service.expand_file_patterns_in_text')
    def test_expand_file_patterns_legacy(self, mock_expand_patterns, mock_expand_template):
        """Test expanding file patterns with legacy context"""
        mock_expand_template.return_value = "expanded_template"
        mock_expand_patterns.return_value = "final_result"

        result = expand_file_patterns("pattern_{src}", self.legacy_context, None)

        self.assertEqual(result, "final_result")

    def test_validate_step_sequence(self):
        """Test validating step sequence"""
        # Create valid steps
        step1 = Step(type=StepType.MKDIR, cmd=["test_dir"])
        step2 = Step(type=StepType.COPY, cmd=["src", "dst"])

        result = validate_step_sequence([step1, step2])

        self.assertEqual(len(result), 0)  # No errors

    def test_validate_step_sequence_with_errors(self):
        """Test validating step sequence with errors"""
        # Create step with valid command but invalid paths for testing validation
        step = Step(type=StepType.COPY, cmd=["", "destination"])  # Empty source path

        result = validate_step_sequence([step])

        self.assertGreater(len(result), 0)  # Should have errors

    def test_validate_single_step_empty_command(self):
        """Test validating step with empty command raises ValueError"""
        with self.assertRaises(ValueError) as context:
            Step(type=StepType.MKDIR, cmd=[])

        self.assertIn("must have non-empty cmd", str(context.exception))


    def test_validate_single_step_copy_empty_paths(self):
        """Test validating copy step with empty paths"""
        step = Step(type=StepType.COPY, cmd=["", ""])  # Empty source and destination

        result = validate_single_step(step)

        self.assertGreater(len(result), 0)
        self.assertIn("Source and destination paths cannot be empty", result[0])

    def test_validate_single_step_mkdir_empty_path(self):
        """Test validating mkdir step with empty path"""
        step = Step(type=StepType.MKDIR, cmd=[""])  # Empty path

        result = validate_single_step(step)

        self.assertGreater(len(result), 0)
        self.assertIn("Path cannot be empty", result[0])

    def test_validate_single_step_shell_empty_command(self):
        """Test validating shell step with empty command"""
        step = Step(type=StepType.SHELL, cmd=[""])  # Empty command

        result = validate_single_step(step)

        self.assertGreater(len(result), 0)
        self.assertIn("Command cannot be empty", result[0])

    def test_optimize_step_sequence_mkdir_consolidation(self):
        """Test optimizing mkdir steps by consolidation"""
        # Create multiple mkdir steps
        step1 = Step(type=StepType.MKDIR, cmd=["dir1"])
        step2 = Step(type=StepType.MKDIR, cmd=["dir2"])
        step3 = Step(type=StepType.COPY, cmd=["src", "dst"])
        step4 = Step(type=StepType.MKDIR, cmd=["dir3"])

        result = optimize_step_sequence([step1, step2, step3, step4])

        # Should have consolidated the first two mkdir steps but kept them separate from the last one
        mkdir_steps = [s for s in result if s.type == StepType.MKDIR]
        self.assertGreater(len(mkdir_steps), 0)

        # Should still have the copy step
        copy_steps = [s for s in result if s.type == StepType.COPY]
        self.assertEqual(len(copy_steps), 1)

    def test_optimize_step_sequence_duplicate_mkdir_removal(self):
        """Test removing duplicate mkdir paths during optimization"""
        # Create duplicate mkdir steps
        step1 = Step(type=StepType.MKDIR, cmd=["same_dir"])
        step2 = Step(type=StepType.MKDIR, cmd=["same_dir"])  # Duplicate

        result = optimize_step_sequence([step1, step2])

        # Should only have one mkdir step after deduplication
        mkdir_steps = [s for s in result if s.type == StepType.MKDIR]
        self.assertEqual(len(mkdir_steps), 1)
        self.assertEqual(mkdir_steps[0].cmd[0], "same_dir")

    def test_optimize_step_sequence_non_mkdir_preserved(self):
        """Test that non-mkdir steps are preserved during optimization"""
        step1 = Step(type=StepType.COPY, cmd=["src", "dst"])
        step2 = Step(type=StepType.REMOVE, cmd=["file"])

        result = optimize_step_sequence([step1, step2])

        # Should preserve all non-mkdir steps
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].type, StepType.COPY)
        self.assertEqual(result[1].type, StepType.REMOVE)


if __name__ == '__main__':
    unittest.main()

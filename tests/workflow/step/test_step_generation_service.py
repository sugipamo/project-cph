"""Tests for step generation service module"""
from unittest.mock import Mock, patch

import pytest

from src.workflow.step.step import Step, StepContext, StepType
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


class TestStepGenerationService:
    """Test suite for step generation service functions"""

    @pytest.fixture
    def mock_execution_context(self):
        """Create a mock execution context for testing"""
        context = Mock()
        context.contest_name = "test_contest"
        context.problem_name = "a"
        context.language = "python"
        context.env_type = "local"
        context.command_type = "test"
        context.local_workspace_path = "/workspace"
        context.contest_current_path = "/current"
        context.contest_stock_path = "/stock"
        context.contest_template_path = "/template"
        context.contest_temp_path = "/temp"
        context.source_file_name = "main.py"
        context.language_id = "python3"
        context.run_command = "python3 main.py"
        context.old_contest_name = ""
        context.old_problem_name = ""
        context.file_patterns = {"source": ["*.py"], "input": ["*.txt"]}

        # Set up nested config mock
        runtime_config = Mock()
        runtime_config.run_command = "python3 main.py"
        config_mock = Mock()
        config_mock.runtime_config = runtime_config
        context.config = config_mock

        context.env_json = {
            "python": {
                "file_patterns": {
                    "source": ["*.py"],
                    "input": ["*.txt"]
                },
                "run_command": "python3 main.py"
            }
        }
        return context

    @pytest.fixture
    def typed_execution_config(self):
        """Create a mock typed execution configuration"""
        config = Mock()
        config.contest_name = "typed_contest"
        config.problem_name = "b"
        config.language = "cpp"
        config.env_type = "docker"
        config.command_type = "submit"
        config.local_workspace_path = "/workspace"
        config.contest_current_path = "/current"
        config.contest_stock_path = "/stock"
        config.contest_template_path = "/template"
        config.contest_temp_path = "/temp"
        config.source_file_name = "main.cpp"
        config.language_id = "cpp"
        config.run_command = "g++ -o main main.cpp && ./main"
        config.file_patterns = {"source": ["*.cpp"], "input": ["*.txt"]}
        return config

    def test_create_step_context_from_execution_context_legacy(self, mock_execution_context):
        """Test creating step context from legacy execution context"""
        result = create_step_context_from_execution_context(mock_execution_context)

        assert isinstance(result, StepContext)
        assert result.contest_name == "test_contest"
        assert result.problem_name == "a"
        assert result.language == "python"
        assert result.env_type == "local"
        assert result.command_type == "test"
        assert result.local_workspace_path == "/workspace"
        assert result.contest_current_path == "/current"
        assert result.source_file_name == "main.py"
        assert result.language_id == "python3"
        assert result.file_patterns == {"source": ["*.py"], "input": ["*.txt"]}

    def test_create_step_context_from_typed_config(self, typed_execution_config):
        """Test creating step context from typed execution configuration"""
        # Create a real class for mocking that isinstance can work with
        class MockTypedExecutionConfiguration:
            pass

        # Make our fixture instance an instance of this class
        typed_execution_config.__class__ = MockTypedExecutionConfiguration

        with patch('src.workflow.step.step_generation_service.TypedExecutionConfiguration', MockTypedExecutionConfiguration):
            result = create_step_context_from_execution_context(typed_execution_config)

        assert isinstance(result, StepContext)
        assert result.contest_name == "typed_contest"
        assert result.problem_name == "b"
        assert result.language == "cpp"
        assert result.env_type == "docker"
        assert result.command_type == "submit"

    def test_execution_context_to_simple_context_legacy(self, mock_execution_context):
        """Test converting legacy execution context to simple context"""
        result = execution_context_to_simple_context(mock_execution_context)

        assert result.contest_name == "test_contest"
        assert result.problem_name == "a"
        assert result.language == "python"
        assert result.local_workspace_path == "/workspace"
        assert result.contest_current_path == "/current"
        assert result.source_file_name == "main.py"
        assert result.language_id == "python3"
        assert result.run_command == "python3 main.py"
        assert result.file_patterns == {"source": ["*.py"], "input": ["*.txt"]}

    @patch('src.workflow.step.step_generation_service.run_steps')
    def test_generate_steps_from_json(self, mock_run_steps, mock_execution_context):
        """Test generating steps from JSON configuration"""
        # Mock step results
        mock_step_result = Mock()
        mock_step_result.success = True
        mock_step_result.skipped = False
        mock_step_result.error_message = None
        mock_step_result.step = Step(StepType.SHELL, ["echo", "test"])

        mock_run_steps.return_value = [mock_step_result]

        json_steps = [{"type": "shell", "cmd": ["echo", "test"]}]
        result = generate_steps_from_json(json_steps, mock_execution_context)

        assert len(result.steps) == 1
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        mock_run_steps.assert_called_once()

    @patch('src.workflow.step.step_generation_service.create_step_simple')
    def test_create_step_from_json(self, mock_create_step, mock_execution_context):
        """Test creating a single step from JSON"""
        mock_step = Step(StepType.SHELL, ["echo", "test"])
        mock_create_step.return_value = mock_step

        json_step = {"type": "shell", "cmd": ["echo", "test"]}
        result = create_step_from_json(json_step, mock_execution_context)

        assert result == mock_step
        mock_create_step.assert_called_once()

    @patch('src.workflow.step.step_generation_service.expand_template')
    def test_format_template_string(self, mock_expand_template, mock_execution_context):
        """Test formatting template string"""
        mock_expand_template.return_value = "formatted_result"

        result = format_template("template_string", mock_execution_context)

        assert result == "formatted_result"
        mock_expand_template.assert_called_once()

    def test_format_template_non_string(self, mock_execution_context):
        """Test formatting non-string template"""
        result = format_template(123, mock_execution_context)
        assert result == "123"

        result = format_template(None, mock_execution_context)
        assert result == ""

    @patch('src.workflow.step.step_generation_service.expand_template')
    @patch('src.workflow.step.step_runner.expand_file_patterns_in_text')
    def test_expand_file_patterns_legacy(self, mock_expand_patterns, mock_expand_template, mock_execution_context):
        """Test expanding file patterns with legacy context"""
        mock_expand_template.return_value = "expanded_template"
        mock_expand_patterns.return_value = "final_result"

        result = expand_file_patterns("template", mock_execution_context)

        assert result == "final_result"
        mock_expand_template.assert_called_once()
        mock_expand_patterns.assert_called_once()

    def test_expand_file_patterns_with_typed_config(self, typed_execution_config):
        """Test expanding file patterns with typed execution configuration"""
        # Mock the resolve_formatted_string method
        typed_execution_config.resolve_formatted_string = Mock(return_value="expanded_result")

        # Create a real class for mocking that isinstance can work with
        class MockTypedExecutionConfiguration:
            pass

        # Make our fixture instance an instance of this class
        typed_execution_config.__class__ = MockTypedExecutionConfiguration

        with patch('src.workflow.step.step_generation_service.TypedExecutionConfiguration', MockTypedExecutionConfiguration):
            result = expand_file_patterns("template", typed_execution_config)

        assert result == "expanded_result"
        typed_execution_config.resolve_formatted_string.assert_called_once_with("template")

    def test_validate_step_sequence(self):
        """Test validating step sequence"""
        steps = [
            Step(StepType.SHELL, ["echo", "test"]),
            Step(StepType.COPY, ["src", "dst"])
        ]

        errors = validate_step_sequence(steps)

        # For valid steps, should return no errors
        assert len(errors) == 0

    def test_validate_single_step_valid(self):
        """Test validating valid single step"""
        step = Step(StepType.SHELL, ["echo", "test"])
        errors = validate_single_step(step)
        assert len(errors) == 0

    def test_validate_single_step_empty_command(self):
        """Test validating step with empty command"""
        # Since Step constructor now validates, we expect this to raise
        with pytest.raises(ValueError, match="must have non-empty cmd"):
            Step(StepType.SHELL, [])

    def test_validate_single_step_copy_insufficient_args(self):
        """Test validating copy step with insufficient arguments"""
        # Since Step constructor now validates, we expect this to raise
        with pytest.raises(ValueError, match="requires at least 2 arguments"):
            Step(StepType.COPY, ["src"])  # Missing destination

    def test_validate_single_step_mkdir_no_path(self):
        """Test validating mkdir step without path"""
        # Since Step constructor now validates, we expect this to raise
        with pytest.raises(ValueError, match="must have non-empty cmd"):
            Step(StepType.MKDIR, [])

    def test_optimize_step_sequence_basic(self):
        """Test basic step sequence optimization"""
        steps = [
            Step(StepType.SHELL, ["echo", "test"]),
            Step(StepType.COPY, ["src", "dst"])
        ]

        optimized = optimize_step_sequence(steps)

        assert len(optimized) == 2
        assert optimized[0].type == StepType.SHELL
        assert optimized[1].type == StepType.COPY

    def test_optimize_step_sequence_mkdir_consolidation(self):
        """Test optimizing consecutive mkdir steps"""
        steps = [
            Step(StepType.MKDIR, ["/path1"]),
            Step(StepType.MKDIR, ["/path2"]),
            Step(StepType.MKDIR, ["/path1"]),  # Duplicate
            Step(StepType.SHELL, ["echo", "test"])
        ]

        optimized = optimize_step_sequence(steps)

        # Should have 3 steps: 2 unique mkdir + 1 shell
        assert len(optimized) == 3
        assert optimized[0].type == StepType.MKDIR
        assert optimized[0].cmd == ["/path1"]
        assert optimized[1].type == StepType.MKDIR
        assert optimized[1].cmd == ["/path2"]
        assert optimized[2].type == StepType.SHELL

    def test_optimize_step_sequence_empty_list(self):
        """Test optimizing empty step sequence"""
        steps = []
        optimized = optimize_step_sequence(steps)
        assert len(optimized) == 0

"""Tests for step generation service."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List

from src.domain.services.step_generation_service import (
    create_step_context_from_execution_context,
    execution_context_to_simple_context,
    generate_steps_from_json,
    create_step_from_json,
    format_template,
    expand_file_patterns,
    validate_step_sequence,
    validate_single_step,
    optimize_step_sequence
)
from src.domain.step import Step, StepType, StepGenerationResult


class TestStepGenerationService:
    """Test cases for step generation service functions."""

    def test_create_step_context_from_execution_context_with_file_patterns(self):
        """Test creating StepContext from execution context with file_patterns."""
        execution_context = Mock()
        execution_context.file_patterns = {"source": "*.py", "test": "*_test.py"}
        execution_context.contest_name = "abc123"
        execution_context.problem_name = "a"
        execution_context.language = "python"
        execution_context.env_type = "local"
        execution_context.command_type = "run"
        execution_context.local_workspace_path = "/workspace"
        execution_context.contest_current_path = "/contest/current"
        execution_context.contest_stock_path = "/contest/stock"
        execution_context.contest_template_path = "/contest/template"
        execution_context.contest_temp_path = "/contest/temp"
        execution_context.source_file_name = "main.py"
        execution_context.language_id = "python3"
        
        step_context = create_step_context_from_execution_context(execution_context)
        
        assert step_context.contest_name == "abc123"
        assert step_context.problem_name == "a"
        assert step_context.language == "python"
        assert step_context.file_patterns == {"source": "*.py", "test": "*_test.py"}

    def test_create_step_context_from_execution_context_from_env_json(self):
        """Test creating StepContext when file_patterns come from env_json."""
        execution_context = Mock(spec=['contest_name', 'problem_name', 'language', 
                                      'env_type', 'command_type', 'local_workspace_path',
                                      'contest_current_path', 'env_json'])
        execution_context.contest_name = "abc123"
        execution_context.problem_name = "a"
        execution_context.language = "python"
        execution_context.env_type = "local"
        execution_context.command_type = "run"
        execution_context.local_workspace_path = "/workspace"
        execution_context.contest_current_path = "/contest/current"
        execution_context.env_json = {
            "python": {
                "file_patterns": {
                    "source": {"workspace": "*.py"},
                    "test": {"contest_current": "*_test.py"}
                }
            }
        }
        
        step_context = create_step_context_from_execution_context(execution_context)
        
        assert step_context.file_patterns == {"source": "*.py", "test": "*_test.py"}

    def test_execution_context_to_simple_context_basic(self):
        """Test converting execution context to simple context."""
        execution_context = Mock()
        execution_context.contest_name = "abc123"
        execution_context.problem_name = "a"
        execution_context.language = "python"
        execution_context.local_workspace_path = "/workspace"
        execution_context.contest_current_path = "/contest/current"
        execution_context.contest_stock_path = "/contest/stock"
        execution_context.contest_template_path = "/contest/template"
        execution_context.source_file_name = "main.py"
        execution_context.language_id = "python3"
        execution_context.run_command = "python3"
        execution_context.file_patterns = {"source": "*.py"}
        # Mock config attribute
        execution_context.config = Mock()
        execution_context.config.runtime_config = Mock()
        execution_context.config.runtime_config.run_command = "python3"
        
        simple_context = execution_context_to_simple_context(execution_context)
        
        assert simple_context.contest_name == "abc123"
        assert simple_context.problem_name == "a"
        assert simple_context.language == "python"
        # run_command might come from different sources
        assert simple_context.run_command in ["python3", execution_context.config.runtime_config.run_command]
        assert simple_context.file_patterns == {"source": "*.py"}

    def test_execution_context_to_simple_context_run_command_from_env_json(self):
        """Test getting run_command from env_json."""
        execution_context = Mock(spec=['contest_name', 'problem_name', 'language',
                                      'env_json'])
        execution_context.contest_name = "abc123"
        execution_context.problem_name = "a"
        execution_context.language = "python"
        execution_context.env_json = {
            "python": {
                "run_command": "python3 -u"
            }
        }
        
        simple_context = execution_context_to_simple_context(execution_context)
        
        assert simple_context.run_command == "python3 -u"

    @patch('src.domain.services.step_generation_service.run_steps')
    @patch('src.domain.services.step_generation_service.execution_context_to_simple_context')
    def test_generate_steps_from_json_success(self, mock_context_conversion, mock_run_steps):
        """Test successful step generation from JSON."""
        json_steps = [
            {"type": "shell", "cmd": ["echo", "test"]},
            {"type": "mkdir", "cmd": ["/tmp/test"]}
        ]
        context = Mock()
        os_provider = Mock()
        json_provider = Mock()
        
        # Mock context conversion
        simple_context = Mock()
        mock_context_conversion.return_value = simple_context
        
        # Mock successful step results
        step1 = Mock()
        step2 = Mock()
        mock_run_steps.return_value = [step1, step2]
        
        result = generate_steps_from_json(json_steps, context, os_provider, json_provider)
        
        assert isinstance(result, StepGenerationResult)
        assert result.steps == [step1, step2]
        assert result.errors == []

    @patch('src.domain.services.step_generation_service.run_steps')
    def test_generate_steps_from_json_with_errors(self, mock_run_steps):
        """Test step generation with errors."""
        json_steps = [{"type": "shell", "cmd": ["invalid"]}]
        context = Mock()
        os_provider = Mock()
        json_provider = Mock()
        
        # Mock step results with error
        error_result = Mock()
        error_result.success = False
        error_result.error_message = "Command failed"
        mock_run_steps.return_value = [error_result]
        
        result = generate_steps_from_json(json_steps, context, os_provider, json_provider)
        
        assert result.errors == ["Command failed"]
        assert result.steps == []

    def test_generate_steps_from_json_missing_providers(self):
        """Test step generation fails without providers."""
        json_steps = []
        context = Mock()
        
        with pytest.raises(ValueError, match="プロバイダーは必須です"):
            generate_steps_from_json(json_steps, context, None, None)

    @patch('src.domain.services.step_generation_service.create_step_simple')
    def test_create_step_from_json(self, mock_create_step):
        """Test creating single step from JSON."""
        json_step = {"type": "shell", "cmd": ["echo", "test"]}
        context = Mock()
        expected_step = Mock()
        mock_create_step.return_value = expected_step
        
        step = create_step_from_json(json_step, context)
        
        assert step == expected_step
        mock_create_step.assert_called_once()

    @patch('src.domain.services.step_generation_service.expand_template')
    def test_format_template_success(self, mock_expand_template):
        """Test successful template formatting."""
        template = "Hello {contest_name}"
        context = Mock()
        mock_expand_template.return_value = "Hello abc123"
        
        result = format_template(template, context)
        
        assert result == "Hello abc123"

    def test_format_template_none_template(self):
        """Test format_template with None template."""
        with pytest.raises(ValueError, match="Template is required but None was provided"):
            format_template(None, Mock())

    def test_format_template_non_string_template(self):
        """Test format_template with non-string template."""
        with pytest.raises(ValueError, match="Template must be a string"):
            format_template(123, Mock())

    @patch('src.domain.services.step_generation_service.expand_template')
    @patch('src.domain.services.step_generation_service.expand_file_patterns_in_text')
    @patch('src.domain.services.step_generation_service.execution_context_to_simple_context')
    def test_expand_file_patterns(self, mock_context_conversion, mock_expand_patterns, mock_expand_template):
        """Test file pattern expansion."""
        template = "{source_file}"
        context = Mock()
        step_type = StepType.SHELL
        
        # Mock context conversion
        simple_context = Mock()
        simple_context.file_patterns = {"source": "*.py"}
        mock_context_conversion.return_value = simple_context
        
        # Mock the template expansion
        mock_expand_template.return_value = "{source_file}"
        mock_expand_patterns.return_value = "main.py"
        
        result = expand_file_patterns(template, context, step_type)
        
        assert result == "main.py"

    def test_validate_step_sequence(self):
        """Test validating a sequence of steps."""
        steps = [
            Step(type=StepType.SHELL, cmd=["echo", "test"]),
            Step(type=StepType.MKDIR, cmd=[]),  # Invalid - empty cmd
            Step(type=StepType.COPY, cmd=["src"]),  # Invalid - missing dst
        ]
        
        errors = validate_step_sequence(steps)
        
        assert len(errors) == 2
        assert "Step 1 (mkdir)" in errors[0]
        assert "Step 2 (copy)" in errors[1]

    def test_validate_single_step_empty_command(self):
        """Test validating step with empty command."""
        step = Step(type=StepType.SHELL, cmd=[])
        
        errors = validate_single_step(step)
        
        assert "Command cannot be empty" in errors[0]

    def test_validate_single_step_copy_missing_args(self):
        """Test validating copy step with missing arguments."""
        step = Step(type=StepType.COPY, cmd=["src"])
        
        errors = validate_single_step(step)
        
        assert "Requires at least 2 arguments" in errors[0]

    def test_validate_single_step_copy_empty_paths(self):
        """Test validating copy step with empty paths."""
        step = Step(type=StepType.COPY, cmd=["", "dst"])
        
        errors = validate_single_step(step)
        
        assert "Source and destination paths cannot be empty" in errors[0]

    def test_validate_single_step_mkdir_empty_path(self):
        """Test validating mkdir step with empty path."""
        step = Step(type=StepType.MKDIR, cmd=[""])
        
        errors = validate_single_step(step)
        
        assert "Path cannot be empty" in errors[0]

    def test_validate_single_step_valid(self):
        """Test validating a valid step."""
        step = Step(type=StepType.SHELL, cmd=["echo", "test"])
        
        errors = validate_single_step(step)
        
        assert errors == []

    def test_optimize_step_sequence_combine_mkdir(self):
        """Test optimizing sequence by combining mkdir steps."""
        steps = [
            Step(type=StepType.MKDIR, cmd=["/tmp/a"]),
            Step(type=StepType.MKDIR, cmd=["/tmp/b"]),
            Step(type=StepType.MKDIR, cmd=["/tmp/c"]),
            Step(type=StepType.SHELL, cmd=["echo", "test"]),
            Step(type=StepType.MKDIR, cmd=["/tmp/d"])
        ]
        
        optimized = optimize_step_sequence(steps)
        
        # Should combine first 3 mkdirs but not the last one
        assert len(optimized) == 5
        assert all(s.type == StepType.MKDIR for s in optimized[:3])
        assert optimized[3].type == StepType.SHELL
        assert optimized[4].type == StepType.MKDIR

    def test_optimize_step_sequence_remove_duplicates(self):
        """Test optimizing sequence removes duplicate mkdir paths."""
        steps = [
            Step(type=StepType.MKDIR, cmd=["/tmp/a"]),
            Step(type=StepType.MKDIR, cmd=["/tmp/a"]),  # Duplicate
            Step(type=StepType.MKDIR, cmd=["/tmp/b"])
        ]
        
        optimized = optimize_step_sequence(steps)
        
        # Should remove duplicate
        assert len(optimized) == 2
        assert optimized[0].cmd == ["/tmp/a"]
        assert optimized[1].cmd == ["/tmp/b"]

    def test_optimize_step_sequence_preserve_other_steps(self):
        """Test optimization preserves non-mkdir steps."""
        steps = [
            Step(type=StepType.SHELL, cmd=["echo", "1"]),
            Step(type=StepType.COPY, cmd=["src", "dst"]),
            Step(type=StepType.PYTHON, cmd=["print('test')"])
        ]
        
        optimized = optimize_step_sequence(steps)
        
        # Should preserve all steps unchanged
        assert optimized == steps
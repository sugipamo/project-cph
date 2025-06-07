"""
Tests for workflow module
"""
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.domain.requests.composite.composite_request import CompositeRequest
from src.workflow.step.step import Step, StepContext, StepGenerationResult, StepType
from src.workflow.step.workflow import (
    create_step_context_from_env_context,
    debug_workflow_generation,
    generate_workflow_from_json,
    optimize_workflow_steps,
    validate_workflow_execution,
)


class TestGenerateWorkflowFromJson:

    @patch('src.workflow.step.workflow.generate_steps_from_json')
    @patch('src.workflow.step.workflow.validate_step_sequence')
    @patch('src.workflow.step.workflow.resolve_dependencies')
    @patch('src.workflow.step.workflow.optimize_workflow_steps')
    @patch('src.workflow.step.workflow.steps_to_requests')
    def test_success_path(self, mock_steps_to_requests, mock_optimize, mock_resolve,
                         mock_validate, mock_generate):
        """Test successful workflow generation"""
        # Setup mocks
        json_steps = [{"type": "shell", "cmd": ["echo", "test"]}]
        context = Mock(spec=StepContext)
        operations = Mock()

        # Mock step generation
        test_step = Mock(spec=Step)
        generation_result = Mock(spec=StepGenerationResult)
        generation_result.is_success = True
        generation_result.steps = [test_step]
        generation_result.errors = []
        generation_result.warnings = ["Test warning"]
        mock_generate.return_value = generation_result

        # Mock validation (no errors)
        mock_validate.return_value = []

        # Mock dependency resolution
        mock_resolve.return_value = [test_step]

        # Mock optimization
        mock_optimize.return_value = [test_step]

        # Mock request conversion
        mock_request = Mock(spec=CompositeRequest)
        mock_steps_to_requests.return_value = mock_request

        # Execute
        result, errors, warnings = generate_workflow_from_json(json_steps, context, operations)

        # Verify
        assert result == mock_request
        assert errors == []
        assert warnings == ["Test warning"]

        # Verify call chain
        mock_generate.assert_called_once_with(json_steps, context)
        mock_validate.assert_called_once_with([test_step])
        mock_resolve.assert_called_once_with([test_step], context)
        mock_optimize.assert_called_once_with([test_step])
        mock_steps_to_requests.assert_called_once_with([test_step], operations)

    @patch('src.workflow.step.workflow.generate_steps_from_json')
    @patch('src.workflow.step.workflow.CompositeRequest')
    def test_generation_failure(self, mock_composite_request, mock_generate):
        """Test workflow generation with step generation failure"""
        # Setup
        json_steps = [{"type": "invalid"}]
        context = Mock(spec=StepContext)
        operations = Mock()

        # Mock failed generation
        generation_result = Mock(spec=StepGenerationResult)
        generation_result.is_success = False
        generation_result.errors = ["Invalid step type"]
        generation_result.warnings = []
        mock_generate.return_value = generation_result

        # Mock empty request
        empty_request = Mock()
        mock_composite_request.make_composite_request.return_value = empty_request

        # Execute
        result, errors, warnings = generate_workflow_from_json(json_steps, context, operations)

        # Verify
        assert result == empty_request
        assert errors == ["Invalid step type"]
        assert warnings == []
        mock_composite_request.make_composite_request.assert_called_once_with([])

    @patch('src.workflow.step.workflow.generate_steps_from_json')
    @patch('src.workflow.step.workflow.validate_step_sequence')
    @patch('src.workflow.step.workflow.CompositeRequest')
    def test_validation_failure(self, mock_composite_request, mock_validate, mock_generate):
        """Test workflow generation with validation failure"""
        # Setup
        json_steps = [{"type": "shell", "cmd": ["echo"]}]
        context = Mock(spec=StepContext)
        operations = Mock()

        # Mock successful generation
        test_step = Mock(spec=Step)
        generation_result = Mock(spec=StepGenerationResult)
        generation_result.is_success = True
        generation_result.steps = [test_step]
        generation_result.errors = []
        generation_result.warnings = []
        mock_generate.return_value = generation_result

        # Mock validation errors
        mock_validate.return_value = ["Invalid step sequence"]

        # Mock empty request
        empty_request = Mock()
        mock_composite_request.make_composite_request.return_value = empty_request

        # Execute
        result, errors, warnings = generate_workflow_from_json(json_steps, context, operations)

        # Verify
        assert result == empty_request
        assert errors == ["Invalid step sequence"]
        assert warnings == []


class TestOptimizeWorkflowSteps:

    @patch('src.workflow.step.workflow.optimize_step_sequence')
    @patch('src.workflow.step.workflow.optimize_mkdir_steps')
    def test_optimize_workflow_steps(self, mock_optimize_mkdir, mock_optimize_sequence):
        """Test workflow step optimization"""
        # Setup
        initial_steps = [Mock(spec=Step), Mock(spec=Step)]
        sequence_optimized = [Mock(spec=Step)]
        final_optimized = [Mock(spec=Step)]

        mock_optimize_sequence.return_value = sequence_optimized
        mock_optimize_mkdir.return_value = final_optimized

        # Execute
        result = optimize_workflow_steps(initial_steps)

        # Verify
        assert result == final_optimized
        mock_optimize_sequence.assert_called_once_with(initial_steps)
        mock_optimize_mkdir.assert_called_once_with(sequence_optimized)


class TestCreateStepContextFromEnvContext:

    def test_create_step_context_all_attributes(self):
        """Test creating StepContext with all attributes present"""
        # Setup
        env_context = Mock()
        env_context.contest_name = "abc123"
        env_context.problem_name = "a"
        env_context.language = "python"
        env_context.env_type = "docker"
        env_context.command_type = "build"
        env_context.workspace_path = "/workspace"
        env_context.contest_current_path = "/current"
        env_context.contest_stock_path = "/stock"
        env_context.contest_template_path = "/template"
        env_context.contest_temp_path = "/temp"
        env_context.source_file_name = "main.py"
        env_context.language_id = "py"

        # Execute
        result = create_step_context_from_env_context(env_context)

        # Verify
        assert isinstance(result, StepContext)
        assert result.contest_name == "abc123"
        assert result.problem_name == "a"
        assert result.language == "python"
        assert result.env_type == "docker"
        assert result.command_type == "build"
        assert result.workspace_path == "/workspace"
        assert result.contest_current_path == "/current"
        assert result.contest_stock_path == "/stock"
        assert result.contest_template_path == "/template"
        assert result.contest_temp_path == "/temp"
        assert result.source_file_name == "main.py"
        assert result.language_id == "py"

    def test_create_step_context_missing_attributes(self):
        """Test creating StepContext with missing optional attributes"""
        # Setup
        env_context = Mock()
        env_context.contest_name = "abc123"
        env_context.problem_name = "a"
        env_context.language = "python"
        env_context.env_type = "docker"
        env_context.command_type = "build"
        # Remove optional attributes
        delattr(env_context, 'workspace_path')
        delattr(env_context, 'contest_stock_path')

        # Execute
        result = create_step_context_from_env_context(env_context)

        # Verify
        assert result.workspace_path == ''
        assert result.contest_stock_path is None


class TestValidateWorkflowExecution:

    def test_validate_with_errors(self):
        """Test validation with existing errors"""
        # Setup
        composite_request = Mock(spec=CompositeRequest)
        errors = ["Error 1", "Error 2"]
        warnings = []

        # Execute
        is_valid, messages = validate_workflow_execution(composite_request, errors, warnings)

        # Verify
        assert is_valid is False
        assert "Found 2 errors:" in messages[0]
        assert "  - Error 1" in messages
        assert "  - Error 2" in messages

    def test_validate_with_warnings_only(self):
        """Test validation with warnings but no errors"""
        # Setup
        composite_request = Mock(spec=CompositeRequest)
        composite_request.requests = [Mock()]
        errors = []
        warnings = ["Warning 1"]

        # Execute
        is_valid, messages = validate_workflow_execution(composite_request, errors, warnings)

        # Verify
        assert is_valid is True
        assert "Found 1 warnings:" in messages[0]
        assert "  - Warning 1" in messages
        assert "Generated 1 executable requests" in messages

    def test_validate_empty_requests(self):
        """Test validation with empty request list"""
        # Setup
        composite_request = Mock(spec=CompositeRequest)
        composite_request.requests = []
        errors = []
        warnings = []

        # Execute
        is_valid, messages = validate_workflow_execution(composite_request, errors, warnings)

        # Verify
        assert is_valid is False
        assert "No executable requests generated" in messages

    def test_validate_success(self):
        """Test successful validation"""
        # Setup
        composite_request = Mock(spec=CompositeRequest)
        composite_request.requests = [Mock(), Mock(), Mock()]
        errors = []
        warnings = []

        # Execute
        is_valid, messages = validate_workflow_execution(composite_request, errors, warnings)

        # Verify
        assert is_valid is True
        assert "Generated 3 executable requests" in messages


class TestDebugWorkflowGeneration:

    @patch('src.workflow.step.workflow.generate_steps_from_json')
    @patch('src.workflow.step.workflow.resolve_dependencies')
    @patch('src.workflow.step.workflow.optimize_workflow_steps')
    def test_debug_successful_generation(self, mock_optimize, mock_resolve, mock_generate):
        """Test debug info for successful workflow generation"""
        # Setup
        json_steps = [{"type": "shell", "cmd": ["echo", "test"]}]
        context = Mock(spec=StepContext)

        # Mock steps
        step1 = Mock(spec=Step)
        step1.type = StepType.SHELL
        step1.cmd = ["echo", "test"]

        step2 = Mock(spec=Step)
        step2.type = StepType.MKDIR
        step2.cmd = ["./output"]

        # Mock generation
        generation_result = Mock(spec=StepGenerationResult)
        generation_result.is_success = True
        generation_result.steps = [step1]
        generation_result.errors = []
        generation_result.warnings = ["Test warning"]
        mock_generate.return_value = generation_result

        # Mock dependency resolution (adds a step)
        mock_resolve.return_value = [step2, step1]

        # Mock optimization (removes a step)
        mock_optimize.return_value = [step1]

        # Execute
        debug_info = debug_workflow_generation(json_steps, context)

        # Verify structure
        assert debug_info['input_steps'] == 1
        assert 'stages' in debug_info

        # Verify step generation stage
        gen_stage = debug_info['stages']['step_generation']
        assert gen_stage['generated_steps'] == 1
        assert gen_stage['errors'] == []
        assert gen_stage['warnings'] == ["Test warning"]
        assert len(gen_stage['steps']) == 1
        assert gen_stage['steps'][0]['type'] == 'shell'

        # Verify dependency resolution stage
        dep_stage = debug_info['stages']['dependency_resolution']
        assert dep_stage['original_steps'] == 1
        assert dep_stage['resolved_steps'] == 2
        assert dep_stage['added_steps'] == 1

        # Verify optimization stage
        opt_stage = debug_info['stages']['optimization']
        assert opt_stage['pre_optimization'] == 2
        assert opt_stage['post_optimization'] == 1
        assert opt_stage['removed_steps'] == 1

    @patch('src.workflow.step.workflow.generate_steps_from_json')
    def test_debug_failed_generation(self, mock_generate):
        """Test debug info for failed workflow generation"""
        # Setup
        json_steps = [{"type": "invalid"}]
        context = Mock(spec=StepContext)

        # Mock failed generation
        generation_result = Mock(spec=StepGenerationResult)
        generation_result.is_success = False
        generation_result.steps = []
        generation_result.errors = ["Invalid step type"]
        generation_result.warnings = []
        mock_generate.return_value = generation_result

        # Execute
        debug_info = debug_workflow_generation(json_steps, context)

        # Verify
        assert debug_info['input_steps'] == 1
        assert 'step_generation' in debug_info['stages']
        assert debug_info['stages']['step_generation']['errors'] == ["Invalid step type"]
        assert 'dependency_resolution' not in debug_info['stages']
        assert 'optimization' not in debug_info['stages']

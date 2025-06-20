"""Tests for WorkflowExecutionService"""

from unittest.mock import Mock, patch

import pytest

from src.configuration.config_manager import TypedExecutionConfiguration
from src.workflow.workflow_execution_service import WorkflowExecutionService
from src.workflow.workflow_result import WorkflowExecutionResult


class TestWorkflowExecutionService:
    """Test WorkflowExecutionService functionality"""

    @pytest.fixture
    def mock_context(self):
        """Create mock execution context"""
        context = Mock(spec=TypedExecutionConfiguration)
        context.command_type = "test_command"
        context.language = "python"
        context.contest_name = "test_contest"
        context.problem_name = "test_problem"
        context.env_type = "local"
        context.env_json = {
            'shared': {
                'environment_logging': {
                    'enabled': False
                }
            }
        }
        return context

    @pytest.fixture
    def mock_infrastructure(self):
        """Create mock infrastructure container"""
        infrastructure = Mock()

        # Mock config manager
        config_manager = Mock()
        config_manager.resolve_config.return_value = []

        # Mock unified logger
        unified_logger = Mock()

        from src.infrastructure.di_container import DIKey
        infrastructure.resolve.side_effect = lambda key: {
            "config_manager": config_manager,
            "unified_logger": unified_logger,
            DIKey.UNIFIED_LOGGER: unified_logger
        }.get(key, Mock())

        return infrastructure

    @pytest.fixture
    def service(self, mock_context, mock_infrastructure):
        """Create WorkflowExecutionService instance"""
        return WorkflowExecutionService(mock_context, mock_infrastructure)

    def test_init(self, mock_context, mock_infrastructure):
        """Test WorkflowExecutionService initialization"""
        service = WorkflowExecutionService(mock_context, mock_infrastructure)

        assert service.context == mock_context
        assert service.infrastructure == mock_infrastructure

    def test_get_workflow_steps_success(self, service, mock_infrastructure):
        """Test successful workflow steps retrieval"""
        expected_steps = [
            {"type": "docker_run", "cmd": ["python", "test.py"]},
            {"type": "copy", "src": "file1", "dest": "file2"}
        ]

        config_manager = mock_infrastructure.resolve("config_manager")
        config_manager.resolve_config.return_value = expected_steps

        result = service._get_workflow_steps()

        assert result == expected_steps
        config_manager.resolve_config.assert_called_once_with(
            ['commands', 'test_command', 'steps'], list
        )

    def test_get_workflow_steps_not_found(self, service, mock_infrastructure):
        """Test workflow steps retrieval when steps not found"""
        config_manager = mock_infrastructure.resolve("config_manager")
        config_manager.resolve_config.side_effect = KeyError("steps not found")

        result = service._get_workflow_steps()

        assert result == []

    def test_get_parallel_config_success(self, service, mock_infrastructure):
        """Test successful parallel config retrieval"""
        config_manager = mock_infrastructure.resolve("config_manager")
        config_manager.resolve_config.side_effect = lambda path, type_: {
            ('commands', 'test_command', 'parallel', 'enabled'): True,
            ('commands', 'test_command', 'parallel', 'max_workers'): 8
        }[tuple(path)]

        result = service._get_parallel_config()

        assert result == {"enabled": True, "max_workers": 8}

    def test_get_parallel_config_defaults(self, service, mock_infrastructure):
        """Test parallel config with defaults when config not found"""
        config_manager = mock_infrastructure.resolve("config_manager")
        config_manager.resolve_config.side_effect = KeyError("parallel config not found")

        result = service._get_parallel_config()

        assert result == {"enabled": False, "max_workers": 4}

    def test_log_environment_info_disabled(self, service):
        """Test environment info logging when disabled"""
        service.context.env_json = {
            'shared': {
                'environment_logging': {
                    'enabled': False
                }
            }
        }

        # Should not raise any exceptions
        service._log_environment_info()

    def test_log_environment_info_no_config(self, service):
        """Test environment info logging when no config"""
        service.context.env_json = None

        # Should not raise any exceptions
        service._log_environment_info()

    def test_log_environment_info_enabled(self, service, mock_infrastructure):
        """Test environment info logging when enabled"""
        service.context.env_json = {
            'shared': {
                'environment_logging': {
                    'enabled': True,
                    'log_level': 'info'
                }
            }
        }

        from src.infrastructure.di_container import DIKey
        unified_logger = mock_infrastructure.resolve(DIKey.UNIFIED_LOGGER)

        service._log_environment_info()

        unified_logger.log_environment_info.assert_called_once_with(
            language_name="python",
            contest_name="test_contest",
            problem_name="test_problem",
            env_type="local",
            env_logging_config={'enabled': True, 'log_level': 'info'}
        )

    def test_log_environment_info_merged_config(self, service, mock_infrastructure):
        """Test environment info logging with merged config structure"""
        service.context.env_json = {
            'environment_logging': {
                'enabled': True,
                'log_level': 'debug'
            }
        }

        from src.infrastructure.di_container import DIKey
        unified_logger = mock_infrastructure.resolve(DIKey.UNIFIED_LOGGER)

        service._log_environment_info()

        unified_logger.log_environment_info.assert_called_once_with(
            language_name="python",
            contest_name="test_contest",
            problem_name="test_problem",
            env_type="local",
            env_logging_config={'enabled': True, 'log_level': 'debug'}
        )

    @patch('src.workflow.workflow_execution_service.create_request')
    def test_create_workflow_tasks(self, mock_create_request, service):
        """Test workflow task creation from steps"""
        from src.operations.constants.request_types import RequestType
        from src.workflow.step.step import Step, StepType

        # Create mock steps
        step1 = Step(StepType.DOCKER_RUN, ["python", "test.py"])
        step2 = Step(StepType.COPY, ["file1", "file2"])

        # Create mock requests
        mock_docker_request = Mock()
        mock_docker_request.request_type = RequestType.DOCKER_REQUEST
        mock_docker_request.op = Mock()
        mock_docker_request.op.__str__ = Mock(return_value="DockerOpType.exec")
        mock_docker_request.container = "test_container"

        mock_file_request = Mock()
        mock_file_request.request_type = RequestType.FILE_REQUEST

        mock_create_request.side_effect = [mock_docker_request, mock_file_request]

        result = service._create_workflow_tasks([step1, step2])

        assert len(result) == 2
        assert result[0]["request_type"] == "docker"
        assert result[0]["operation"] == "exec"
        assert result[0]["container_name"] == "test_container"
        assert result[1]["request_type"] == "file"

    def test_should_allow_failure_default(self, service):
        """Test should_allow_failure with default behavior"""
        mock_result = Mock()
        mock_result.request = Mock()
        mock_result.request.allow_failure = False

        result = service._should_allow_failure(mock_result)

        assert result is False

    def test_should_allow_failure_allowed(self, service):
        """Test should_allow_failure when failure is allowed"""
        mock_result = Mock()
        mock_result.request = Mock()
        mock_result.request.allow_failure = True

        result = service._should_allow_failure(mock_result)

        assert result is True

    def test_should_allow_failure_test_command_workaround(self, service):
        """Test should_allow_failure with TEST command workaround"""
        from src.operations.constants.request_types import RequestType

        mock_result = Mock()
        mock_result.request = Mock()
        mock_result.request.request_type = RequestType.SHELL_REQUEST
        mock_result.request.cmd = ["python3", "workspace/main.py"]
        mock_result.request.allow_failure = False

        result = service._should_allow_failure(mock_result)

        assert result is True

    def test_analyze_execution_results_all_success(self, service):
        """Test execution result analysis with all successful results"""
        mock_results = [Mock(), Mock()]
        for result in mock_results:
            result.success = True

        success, errors = service._analyze_execution_results(mock_results)

        assert success is True
        assert errors == []

    def test_analyze_execution_results_with_failures(self, service):
        """Test execution result analysis with failures"""
        mock_results = [Mock(), Mock()]
        mock_results[0].success = True
        mock_results[1].success = False
        mock_results[1].get_error_output.return_value = "Test error"

        # Mock should_allow_failure to return False
        with patch.object(service, '_should_allow_failure', return_value=False):
            success, errors = service._analyze_execution_results(mock_results)

        assert success is False
        assert len(errors) == 1
        assert "Step 1 failed: Test error" in errors

    def test_analyze_execution_results_with_allowed_failures(self, service):
        """Test execution result analysis with allowed failures"""
        mock_results = [Mock()]
        mock_results[0].success = False
        mock_results[0].get_error_output.return_value = "Allowed error"

        # Mock should_allow_failure to return True
        with patch.object(service, '_should_allow_failure', return_value=True):
            success, errors = service._analyze_execution_results(mock_results)

        assert success is True
        assert len(errors) == 1
        assert "Step 0 failed (allowed): Allowed error" in errors

    def test_create_error_result(self, service):
        """Test error result creation"""
        errors = ["Error 1", "Error 2"]
        warnings = ["Warning 1"]
        prep_results = [Mock()]

        result = service._create_error_result(errors, warnings, prep_results)

        assert isinstance(result, WorkflowExecutionResult)
        assert result.success is False
        assert result.errors == errors
        assert result.warnings == warnings
        assert result.preparation_results == prep_results
        assert result.results == []

    def test_debug_log(self, service, mock_infrastructure):
        """Test debug logging"""
        from src.infrastructure.di_container import DIKey
        unified_logger = mock_infrastructure.resolve(DIKey.UNIFIED_LOGGER)

        service._debug_log("Test debug message")

        unified_logger.debug.assert_called_once_with("Test debug message")

    @patch('src.workflow.workflow_execution_service.run_steps')
    @patch('src.workflow.workflow_execution_service.generate_workflow_from_json')
    @patch('src.workflow.workflow_execution_service.create_step_context_from_env_context')
    @patch('src.workflow.workflow_execution_service.execution_context_to_simple_context')
    def test_prepare_workflow_steps_success(self, mock_simple_context, mock_step_context,
                                          mock_generate_workflow, mock_run_steps, service):
        """Test successful workflow step preparation"""
        # Mock workflow steps
        service._get_workflow_steps = Mock(return_value=[{"type": "test"}])

        # Mock step results
        mock_step_result = Mock()
        mock_step_result.success = True
        mock_run_steps.return_value = [mock_step_result]

        # Mock workflow generation
        mock_composite_request = Mock()
        mock_generate_workflow.return_value = (mock_composite_request, [], [])

        result, errors, warnings = service._prepare_workflow_steps()

        assert result == mock_composite_request
        assert errors == []
        assert warnings == []

    def test_prepare_workflow_steps_no_steps(self, service):
        """Test workflow step preparation with no steps"""
        service._get_workflow_steps = Mock(return_value=[])

        result, errors, warnings = service._prepare_workflow_steps()

        assert result is None
        assert "No workflow steps found for command" in errors
        assert warnings == []

    def test_execute_preparation_phase(self, service):
        """Test preparation phase execution"""
        mock_composite_request = Mock()

        results, errors = service._execute_preparation_phase(mock_composite_request)

        assert results == []
        assert errors == []

    @patch('src.workflow.workflow_execution_service.UnifiedDriver')
    def test_execute_main_workflow_sequential(self, mock_unified_driver_class, service, mock_infrastructure):
        """Test main workflow execution in sequential mode"""
        mock_composite_request = Mock()
        mock_execution_result = [Mock(), Mock()]
        mock_composite_request.execute_operation.return_value = mock_execution_result

        mock_driver = Mock()
        mock_unified_driver_class.return_value = mock_driver

        results = service._execute_main_workflow(mock_composite_request, use_parallel=False)

        assert results == mock_execution_result
        mock_composite_request.execute_operation.assert_called_once()

    @patch('src.workflow.workflow_execution_service.UnifiedDriver')
    def test_execute_main_workflow_parallel(self, mock_unified_driver_class, service, mock_infrastructure):
        """Test main workflow execution in parallel mode"""
        mock_composite_request = Mock()
        mock_execution_result = [Mock(), Mock()]
        mock_composite_request.execute_parallel.return_value = mock_execution_result

        mock_driver = Mock()
        mock_unified_driver_class.return_value = mock_driver

        results = service._execute_main_workflow(mock_composite_request, use_parallel=True, max_workers=8)

        assert results == mock_execution_result
        mock_composite_request.execute_parallel.assert_called_once_with(
            mock_driver, max_workers=8, logger=mock_infrastructure.resolve("unified_logger")
        )

    @patch('src.workflow.workflow_execution_service.UnifiedDriver')
    def test_execute_main_workflow_single_result(self, mock_unified_driver_class, service, mock_infrastructure):
        """Test main workflow execution with single result"""
        mock_composite_request = Mock()
        mock_execution_result = Mock()
        mock_composite_request.execute_operation.return_value = mock_execution_result

        mock_driver = Mock()
        mock_unified_driver_class.return_value = mock_driver

        results = service._execute_main_workflow(mock_composite_request, use_parallel=False)

        assert results == [mock_execution_result]

    @patch.object(WorkflowExecutionService, '_prepare_workflow_steps')
    @patch.object(WorkflowExecutionService, '_execute_preparation_phase')
    @patch.object(WorkflowExecutionService, '_execute_main_workflow')
    @patch.object(WorkflowExecutionService, '_analyze_execution_results')
    def test_execute_workflow_full_success(self, mock_analyze, mock_execute_main,
                                         mock_execute_prep, mock_prepare, service):
        """Test full workflow execution with success"""
        # Mock all internal methods
        mock_composite_request = Mock()
        mock_prepare.return_value = (mock_composite_request, [], [])
        mock_execute_prep.return_value = ([], [])
        mock_results = [Mock()]
        mock_execute_main.return_value = mock_results
        mock_analyze.return_value = (True, [])

        result = service.execute_workflow()

        assert isinstance(result, WorkflowExecutionResult)
        assert result.success is True
        assert result.results == mock_results

    @patch.object(WorkflowExecutionService, '_prepare_workflow_steps')
    def test_execute_workflow_preparation_errors(self, mock_prepare, service):
        """Test workflow execution with preparation errors"""
        mock_prepare.return_value = (None, ["Preparation error"], [])

        result = service.execute_workflow()

        assert isinstance(result, WorkflowExecutionResult)
        assert result.success is False
        assert "Preparation error" in result.errors

    def test_execute_workflow_with_parallel_override(self, service):
        """Test workflow execution with parallel parameter override"""
        service._get_parallel_config = Mock(return_value={"enabled": False, "max_workers": 4})
        service._log_environment_info = Mock()
        service._prepare_workflow_steps = Mock(return_value=(None, ["No steps"], []))

        result = service.execute_workflow(parallel=True, max_workers=8)

        assert isinstance(result, WorkflowExecutionResult)
        assert result.success is False
        # Verify that parallel config was overridden
        assert hasattr(service.context, '_parallel_config')

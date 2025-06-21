"""Tests for workflow execution service"""
import unittest
from typing import Optional
from unittest.mock import MagicMock, Mock, patch

from src.configuration.config_manager import TypedExecutionConfiguration
from src.workflow.step.step import Step, StepType
from src.workflow.workflow_execution_service import WorkflowExecutionService
from src.workflow.workflow_result import WorkflowExecutionResult


class TestWorkflowExecutionService(unittest.TestCase):
    """Test cases for WorkflowExecutionService"""

    def setUp(self):
        """Set up test environment"""
        # Mock TypedExecutionConfiguration
        self.context = Mock(spec=TypedExecutionConfiguration)
        self.context.contest_name = "test_contest"
        self.context.problem_name = "test_problem"
        self.context.language = "python3"
        self.context.env_type = "local"
        self.context.command_type = "build"
        self.context.env_json = {
            "shared": {
                "environment_logging": {
                    "enabled": False
                }
            }
        }

        # Mock infrastructure
        self.infrastructure = Mock()
        self.mock_config_manager = Mock()
        self.mock_logger = Mock()
        from src.infrastructure.di_container import DIKey
        self.infrastructure.resolve.side_effect = lambda key: {
            "config_manager": self.mock_config_manager,
            "unified_logger": self.mock_logger,
            DIKey.UNIFIED_LOGGER: self.mock_logger
        }.get(key, Mock())

        # Create service instance
        self.service = WorkflowExecutionService(self.context, self.infrastructure)

    def test_init(self):
        """Test service initialization"""
        self.assertEqual(self.service.context, self.context)
        self.assertEqual(self.service.infrastructure, self.infrastructure)

    @patch('src.workflow.workflow_execution_service.UnifiedDriver')
    def test_execute_workflow_success(self, mock_unified_driver):
        """Test successful workflow execution"""
        # Mock configuration
        self.mock_config_manager.resolve_config.side_effect = lambda path, type_: {
            ('commands', 'build', 'steps'): [{"type": "mkdir", "cmd": ["test"]}],
            ('commands', 'build', 'parallel', 'enabled'): False,
            ('commands', 'build', 'parallel', 'max_workers'): 4
        }[tuple(path)]

        # Mock workflow preparation
        mock_composite = Mock()
        mock_composite.execute_operation.return_value = [Mock(success=True)]

        with patch.object(self.service, '_prepare_workflow_steps') as mock_prepare:
            mock_prepare.return_value = (mock_composite, [], [])

            with patch.object(self.service, '_execute_preparation_phase') as mock_prep:
                mock_prep.return_value = ([], [])

                result = self.service.execute_workflow(parallel=None, max_workers=None)

                self.assertIsInstance(result, WorkflowExecutionResult)
                self.assertTrue(result.success)

    def test_execute_workflow_with_parallel_override(self):
        """Test workflow execution with parallel parameter override"""
        # Mock configuration
        self.mock_config_manager.resolve_config.side_effect = lambda path, type_: {
            ('commands', 'build', 'steps'): [{"type": "mkdir", "cmd": ["test"]}],
            ('commands', 'build', 'parallel', 'enabled'): False,
            ('commands', 'build', 'parallel', 'max_workers'): 4
        }[tuple(path)]

        mock_composite = Mock()
        mock_composite.execute_parallel.return_value = [Mock(success=True)]

        with patch.object(self.service, '_prepare_workflow_steps') as mock_prepare:
            mock_prepare.return_value = (mock_composite, [], [])

            with patch.object(self.service, '_execute_preparation_phase') as mock_prep:
                mock_prep.return_value = ([], [])

                result = self.service.execute_workflow(parallel=True, max_workers=8)

                self.assertTrue(result.success)
                # Verify parallel execution was called with overridden parameters
                mock_composite.execute_parallel.assert_called_once()

    def test_execute_workflow_preparation_errors(self):
        """Test workflow execution with preparation errors"""
        # Mock configuration
        self.mock_config_manager.resolve_config.side_effect = lambda path, type_: {
            ('commands', 'build', 'steps'): [{"type": "mkdir", "cmd": ["test"]}],
            ('commands', 'build', 'parallel', 'enabled'): False,
            ('commands', 'build', 'parallel', 'max_workers'): 4
        }[tuple(path)]

        with patch.object(self.service, '_prepare_workflow_steps') as mock_prepare:
            mock_prepare.return_value = (None, ["Preparation error"], [])

            result = self.service.execute_workflow(parallel=None, max_workers=None)

            self.assertFalse(result.success)
            self.assertIn("Preparation error", result.errors)

    def test_execute_workflow_execution_errors(self):
        """Test workflow execution with execution errors"""
        # Mock configuration
        self.mock_config_manager.resolve_config.side_effect = lambda path, type_: {
            ('commands', 'build', 'steps'): [{"type": "mkdir", "cmd": ["test"]}],
            ('commands', 'build', 'parallel', 'enabled'): False,
            ('commands', 'build', 'parallel', 'max_workers'): 4
        }[tuple(path)]

        mock_composite = Mock()
        mock_result = Mock()
        mock_result.success = False
        mock_result.get_error_output.return_value = "Execution error"
        mock_composite.execute_operation.return_value = [mock_result]

        with patch.object(self.service, '_prepare_workflow_steps') as mock_prepare:
            mock_prepare.return_value = (mock_composite, [], [])

            with patch.object(self.service, '_execute_preparation_phase') as mock_prep:
                mock_prep.return_value = ([], [])

                with patch.object(self.service, '_should_allow_failure') as mock_allow:
                    mock_allow.return_value = False

                    result = self.service.execute_workflow(parallel=None, max_workers=None)

                    self.assertFalse(result.success)
                    self.assertGreater(len(result.errors), 0)

    def test_get_workflow_steps_success(self):
        """Test successful workflow steps retrieval"""
        expected_steps = [{"type": "mkdir", "cmd": ["test"]}]
        self.mock_config_manager.resolve_config.return_value = expected_steps

        result = self.service._get_workflow_steps()

        self.assertEqual(result, expected_steps)
        self.mock_config_manager.resolve_config.assert_called_once_with(
            ['commands', 'build', 'steps'], list
        )


    def test_get_parallel_config_success(self):
        """Test successful parallel configuration retrieval"""
        self.mock_config_manager.resolve_config.side_effect = lambda path, type_: {
            ('commands', 'build', 'parallel', 'enabled'): True,
            ('commands', 'build', 'parallel', 'max_workers'): 8
        }[tuple(path)]

        result = self.service._get_parallel_config()

        self.assertEqual(result, {"enabled": True, "max_workers": 8})


    def test_create_workflow_tasks_docker_request(self):
        """Test creating workflow tasks with docker request"""
        # Create a mock step
        step = Mock(spec=Step)
        step.type = StepType.DOCKER_BUILD
        step.cmd = ["build", "-t", "test:latest", "."]

        # Mock request creation
        mock_request = Mock()
        mock_request.request_type = Mock()
        mock_request.request_type.name = "DOCKER_REQUEST"  # Simulate enum

        with patch('src.workflow.workflow_execution_service.create_request') as mock_create:
            mock_create.return_value = mock_request

            result = self.service._create_workflow_tasks([step])

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["request_object"], mock_request)
            self.assertIn("docker_build", result[0]["command"])

    def test_create_workflow_tasks_file_request(self):
        """Test creating workflow tasks with file request"""
        step = Mock(spec=Step)
        step.type = StepType.MKDIR
        step.cmd = ["test_dir"]

        from src.operations.constants.request_types import RequestType

        mock_request = Mock()
        mock_request.request_type = RequestType.FILE_REQUEST

        with patch('src.workflow.workflow_execution_service.create_request') as mock_create:
            mock_create.return_value = mock_request

            result = self.service._create_workflow_tasks([step])

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["request_type"], "file")

    def test_log_environment_info_disabled(self):
        """Test environment logging when disabled"""
        self.context.env_json = {
            "shared": {
                "environment_logging": {
                    "enabled": False
                }
            }
        }

        # Should not raise any exceptions
        self.service._log_environment_info()

    def test_log_environment_info_enabled(self):
        """Test environment logging when enabled"""
        self.context.env_json = {
            "shared": {
                "environment_logging": {
                    "enabled": True,
                    "log_level": "INFO"
                }
            }
        }

        mock_logger = Mock()
        self.infrastructure.resolve.return_value = mock_logger

        self.service._log_environment_info()

        mock_logger.log_environment_info.assert_called_once()


    def test_log_environment_info_merged_config(self):
        """Test environment logging with merged configuration"""
        self.context.env_json = {
            "environment_logging": {
                "enabled": True,
                "log_level": "DEBUG"
            }
        }

        mock_logger = Mock()
        self.infrastructure.resolve.return_value = mock_logger

        self.service._log_environment_info()

        mock_logger.log_environment_info.assert_called_once()

    @patch('src.workflow.workflow_execution_service.run_steps')
    @patch('src.workflow.workflow_execution_service.generate_workflow_from_json')
    def test_prepare_workflow_steps_success(self, mock_generate, mock_run_steps):
        """Test successful workflow step preparation"""
        # Mock workflow steps
        json_steps = [{"type": "mkdir", "cmd": ["test"]}]

        with patch.object(self.service, '_get_workflow_steps') as mock_get_steps:
            mock_get_steps.return_value = json_steps

            # Mock step results
            mock_result = Mock()
            mock_result.success = True
            mock_result.error_message = None
            mock_run_steps.return_value = [mock_result]

            # Mock workflow generation
            mock_composite = Mock()
            mock_generate.return_value = (mock_composite, [], [])

            result = self.service._prepare_workflow_steps()

            self.assertEqual(result, (mock_composite, [], []))

    def test_prepare_workflow_steps_no_steps(self):
        """Test workflow step preparation with no steps"""
        with patch.object(self.service, '_get_workflow_steps') as mock_get_steps:
            mock_get_steps.return_value = []

            result = self.service._prepare_workflow_steps()

            self.assertEqual(result[0], None)
            self.assertIn("No workflow steps found", result[1][0])

    @patch('src.workflow.workflow_execution_service.run_steps')
    def test_prepare_workflow_steps_with_errors(self, mock_run_steps):
        """Test workflow step preparation with step errors"""
        json_steps = [{"type": "invalid", "cmd": []}]

        with patch.object(self.service, '_get_workflow_steps') as mock_get_steps:
            mock_get_steps.return_value = json_steps

            # Mock step result with error
            mock_result = Mock()
            mock_result.success = False
            mock_result.error_message = "Invalid step type"
            mock_run_steps.return_value = [mock_result]

            result = self.service._prepare_workflow_steps()

            self.assertEqual(result[0], None)
            self.assertIn("Invalid step type", result[1][0])

    def test_execute_preparation_phase(self):
        """Test preparation phase execution"""
        mock_composite = Mock()

        result = self.service._execute_preparation_phase(mock_composite)

        # Currently returns empty results as preparation is not implemented
        self.assertEqual(result, ([], []))

    @patch('src.workflow.workflow_execution_service.UnifiedDriver')
    def test_execute_main_workflow_sequential(self, mock_unified_driver_class):
        """Test main workflow execution in sequential mode"""
        mock_composite = Mock()
        mock_result = Mock(success=True)
        mock_composite.execute_operation.return_value = [mock_result]

        mock_driver = Mock()
        mock_unified_driver_class.return_value = mock_driver

        result = self.service._execute_main_workflow(mock_composite, use_parallel=False)

        self.assertEqual(result, [mock_result])
        mock_composite.execute_operation.assert_called_once_with(mock_driver, logger=self.mock_logger)

    @patch('src.workflow.workflow_execution_service.UnifiedDriver')
    def test_execute_main_workflow_parallel(self, mock_unified_driver_class):
        """Test main workflow execution in parallel mode"""
        mock_composite = Mock()
        mock_result = Mock(success=True)
        mock_composite.execute_parallel.return_value = [mock_result]

        mock_driver = Mock()
        mock_unified_driver_class.return_value = mock_driver

        result = self.service._execute_main_workflow(mock_composite, use_parallel=True, max_workers=8)

        self.assertEqual(result, [mock_result])
        mock_composite.execute_parallel.assert_called_once_with(mock_driver, max_workers=8, logger=self.mock_logger)


    @patch('src.workflow.workflow_execution_service.UnifiedDriver')
    def test_execute_main_workflow_single_result(self, mock_unified_driver_class):
        """Test main workflow execution with single result"""
        mock_composite = Mock()
        mock_result = Mock(success=True)
        mock_composite.execute_operation.return_value = mock_result  # Single result, not list

        mock_driver = Mock()
        mock_unified_driver_class.return_value = mock_driver

        result = self.service._execute_main_workflow(mock_composite, use_parallel=False)

        self.assertEqual(result, [mock_result])

    def test_analyze_execution_results_all_success(self):
        """Test analyzing execution results with all successful"""
        mock_result = Mock()
        mock_result.success = True

        success, errors = self.service._analyze_execution_results([mock_result])

        self.assertTrue(success)
        self.assertEqual(len(errors), 0)

    def test_analyze_execution_results_with_allowed_failure(self):
        """Test analyzing execution results with allowed failure"""
        mock_result = Mock()
        mock_result.success = False
        mock_result.get_error_output.return_value = "Test error"

        with patch.object(self.service, '_should_allow_failure') as mock_allow:
            mock_allow.return_value = True

            success, errors = self.service._analyze_execution_results([mock_result])

            self.assertTrue(success)  # Should still be successful due to allowed failure
            self.assertGreater(len(errors), 0)
            self.assertIn("allowed", errors[0])

    def test_analyze_execution_results_with_critical_failure(self):
        """Test analyzing execution results with critical failure"""
        mock_result = Mock()
        mock_result.success = False
        mock_result.get_error_output.return_value = "Critical error"

        with patch.object(self.service, '_should_allow_failure') as mock_allow:
            mock_allow.return_value = False

            success, errors = self.service._analyze_execution_results([mock_result])

            self.assertFalse(success)
            self.assertGreater(len(errors), 0)
            self.assertIn("Critical error", errors[0])

    def test_should_allow_failure_basic(self):
        """Test basic failure allowance check"""
        mock_result = Mock()
        mock_request = Mock()
        mock_request.allow_failure = True
        mock_result.request = mock_request

        result = self.service._should_allow_failure(mock_result)

        self.assertTrue(result)




    def test_should_allow_failure_test_step_workaround(self):
        """Test failure allowance check with TEST step workaround"""
        from src.operations.constants.request_types import RequestType

        mock_result = Mock()
        mock_request = Mock()
        mock_request.allow_failure = False
        mock_request.request_type = RequestType.SHELL_REQUEST
        mock_request.cmd = ["python3", "workspace/main.py"]
        mock_result.request = mock_request

        result = self.service._should_allow_failure(mock_result)

        self.assertTrue(result)  # Should be True due to workaround

    def test_create_error_result(self):
        """Test creating error result"""
        errors = ["Error 1", "Error 2"]
        warnings = ["Warning 1"]
        prep_results = [Mock()]

        result = self.service._create_error_result(errors, warnings, prep_results)

        self.assertIsInstance(result, WorkflowExecutionResult)
        self.assertFalse(result.success)
        self.assertEqual(result.errors, errors)
        self.assertEqual(result.warnings, warnings)
        self.assertEqual(result.preparation_results, prep_results)

    def test_debug_log(self):
        """Test debug logging"""
        test_message = "Debug message"

        self.service._debug_log(test_message)

        self.mock_logger.debug.assert_called_once_with(test_message)


if __name__ == '__main__':
    unittest.main()

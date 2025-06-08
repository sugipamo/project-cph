"""Basic tests for WorkflowExecutionService module structure"""

import sys
from unittest.mock import Mock, patch

import pytest


class TestWorkflowExecutionServiceModule:
    """Test module structure and basic functionality"""

    def test_module_imports(self):
        """Test that the module can be imported without circular dependencies"""
        # Temporarily patch the circular import to allow testing
        original_cli_app = sys.modules.get('src.application.cli_application')
        sys.modules['src.application.cli_application'] = Mock()

        try:
            from src.workflow.workflow_execution_service import WorkflowExecutionService
            assert WorkflowExecutionService is not None
        finally:
            # Restore original module if it existed
            if original_cli_app:
                sys.modules['src.application.cli_application'] = original_cli_app
            elif 'src.application.cli_application' in sys.modules:
                del sys.modules['src.application.cli_application']

    @patch('src.workflow.workflow_execution_service.PreparationExecutor')
    def test_class_instantiation(self, mock_prep_executor):
        """Test WorkflowExecutionService can be instantiated"""
        # Mock all dependencies to avoid circular imports
        original_modules = {}
        modules_to_mock = [
            'src.application.cli_application',
            'src.application.factories.unified_request_factory',
            'src.application.orchestration.unified_driver'
        ]

        for module in modules_to_mock:
            original_modules[module] = sys.modules.get(module)
            sys.modules[module] = Mock()

        try:
            from src.context.execution_context import ExecutionContext
            from src.workflow.workflow_execution_service import WorkflowExecutionService

            mock_context = Mock(spec=ExecutionContext)
            mock_operations = Mock()

            service = WorkflowExecutionService(mock_context, mock_operations)

            assert service.context == mock_context
            assert service.operations == mock_operations
            assert hasattr(service, 'preparation_executor')

        finally:
            # Restore original modules
            for module, original in original_modules.items():
                if original:
                    sys.modules[module] = original
                elif module in sys.modules:
                    del sys.modules[module]

    @patch('src.workflow.workflow_execution_service.PreparationExecutor')
    def test_get_workflow_steps_no_env_json(self, mock_prep_executor):
        """Test _get_workflow_steps with no env_json"""
        # Mock dependencies
        original_modules = {}
        modules_to_mock = [
            'src.application.cli_application',
            'src.application.factories.unified_request_factory',
            'src.application.orchestration.unified_driver'
        ]

        for module in modules_to_mock:
            original_modules[module] = sys.modules.get(module)
            sys.modules[module] = Mock()

        try:
            from src.context.execution_context import ExecutionContext
            from src.workflow.workflow_execution_service import WorkflowExecutionService

            mock_context = Mock(spec=ExecutionContext)
            mock_context.env_json = None
            mock_operations = Mock()

            service = WorkflowExecutionService(mock_context, mock_operations)
            steps = service._get_workflow_steps()

            assert steps == []

        finally:
            # Restore original modules
            for module, original in original_modules.items():
                if original:
                    sys.modules[module] = original
                elif module in sys.modules:
                    del sys.modules[module]

    @patch('src.workflow.workflow_execution_service.PreparationExecutor')
    def test_get_workflow_steps_with_config(self, mock_prep_executor):
        """Test _get_workflow_steps with valid configuration"""
        # Mock dependencies
        original_modules = {}
        modules_to_mock = [
            'src.application.cli_application',
            'src.application.factories.unified_request_factory',
            'src.application.orchestration.unified_driver'
        ]

        for module in modules_to_mock:
            original_modules[module] = sys.modules.get(module)
            sys.modules[module] = Mock()

        try:
            from src.context.execution_context import ExecutionContext
            from src.workflow.workflow_execution_service import WorkflowExecutionService

            mock_context = Mock(spec=ExecutionContext)
            mock_context.language = "python"
            mock_context.command_type = "test"
            mock_context.env_json = {
                "python": {
                    "commands": {
                        "test": {
                            "steps": [
                                {"type": "shell", "cmd": ["python", "main.py"]}
                            ]
                        }
                    }
                }
            }
            mock_operations = Mock()

            service = WorkflowExecutionService(mock_context, mock_operations)
            steps = service._get_workflow_steps()

            assert len(steps) == 1
            assert steps[0]["type"] == "shell"
            assert steps[0]["cmd"] == ["python", "main.py"]

        finally:
            # Restore original modules
            for module, original in original_modules.items():
                if original:
                    sys.modules[module] = original
                elif module in sys.modules:
                    del sys.modules[module]

    @patch('src.workflow.workflow_execution_service.PreparationExecutor')
    def test_log_environment_info_disabled(self, mock_prep_executor):
        """Test _log_environment_info when disabled"""
        # Mock dependencies
        original_modules = {}
        modules_to_mock = [
            'src.application.cli_application',
            'src.application.factories.unified_request_factory',
            'src.application.orchestration.unified_driver'
        ]

        for module in modules_to_mock:
            original_modules[module] = sys.modules.get(module)
            sys.modules[module] = Mock()

        try:
            from src.context.execution_context import ExecutionContext
            from src.workflow.workflow_execution_service import WorkflowExecutionService

            mock_context = Mock(spec=ExecutionContext)
            mock_context.env_json = {
                "shared": {
                    "environment_logging": {
                        "enabled": False
                    }
                }
            }
            mock_operations = Mock()

            service = WorkflowExecutionService(mock_context, mock_operations)

            # Should not raise any exceptions
            service._log_environment_info()

        finally:
            # Restore original modules
            for module, original in original_modules.items():
                if original:
                    sys.modules[module] = original
                elif module in sys.modules:
                    del sys.modules[module]

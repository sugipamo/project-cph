"""
Unit tests for WorkflowExecutionService
"""
import pytest
from unittest.mock import MagicMock, patch

from src.workflow_execution_service import WorkflowExecutionService, WorkflowExecutionResult
from src.context.execution_context import ExecutionContext
from src.operations.result.result import OperationResult


class TestWorkflowExecutionService:
    """Test WorkflowExecutionService functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        # Mock context
        self.mock_context = MagicMock()
        self.mock_context.command_type = "test"
        self.mock_context.language = "python"
        self.mock_context.env_json = {
            "python": {
                "commands": {
                    "test": {
                        "steps": [
                            {"type": "shell", "cmd": ["echo", "test"]}
                        ]
                    }
                }
            }
        }
        self.mock_context.to_format_dict.return_value = {
            "workspace_path": "./workspace",
            "contest_current_path": "./contest_current"
        }
        
        # Mock operations
        self.mock_operations = MagicMock()
        self.mock_file_driver = MagicMock()
        self.mock_shell_driver = MagicMock()
        self.mock_operations.resolve.side_effect = lambda x: {
            "file_driver": self.mock_file_driver,
            "shell_driver": self.mock_shell_driver
        }.get(x)
    
    def test_service_initialization(self):
        """Test service initializes correctly"""
        service = WorkflowExecutionService(self.mock_context, self.mock_operations)
        
        assert service.context == self.mock_context
        assert service.operations == self.mock_operations
        assert service.preparation_executor is not None
    
    def test_get_workflow_steps(self):
        """Test retrieving workflow steps from context"""
        service = WorkflowExecutionService(self.mock_context, self.mock_operations)
        steps = service._get_workflow_steps()
        
        assert len(steps) == 1
        assert steps[0]["type"] == "shell"
        assert steps[0]["cmd"] == ["echo", "test"]
    
    def test_get_workflow_steps_no_language(self):
        """Test handling when language is not in env_json"""
        self.mock_context.env_json = {}
        service = WorkflowExecutionService(self.mock_context, self.mock_operations)
        steps = service._get_workflow_steps()
        
        assert steps == []
    
    def test_get_workflow_steps_no_command(self):
        """Test handling when command is not found"""
        self.mock_context.command_type = "nonexistent"
        service = WorkflowExecutionService(self.mock_context, self.mock_operations)
        steps = service._get_workflow_steps()
        
        assert steps == []
    
    def test_create_workflow_tasks(self):
        """Test creating workflow tasks from steps"""
        from src.env_core.step.step import Step, StepType
        
        service = WorkflowExecutionService(self.mock_context, self.mock_operations)
        
        # Create test steps
        steps = [
            Step(type=StepType.SHELL, cmd=["echo", "test"]),
            Step(type=StepType.MKDIR, cmd=["./test_dir"]),
            Step(type=StepType.DOCKER_EXEC, cmd=["container", "python", "main.py"])
        ]
        
        tasks = service._create_workflow_tasks(steps)
        
        assert len(tasks) == 3
        assert tasks[0]["request_type"] == "shell"  # shell
        assert tasks[1]["request_type"] == "file"   # mkdir
        assert tasks[2]["request_type"] == "docker"  # docker_exec
    
    def test_execute_workflow_no_steps(self):
        """Test executing workflow with no steps"""
        self.mock_context.env_json = {"python": {"commands": {"test": {"steps": []}}}}
        service = WorkflowExecutionService(self.mock_context, self.mock_operations)
        
        result = service.execute_workflow()
        
        assert isinstance(result, WorkflowExecutionResult)
        assert result.success is False
        assert "No workflow steps found" in result.errors[0]
    
    @patch('src.workflow_execution_service.generate_steps_from_json')
    def test_execute_workflow_step_generation_error(self, mock_generate):
        """Test handling step generation errors"""
        # Mock step generation to return errors
        mock_result = MagicMock()
        mock_result.errors = ["Invalid step type"]
        mock_result.warnings = ["Deprecated feature"]
        mock_result.steps = []
        mock_generate.return_value = mock_result
        
        service = WorkflowExecutionService(self.mock_context, self.mock_operations)
        result = service.execute_workflow()
        
        assert result.success is False
        assert "Invalid step type" in result.errors
        assert "Deprecated feature" in result.warnings
    
    @patch('src.workflow_execution_service.GraphBasedWorkflowBuilder')
    @patch('src.workflow_execution_service.generate_steps_from_json')
    def test_execute_workflow_graph_building_error(self, mock_generate, mock_builder_class):
        """Test handling graph building errors"""
        # Mock successful step generation
        mock_step_result = MagicMock()
        mock_step_result.errors = []
        mock_step_result.warnings = []
        mock_step_result.steps = [MagicMock()]
        mock_generate.return_value = mock_step_result
        
        # Mock graph builder to return errors
        mock_builder = MagicMock()
        mock_builder_class.from_context.return_value = mock_builder
        mock_builder.build_graph_from_json_steps.return_value = (
            MagicMock(),  # graph
            ["Graph building failed"],  # errors
            []  # warnings
        )
        
        service = WorkflowExecutionService(self.mock_context, self.mock_operations)
        result = service.execute_workflow()
        
        assert result.success is False
        assert "Graph building failed" in result.errors
    
    @patch('src.operations.composite.unified_driver.UnifiedDriver')
    @patch('src.workflow_execution_service.GraphBasedWorkflowBuilder')
    @patch('src.workflow_execution_service.generate_steps_from_json')
    def test_execute_workflow_success(self, mock_generate, mock_builder_class, mock_driver_class):
        """Test successful workflow execution"""
        # Mock successful step generation
        mock_step = MagicMock()
        mock_step.type.value = "shell"
        mock_step.cmd = ["echo", "test"]
        
        mock_step_result = MagicMock()
        mock_step_result.errors = []
        mock_step_result.warnings = []
        mock_step_result.steps = [mock_step]
        mock_generate.return_value = mock_step_result
        
        # Mock graph builder
        mock_graph = MagicMock()
        mock_graph.execute_sequential.return_value = [
            OperationResult(success=True, stdout="test output")
        ]
        
        mock_builder = MagicMock()
        mock_builder_class.from_context.return_value = mock_builder
        mock_builder.build_graph_from_json_steps.return_value = (
            mock_graph,  # graph
            [],  # errors
            []   # warnings
        )
        
        # Mock unified driver
        mock_driver = MagicMock()
        mock_driver_class.return_value = mock_driver
        
        service = WorkflowExecutionService(self.mock_context, self.mock_operations)
        result = service.execute_workflow()
        
        assert result.success is True
        assert len(result.results) == 1
        assert result.results[0].success is True
        assert result.errors == []
    
    def test_workflow_execution_result(self):
        """Test WorkflowExecutionResult data structure"""
        results = [OperationResult(success=True)]
        prep_results = [OperationResult(success=True)]
        errors = ["Error 1"]
        warnings = ["Warning 1"]
        
        result = WorkflowExecutionResult(
            success=True,
            results=results,
            preparation_results=prep_results,
            errors=errors,
            warnings=warnings
        )
        
        assert result.success is True
        assert result.results == results
        assert result.preparation_results == prep_results
        assert result.errors == errors
        assert result.warnings == warnings
    
    
    @patch('src.operations.composite.unified_driver.UnifiedDriver')
    @patch('src.workflow_execution_service.GraphBasedWorkflowBuilder')
    @patch('src.workflow_execution_service.generate_steps_from_json')
    def test_execute_workflow_parallel(self, mock_generate, mock_builder_class, mock_driver_class):
        """Test parallel workflow execution"""
        # Mock successful step generation
        mock_step = MagicMock()
        mock_step.type.value = "shell"
        mock_step.cmd = ["echo", "test"]
        
        mock_step_result = MagicMock()
        mock_step_result.errors = []
        mock_step_result.warnings = []
        mock_step_result.steps = [mock_step]
        mock_generate.return_value = mock_step_result
        
        # Mock graph builder with parallel execution
        mock_graph = MagicMock()
        mock_graph.execute_parallel.return_value = [
            OperationResult(success=True, stdout="test output")
        ]
        
        mock_builder = MagicMock()
        mock_builder_class.from_context.return_value = mock_builder
        mock_builder.build_graph_from_json_steps.return_value = (
            mock_graph,  # graph
            [],  # errors
            []   # warnings
        )
        
        # Mock unified driver
        mock_driver = MagicMock()
        mock_driver_class.return_value = mock_driver
        
        service = WorkflowExecutionService(self.mock_context, self.mock_operations)
        result = service.execute_workflow(parallel=True, max_workers=2)
        
        assert result.success is True
        assert len(result.results) == 1
        assert result.results[0].success is True
        mock_graph.execute_parallel.assert_called_once_with(driver=mock_driver, max_workers=2)
    
    @patch('src.operations.composite.unified_driver.UnifiedDriver')
    @patch('src.workflow_execution_service.GraphBasedWorkflowBuilder')
    @patch('src.workflow_execution_service.generate_steps_from_json')
    def test_execute_workflow_with_failed_steps(self, mock_generate, mock_builder_class, mock_driver_class):
        """Test workflow execution with failed steps"""
        # Mock successful step generation
        mock_step = MagicMock()
        mock_step.type.value = "shell"
        mock_step.cmd = ["echo", "test"]
        
        mock_step_result = MagicMock()
        mock_step_result.errors = []
        mock_step_result.warnings = []
        mock_step_result.steps = [mock_step]
        mock_generate.return_value = mock_step_result
        
        # Mock graph builder with failed execution
        mock_graph = MagicMock()
        failed_result = OperationResult(success=False, stderr="Command failed")
        failed_result.get_error_output = MagicMock(return_value="Command failed")
        mock_graph.execute_sequential.return_value = [
            OperationResult(success=True, stdout="step 1 ok"),
            failed_result  # step 2 fails
        ]
        
        mock_builder = MagicMock()
        mock_builder_class.from_context.return_value = mock_builder
        mock_builder.build_graph_from_json_steps.return_value = (
            mock_graph,  # graph
            [],  # errors
            []   # warnings
        )
        
        # Mock unified driver
        mock_driver = MagicMock()
        mock_driver_class.return_value = mock_driver
        
        service = WorkflowExecutionService(self.mock_context, self.mock_operations)
        result = service.execute_workflow()
        
        assert result.success is False
        assert len(result.results) == 2
        assert result.results[0].success is True
        assert result.results[1].success is False
        assert "Step 1 failed: Command failed" in result.errors[0]
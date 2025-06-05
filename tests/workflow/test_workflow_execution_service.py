"""
Comprehensive tests for WorkflowExecutionService
This is a critical untested module that orchestrates the entire workflow execution process
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.workflow_execution_service import WorkflowExecutionService, WorkflowExecutionResult
from src.context.execution_context import ExecutionContext
from src.env_core.step.step import Step, StepType
from src.operations.result.result import OperationResult


class TestWorkflowExecutionService:
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock ExecutionContext"""
        context = Mock(spec=ExecutionContext)
        context.env_json = {
            "python": {
                "commands": {
                    "build": {
                        "steps": [
                            {
                                "type": "copy",
                                "cmd": ["./src", "./workspace"]
                            },
                            {
                                "type": "shell",
                                "cmd": ["echo", "Hello"]
                            }
                        ]
                    }
                }
            }
        }
        context.language = "python"
        context.command_type = "build"
        context.working_directory = "/test/dir"
        context.contest_name = "test_contest"
        context.task_label = "a"
        return context
    
    @pytest.fixture
    def mock_operations(self):
        """Create mock operations container"""
        operations = Mock()
        operations.shell_driver = Mock()
        operations.file_driver = Mock()
        operations.docker_driver = Mock()
        return operations
    
    @pytest.fixture
    def service(self, mock_context, mock_operations):
        """Create WorkflowExecutionService instance"""
        return WorkflowExecutionService(mock_context, mock_operations)
    
    def test_init(self, mock_context, mock_operations):
        """Test service initialization"""
        service = WorkflowExecutionService(mock_context, mock_operations)
        assert service.context == mock_context
        assert service.operations == mock_operations
        assert service.preparation_executor is not None
    
    def test_get_workflow_steps(self, service):
        """Test getting workflow steps from context"""
        steps = service._get_workflow_steps()
        assert len(steps) == 2
        assert steps[0]["type"] == "copy"
        assert steps[1]["type"] == "shell"
    
    def test_get_workflow_steps_no_env_json(self, service):
        """Test getting workflow steps when env_json is None"""
        service.context.env_json = None
        steps = service._get_workflow_steps()
        assert steps == []
    
    def test_get_workflow_steps_no_language(self, service):
        """Test getting workflow steps when language not in env_json"""
        service.context.language = "rust"
        steps = service._get_workflow_steps()
        assert steps == []
    
    @patch('src.workflow_execution_service.generate_steps_from_json')
    def test_execute_workflow_no_steps(self, mock_generate, service):
        """Test executing workflow with no steps"""
        service.context.env_json = None
        result = service.execute_workflow()
        
        assert isinstance(result, WorkflowExecutionResult)
        assert not result.success
        assert result.errors == ["No workflow steps found for command"]
        assert result.results == []
        assert result.preparation_results == []
    
    @patch('src.workflow_execution_service.generate_steps_from_json')
    def test_execute_workflow_step_generation_error(self, mock_generate, service):
        """Test executing workflow when step generation fails"""
        mock_result = Mock()
        mock_result.errors = ["Step generation error"]
        mock_result.warnings = ["Warning 1"]
        mock_generate.return_value = mock_result
        
        result = service.execute_workflow()
        
        assert not result.success
        assert result.errors == ["Step generation error"]
        assert result.warnings == ["Warning 1"]
    
    @patch('src.workflow_execution_service.generate_steps_from_json')
    @patch('src.workflow_execution_service.GraphBasedWorkflowBuilder')
    def test_execute_workflow_graph_build_error(self, mock_builder_class, mock_generate, service):
        """Test executing workflow when graph building fails"""
        # Mock step generation success
        mock_result = Mock()
        mock_result.errors = []
        mock_result.warnings = []
        mock_result.steps = [Mock(spec=Step)]
        mock_generate.return_value = mock_result
        
        # Mock graph building failure
        mock_builder = Mock()
        mock_builder.build_graph_from_json_steps.return_value = (None, ["Graph error"], ["Graph warning"])
        mock_builder_class.from_context.return_value = mock_builder
        
        result = service.execute_workflow()
        
        assert not result.success
        assert result.errors == ["Graph error"]
        assert result.warnings == ["Graph warning"]
    
    @patch('src.workflow_execution_service.generate_steps_from_json')
    @patch('src.workflow_execution_service.GraphBasedWorkflowBuilder')
    @patch('src.workflow_execution_service.create_composite_request')
    @patch('src.operations.composite.unified_driver.UnifiedDriver')
    def test_execute_workflow_success(self, mock_unified_driver_class, mock_create_composite_request, 
                                    mock_builder_class, mock_generate, service):
        """Test successful workflow execution"""
        # Mock step generation
        mock_step = Mock(spec=Step)
        mock_step.type = StepType.SHELL
        mock_step.cmd = ["echo", "test"]
        
        mock_result = Mock()
        mock_result.errors = []
        mock_result.warnings = []
        mock_result.steps = [mock_step]
        mock_generate.return_value = mock_result
        
        # Mock graph building
        mock_builder = Mock()
        mock_builder.build_graph_from_json_steps.return_value = (Mock(), [], [])
        mock_builder_class.from_context.return_value = mock_builder
        
        # Mock request conversion
        mock_composite = Mock()
        mock_create_composite_request.return_value = mock_composite
        
        # Mock execution
        mock_unified_driver = Mock()
        mock_unified_driver_class.return_value = mock_unified_driver
        
        success_result = Mock(spec=OperationResult)
        success_result.success = True
        mock_composite.execute.return_value = success_result
        
        result = service.execute_workflow()
        
        assert result.success
        assert len(result.results) == 1
        assert result.errors == []
    
    @patch('src.workflow_execution_service.generate_steps_from_json')
    @patch('src.workflow_execution_service.GraphBasedWorkflowBuilder')
    @patch('src.workflow_execution_service.create_composite_request')
    @patch('src.operations.composite.unified_driver.UnifiedDriver')
    def test_execute_workflow_failure(self, mock_unified_driver_class, mock_create_composite_request,
                                    mock_builder_class, mock_generate, service):
        """Test workflow execution with failure"""
        # Setup mocks similar to success case
        mock_step = Mock(spec=Step)
        mock_step.type = StepType.SHELL
        mock_result = Mock()
        mock_result.errors = []
        mock_result.warnings = []
        mock_result.steps = [mock_step]
        mock_generate.return_value = mock_result
        
        mock_builder = Mock()
        mock_builder.build_graph_from_json_steps.return_value = (Mock(), [], [])
        mock_builder_class.from_context.return_value = mock_builder
        
        mock_composite = Mock()
        mock_create_composite_request.return_value = mock_composite
        
        mock_unified_driver = Mock()
        mock_unified_driver_class.return_value = mock_unified_driver
        
        # Create failure result
        failure_result = Mock(spec=OperationResult)
        failure_result.success = False
        failure_result.get_error_output.return_value = "Command failed"
        failure_result.request = None
        mock_composite.execute.return_value = failure_result
        
        # Mock unified factory for _create_workflow_tasks
        with patch('src.operations.factory.unified_request_factory.create_request') as mock_factory:
            mock_factory.return_value = None  # Return None to skip task creation
            result = service.execute_workflow()
        
        assert not result.success
        assert len(result.results) == 1
        assert "Step 0 failed: Command failed" in result.errors
    
    def test_create_workflow_tasks(self, service):
        """Test creating workflow tasks from steps"""
        # Create test steps
        step1 = Mock(spec=Step)
        step1.type = StepType.SHELL
        step1.cmd = ["echo", "test"]
        
        step2 = Mock(spec=Step)
        step2.type = StepType.COPY
        step2.cmd = ["src", "dst"]
        
        # Mock unified factory
        mock_shell_request = Mock()
        mock_shell_request.__class__.__name__ = "ShellRequest"
        
        mock_file_request = Mock()
        mock_file_request.__class__.__name__ = "FileRequest"
        
        with patch('src.operations.factory.unified_request_factory.create_request') as mock_factory:
            mock_factory.side_effect = [
                mock_shell_request,
                mock_file_request
            ]
            
            tasks = service._create_workflow_tasks([step1, step2])
            
            assert len(tasks) == 2
            assert tasks[0]["request_type"] == "shell"
            assert tasks[0]["command"] == "shell echo test"
            assert tasks[1]["request_type"] == "file"
            assert tasks[1]["command"] == "copy src dst"
    
    def test_create_workflow_tasks_docker(self, service):
        """Test creating workflow tasks for docker requests"""
        step = Mock(spec=Step)
        step.type = StepType.SHELL
        step.cmd = ["docker", "run"]
        
        mock_docker_request = Mock()
        mock_docker_request.__class__.__name__ = "DockerRequest"
        mock_docker_request.op = Mock()
        mock_docker_request.op.__str__ = lambda x: "DockerOpType.exec"
        mock_docker_request.container = "test_container"
        
        with patch('src.operations.factory.unified_request_factory.create_request') as mock_factory:
            mock_factory.return_value = mock_docker_request
            
            tasks = service._create_workflow_tasks([step])
            
            assert len(tasks) == 1
            assert tasks[0]["request_type"] == "docker"
            assert tasks[0]["operation"] == "exec"
            assert tasks[0]["container_name"] == "test_container"
    
    @patch('src.workflow_execution_service.generate_steps_from_json')
    @patch('src.workflow_execution_service.GraphBasedWorkflowBuilder')
    @patch('src.workflow_execution_service.create_composite_request')
    @patch('src.operations.composite.unified_driver.UnifiedDriver')
    def test_execute_workflow_with_preparation(self, mock_unified_driver_class, mock_create_composite_request,
                                             mock_builder_class, mock_generate, service):
        """Test workflow execution with preparation tasks"""
        # Setup basic mocks
        mock_step = Mock(spec=Step)
        mock_step.type = StepType.SHELL
        mock_step.cmd = ["echo", "test"]
        mock_result = Mock()
        mock_result.errors = []
        mock_result.warnings = []
        mock_result.steps = [mock_step]
        mock_generate.return_value = mock_result
        
        mock_builder = Mock()
        mock_builder.build_graph_from_json_steps.return_value = (Mock(), [], [])
        mock_builder_class.from_context.return_value = mock_builder
        
        mock_composite = Mock()
        mock_create_composite_request.return_value = mock_composite
        
        mock_unified_driver = Mock()
        mock_unified_driver_class.return_value = mock_unified_driver
        
        # Mock preparation executor
        prep_task = {"command": "prep_task"}
        service.preparation_executor.analyze_and_prepare = Mock(return_value=([prep_task], []))
        
        prep_request = Mock()
        service.preparation_executor.convert_to_workflow_requests = Mock(return_value=[prep_request])
        
        # Mock execution results
        prep_result = Mock(spec=OperationResult)
        prep_result.success = True
        
        main_result = Mock(spec=OperationResult)
        main_result.success = True
        
        mock_composite.execute.return_value = main_result
        
        # Mock DriverBoundRequest and unified factory
        with patch('src.workflow_execution_service.DriverBoundRequest') as mock_driver_bound:
            with patch('src.operations.factory.unified_request_factory.create_request') as mock_factory:
                mock_request = Mock()
                mock_request.__class__.__name__ = "ShellRequest"
                mock_factory.return_value = mock_request
                
                mock_bound = Mock()
                mock_bound.execute.return_value = prep_result
                mock_driver_bound.return_value = mock_bound
                
                result = service.execute_workflow()
                
                assert result.success
                assert len(result.preparation_results) == 1
                assert result.preparation_results[0] == prep_result
    
    @patch('src.workflow_execution_service.generate_steps_from_json')
    @patch('src.workflow_execution_service.GraphBasedWorkflowBuilder')
    @patch('src.workflow_execution_service.create_composite_request')
    @patch('src.operations.composite.unified_driver.UnifiedDriver')
    def test_execute_workflow_with_allowed_failure(self, mock_unified_driver_class, mock_create_composite_request,
                                                  mock_builder_class, mock_generate, service):
        """Test workflow execution with allowed failures"""
        # Setup mocks
        mock_step = Mock(spec=Step)
        mock_step.type = StepType.SHELL
        mock_result = Mock()
        mock_result.errors = []
        mock_result.warnings = []
        mock_result.steps = [mock_step]
        mock_generate.return_value = mock_result
        
        mock_builder = Mock()
        mock_builder.build_graph_from_json_steps.return_value = (Mock(), [], [])
        mock_builder_class.from_context.return_value = mock_builder
        
        mock_composite = Mock()
        mock_create_composite_request.return_value = mock_composite
        
        mock_unified_driver = Mock()
        mock_unified_driver_class.return_value = mock_unified_driver
        
        # Create failure result with allow_failure
        failure_result = Mock(spec=OperationResult)
        failure_result.success = False
        failure_result.get_error_output.return_value = "Test failed"
        
        mock_request = Mock()
        mock_request.allow_failure = True
        failure_result.request = mock_request
        
        mock_composite.execute.return_value = failure_result
        
        # Mock unified factory for _create_workflow_tasks
        with patch('src.operations.factory.unified_request_factory.create_request') as mock_factory:
            mock_factory.return_value = None  # Return None to skip task creation
            result = service.execute_workflow()
        
        # Should succeed because failure is allowed
        assert result.success
        assert len(result.results) == 1
        assert "Step 0 failed (allowed): Test failed" in result.errors
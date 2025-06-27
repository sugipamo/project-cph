"""Comprehensive tests for workflow execution engine"""
import pytest
from unittest.mock import Mock, patch
from src.domain.workflow import Workflow
from src.domain.step import Step, StepType
from src.domain.step_runner import ExecutionContext, expand_template
from src.domain.services.workflow_execution_service import WorkflowExecutionService


class TestWorkflowExecution:
    """Test workflow execution with both sequential and parallel steps"""
    
    @pytest.fixture
    def mock_logger(self):
        """Mock logger for testing"""
        logger = Mock()
        logger.log_start = Mock()
        logger.log_success = Mock()
        logger.log_failure = Mock()
        logger.log_info = Mock()
        return logger
    
    @pytest.fixture
    def mock_request_factory(self):
        """Mock request factory"""
        factory = Mock()
        factory.create = Mock()
        return factory
    
    @pytest.fixture
    def execution_context(self):
        """Sample execution context"""
        return ExecutionContext(
            problem_id="test_problem",
            test_case_id="test_case_1",
            values={"var1": "value1", "var2": "value2"},
            results={}
        )
    
    def test_sequential_workflow_execution(self, mock_logger, mock_request_factory, execution_context):
        """Test sequential workflow execution"""
        # Create sequential steps
        step1 = Step(
            name="step1",
            type=StepType.FILE,
            is_parallel=False,
            config={"action": "read", "path": "test.txt"}
        )
        step2 = Step(
            name="step2", 
            type=StepType.SHELL,
            is_parallel=False,
            config={"command": "echo 'test'"}
        )
        
        workflow = Workflow(
            name="test_workflow",
            steps=[step1, step2]
        )
        
        # Setup mocks
        mock_request_factory.create.return_value.execute.return_value = Mock(success=True)
        
        service = WorkflowExecutionService(
            logger=mock_logger,
            request_factory=mock_request_factory,
            error_converter=Mock()
        )
        
        # Execute workflow
        result = service.execute_workflow(workflow, execution_context)
        
        # Verify sequential execution
        assert mock_request_factory.create.call_count == 2
        assert result.success == True
    
    def test_parallel_workflow_execution(self, mock_logger, mock_request_factory, execution_context):
        """Test parallel workflow execution"""
        # Create parallel steps
        parallel_steps = [
            Step(
                name=f"parallel_step_{i}",
                type=StepType.SHELL,
                is_parallel=True,
                config={"command": f"echo 'parallel {i}'"}
            )
            for i in range(3)
        ]
        
        workflow = Workflow(
            name="parallel_workflow",
            steps=parallel_steps
        )
        
        # Setup mocks
        mock_request_factory.create.return_value.execute.return_value = Mock(success=True)
        
        service = WorkflowExecutionService(
            logger=mock_logger,
            request_factory=mock_request_factory,
            error_converter=Mock()
        )
        
        # Execute workflow
        with patch('concurrent.futures.ThreadPoolExecutor') as mock_executor:
            mock_future = Mock()
            mock_future.result.return_value = Mock(success=True)
            mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future
            
            result = service.execute_workflow(workflow, execution_context)
            
            # Verify parallel execution
            assert mock_executor.return_value.__enter__.return_value.submit.call_count == 3
    
    def test_workflow_error_handling(self, mock_logger, mock_request_factory, execution_context):
        """Test workflow handles step failures properly"""
        step1 = Step(
            name="failing_step",
            type=StepType.SHELL,
            is_parallel=False,
            config={"command": "exit 1"}
        )
        
        workflow = Workflow(
            name="failing_workflow",
            steps=[step1]
        )
        
        # Setup mock to return failure
        mock_request_factory.create.return_value.execute.return_value = Mock(
            success=False,
            error="Command failed"
        )
        
        service = WorkflowExecutionService(
            logger=mock_logger,
            request_factory=mock_request_factory,
            error_converter=Mock()
        )
        
        # Execute workflow
        result = service.execute_workflow(workflow, execution_context)
        
        # Verify failure handling
        assert result.success == False
        assert mock_logger.log_failure.called
    
    def test_template_expansion_in_steps(self, execution_context):
        """Test template variable expansion in step configuration"""
        template = "Path: ${var1}/file_${var2}.txt"
        expanded = expand_template(template, execution_context)
        
        assert expanded == "Path: value1/file_value2.txt"
    
    def test_conditional_step_execution(self, mock_logger, mock_request_factory, execution_context):
        """Test conditional step execution based on test conditions"""
        step_with_condition = Step(
            name="conditional_step",
            type=StepType.SHELL,
            is_parallel=False,
            config={"command": "echo 'conditional'"},
            test="var1 == 'value1'"  # This condition should pass
        )
        
        step_with_failing_condition = Step(
            name="skipped_step",
            type=StepType.SHELL,
            is_parallel=False,
            config={"command": "echo 'should not run'"},
            test="var1 == 'wrong_value'"  # This condition should fail
        )
        
        workflow = Workflow(
            name="conditional_workflow",
            steps=[step_with_condition, step_with_failing_condition]
        )
        
        # Setup mocks
        mock_request_factory.create.return_value.execute.return_value = Mock(success=True)
        
        service = WorkflowExecutionService(
            logger=mock_logger,
            request_factory=mock_request_factory,
            error_converter=Mock()
        )
        
        # Execute workflow
        result = service.execute_workflow(workflow, execution_context)
        
        # Only the first step should execute
        assert mock_request_factory.create.call_count == 1
    
    def test_step_result_propagation(self, mock_logger, mock_request_factory, execution_context):
        """Test that step results are properly propagated to context"""
        step1 = Step(
            name="producer_step",
            type=StepType.SHELL,
            is_parallel=False,
            config={"command": "echo 'output'"}
        )
        
        step2 = Step(
            name="consumer_step",
            type=StepType.SHELL,
            is_parallel=False,
            config={"command": "echo '${producer_step.output}'"}
        )
        
        workflow = Workflow(
            name="result_propagation_workflow",
            steps=[step1, step2]
        )
        
        # Setup mocks
        result1 = Mock(success=True, output="test_output")
        result2 = Mock(success=True)
        
        mock_request_factory.create.return_value.execute.side_effect = [result1, result2]
        
        service = WorkflowExecutionService(
            logger=mock_logger,
            request_factory=mock_request_factory,
            error_converter=Mock()
        )
        
        # Execute workflow
        result = service.execute_workflow(workflow, execution_context)
        
        # Verify results are stored in context
        assert "producer_step" in execution_context.results
    
    def test_workflow_timeout_handling(self, mock_logger, mock_request_factory, execution_context):
        """Test workflow handles timeouts properly"""
        step_with_timeout = Step(
            name="timeout_step",
            type=StepType.SHELL,
            is_parallel=False,
            config={"command": "sleep 10", "timeout": 1}  # 1 second timeout
        )
        
        workflow = Workflow(
            name="timeout_workflow",
            steps=[step_with_timeout]
        )
        
        # Setup mock to simulate timeout
        mock_request_factory.create.return_value.execute.side_effect = TimeoutError("Step timed out")
        
        service = WorkflowExecutionService(
            logger=mock_logger,
            request_factory=mock_request_factory,
            error_converter=Mock()
        )
        
        # Execute workflow
        with pytest.raises(TimeoutError):
            service.execute_workflow(workflow, execution_context)
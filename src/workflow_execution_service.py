"""
Workflow execution service to replace the removed EnvWorkflowService
Integrates workflow building, fitting, and execution
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from src.env_core.step.step import Step, StepType
from src.env_core.step.core import generate_steps_from_json
from src.env_core.workflow.graph_based_workflow_builder import GraphBasedWorkflowBuilder
from src.env_core.workflow.pure_request_factory import PureRequestFactory, PureRequest
from src.env_core.step.request_converter import steps_to_pure_sequence, PureStepSequence
from src.env_integration.fitting.preparation_executor import PreparationExecutor
from src.env_integration.fitting.pure_request_converter import PureRequestConverter
from src.context.execution_context import ExecutionContext
from src.operations.result.result import OperationResult
from src.operations.composite.driver_bound_request import DriverBoundRequest


@dataclass
class WorkflowExecutionResult:
    """Result of workflow execution"""
    success: bool
    results: List[OperationResult]
    preparation_results: List[OperationResult]
    errors: List[str]
    warnings: List[str]


class WorkflowExecutionService:
    """
    Service for executing workflows with environment preparation
    Replaces the removed EnvWorkflowService
    """
    
    def __init__(self, context: ExecutionContext, operations):
        """
        Initialize workflow execution service
        
        Args:
            context: Execution context with configuration
            operations: Operations container for drivers
        """
        self.context = context
        self.operations = operations
        self.preparation_executor = PreparationExecutor(operations, context)
        self.pure_request_converter = PureRequestConverter(operations, context)
    
    def execute_workflow(self, parallel: bool = False, max_workers: int = 4) -> WorkflowExecutionResult:
        """
        Execute workflow based on context configuration
        
        Args:
            parallel: Whether to execute in parallel
            max_workers: Maximum number of parallel workers
            
        Returns:
            WorkflowExecutionResult with execution results
        """
        # Get workflow steps from context
        json_steps = self._get_workflow_steps()
        if not json_steps:
            return WorkflowExecutionResult(
                success=False,
                results=[],
                preparation_results=[],
                errors=["No workflow steps found for command"],
                warnings=[]
            )
        
        # Generate Step objects from JSON
        step_result = generate_steps_from_json(
            json_steps, 
            self.context
        )
        
        
        if step_result.errors:
            return WorkflowExecutionResult(
                success=False,
                results=[],
                preparation_results=[],
                errors=step_result.errors,
                warnings=step_result.warnings
            )
        
        # Build workflow graph
        builder = GraphBasedWorkflowBuilder.from_context(self.context)
        graph, graph_errors, graph_warnings = builder.build_graph_from_json_steps(json_steps)
        
        
        if graph_errors:
            return WorkflowExecutionResult(
                success=False,
                results=[],
                preparation_results=[],
                errors=graph_errors,
                warnings=graph_warnings + step_result.warnings
            )
        
        # Convert steps to pure requests (env.json step reproduction only)
        pure_sequence = steps_to_pure_sequence(step_result.steps)
        
        # Analyze environment and prepare if needed (fitting responsibility)
        preparation_results = []
        if pure_sequence.steps:
            # Convert pure requests for fitting analysis
            pure_requests = [self._convert_pure_step_to_pure_request(step) for step in pure_sequence.steps]
            workflow_tasks = self._create_workflow_tasks_from_pure_requests(pure_requests)
            
            preparation_tasks, statuses = self.preparation_executor.analyze_and_prepare(workflow_tasks)
            
            if preparation_tasks:
                # Convert preparation tasks to requests
                preparation_requests = self.preparation_executor.convert_to_workflow_requests(preparation_tasks)
                
                # Execute preparation tasks
                from src.operations.composite.unified_driver import UnifiedDriver
                unified_driver = UnifiedDriver(self.operations)
                
                for request in preparation_requests:
                    bound_request = DriverBoundRequest(request, unified_driver)
                    result = bound_request.execute()
                    preparation_results.append(result)
                    
                    if not result.success:
                        return WorkflowExecutionResult(
                            success=False,
                            results=[],
                            preparation_results=preparation_results,
                            errors=[f"Preparation failed: {result.get_error_output()}"],
                            warnings=graph_warnings + step_result.warnings
                        )
        
        # Execute main workflow
        from src.operations.composite.unified_driver import UnifiedDriver
        unified_driver = UnifiedDriver(self.operations)
        
        
        if parallel:
            results = graph.execute_parallel(driver=unified_driver, max_workers=max_workers)
        else:
            results = graph.execute_sequential(driver=unified_driver)
        
        # Check if all results are successful (considering allow_failure)
        critical_failures = []
        errors = []
        for i, result in enumerate(results):
            if not result.success:
                # Check if this request has allow_failure=true
                request = result.request if hasattr(result, 'request') else None
                allow_failure = getattr(request, 'allow_failure', False) if request else False
                
                # Temporary workaround for TEST steps allow_failure issue
                if hasattr(request, '__class__') and 'Shell' in request.__class__.__name__:
                    if hasattr(request, 'cmd') and request.cmd and len(request.cmd) > 0:
                        full_cmd_str = str(request.cmd)
                        if 'python3' in full_cmd_str and 'workspace/main.py' in full_cmd_str:
                            allow_failure = True
                
                if allow_failure:
                    # Failure is allowed, don't count as critical
                    errors.append(f"Step {i} failed (allowed): {result.get_error_output()}")
                else:
                    # Critical failure
                    critical_failures.append(result)
                    errors.append(f"Step {i} failed: {result.get_error_output()}")
        
        # Success if no critical failures occurred
        success = len(critical_failures) == 0
        
        return WorkflowExecutionResult(
            success=success,
            results=results,
            preparation_results=preparation_results,
            errors=errors,
            warnings=graph_warnings + step_result.warnings
        )
    
    def _get_workflow_steps(self) -> List[Dict]:
        """Get workflow steps from context configuration"""
        if not self.context.env_json or self.context.language not in self.context.env_json:
            return []
        
        language_config = self.context.env_json[self.context.language]
        commands = language_config.get('commands', {})
        command_config = commands.get(self.context.command_type, {})
        
        steps = command_config.get('steps', [])
        
        
        return steps
    
    def _convert_pure_step_to_pure_request(self, pure_step) -> PureRequest:
        """Convert PureStepRequest to PureRequest for compatibility"""
        return PureRequest(
            type=pure_step.step_type,
            operation=pure_step.action,
            params=pure_step.parameters,
            allow_failure=pure_step.allow_failure,
            show_output=pure_step.show_output
        )
    
    def _create_workflow_tasks_from_pure_requests(self, pure_requests: List[PureRequest]) -> List[Dict]:
        """Convert pure requests to workflow tasks for fitting analysis"""
        workflow_tasks = []
        
        for pure_request in pure_requests:
            # Create task representation from pure request
            task = {
                "request_object": pure_request,
                "command": f"{pure_request.type} {pure_request.operation}",
                "request_type": pure_request.type
            }
            
            # Add operation info for docker requests
            if pure_request.type == "docker":
                task["operation"] = pure_request.operation
                
                # Add container name if available
                if "container" in pure_request.params:
                    task["container_name"] = pure_request.params["container"]
            
            workflow_tasks.append(task)
        
        return workflow_tasks
    

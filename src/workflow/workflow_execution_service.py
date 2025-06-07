"""Workflow execution service to replace the removed EnvWorkflowService
Integrates workflow building, fitting, and execution
"""

from src.application.factories.unified_request_factory import create_composite_request, create_request
from src.application.orchestration.unified_driver import UnifiedDriver
from src.context.execution_context import ExecutionContext
from src.workflow.preparation.preparation_executor import PreparationExecutor
from src.workflow.step.core import generate_steps_from_json
from src.workflow.step.step import Step, StepType
from src.workflow.workflow.graph_based_workflow_builder import GraphBasedWorkflowBuilder
from src.workflow.workflow_result import WorkflowExecutionResult


class WorkflowExecutionService:
    """Service for executing workflows with environment preparation
    Replaces the removed EnvWorkflowService
    """

    def __init__(self, context: ExecutionContext, operations):
        """Initialize workflow execution service

        Args:
            context: Execution context with configuration
            operations: Operations container for drivers
        """
        self.context = context
        self.operations = operations
        self.preparation_executor = PreparationExecutor(operations, context)

    def execute_workflow(self, parallel: bool = False, max_workers: int = 4) -> WorkflowExecutionResult:
        """Execute workflow based on context configuration

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

        # Convert steps to operations requests using unified factory
        operations_composite = create_composite_request(step_result.steps, self.context)

        # Analyze environment and prepare if needed (fitting responsibility)
        preparation_results = []
        workflow_tasks = self._create_workflow_tasks(step_result.steps)

        if workflow_tasks:
            preparation_tasks, statuses = self.preparation_executor.analyze_and_prepare(workflow_tasks)

            if preparation_tasks:
                # Convert preparation tasks to requests
                preparation_requests = self.preparation_executor.convert_to_workflow_requests(preparation_tasks)

                # Execute preparation tasks
                unified_driver = UnifiedDriver(self.operations)

                for request in preparation_requests:
                    result = request.execute(unified_driver)
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
        unified_driver = UnifiedDriver(self.operations)

        # Execute the operations requests directly
        execution_result = operations_composite.execute(unified_driver)

        # CompositeRequest returns a list of results, so flatten if needed
        if isinstance(execution_result, list):
            results = execution_result
        else:
            results = [execution_result]

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

    def _get_workflow_steps(self) -> list[dict]:
        """Get workflow steps from context configuration"""
        if not self.context.env_json or self.context.language not in self.context.env_json:
            return []

        language_config = self.context.env_json[self.context.language]
        commands = language_config.get('commands', {})
        command_config = commands.get(self.context.command_type, {})

        steps = command_config.get('steps', [])


        return steps

    def _create_workflow_tasks(self, steps: list[Step]) -> list[dict]:
        """Convert steps to workflow tasks for fitting analysis"""
        workflow_tasks = []

        for step in steps:
            # Create request from step using unified factory
            request = create_request(step, self.context)
            if request:
                # Determine request type based on actual request class
                if request.__class__.__name__ == "DockerRequest":
                    request_type = "docker"
                elif request.__class__.__name__ == "FileRequest":
                    request_type = "file"
                elif request.__class__.__name__ == "ShellRequest":
                    request_type = "shell"
                elif step.type.value.startswith("docker"):
                    request_type = "docker"
                elif step.type in [StepType.MKDIR, StepType.TOUCH, StepType.COPY,
                                 StepType.MOVE, StepType.REMOVE, StepType.RMTREE]:
                    request_type = "file"
                else:
                    request_type = "other"

                # Create task representation
                task = {
                    "request_object": request,
                    "command": f"{step.type.value} {' '.join(step.cmd)}",
                    "request_type": request_type
                }

                # Add operation info for docker requests
                if request_type == "docker" and hasattr(request, 'op'):
                    # Extract operation name from DockerOpType enum
                    op_name = str(request.op).split('.')[-1].lower()  # e.g., "exec"
                    task["operation"] = op_name

                    # Add container name if available
                    if hasattr(request, 'container'):
                        task["container_name"] = request.container

                workflow_tasks.append(task)

        return workflow_tasks


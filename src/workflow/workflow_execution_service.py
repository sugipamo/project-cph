"""Workflow execution service to replace the removed EnvWorkflowService
Integrates workflow building, fitting, and execution
"""

from src.application.factories.unified_request_factory import create_composite_request, create_request
from src.application.orchestration.unified_driver import UnifiedDriver
from src.configuration.adapters.execution_context_adapter import ExecutionContextAdapter
from src.utils.debug_logger import DebugLogger
from src.workflow.builder.graph_based_workflow_builder import GraphBasedWorkflowBuilder
from src.workflow.step.step import Step, StepType
from src.workflow.step.step_generation_service import generate_steps_from_json
from src.workflow.workflow_result import WorkflowExecutionResult


class WorkflowExecutionService:
    """Service for executing workflows with environment preparation
    Replaces the removed EnvWorkflowService
    """

    def __init__(self, context: ExecutionContextAdapter, operations):
        """Initialize workflow execution service

        Args:
            context: Execution context adapter with configuration
            operations: Operations container for drivers
        """
        self.context = context
        self.operations = operations

    def execute_workflow(self, parallel: bool = False, max_workers: int = 4) -> WorkflowExecutionResult:
        """Execute workflow based on context configuration

        Args:
            parallel: Whether to execute in parallel
            max_workers: Maximum number of parallel workers

        Returns:
            WorkflowExecutionResult with execution results
        """
        # Log environment information if configured
        self._log_environment_info()

        # Prepare workflow steps
        steps, errors, warnings = self._prepare_workflow_steps()
        if errors:
            return self._create_error_result(errors, warnings)

        # Create operations composite
        operations_composite = create_composite_request(steps, self.context)

        # Execute preparation phase
        preparation_results, prep_errors = self._execute_preparation_phase(steps)
        if prep_errors:
            return self._create_error_result(prep_errors, warnings, preparation_results)

        # Execute main workflow
        results = self._execute_main_workflow(operations_composite)

        # Analyze results
        success, result_errors = self._analyze_execution_results(results)

        # Return final result
        return WorkflowExecutionResult(
            success=success,
            results=results,
            preparation_results=preparation_results,
            errors=result_errors,
            warnings=warnings
        )

    def _get_workflow_steps(self) -> list[dict]:
        """Get workflow steps from context configuration"""
        if not self.context.env_json:
            return []

        # JsonConfigLoader.get_language_config()使用時は、マージ済み設定から直接取得
        if self.context.language in self.context.env_json:
            # 従来形式（言語がトップレベルキー）
            language_config = self.context.env_json[self.context.language]
        else:
            # JsonConfigLoader形式（マージ済み設定）
            language_config = self.context.env_json

        commands = language_config.get('commands', {})
        command_config = commands.get(self.context.command_type, {})

        # All commands now use unified steps structure
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

    def _log_environment_info(self):
        """Log environment information based on configuration"""
        if not self.context.env_json:
            return

        # Get environment logging configuration from shared config
        shared_config = self.context.env_json.get('shared', {})
        env_logging_config = shared_config.get('environment_logging', {})

        if not env_logging_config.get('enabled', False):
            return

        # Create a basic debug logger instance just for environment logging
        debug_logger = DebugLogger({})

        # Log environment information
        debug_logger.log_environment_info(
            language_name=self.context.language,
            contest_name=self.context.contest_name,
            problem_name=self.context.problem_name,
            env_type=self.context.env_type,
            env_logging_config=env_logging_config
        )

    def _prepare_workflow_steps(self):
        """Prepare workflow steps from context configuration."""
        # Get workflow steps from context
        json_steps = self._get_workflow_steps()
        if not json_steps:
            return None, ["No workflow steps found for command"], []

        # Generate Step objects from JSON
        step_result = generate_steps_from_json(json_steps, self.context)
        if step_result.errors:
            return None, step_result.errors, step_result.warnings

        # Build workflow graph
        builder = GraphBasedWorkflowBuilder.from_context(self.context)
        graph, graph_errors, graph_warnings = builder.build_graph_from_json_steps(json_steps)
        if graph_errors:
            return None, graph_errors, graph_warnings + step_result.warnings

        return step_result.steps, [], graph_warnings + step_result.warnings

    def _execute_preparation_phase(self, steps):
        """Execute environment preparation if needed."""
        preparation_results = []
        # TODO: Restore preparation functionality when PreparationExecutor is available
        return preparation_results, []

    def _execute_main_workflow(self, operations_composite):
        """Execute the main workflow operations."""
        unified_driver = UnifiedDriver(self.operations)
        execution_result = operations_composite.execute_operation(unified_driver)

        # CompositeRequest returns a list of results, so flatten if needed
        if isinstance(execution_result, list):
            return execution_result
        return [execution_result]

    def _analyze_execution_results(self, results):
        """Analyze execution results for success/failure."""
        critical_failures = []
        errors = []

        for i, result in enumerate(results):
            if not result.success:
                allow_failure = self._should_allow_failure(result)
                if allow_failure:
                    errors.append(f"Step {i} failed (allowed): {result.get_error_output()}")
                else:
                    critical_failures.append(result)
                    errors.append(f"Step {i} failed: {result.get_error_output()}")

        success = len(critical_failures) == 0
        return success, errors

    def _should_allow_failure(self, result):
        """Determine if a failure should be allowed based on request type."""
        request = result.request if hasattr(result, 'request') else None
        allow_failure = getattr(request, 'allow_failure', False) if request else False

        # Temporary workaround for TEST steps allow_failure issue
        if (hasattr(request, '__class__') and 'Shell' in request.__class__.__name__
            and hasattr(request, 'cmd') and request.cmd and len(request.cmd) > 0):
            full_cmd_str = str(request.cmd)
            if 'python3' in full_cmd_str and 'workspace/main.py' in full_cmd_str:
                allow_failure = True

        return allow_failure

    def _create_error_result(self, errors, warnings, preparation_results=None):
        """Create error result with consistent structure."""
        return WorkflowExecutionResult(
            success=False,
            results=[],
            preparation_results=preparation_results or [],
            errors=errors,
            warnings=warnings
        )


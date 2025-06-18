"""Workflow execution service to replace the removed EnvWorkflowService
Integrates workflow building, fitting, and execution
"""

from typing import Optional

from src.application.factories.unified_request_factory import create_request
from src.application.orchestration.unified_driver import UnifiedDriver
from src.configuration.config_manager import TypedExecutionConfiguration

# DebugLogger functionality now handled by src/logging UnifiedLogger
from src.operations.constants.request_types import RequestType
from src.workflow.step.step import Step, StepType
from src.workflow.workflow_result import WorkflowExecutionResult


class WorkflowExecutionService:
    """Service for executing workflows with environment preparation
    Replaces the removed EnvWorkflowService
    """

    def __init__(self, context: TypedExecutionConfiguration, infrastructure):
        """Initialize workflow execution service

        Args:
            context: Typed execution configuration
            infrastructure: Infrastructure container for drivers
        """
        self.context = context
        self.infrastructure = infrastructure

    def execute_workflow(self, parallel: Optional[bool] = None, max_workers: Optional[int] = None) -> WorkflowExecutionResult:
        """Execute workflow based on context configuration

        Args:
            parallel: Whether to execute in parallel (overrides configuration if specified)
            max_workers: Maximum number of parallel workers (overrides configuration if specified)

        Returns:
            WorkflowExecutionResult with execution results
        """
        # Get parallel configuration from context
        parallel_config = self._get_parallel_config()

        # Override with parameters if specified
        use_parallel = parallel if parallel is not None else parallel_config["enabled"]
        use_max_workers = max_workers if max_workers is not None else parallel_config["max_workers"]

        # Store parallel config in context for request factories
        self.context._parallel_config = parallel_config

        # Log environment information if configured
        self._log_environment_info()

        # Prepare workflow (now returns optimized composite request)
        operations_composite, errors, warnings = self._prepare_workflow_steps()
        if errors:
            return self._create_error_result(errors, warnings)

        # Execute preparation phase (now using composite request)
        preparation_results, prep_errors = self._execute_preparation_phase(operations_composite)
        if prep_errors:
            return self._create_error_result(prep_errors, warnings, preparation_results)

        # Execute main workflow
        results = self._execute_main_workflow(operations_composite, use_parallel, use_max_workers)

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

        commands = language_config['commands']
        command_config = commands[self.context.command_type]

        # All commands now use unified steps structure
        steps = command_config['steps']

        return steps

    def _get_parallel_config(self) -> dict:
        """Get parallel execution configuration from context"""
        if not self.context.env_json:
            return {"enabled": False, "max_workers": 4}

        # JsonConfigLoader.get_language_config()使用時は、マージ済み設定から直接取得
        if self.context.language in self.context.env_json:
            # 従来形式（言語がトップレベルキー）
            language_config = self.context.env_json[self.context.language]
        else:
            # JsonConfigLoader形式（マージ済み設定）
            language_config = self.context.env_json

        commands = language_config['commands']
        command_config = commands[self.context.command_type]

        # Get parallel configuration
        parallel_config = command_config['parallel']
        return {
            "enabled": parallel_config['enabled'],
            "max_workers": parallel_config['max_workers']
        }

    def _create_workflow_tasks(self, steps: list[Step]) -> list[dict]:
        """Convert steps to workflow tasks for fitting analysis"""
        workflow_tasks = []

        for step in steps:
            # Create request from step using unified factory
            request = create_request(step, self.context)
            if request:
                # Determine request type based on request_type property
                if hasattr(request, 'request_type'):
                    if request.request_type == RequestType.DOCKER_REQUEST:
                        request_type = "docker"
                    elif request.request_type == RequestType.FILE_REQUEST:
                        request_type = "file"
                    elif request.request_type == RequestType.SHELL_REQUEST:
                        request_type = "shell"
                    else:
                        request_type = "unknown"
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
        shared_config = self.context.env_json['shared']
        env_logging_config = shared_config['environment_logging']

        if not (env_logging_config['enabled']):
            return

        # Use unified logger from infrastructure container for environment logging
        from src.infrastructure.di_container import DIKey
        unified_logger = self.infrastructure.resolve(DIKey.UNIFIED_LOGGER)

        # Log environment information
        unified_logger.log_environment_info(
            language_name=self.context.language,
            contest_name=self.context.contest_name,
            problem_name=self.context.problem_name,
            env_type=self.context.env_type,
            env_logging_config=env_logging_config
        )

    def _prepare_workflow_steps(self):
        """Prepare workflow steps from context configuration.

        Returns the OPTIMIZED composite request instead of raw steps.
        """
        # Get workflow steps from context
        json_steps = self._get_workflow_steps()
        if not json_steps:
            return None, ["No workflow steps found for command"], []

        # Generate Step objects from JSON and get step results with skip information
        from src.workflow.step.step_generation_service import execution_context_to_simple_context
        from src.workflow.step.step_runner import run_steps
        simple_context = execution_context_to_simple_context(self.context)
        step_results = run_steps(json_steps, simple_context)

        # Note: step_results are no longer stored since we directly return CompositeRequest execution results

        # Check for errors in step results
        errors = []
        for i, result in enumerate(step_results):
            if not result.success and result.error_message:
                errors.append(f"Step {i}: {result.error_message}")

        if errors:
            return None, errors, []

        # Use the OPTIMIZED workflow generation
        from src.workflow.step.workflow import create_step_context_from_env_context, generate_workflow_from_json
        step_context = create_step_context_from_env_context(self.context)
        composite_request, workflow_errors, workflow_warnings = generate_workflow_from_json(json_steps, step_context, self.infrastructure)

        if workflow_errors:
            return None, workflow_errors, workflow_warnings

        # Return the optimized composite request directly
        return composite_request, [], workflow_warnings

    def _execute_preparation_phase(self, composite_request):
        """Execute environment preparation if needed."""
        preparation_results = []
        # TODO: Restore preparation functionality when PreparationExecutor is available
        return preparation_results, []

    def _execute_main_workflow(self, operations_composite, use_parallel=False, max_workers=4):
        """Execute the main workflow operations."""

        # Get logger from infrastructure
        from src.infrastructure.di_container import DIKey
        logger = self.infrastructure.resolve(DIKey.UNIFIED_LOGGER)

        unified_driver = UnifiedDriver(self.infrastructure, logger)

        # Check if composite request supports parallel execution
        if use_parallel and hasattr(operations_composite, 'execute_parallel'):
            execution_result = operations_composite.execute_parallel(unified_driver, max_workers=max_workers, logger=logger)
        else:
            execution_result = operations_composite.execute_operation(unified_driver, logger=logger)

        # CompositeRequest returns a list of results, so flatten if needed
        if isinstance(execution_result, list):
            results = execution_result
        else:
            results = [execution_result]

        # Return the results directly since they include all executed steps
        # (original JSON steps + dependency-resolved steps + optimized steps)
        return results

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
        if (hasattr(request, 'request_type') and request.request_type == RequestType.SHELL_REQUEST
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


"""Workflow execution service to replace the removed EnvWorkflowService
from src.core.workflow.workflow.step.workflow import create_step_context_from_env_context, generate_workflow_from_json
Integrates workflow building, fitting, and execution
"""

from typing import Optional

# 互換性維持: TypedExecutionConfigurationは依存性注入で提供される
# 互換性維持: infrastructure層への直接依存を削除、依存性注入で解決
# DebugLogger functionality now handled by src/logging UnifiedLogger
from src.operations.requests.request_types import RequestType
from src.operations.requests.request_factory import create_request
from src.domain.step import Step, StepType
from src.operations.results.__init__ import WorkflowExecutionResult


class WorkflowExecutionService:
    """Service for executing workflows with environment preparation
    Replaces the removed EnvWorkflowService
    """

    def __init__(self, context, infrastructure):
        """Initialize workflow execution service

        Args:
            context: Typed execution configuration
            infrastructure: Infrastructure container for drivers
        """
        self.context = context
        self.infrastructure = infrastructure

    def execute_workflow(self, parallel: Optional[bool], max_workers: Optional[int]) -> WorkflowExecutionResult:
        """Execute workflow based on context configuration

        Args:
            parallel: Whether to execute in parallel (overrides configuration if specified)
            max_workers: Maximum number of parallel workers (overrides configuration if specified)

        Returns:
            WorkflowExecutionResult with execution results
        """
        # Get parallel configuration from context
        parallel_config = self._get_parallel_config()

        # Override with parameters if specified - no fallback logic
        if parallel is not None:
            use_parallel = parallel
        else:
            use_parallel = parallel_config["enabled"]

        if max_workers is not None:
            use_max_workers = max_workers
        else:
            use_max_workers = parallel_config["max_workers"]

        # Store parallel config in context for request factories
        self.context._parallel_config = parallel_config

        # Log environment information if configured
        self._log_environment_info()

        # Prepare workflow (now returns optimized composite request)
        operations_composite, errors, warnings = self._prepare_workflow_steps()
        if errors:
            return self._create_error_result(errors, warnings, None)

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
        """Get workflow steps from context using injected config system"""
        try:
            # infrastructureから適切にconfig_managerを注入
            config_manager = self.infrastructure.resolve("config_manager")

            # steps設定のパスを構築
            steps_path = ['commands', self.context.command_type, 'steps']

            # steps設定を取得
            steps = config_manager.resolve_config(steps_path, list)
            self._debug_log(f"Found {len(steps)} steps for command '{self.context.command_type}'")

            return steps

        except (KeyError, TypeError) as e:
            # 設定が見つからない場合（互換性維持のコメント）
            self._debug_log(f"Failed to get workflow steps from new config system: {e}")
            self._debug_log(f"command_type={self.context.command_type}")
            raise

    def _get_parallel_config(self) -> dict:
        """Get parallel execution configuration from context using injected config system"""
        try:
            # infrastructureから適切にconfig_managerを注入
            config_manager = self.infrastructure.resolve("config_manager")

            # parallel設定のパスを構築
            parallel_path = ['commands', self.context.command_type, 'parallel']

            # parallel設定を取得
            enabled = config_manager.resolve_config([*parallel_path, 'enabled'], bool)
            max_workers = config_manager.resolve_config([*parallel_path, 'max_workers'], int)

            return {
                "enabled": enabled,
                "max_workers": max_workers
            }

        except (KeyError, TypeError) as e:
            # 設定が見つからない場合は明示的にエラーを発生させる
            self._debug_log(f"Failed to get parallel config: {e}")
            self._debug_log(f"command_type={self.context.command_type}")
            raise

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
        # Handle both merged and non-merged config structures
        if 'shared' in self.context.env_json:
            shared_config = self.context.env_json['shared']
        else:
            # For merged configs, shared settings are at the root level
            shared_config = self.context.env_json

        # Check if environment_logging exists - raise error if missing
        if 'environment_logging' not in shared_config:
            raise KeyError("Required environment_logging configuration not found in shared config")

        env_logging_config = shared_config['environment_logging']

        if not (env_logging_config['enabled']):
            return

        # Use unified logger from infrastructure container for environment logging
        # 互換性維持: infrastructure層への直接依存を削除、依存性注入で解決
        unified_logger = self.infrastructure.resolve("unified_logger")

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
        # Note: Step generation now handled by generate_workflow_from_json only

        # Use the OPTIMIZED workflow generation
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

        # Get logger and config manager from infrastructure
        # 互換性維持: infrastructure層への直接依存を削除、依存性注入で解決
        logger = self.infrastructure.resolve("unified_logger")
        self.infrastructure.resolve("config_manager")

        # UnifiedDriverは外部から注入されるべきです
        unified_driver = self.infrastructure.resolve("unified_driver")

        # Check if composite request supports parallel execution - no fallback
        if use_parallel:
            if not hasattr(operations_composite, 'execute_parallel'):
                raise AttributeError(f"Composite request {type(operations_composite)} does not support parallel execution")
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
        if not hasattr(result, 'request'):
            raise AttributeError(f"Result object {type(result)} does not have required 'request' attribute")
        request = result.request
        if request is None:
            raise ValueError("Result request is None")
        if not hasattr(request, 'allow_failure'):
            raise AttributeError(f"Request object {type(request)} does not have required 'allow_failure' attribute")
        allow_failure = request.allow_failure

        # Temporary workaround for TEST steps allow_failure issue
        if (hasattr(request, 'request_type') and request.request_type == RequestType.SHELL_REQUEST
            and hasattr(request, 'cmd') and request.cmd and len(request.cmd) > 0):
            full_cmd_str = str(request.cmd)
            if 'python3' in full_cmd_str and 'workspace/main.py' in full_cmd_str:
                allow_failure = True

        return allow_failure

    def _create_error_result(self, errors, warnings, preparation_results):
        """Create error result with consistent structure."""
        return WorkflowExecutionResult(
            success=False,
            results=[],
            preparation_results=preparation_results,
            errors=errors,
            warnings=warnings
        )

    def _debug_log(self, message: str):
        """Log debug message using infrastructure logger."""
        # 互換性維持: infrastructure層への直接依存を削除、依存性注入で解決
        logger = self.infrastructure.resolve("unified_logger")
        logger.debug(message)


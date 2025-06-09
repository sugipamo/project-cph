"""Command processor for handling file_preparation commands."""
import logging
from typing import Any, Dict, List, Optional, Tuple

from src.domain.constants.operation_type import OperationType
from src.domain.requests.base.base_request import BaseRequest
from src.domain.results.result import OperationResult

from .state_definitions import WorkflowContext, WorkflowState
from .state_manager import StateManager


class FilePreparationRequest(BaseRequest):
    """Request for executing state transitions."""

    def __init__(
        self,
        target_state: str,
        context_params: Dict[str, str],
        additional_actions: Optional[List[Dict[str, Any]]] = None,
        dry_run: bool = False
    ):
        """Initialize state transition request."""
        super().__init__()
        self.target_state = target_state
        self.context_params = context_params
        self.additional_actions = additional_actions or []
        self.dry_run = dry_run

    @property
    def operation_type(self) -> OperationType:
        """Return the operation type."""
        return OperationType.FILE_PREPARATION

    def _execute_core(self, driver) -> OperationResult:
        """Execute the state transition."""
        if driver is None:
            return OperationResult(
                op=self.operation_type,
                success=False,
                error_message="State transition requires a FilePreparationDriver"
            )

        # If driver is UnifiedDriver, resolve the actual FilePreparationDriver
        if hasattr(driver, '_get_cached_driver'):
            try:
                actual_driver = driver._get_cached_driver("file_preparation_driver")
                return actual_driver.execute_file_preparation(self)
            except Exception as e:
                return OperationResult(
                    op=self.operation_type,
                    success=False,
                    error_message=f"Failed to resolve file_preparation_driver: {e!s}"
                )

        # Check if driver has execute_file_preparation method
        if hasattr(driver, 'execute_file_preparation'):
            return driver.execute_file_preparation(self)
        return OperationResult(
            op=self.operation_type,
            success=False,
            error_message=f"Driver {type(driver).__name__} does not support state transitions"
        )


class FilePreparationDriver:
    """Driver for executing state transitions."""

    def __init__(self, state_manager: StateManager):
        """Initialize with state manager."""
        self.state_manager = state_manager
        self.logger = logging.getLogger(__name__)

    def execute_file_preparation(self, request: FilePreparationRequest) -> OperationResult:
        """Execute a state transition request."""
        try:
            # Parse target state
            target_state = WorkflowState(request.target_state)

            # Create target context
            target_context = WorkflowContext(
                contest_name=request.context_params.get("contest_name"),
                problem_name=request.context_params.get("problem_name"),
                language=request.context_params.get("language")
            )

            # Execute transition
            success, results = self.state_manager.execute_transition(
                target_state=target_state,
                target_context=target_context,
                dry_run=request.dry_run
            )

            result_message = "\\n".join(results)

            return OperationResult(
                op=request.operation_type,
                success=success,
                content=result_message,
                metadata={
                    "target_state": target_state.value,
                    "target_context": target_context.to_dict(),
                    "steps": results,
                    "additional_actions": len(request.additional_actions)
                }
            )

        except ValueError as e:
            return OperationResult(
                op=request.operation_type,
                success=False,
                error_message=f"Invalid state transition parameters: {e!s}"
            )
        except Exception as e:
            self.logger.error(f"State transition failed: {e!s}", exc_info=True)
            return OperationResult(
                op=request.operation_type,
                success=False,
                error_message=f"State transition failed: {e!s}"
            )


class CommandProcessor:
    """Processes commands with file_preparation support."""

    def __init__(self, operations, state_manager: StateManager):
        """Initialize command processor with DI container."""
        self.operations = operations
        self.state_manager = state_manager
        self.state_driver = FilePreparationDriver(state_manager)
        self.logger = logging.getLogger(__name__)

    def process_command(self, command_config: Dict[str, Any], context_vars: Dict[str, str]) -> Tuple[List[BaseRequest], Dict[str, Any]]:
        """Process a command configuration and return requests."""
        requests = []
        metadata = {
            "command_type": "unknown",
            "has_file_preparation": False,
            "additional_actions": 0
        }

        # Check if this is a state transition command
        if "file_preparation" in command_config:
            file_preparation = command_config["file_preparation"]
            metadata["command_type"] = "file_preparation"
            metadata["has_file_preparation"] = True

            # Create state transition request
            target_state = file_preparation.get("target", "working")
            context_params = file_preparation.get("context", {})

            # Resolve context parameters using context_vars
            resolved_context = {}
            for key, value in context_params.items():
                if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
                    var_name = value[1:-1]
                    resolved_context[key] = context_vars.get(var_name, value)
                else:
                    resolved_context[key] = value

            # Get additional actions
            additional_actions = command_config.get("additional_actions", [])
            metadata["additional_actions"] = len(additional_actions)

            # Create the state transition request
            transition_request = FilePreparationRequest(
                target_state=target_state,
                context_params=resolved_context,
                additional_actions=additional_actions
            )

            requests.append(transition_request)

            # Process additional actions as separate requests
            for action in additional_actions:
                action_request = self._create_action_request(action, context_vars)
                if action_request:
                    requests.append(action_request)

        # Handle legacy step-based commands
        elif "steps" in command_config:
            metadata["command_type"] = "legacy_steps"
            # Convert steps to requests (existing logic)
            for step in command_config["steps"]:
                step_request = self._create_step_request(step, context_vars)
                if step_request:
                    requests.append(step_request)

        # Handle simple action commands
        elif "action" in command_config:
            metadata["command_type"] = "simple_action"
            action_request = self._create_action_request(command_config["action"], context_vars)
            if action_request:
                requests.append(action_request)

        return requests, metadata

    def _create_action_request(self, action: Dict[str, Any], context_vars: Dict[str, str]) -> Optional[BaseRequest]:
        """Create a request from an action configuration."""
        action_type = action.get("type")

        if action_type == "python":
            from src.domain.requests.python.python_request import PythonRequest
            return PythonRequest(
                code_or_file=action.get("cmd", []),
                show_output=action.get("show_output", True)
            )

        if action_type == "shell":
            from src.domain.requests.shell.shell_request import ShellRequest
            return ShellRequest(
                cmd=action.get("cmd", []),
                allow_failure=action.get("allow_failure", False),
                cwd=action.get("cwd"),
                env=action.get("env")
            )

        if action_type == "oj":
            # Treat as shell request
            from src.domain.requests.shell.shell_request import ShellRequest
            return ShellRequest(
                cmd=action.get("cmd", []),
                allow_failure=action.get("allow_failure", False),
                cwd=action.get("cwd"),
                env=action.get("env")
            )

        if action_type == "file":
            from src.domain.requests.file.file_op_type import FileOpType
            from src.domain.requests.file.file_request import FileRequest

            file_op = action.get("operation", "copy")
            if file_op == "copy":
                return FileRequest(FileOpType.COPY, action.get("from"), action.get("to"))
            if file_op == "move":
                return FileRequest(FileOpType.MOVE, action.get("from"), action.get("to"))

        elif action_type == "show_state":
            # Special action for showing current state
            return StateShowRequest()

        return None

    def _create_step_request(self, step: Dict[str, Any], context_vars: Dict[str, str]) -> Optional[BaseRequest]:
        """Create a request from a legacy step configuration."""
        # This maintains compatibility with existing step-based commands
        return self._create_action_request(step, context_vars)

    def get_state_driver(self) -> FilePreparationDriver:
        """Get the state transition driver."""
        return self.state_driver


class StateShowRequest(BaseRequest):
    """Request to show current workflow state."""

    def __init__(self):
        """Initialize state show request."""
        super().__init__()

    @property
    def operation_type(self) -> OperationType:
        """Return the operation type."""
        return OperationType.STATE_SHOW

    def _execute_core(self, driver) -> OperationResult:
        """Execute the state show request."""
        if driver is None:
            return OperationResult(
                op=self.operation_type,
                success=False,
                error_message="State show requires a FilePreparationDriver"
            )

        try:
            summary = driver.state_manager.get_state_summary()

            # フォーマットされた出力を作成
            lines = []

            if summary["current_problem"]:
                lines.append(f"📍 現在の問題: {summary['current_problem']}")
                lines.append(f"📁 作業ディレクトリ: {summary['working_directory']}")
                if summary["has_unsaved_changes"]:
                    lines.append("⚠️  未保存の変更があります")
            else:
                lines.append("📍 現在作業中の問題はありません")

            if summary["available_problems"]:
                lines.append("\n📚 利用可能な問題:")
                for problem in sorted(summary["available_problems"]):
                    lines.append(f"   - {problem}")

            return OperationResult(
                op=self.operation_type,
                success=True,
                content="\n".join(lines),
                metadata=summary
            )

        except Exception as e:
            return OperationResult(
                op=self.operation_type,
                success=False,
                error_message=f"Failed to get state: {e!s}"
            )

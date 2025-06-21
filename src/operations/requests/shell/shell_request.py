"""Shell command execution request."""
import time
import uuid
from typing import Any, Optional, Union

from src.operations.constants.operation_type import OperationType
from src.operations.constants.request_types import RequestType
from src.operations.requests.base.base_request import OperationRequestFoundation
from src.operations.results.result import OperationResult


class ShellRequest(OperationRequestFoundation):
    """Request for executing shell commands."""

    def __init__(self, cmd: Union[str, list[str]], cwd: Optional[str],
                 env: Optional[dict[str, str]], inputdata: Optional[str],
                 timeout: Optional[int], debug_tag: Optional[str],
                 name: Optional[str], show_output: bool,
                 allow_failure: bool):
        super().__init__(name=name, debug_tag=debug_tag, _executed=False, _result=None, _debug_info=None)
        self.cmd = cmd
        self.cwd = cwd
        self.env = env
        self.inputdata = inputdata
        self.timeout = timeout
        self.show_output = show_output
        self.allow_failure = allow_failure

    @property
    def operation_type(self) -> OperationType:
        """Return the operation type."""
        return OperationType.SHELL

    @property
    def request_type(self) -> RequestType:
        """Return the request type for type-safe identification."""
        return RequestType.SHELL_REQUEST

    def _execute_core(self, driver: Any, logger: Optional[Any]) -> OperationResult:
        """Core execution logic for shell commands."""
        start_time = time.perf_counter()

        try:
            completed = self._execute_shell_command(driver, logger)
            end_time = time.perf_counter()
            return self._create_success_result(completed, start_time, end_time)
        except Exception as e:
            end_time = time.perf_counter()
            return self._create_error_result(e, driver, logger, start_time, end_time)

    def _execute_shell_command(self, driver: Any, logger: Optional[Any]):
        """Execute the shell command with retry logic."""
        from src.infrastructure.patterns.retry_decorator import COMMAND_RETRY_CONFIG, RetryableOperation
        # Create a new config with logger if provided
        config = COMMAND_RETRY_CONFIG
        if logger:
            config = RetryableOperation(config, logger).retry_config
        retryable = RetryableOperation(config, logger)

        def execute_command():
            actual_driver = self._get_actual_driver(driver)
            return actual_driver.execute_shell_command(
                self.cmd,
                cwd=self.cwd,
                env=self.env,
                inputdata=self.inputdata,
                timeout=self.timeout
            )

        return retryable.execute_with_retry(execute_command)

    def _get_actual_driver(self, driver: Any):
        """Get the actual driver, handling unified driver case."""
        if hasattr(driver, '_get_cached_driver') and callable(driver._get_cached_driver):
            return driver._get_cached_driver("shell_driver")
        return driver

    def _create_success_result(self, completed, start_time: float, end_time: float) -> OperationResult:
        """Create a successful operation result."""
        return OperationResult(
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
            request=self,
            cmd=self.cmd,
            start_time=start_time,
            end_time=end_time
        )

    def _create_error_result(self, e: Exception, driver: Any, logger: Optional[Any], start_time: float, end_time: float) -> OperationResult:
        """Create an error operation result with proper logging."""
        formatted_error = f"Shell command failed: {e}"

        if logger:
            from src.operations.exceptions.error_codes import classify_error
            error_code = classify_error(e)
            self._log_error(driver, e, error_code, logger)

        return OperationResult(
            stdout="",
            stderr=formatted_error,
            returncode=None,
            request=self,
            cmd=self.cmd,
            start_time=start_time,
            end_time=end_time
        )

    def _log_error(self, driver: Any, e: Exception, error_code, logger: Any):
        """Log error with correlation ID."""
        error_id = str(uuid.uuid4())[:8]
        if hasattr(logger, 'log_error_with_correlation'):
            logger.log_error_with_correlation(
                error_id, error_code.value, str(e),
                {'command': self.cmd, 'cwd': self.cwd}
            )
        else:
            logger.error(f"Shell command failed [{error_id}]: {e}")

    def __repr__(self) -> str:
        """String representation of the request."""
        return f"<ShellRequest cmd={self.cmd}>"

"""Shell command execution request."""
import time
import uuid
from typing import Any, Optional, Union

from src.domain.constants.operation_type import OperationType
from src.domain.requests.base.base_request import BaseRequest
from src.domain.results.result import OperationResult


class ShellRequest(BaseRequest):
    """Request for executing shell commands."""

    def __init__(self, cmd: Union[str, list[str]], cwd: Optional[str] = None,
                 env: Optional[dict[str, str]] = None, inputdata: Optional[str] = None,
                 timeout: Optional[int] = None, debug_tag: Optional[str] = None,
                 name: Optional[str] = None, show_output: bool = True,
                 allow_failure: bool = False):
        super().__init__(name=name, debug_tag=debug_tag)
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

    def _execute_core(self, driver: Any) -> OperationResult:
        """Core execution logic for shell commands."""
        start_time = time.perf_counter()

        try:
            completed = self._execute_shell_command(driver)
            end_time = time.perf_counter()
            return self._create_success_result(completed, start_time, end_time)
        except Exception as e:
            end_time = time.perf_counter()
            return self._create_error_result(e, driver, start_time, end_time)

    def _execute_shell_command(self, driver: Any):
        """Execute the shell command with retry logic."""
        from src.utils.retry_decorator import COMMAND_RETRY_CONFIG, RetryableOperation
        retryable = RetryableOperation(COMMAND_RETRY_CONFIG)

        def execute_command():
            actual_driver = self._get_actual_driver(driver)
            return actual_driver.run(
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

    def _create_error_result(self, e: Exception, driver: Any, start_time: float, end_time: float) -> OperationResult:
        """Create an error operation result with proper logging."""
        from src.domain.exceptions.error_codes import ErrorSuggestion, classify_error
        error_code = classify_error(e, "shell command")
        suggestion = ErrorSuggestion.get_suggestion(error_code)
        formatted_error = f"Shell command failed: {e}\nError Code: {error_code.value}\nSuggestion: {suggestion}"

        self._log_error(driver, e, error_code)

        return OperationResult(
            stdout="",
            stderr=formatted_error,
            returncode=None,
            request=self,
            cmd=self.cmd,
            start_time=start_time,
            end_time=end_time
        )

    def _log_error(self, driver: Any, e: Exception, error_code):
        """Log error with correlation ID."""
        error_id = str(uuid.uuid4())[:8]
        try:
            if hasattr(driver, 'logger') and hasattr(driver.logger, 'log_error_with_correlation'):
                driver.logger.log_error_with_correlation(
                    error_id, error_code.value, str(e),
                    {'command': self.cmd, 'cwd': self.cwd}
                )
        except Exception:
            import logging
            logging.error(f"Shell command failed [{error_id}]: {e}")

    def __repr__(self) -> str:
        """String representation of the request."""
        return f"<ShellRequest cmd={self.cmd}>"

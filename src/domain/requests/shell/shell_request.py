"""Shell command execution request."""
import time
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
        """Core execution logic for shell commands.

        Performance optimizations:
        - More precise timing with perf_counter
        - Optimized imports
        """
        start_time = time.perf_counter()
        try:
            # Handle unified driver case using duck typing
            actual_driver = driver
            if hasattr(driver, '_get_cached_driver') and callable(driver._get_cached_driver):
                actual_driver = driver._get_cached_driver("shell_driver")

            # Use the shell driver to run the command
            completed = actual_driver.run(
                self.cmd,
                cwd=self.cwd,
                env=self.env,
                inputdata=self.inputdata,
                timeout=self.timeout
            )
            end_time = time.perf_counter()
            return OperationResult(
                stdout=completed.stdout,
                stderr=completed.stderr,
                returncode=completed.returncode,
                request=self,
                cmd=self.cmd,
                start_time=start_time,
                end_time=end_time
            )
        except Exception as e:
            end_time = time.perf_counter()
            return OperationResult(
                stdout="",
                stderr=str(e),
                returncode=None,
                request=self,
                cmd=self.cmd,
                start_time=start_time,
                end_time=end_time
            )

    def __repr__(self) -> str:
        """String representation of the request."""
        return f"<ShellRequest cmd={self.cmd}>"

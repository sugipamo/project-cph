"""Python code execution request."""
from typing import Any, Optional, Union

from src.operations.constants.operation_type import OperationType
from src.operations.requests.request_factory import OperationRequestFoundation
from src.operations.requests.request_types import RequestType
from src.operations.results.result import OperationResult


class PythonRequest(OperationRequestFoundation):
    """Request for executing Python code or scripts."""

    _require_driver = True

    def __init__(self, code_or_file: Union[str, list[str]], cwd: Optional[str],
                 show_output: bool, name: Optional[str],
                 debug_tag: Optional[str], allow_failure: bool,
                 os_provider: Any, python_utils: Any, time_ops: Any):
        super().__init__(name=name, debug_tag=debug_tag)
        self.code_or_file = code_or_file  # Code string or filename
        self.cwd = cwd
        self.show_output = show_output
        self.allow_failure = allow_failure

        # Infrastructure services injected from main.py
        self._os_provider = os_provider
        self._python_utils = python_utils
        self._time_ops = time_ops

    def _get_os_provider(self, driver):
        """Get OS provider from injected dependency."""
        return self._os_provider

    @property
    def operation_type(self) -> OperationType:
        return OperationType.PYTHON

    @property
    def request_type(self) -> RequestType:
        return RequestType.PYTHON_REQUEST

    def _execute_core(self, driver: Any = None, logger: Optional[Any] = None) -> OperationResult:
        os_provider = self._get_os_provider(driver)
        start_time = self._time_ops.current_time()
        old_cwd = os_provider.getcwd()

        try:
            if self.cwd:
                os_provider.chdir(self.cwd)

            if logger:
                logger.debug(f"Executing Python code: {self.code_or_file}")
            stdout, stderr, returncode = self._execute_python_code(driver)
            end_time = self._time_ops.current_time()

            return OperationResult(
                success=returncode == 0,
                returncode=returncode,
                stdout=stdout,
                stderr=stderr,
                content=None,
                exists=None,
                path=None,
                op=self.operation_type,
                cmd=None,
                request=self,
                start_time=start_time,
                end_time=end_time,
                error_message=None if returncode == 0 else stderr,
                exception=None,
                metadata={},
                skipped=False
            )

        except Exception as e:
            end_time = self._time_ops.current_time()
            if logger:
                logger.error(f"Python execution failed: {e}")
            return OperationResult(
                success=False,
                returncode=1,
                stdout="",
                stderr=str(e),
                content=None,
                exists=None,
                path=None,
                op=self.operation_type,
                cmd=None,
                request=self,
                start_time=start_time,
                end_time=end_time,
                error_message=str(e),
                exception=e,
                metadata={},
                skipped=False
            )
        finally:
            if self.cwd:
                os_provider.chdir(old_cwd)

    def _execute_python_code(self, driver: Any) -> tuple[str, str, int]:
        """Execute Python code using appropriate driver."""
        # Try different driver resolution strategies
        if driver and hasattr(driver, 'python_driver'):
            return self._execute_with_direct_driver(driver.python_driver)
        if driver and hasattr(driver, 'resolve') and callable(driver.resolve):
            python_driver = driver.resolve('python_driver')
            return self._execute_with_direct_driver(python_driver)

        raise ValueError("No valid python driver found")

    def _execute_with_direct_driver(self, python_driver: Any) -> tuple[str, str, int]:
        """Execute Python code using direct python driver."""
        is_script = self._determine_script_type(python_driver)

        if is_script:
            return python_driver.run_script_file(self.code_or_file[0], cwd=self.cwd)
        code = self._prepare_code_string()
        return python_driver.run_code_string(code, cwd=self.cwd)


    def _determine_script_type(self, python_driver: Any) -> bool:
        """Determine if the code_or_file represents a script file."""
        if hasattr(python_driver, 'is_script_file'):
            return python_driver.is_script_file(self.code_or_file)

        # Driver does not support is_script_file, use injected python_utils
        if isinstance(self.code_or_file, list):
            return self._python_utils.is_script_file(self.code_or_file)
        return self._python_utils.is_script_file([self.code_or_file])

    def _prepare_code_string(self) -> str:
        """Prepare code string from code_or_file input."""
        if isinstance(self.code_or_file, list):
            return "\n".join(self.code_or_file)
        return self.code_or_file

    def __repr__(self) -> str:
        return f"<PythonRequest code_or_file={self.code_or_file}>"

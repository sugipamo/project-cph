"""Python code execution request."""
import time
from typing import Any, Optional, Union

from src.infrastructure.drivers.python.utils.python_utils import PythonUtils
from src.operations.constants.operation_type import OperationType
from src.operations.requests.base.base_request import OperationRequestFoundation
from src.operations.results.result import OperationResult


class PythonRequest(OperationRequestFoundation):
    """Request for executing Python code or scripts."""

    _require_driver = True

    def __init__(self, code_or_file: Union[str, list[str]], cwd: Optional[str] = None,
                 show_output: bool = True, name: Optional[str] = None,
                 debug_tag: Optional[str] = None):
        super().__init__(name=name, debug_tag=debug_tag)
        self.code_or_file = code_or_file  # Code string or filename
        self.cwd = cwd
        self.show_output = show_output

    @property
    def operation_type(self) -> OperationType:
        return OperationType.PYTHON

    def _execute_core(self, driver: Any = None, logger: Optional[Any] = None) -> OperationResult:
        import os
        start_time = time.time()
        old_cwd = os.getcwd()

        try:
            if self.cwd:
                os.chdir(self.cwd)

            if logger:
                logger.debug(f"Executing Python code: {self.code_or_file}")
            stdout, stderr, returncode = self._execute_python_code(driver)
            end_time = time.time()

            return OperationResult(
                stdout=stdout,
                stderr=stderr,
                returncode=returncode,
                request=self,
                start_time=start_time,
                end_time=end_time
            )

        except Exception as e:
            end_time = time.time()
            if logger:
                logger.error(f"Python execution failed: {e}")
            return OperationResult(
                stdout="",
                stderr=str(e),
                returncode=1,
                request=self,
                start_time=start_time,
                end_time=end_time,
                error_message=str(e)
            )
        finally:
            if self.cwd:
                os.chdir(old_cwd)

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
        
        # Driver does not support is_script_file, use PythonUtils as last resort
        return PythonUtils.is_script_file(self.code_or_file)

    def _prepare_code_string(self) -> str:
        """Prepare code string from code_or_file input."""
        if isinstance(self.code_or_file, list):
            return "\n".join(self.code_or_file)
        return self.code_or_file

    def __repr__(self) -> str:
        return f"<PythonRequest code_or_file={self.code_or_file}>"

"""Python code execution driver."""
from abc import abstractmethod
from typing import Any, Optional

from src.configuration.config_manager import TypeSafeConfigNodeManager
from src.infrastructure.drivers.base.base_driver import ExecutionDriverInterface
from src.infrastructure.drivers.python.utils.python_utils import PythonUtils


class PythonDriver(ExecutionDriverInterface):
    """Abstract base class for Python code execution."""

    def __init__(self, config_manager: TypeSafeConfigNodeManager):
        """Initialize PythonDriver with configuration manager."""
        self.config_manager = config_manager
        self.python_utils = PythonUtils(self.config_manager)

    @abstractmethod
    def run_code_string(self, code: str, cwd: Optional[str]) -> tuple[str, str, int]:
        """Execute Python code string.

        Args:
            code: Python code to execute
            cwd: Working directory

        Returns:
            Tuple of (stdout, stderr, return_code)
        """

    @abstractmethod
    def run_script_file(self, file_path: str, cwd: Optional[str]) -> tuple[str, str, int]:
        """Execute Python script file.

        Args:
            file_path: Path to Python script
            cwd: Working directory

        Returns:
            Tuple of (stdout, stderr, return_code)
        """

    def execute_command(self, request: Any) -> Any:
        """Execute a Python request."""
        if hasattr(request, 'code_or_file'):
            if self.python_utils.is_script_file(request.code_or_file):
                return self.run_script_file(
                    request.code_or_file[0],
                    cwd=getattr(request, 'cwd', None)
                )
            if isinstance(request.code_or_file, list):
                code = "\n".join(request.code_or_file)
            else:
                code = request.code_or_file
            return self.run_code_string(
                code,
                cwd=getattr(request, 'cwd', None)
            )
        raise ValueError("Invalid request type for PythonDriver")

    def validate(self, request: Any) -> bool:
        """Validate if this driver can handle the request."""
        return hasattr(request, 'code_or_file')


class LocalPythonDriver(PythonDriver):
    """Local Python execution driver using subprocess."""

    def __init__(self, config_manager: TypeSafeConfigNodeManager):
        """Initialize LocalPythonDriver with configuration manager."""
        super().__init__(config_manager)

    def run_code_string(self, code: str, cwd: Optional[str]) -> tuple[str, str, int]:
        """Execute Python code string using subprocess."""
        return self.python_utils.run_code_string(code, cwd)

    def run_script_file(self, file_path: str, cwd: Optional[str]) -> tuple[str, str, int]:
        """Execute Python script file using subprocess."""
        return self.python_utils.run_script_file(file_path, cwd)

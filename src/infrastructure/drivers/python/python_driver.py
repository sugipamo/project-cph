"""Python code execution driver."""
import subprocess
import sys
from abc import abstractmethod
from typing import Any, Optional

from src.infrastructure.drivers.base.base_driver import BaseDriver
from src.infrastructure.drivers.python.utils.python_utils import PythonUtils


class PythonDriver(BaseDriver):
    """Abstract base class for Python code execution."""

    @abstractmethod
    def run_code_string(self, code: str, cwd: Optional[str] = None) -> tuple[str, str, int]:
        """Execute Python code string.

        Args:
            code: Python code to execute
            cwd: Working directory

        Returns:
            Tuple of (stdout, stderr, return_code)
        """

    @abstractmethod
    def run_script_file(self, file_path: str, cwd: Optional[str] = None) -> tuple[str, str, int]:
        """Execute Python script file.

        Args:
            file_path: Path to Python script
            cwd: Working directory

        Returns:
            Tuple of (stdout, stderr, return_code)
        """

    def execute(self, request: Any) -> Any:
        """Execute a Python request."""
        if hasattr(request, 'code_or_file'):
            if PythonUtils.is_script_file(request.code_or_file):
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

    def run_code_string(self, code: str, cwd: Optional[str] = None) -> tuple[str, str, int]:
        """Execute Python code string using subprocess."""
        result = subprocess.run(
            [sys.executable, '-c', code],
            cwd=cwd,
            capture_output=True,
            text=True, check=False
        )

        return result.stdout, result.stderr, result.returncode

    def run_script_file(self, file_path: str, cwd: Optional[str] = None) -> tuple[str, str, int]:
        """Execute Python script file using subprocess."""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, file_path],
            cwd=cwd,
            capture_output=True,
            text=True, check=False
        )

        return result.stdout, result.stderr, result.returncode

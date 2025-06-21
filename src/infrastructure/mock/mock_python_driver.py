"""Mock python driver for testing."""
from typing import Optional

from src.infrastructure.drivers.python.python_driver import PythonDriver


class MockPythonDriver(PythonDriver):
    """Mock implementation of python driver for testing."""

    def __init__(self):
        """Initialize mock python driver."""
        self._code_executed = []
        self._files_executed = []
        self._responses = {}  # code/file -> (stdout, stderr, returncode)
        self._default_response = ("mock python output", "", 0)

    def run_code_string(self, code: str, cwd: Optional[str]) -> tuple[str, str, int]:
        """Execute Python code string (mocked).

        Args:
            code: Python code to execute
            cwd: Working directory

        Returns:
            Tuple of (stdout, stderr, returncode)
        """
        self._code_executed.append({
            'code': code,
            'cwd': cwd,
            'type': 'string'
        })

        return self._responses[code]

    def run_script_file(self, file_path: str, cwd: Optional[str]) -> tuple[str, str, int]:
        """Execute Python script file (mocked).

        Args:
            file_path: Path to Python script
            cwd: Working directory

        Returns:
            Tuple of (stdout, stderr, returncode)
        """
        self._files_executed.append({
            'file_path': file_path,
            'cwd': cwd,
            'type': 'file'
        })

        return self._responses[file_path]

    def is_script_file(self, code_or_file) -> bool:
        """Check if input is a script file (mocked).

        Args:
            code_or_file: Code string or file path

        Returns:
            True if it looks like a file path
        """
        if isinstance(code_or_file, list) and len(code_or_file) == 1:
            return code_or_file[0].endswith('.py')
        if isinstance(code_or_file, str):
            return code_or_file.endswith('.py')
        return False

    def set_response(self, code_or_file: str, stdout: str, stderr: str,
                    returncode: int) -> None:
        """Set predefined response for code or file.

        Args:
            code_or_file: Code string or file path
            stdout: Standard output to return
            stderr: Standard error to return
            returncode: Return code to return
        """
        self._responses[code_or_file] = (stdout, stderr, returncode)

    def set_default_response(self, stdout: str, stderr: str,
                           returncode: int) -> None:
        """Set default response for unknown code/files.

        Args:
            stdout: Default standard output
            stderr: Default standard error
            returncode: Default return code
        """
        self._default_response = (stdout, stderr, returncode)

    def get_executed_code(self) -> list[dict]:
        """Get list of executed code strings.

        Returns:
            List of code execution details
        """
        return list(self._code_executed)

    def get_executed_files(self) -> list[dict]:
        """Get list of executed files.

        Returns:
            List of file execution details
        """
        return list(self._files_executed)

    def get_all_executions(self) -> list[dict]:
        """Get all executions (code and files).

        Returns:
            List of all execution details
        """
        return self._code_executed + self._files_executed

    def clear_history(self) -> None:
        """Clear execution history."""
        self._code_executed.clear()
        self._files_executed.clear()

    def was_code_executed(self, code: str) -> bool:
        """Check if specific code was executed.

        Args:
            code: Code to check

        Returns:
            True if code was executed
        """
        return any(item['code'] == code for item in self._code_executed)

    def was_file_executed(self, file_path: str) -> bool:
        """Check if specific file was executed.

        Args:
            file_path: File path to check

        Returns:
            True if file was executed
        """
        return any(item['file_path'] == file_path for item in self._files_executed)

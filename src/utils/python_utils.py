"""Python utilities for code execution and file handling."""
import contextlib
import io
import pathlib
import subprocess
import traceback
from typing import Optional

# 互換性維持: configuration層への逆方向依存を削除、依存性注入で解決
from src.operations.python_exceptions import (
    PythonConfigError,
    PythonInterpreterError,
)


class PythonUtils:
    """Utility class for Python code operations."""
    def __init__(self, config_provider):
        """Initialize PythonUtils with configuration provider.
        Args:
            config_provider: Configuration provider instance
        """
        self.config_provider = config_provider
        self._python_interpreter = None
    def is_script_file(self, code_or_file: list[str]) -> bool:
        """Determine if code_or_file is a script file.
        Args:
            code_or_file: List of strings (if single element, might be a filename)
        Returns:
            True if it's a file, False otherwise
        """
        return len(code_or_file) == 1 and pathlib.Path(code_or_file[0]).is_file()
    def run_script_file(self, filename: str, cwd: Optional[str]) -> tuple[str, str, int]:
        """Run Python script file.
        Args:
            filename: Script filename
            cwd: Working directory
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        python_interpreter = self._get_python_interpreter()
        result = subprocess.run([
            python_interpreter, filename
        ], capture_output=True, text=True, cwd=cwd, check=False)
        return result.stdout, result.stderr, result.returncode
    def run_code_string(self, code: str, cwd: Optional[str]) -> tuple[str, str, int]:
        """Run Python code string.
        Args:
            code: Python code to execute
            cwd: Working directory (unused for exec)
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        returncode = 0
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            try:
                exec(code, {})
            except Exception as e:
                traceback.print_exc(file=buf_err)
                returncode = self._get_error_return_code(e)
        return buf_out.getvalue(), buf_err.getvalue(), returncode
    def _get_python_interpreter(self) -> str:
        """Get the Python interpreter to use.
        Returns:
            Path to Python interpreter
        Raises:
            PythonInterpreterError: If no suitable interpreter is found
        """
        if self._python_interpreter is not None:
            return self._python_interpreter
        try:
            default_interpreter = self.config_manager.resolve_config(
                ['python_config', 'interpreters', 'default'], str
            )
        except KeyError as e:
            raise PythonConfigError("No default Python interpreter configured") from e
        # フォールバック処理は禁止、必要なエラーを見逃すことになる
        try:
            alternatives = self.config_manager.resolve_config(
                ['python_config', 'interpreters', 'alternatives'], list
            )
        except KeyError as e:
            raise RuntimeError("Python interpreters alternatives configuration is required") from e
        # Try to find a working interpreter
        for interpreter in [default_interpreter, *alternatives]:
            if self._test_interpreter(interpreter):
                self._python_interpreter = interpreter
                return interpreter
        raise PythonInterpreterError(
            f"No working Python interpreter found. Tried: {[default_interpreter, *alternatives]}"
        )
    def _test_interpreter(self, interpreter: str) -> bool:
        """Test if an interpreter is available and working.
        Args:
            interpreter: Path to interpreter to test
        Returns:
            True if interpreter is working, False otherwise
        """
        try:
            result = subprocess.run(
                [interpreter, '--version'],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            raise PythonConfigError(f"Failed to validate Python interpreter: {e}") from e
    def _get_error_return_code(self, exception: Exception) -> int:
        """Get appropriate return code based on exception type.
        Args:
            exception: The exception that occurred
        Returns:
            Appropriate return code
        """
        try:
            self.config_manager.resolve_config(
                ['python_config', 'error_handling'], dict
            )
            if isinstance(exception, SyntaxError):
                return 2  # Syntax error
            if isinstance(exception, ImportError):
                return 3  # Import error
            if isinstance(exception, KeyboardInterrupt):
                return 128 + 2  # SIGINT
            return 1  # General error
        except KeyError as e:
            raise PythonConfigError(f"Error code configuration not found: {e}") from e

"""Python utilities for code execution and file handling."""
import pathlib
import subprocess
import contextlib
import io
import traceback
from typing import List, Tuple, Optional


class PythonUtils:
    """Utility class for Python code operations."""
    
    @staticmethod
    def is_script_file(code_or_file: List[str]) -> bool:
        """
        Determine if code_or_file is a script file.
        
        Args:
            code_or_file: List of strings (if single element, might be a filename)
            
        Returns:
            True if it's a file, False otherwise
        """
        return len(code_or_file) == 1 and pathlib.Path(code_or_file[0]).is_file()

    @staticmethod
    def run_script_file(filename: str, cwd: Optional[str] = None) -> Tuple[str, str, int]:
        """
        Run Python script file.
        
        Args:
            filename: Script filename
            cwd: Working directory
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        result = subprocess.run([
            subprocess.getoutput('which python3') or 'python3', filename
        ], capture_output=True, text=True, cwd=cwd)
        return result.stdout, result.stderr, result.returncode

    @staticmethod
    def run_code_string(code: str, cwd: Optional[str] = None) -> Tuple[str, str, int]:
        """
        Run Python code string.
        
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
            except Exception:
                traceback.print_exc(file=buf_err)
                returncode = 1
        return buf_out.getvalue(), buf_err.getvalue(), returncode
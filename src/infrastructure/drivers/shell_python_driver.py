"""Unified driver for shell and Python command execution."""
from abc import abstractmethod
from pathlib import Path
from typing import Any, Optional, Union

from src.infrastructure.drivers.base_driver import BaseDriverImplementation
from src.utils.python_utils import PythonUtils
from src.utils.shell_utils import ShellUtils


class ShellPythonDriver(BaseDriverImplementation):
    """Combined driver for shell and Python command execution."""

    def __init__(self, config_manager: Any, file_driver: Any, container=None):
        """Initialize with config manager and file driver."""
        super().__init__(container)
        self.config_manager = config_manager
        self.file_driver = file_driver
        self.python_utils = PythonUtils(self.config_manager)

    def _get_typed_default(self, key_path: str, default_type: type) -> Any:
        """Get typed default value from infrastructure defaults.
        
        Args:
            key_path: Dot-separated path (e.g., 'infrastructure_defaults.shell.timeout')
            default_type: Expected type of the value
            
        Returns:
            Default value of the specified type
        """
        # Convert list path to dot notation
        value = self._get_default_value(key_path)
        
        # Type-specific defaults if value is None
        if value is None:
            if default_type is dict:
                return {}
            elif default_type is int:
                return 30
            elif default_type is str:
                return ""
                
        return value

    @abstractmethod
    def execute_shell_command(self, cmd: Union[str, list[str]], cwd: Optional[str] = None,
                            env: Optional[dict[str, str]] = None, inputdata: Optional[str] = None,
                            timeout: Optional[int] = None) -> Any:
        """Execute a shell command."""

    @abstractmethod
    def run_python_code(self, code: str, cwd: Optional[str]) -> tuple[str, str, int]:
        """Execute Python code string."""

    @abstractmethod
    def run_python_script(self, file_path: str, cwd: Optional[str]) -> tuple[str, str, int]:
        """Execute Python script file."""

    def execute_command(self, request: Any) -> Any:
        """Execute a shell or Python request."""
        # Handle shell requests
        if hasattr(request, 'cmd'):
            return self.execute_shell_command(
                cmd=request.cmd,
                cwd=request.cwd if hasattr(request, 'cwd') else self._get_typed_default('infrastructure_defaults.shell.cwd', type(None)),
                env=request.env if hasattr(request, 'env') else self._get_typed_default('infrastructure_defaults.shell.env', dict),
                inputdata=request.inputdata if hasattr(request, 'inputdata') else self._get_typed_default('infrastructure_defaults.shell.inputdata', type(None)),
                timeout=request.timeout if hasattr(request, 'timeout') else self._get_typed_default('infrastructure_defaults.shell.timeout', int)
            )
        
        # Handle Python requests
        if hasattr(request, 'code_or_file'):
            cwd = request.cwd if hasattr(request, 'cwd') else self._get_typed_default('infrastructure_defaults.python.cwd', type(None))
            
            if self.python_utils.is_script_file(request.code_or_file):
                return self.run_python_script(request.code_or_file[0], cwd)
            
            code = "\n".join(request.code_or_file) if isinstance(request.code_or_file, list) else request.code_or_file
            return self.run_python_code(code, cwd)
        
        raise ValueError("Invalid request type for ShellPythonDriver")

    def validate(self, request: Any) -> bool:
        """Validate if this driver can handle the request."""
        return hasattr(request, 'cmd') or hasattr(request, 'code_or_file')



class LocalShellPythonDriver(ShellPythonDriver):
    """Local implementation of shell and Python execution driver."""

    def execute_shell_command(self, cmd: Union[str, list[str]], cwd: Optional[str] = None,
                            env: Optional[dict[str, str]] = None, inputdata: Optional[str] = None,
                            timeout: Optional[int] = None) -> Any:
        """Execute a shell command using subprocess."""
        # Create cwd directory if specified
        if cwd:
            cwd_path = Path(cwd)
            if not cwd_path.exists():
                self.file_driver.makedirs(cwd_path, exist_ok=True)

        return ShellUtils.run_subprocess(
            cmd=cmd,
            cwd=cwd,
            env=env,
            inputdata=inputdata,
            timeout=timeout
        )

    def run_python_code(self, code: str, cwd: Optional[str]) -> tuple[str, str, int]:
        """Execute Python code string using subprocess."""
        return self.python_utils.run_code_string(code, cwd)

    def run_python_script(self, file_path: str, cwd: Optional[str]) -> tuple[str, str, int]:
        """Execute Python script file using subprocess."""
        return self.python_utils.run_script_file(file_path, cwd)
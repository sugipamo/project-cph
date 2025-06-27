"""Unified driver for shell and Python command execution."""
import json
from abc import abstractmethod
from pathlib import Path
from typing import Any, Optional, Union

from src.infrastructure.drivers.generic.base_driver import ExecutionDriverInterface
from src.utils.python_utils import PythonUtils
from src.utils.shell_utils import ShellUtils


class ShellPythonDriver(ExecutionDriverInterface):
    """Combined driver for shell and Python command execution."""

    def __init__(self, config_manager: Any, file_driver: Any):
        """Initialize with config manager and file driver."""
        self.config_manager = config_manager
        self.file_driver = file_driver
        self.python_utils = PythonUtils(self.config_manager)
        self._infrastructure_defaults = self._load_infrastructure_defaults()

    def _load_infrastructure_defaults(self) -> dict[str, Any]:
        """Load infrastructure defaults from config file."""
        try:
            config_path = Path(__file__).parents[3] / "config" / "system" / "infrastructure_defaults.json"
            with open(config_path, encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "infrastructure_defaults": {
                    "shell": {"cwd": None, "env": {}, "inputdata": None, "timeout": 30},
                    "python": {"cwd": None}
                }
            }

    def _get_default_value(self, path: list[str], default_type: type) -> Any:
        """Get default value from infrastructure defaults."""
        current = self._infrastructure_defaults
        try:
            for key in path:
                current = current[key]
            if isinstance(current, default_type) or (default_type is type(None) and current is None):
                return current
        except (KeyError, TypeError):
            pass
        
        if default_type is dict:
            return {}
        if default_type is int:
            return 30
        return None

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
                cwd=request.cwd if hasattr(request, 'cwd') else self._get_default_value(['infrastructure_defaults', 'shell', 'cwd'], type(None)),
                env=request.env if hasattr(request, 'env') else self._get_default_value(['infrastructure_defaults', 'shell', 'env'], dict),
                inputdata=request.inputdata if hasattr(request, 'inputdata') else self._get_default_value(['infrastructure_defaults', 'shell', 'inputdata'], type(None)),
                timeout=request.timeout if hasattr(request, 'timeout') else self._get_default_value(['infrastructure_defaults', 'shell', 'timeout'], int)
            )
        
        # Handle Python requests
        if hasattr(request, 'code_or_file'):
            cwd = request.cwd if hasattr(request, 'cwd') else self._get_default_value(['infrastructure_defaults', 'python', 'cwd'], type(None))
            
            if self.python_utils.is_script_file(request.code_or_file):
                return self.run_python_script(request.code_or_file[0], cwd)
            
            code = "\n".join(request.code_or_file) if isinstance(request.code_or_file, list) else request.code_or_file
            return self.run_python_code(code, cwd)
        
        raise ValueError("Invalid request type for ShellPythonDriver")

    def validate(self, request: Any) -> bool:
        """Validate if this driver can handle the request."""
        return hasattr(request, 'cmd') or hasattr(request, 'code_or_file')

    def initialize(self) -> None:
        """Initialize the driver."""
        pass

    def cleanup(self) -> None:
        """Clean up resources."""
        pass


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
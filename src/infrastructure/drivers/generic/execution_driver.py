"""Consolidated execution driver for shell and Python commands."""
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.infrastructure.di_container import DIContainer
from src.infrastructure.drivers.generic.base_driver import BaseDriverImplementation
from src.utils.python_utils import PythonUtils
from src.utils.shell_utils import ShellUtils


class ExecutionDriver(BaseDriverImplementation):
    """Unified driver for shell and Python command execution."""

    def __init__(self, config_manager: Any, file_driver: Any,
                 container: Optional[DIContainer]):
        """Initialize execution driver.
        
        Args:
            config_manager: Configuration manager
            file_driver: File driver for filesystem operations
            container: Optional DI container for dependency resolution
        """
        super().__init__(container)
        self.config_manager = config_manager
        self.file_driver = file_driver
        self.python_utils = PythonUtils(self.config_manager)

    def execute_command(self, request: Any) -> Any:
        """Execute a shell or Python request.
        
        Routes to appropriate method based on request type.
        """
        # Handle shell requests
        if hasattr(request, 'cmd'):
            # Get values from request or config
            cwd = request.cwd if hasattr(request, 'cwd') and request.cwd is not None else self._get_default_value("infrastructure_defaults.shell.cwd")
            env = request.env if hasattr(request, 'env') and request.env is not None else self._get_default_value("infrastructure_defaults.shell.env")
            inputdata = request.inputdata if hasattr(request, 'inputdata') and request.inputdata is not None else self._get_default_value("infrastructure_defaults.shell.inputdata")
            timeout = request.timeout if hasattr(request, 'timeout') and request.timeout is not None else self._get_default_value("infrastructure_defaults.shell.timeout")
            
            return self.execute_shell_command(
                cmd=request.cmd,
                cwd=cwd,
                env=env,
                inputdata=inputdata,
                timeout=timeout
            )

        # Handle Python requests
        if hasattr(request, 'code_or_file'):
            cwd = request.cwd if hasattr(request, 'cwd') and request.cwd is not None else self._get_default_value("infrastructure_defaults.python.cwd")

            if self.python_utils.is_script_file(request.code_or_file):
                return self.run_python_script(request.code_or_file[0], cwd)

            code = "\n".join(request.code_or_file) if isinstance(request.code_or_file, list) else request.code_or_file
            return self.run_python_code(code, cwd)

        raise ValueError("Invalid request type for ExecutionDriver")

    def validate(self, request: Any) -> bool:
        """Validate if this driver can handle the request."""
        return hasattr(request, 'cmd') or hasattr(request, 'code_or_file')

    def execute_shell_command(self,
                            cmd: Union[str, List[str]],
                            cwd: Optional[str],
                            env: Optional[Dict[str, str]],
                            inputdata: Optional[str],
                            timeout: Optional[int]) -> Any:
        """Execute a shell command using subprocess.
        
        Args:
            cmd: Command to execute (string or list)
            cwd: Working directory
            env: Environment variables
            inputdata: Input data to send to process
            timeout: Command timeout in seconds
            
        Returns:
            Execution result
        """
        # Ensure we have valid values (cwd can be None from config)
        if cwd is None:
            cwd = "."
        if inputdata is None:
            inputdata = ""

        # Create cwd directory if specified and doesn't exist
        if cwd:
            cwd_path = Path(cwd)
            if not cwd_path.exists():
                self.log_debug(f"Creating working directory: {cwd_path}")
                self.file_driver.makedirs(cwd_path, exist_ok=True)

        self.log_info("Executing shell command", cmd=cmd if isinstance(cmd, str) else " ".join(cmd))

        return ShellUtils.run_subprocess(
            cmd=cmd,
            cwd=cwd,
            env=env,
            inputdata=inputdata,
            timeout=timeout
        )

    def run_python_code(self, code: str, cwd: Optional[str]) -> Tuple[str, str, int]:
        """Execute Python code string using subprocess.
        
        Args:
            code: Python code to execute
            cwd: Working directory
            
        Returns:
            Tuple of (stdout, stderr, returncode)
        """
        if cwd is None:
            cwd = self._get_default_value("infrastructure_defaults.python.cwd")

        self.log_info("Executing Python code", code_length=len(code))

        return self.python_utils.run_code_string(code, cwd)

    def run_python_script(self, file_path: str, cwd: Optional[str]) -> Tuple[str, str, int]:
        """Execute Python script file using subprocess.
        
        Args:
            file_path: Path to Python script
            cwd: Working directory
            
        Returns:
            Tuple of (stdout, stderr, returncode)
        """
        if cwd is None:
            cwd = self._get_default_value("infrastructure_defaults.python.cwd")

        self.log_info(f"Executing Python script: {file_path}")

        return self.python_utils.run_script_file(file_path, cwd)

    def chmod(self, path: str, mode: str, cwd: Optional[str]) -> Any:
        """Change file permissions using chmod command.
        
        Args:
            path: File path
            mode: Permission mode (e.g., '+x', '755')
            cwd: Working directory
            
        Returns:
            Execution result
        """
        cmd = ["chmod", mode, path]

        self.log_info(f"Changing permissions: {path} to {mode}")

        return self.execute_shell_command(cmd, cwd=cwd)

    def which(self, command: str) -> Optional[str]:
        """Find the path of a command using 'which'.
        
        Args:
            command: Command name to find
            
        Returns:
            Path to command or None if not found
        """
        result = self.execute_shell_command(["which", command])

        if result.returncode == 0 and result.stdout:
            return result.stdout.strip()

        return None

    def is_command_available(self, command: str) -> bool:
        """Check if a command is available in the system.
        
        Args:
            command: Command name to check
            
        Returns:
            True if command is available
        """
        return self.which(command) is not None

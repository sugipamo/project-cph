"""Local shell driver implementation using subprocess."""
from typing import Any, Optional, Union

from src.infrastructure.drivers.shell.shell_driver import ShellDriver
from src.infrastructure.drivers.shell.utils.shell_utils import ShellUtils


class LocalShellDriver(ShellDriver):
    """Local shell driver implementation using subprocess."""

    def __init__(self, file_driver: Any):
        """Initialize with file driver for directory operations."""
        super().__init__()
        self.file_driver = file_driver

    def run(self, cmd: Union[str, list[str]], cwd: Optional[str] = None,
            env: Optional[dict[str, str]] = None, inputdata: Optional[str] = None,
            timeout: Optional[int] = None) -> Any:
        """Execute a shell command using subprocess.

        Args:
            cmd: Command to execute (string or list of arguments)
            cwd: Working directory for command execution
            env: Environment variables
            inputdata: Input data to pass to the command
            timeout: Command timeout in seconds

        Returns:
            Command execution result
        """
        # Create cwd directory if specified
        if cwd is not None:
            from pathlib import Path
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

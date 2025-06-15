"""Abstract base class for shell command execution."""
from abc import abstractmethod
from typing import Any, Optional, Union

from src.infrastructure.drivers.base.base_driver import ExecutionDriverInterface


class ShellDriver(ExecutionDriverInterface):
    """Abstract base class for shell command execution."""

    @abstractmethod
    def run(self, cmd: Union[str, list[str]], cwd: Optional[str] = None,
            env: Optional[dict[str, str]] = None, inputdata: Optional[str] = None,
            timeout: Optional[int] = None) -> Any:
        """Execute a shell command.

        Args:
            cmd: Command to execute (string or list of arguments)
            cwd: Working directory for command execution
            env: Environment variables
            inputdata: Input data to pass to the command
            timeout: Command timeout in seconds

        Returns:
            Command execution result
        """

    def execute_command(self, request: Any) -> Any:
        """Execute a shell request."""
        # Delegate to run method for backward compatibility
        if hasattr(request, 'cmd'):
            return self.run(
                cmd=request.cmd,
                cwd=getattr(request, 'cwd', None),
                env=getattr(request, 'env', None),
                inputdata=getattr(request, 'inputdata', None),
                timeout=getattr(request, 'timeout', None)
            )
        raise ValueError("Invalid request type for ShellDriver")

    def validate(self, request: Any) -> bool:
        """Validate if this driver can handle the request."""
        return hasattr(request, 'cmd')

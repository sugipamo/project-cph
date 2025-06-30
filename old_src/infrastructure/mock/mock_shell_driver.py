"""Mock shell driver for testing."""
from typing import Optional, Union

from old_src.infrastructure.drivers.shell.shell_driver import ShellDriver
from old_src.operations.results.shell_result import ShellResult


class MockShellDriver(ShellDriver):
    """Mock implementation of shell driver for testing."""

    def __init__(self, file_driver):
        """Initialize mock shell driver."""
        self._commands_executed = []
        self._responses = {}
        self._default_response = ShellResult(
            success=True,
            stdout="mock output",
            stderr="",
            returncode=0,
            cmd="mock command",
            error_message=None,
            exception=None,
            start_time=0.0,
            end_time=0.0,
            request=None,
            metadata={},
            op="mock_shell_operation"
        )
        self.file_driver = file_driver

    def execute_shell_command(self, cmd: Union[str, list[str]], cwd: Optional[str],
                            env: Optional[dict[str, str]], inputdata: Optional[str],
                            timeout: Optional[int]) -> ShellResult:
        """Execute a shell command (mocked).

        Args:
            cmd: Command to execute
            cwd: Working directory
            env: Environment variables
            inputdata: Input data
            timeout: Command timeout

        Returns:
            Mocked shell result
        """
        cmd_str = ' '.join(cmd) if isinstance(cmd, list) else cmd

        self._commands_executed.append({
            'cmd': cmd_str,
            'cwd': cwd,
            'env': env,
            'inputdata': inputdata,
            'timeout': timeout
        })

        # Return predefined response if available, otherwise default
        return self._responses[cmd_str]

    def execute_command(self, command: str, cwd: Optional[str],
                       timeout: Optional[int], show_output: bool) -> ShellResult:
        """Execute a shell command (mocked).

        Args:
            command: Command to execute
            cwd: Working directory
            timeout: Command timeout
            show_output: Whether to show output

        Returns:
            Mocked shell result
        """
        self._commands_executed.append({
            'command': command,
            'cwd': cwd,
            'timeout': timeout,
            'show_output': show_output
        })

        # Return predefined response if available, otherwise default
        return self._responses[command]

    def set_response(self, command: str, response: ShellResult) -> None:
        """Set predefined response for a command.

        Args:
            command: Command to set response for
            response: Response to return
        """
        self._responses[command] = response

    def set_default_response(self, response: ShellResult) -> None:
        """Set default response for unknown commands.

        Args:
            response: Default response
        """
        self._default_response = response

    def get_executed_commands(self) -> list[dict]:
        """Get list of executed commands.

        Returns:
            List of command execution details
        """
        return self._commands_executed.copy()

    def clear_history(self) -> None:
        """Clear command execution history."""
        self._commands_executed.clear()

    def was_command_executed(self, command: str) -> bool:
        """Check if a specific command was executed.

        Args:
            command: Command to check

        Returns:
            True if command was executed
        """
        return any(cmd['command'] == command for cmd in self._commands_executed)

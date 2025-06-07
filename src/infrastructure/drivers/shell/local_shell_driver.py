"""Local shell driver implementation using subprocess."""
from typing import Any, Dict, Optional, Union, List
from src.infrastructure.drivers.shell.shell_driver import ShellDriver
from src.shared.utils.shell.shell_utils import ShellUtils


class LocalShellDriver(ShellDriver):
    """Local shell driver implementation using subprocess."""
    
    def run(self, cmd: Union[str, List[str]], cwd: Optional[str] = None, 
            env: Optional[Dict[str, str]] = None, inputdata: Optional[str] = None, 
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
        return ShellUtils.run_subprocess(
            cmd=cmd,
            cwd=cwd,
            env=env,
            inputdata=inputdata,
            timeout=timeout
        )
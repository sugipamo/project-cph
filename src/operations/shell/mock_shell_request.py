from typing import List, Optional
from src.operations.shell.shell_result import ShellResult

class MockShellRequest:
    def __init__(self, cmd: List[str], stdout: str = "", stderr: str = "", returncode: int = 0, env=None, inputdata=None, timeout=None):
        self.cmd = cmd
        self.env = env
        self.inputdata = inputdata
        self.timeout = timeout
        self._executed = False
        self._result = None
        self.mock_stdout = stdout
        self.mock_stderr = stderr
        self.mock_returncode = returncode
        self.history = []

    def execute(self):
        if self._executed:
            raise RuntimeError("This MockShellRequest has already been executed.")
        self.history.append({
            "cmd": self.cmd,
            "env": self.env,
            "inputdata": self.inputdata,
            "timeout": self.timeout
        })
        self._result = ShellResult(
            stdout=self.mock_stdout,
            stderr=self.mock_stderr,
            returncode=self.mock_returncode,
            request=self
        )
        self._executed = True
        return self._result

class MockShellInteractiveRequest:
    def __init__(self, cmd: List[str], stdout_lines: Optional[List[str]] = None, stderr_lines: Optional[List[str]] = None, returncode: int = 0, env=None, timeout=None):
        self.cmd = cmd
        self.env = env
        self.timeout = timeout
        self.stdout_lines = stdout_lines or []
        self.stderr_lines = stderr_lines or []
        self.returncode = returncode
        self.input_history = []
        self._is_running = False

    def start(self):
        self._is_running = True
        return self

    def send_input(self, data):
        self.input_history.append(data)

    def read_output_line(self, timeout=None):
        if self.stdout_lines:
            return self.stdout_lines.pop(0)
        return None

    def read_error_line(self, timeout=None):
        if self.stderr_lines:
            return self.stderr_lines.pop(0)
        return None

    def is_running(self):
        return self._is_running

    def stop(self, force=False):
        self._is_running = False

    def wait(self):
        self._is_running = False
        return ShellResult(
            stdout=''.join(self.stdout_lines),
            stderr=''.join(self.stderr_lines),
            returncode=self.returncode,
            request=self
        ) 
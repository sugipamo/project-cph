import subprocess
from .shell_result import ShellResult
from src.operations.operation_type import OperationType

class ShellRequest:
    def __init__(self, cmd, cwd=None, env=None, inputdata=None, timeout=None):
        self.cmd = cmd
        self.cwd = cwd
        self.env = env
        self.inputdata = inputdata
        self.timeout = timeout
        self._executed = False
        self._result = None

    @property
    def operation_type(self):
        return OperationType.SHELL

    def execute(self):
        if self._executed:
            raise RuntimeError("This ShellRequest has already been executed.")
        try:
            completed = subprocess.run(
                self.cmd,
                input=self.inputdata,
                cwd=self.cwd,
                env=self.env,
                text=True,
                capture_output=True,
                timeout=self.timeout
            )
            self._result = ShellResult(
                stdout=completed.stdout,
                stderr=completed.stderr,
                returncode=completed.returncode,
                request=self
            )
        except Exception as e:
            self._result = ShellResult(
                stdout="",
                stderr=str(e),
                returncode=-1,
                request=self,
                exception=e,
                error_message=str(e)
            )
        self._executed = True
        return self._result 
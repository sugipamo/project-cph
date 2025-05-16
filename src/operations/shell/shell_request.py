import subprocess
from src.operations.result import OperationResult
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
        import time
        start_time = time.time()
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
            end_time = time.time()
            self._result = OperationResult(
                stdout=completed.stdout,
                stderr=completed.stderr,
                returncode=completed.returncode,
                request=self,
                cmd=self.cmd,
                start_time=start_time,
                end_time=end_time
            )
        except Exception as e:
            end_time = time.time()
            self._result = OperationResult(
                stdout="",
                stderr=str(e),
                returncode=-1,
                request=self,
                cmd=self.cmd,
                start_time=start_time,
                end_time=end_time,
                error_message=str(e),
                exception=e
            )
        self._executed = True
        return self._result 
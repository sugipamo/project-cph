import subprocess
from src.operations.result import OperationResult
from src.operations.operation_type import OperationType
import inspect
import os
from src.operations.base_request import BaseRequest

class ShellRequest(BaseRequest):
    def __init__(self, cmd, cwd=None, env=None, inputdata=None, timeout=None, debug_tag=None, name=None):
        super().__init__(name=name, debug_tag=debug_tag)
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

    def execute(self, driver=None):
        if self._executed:
            raise RuntimeError("This ShellRequest has already been executed.")
        if driver is None:
            raise ValueError("ShellRequest.execute()にはdriverが必須です")
        import time
        start_time = time.time()
        try:
            completed = driver.run(
                self.cmd,
                cwd=self.cwd,
                env=self.env,
                inputdata=self.inputdata,
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
                returncode=None,
                request=self,
                cmd=self.cmd,
                start_time=start_time,
                end_time=end_time
            )
        self._executed = True
        return self._result

    def __repr__(self):
        return f"<ShellRequest cmd={self.cmd}>" 
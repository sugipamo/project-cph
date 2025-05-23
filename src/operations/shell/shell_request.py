import subprocess
from src.operations.result import OperationResult
from src.operations.constants.operation_type import OperationType
import inspect
import os
from src.operations.base_request import BaseRequest
from src.operations.shell.shell_util import ShellUtil

class ShellRequest(BaseRequest):
    def __init__(self, cmd, cwd=None, env=None, inputdata=None, timeout=None, debug_tag=None, name=None, show_output=True):
        super().__init__(name=name, debug_tag=debug_tag)
        self.cmd = cmd
        self.cwd = cwd
        self.env = env
        self.inputdata = inputdata
        self.timeout = timeout
        self.show_output = show_output
        self._executed = False
        self._result = None

    @property
    def operation_type(self):
        return OperationType.SHELL

    def execute(self, driver):
        return super().execute(driver)

    def _execute_core(self, driver):
        import time
        start_time = time.time()
        try:
            completed = ShellUtil.run_subprocess(
                self.cmd,
                cwd=self.cwd,
                env=self.env,
                inputdata=self.inputdata,
                timeout=self.timeout
            )
            end_time = time.time()
            return OperationResult(
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
            return OperationResult(
                stdout="",
                stderr=str(e),
                returncode=None,
                request=self,
                cmd=self.cmd,
                start_time=start_time,
                end_time=end_time
            )

    def __repr__(self):
        return f"<ShellRequest cmd={self.cmd}>" 
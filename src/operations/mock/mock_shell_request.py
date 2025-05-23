from src.operations.result import OperationResult
from src.operations.constants.operation_type import OperationType
from src.operations.base_request import BaseRequest
from typing import List, Optional

class MockShellRequest(BaseRequest):
    _require_driver = False
    def __init__(self, cmd: List[str], stdout: str = "", stderr: str = "", returncode: int = 0, env=None, inputdata=None, timeout=None, name=None, debug_tag=None):
        super().__init__(name=name, debug_tag=debug_tag)
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

    def execute(self, driver=None):
        return super().execute(driver)

    def _execute_core(self, driver=None):
        self.history.append({
            "cmd": self.cmd,
            "env": self.env,
            "inputdata": self.inputdata,
            "timeout": self.timeout
        })
        return OperationResult(
            stdout=self.mock_stdout,
            stderr=self.mock_stderr,
            returncode=self.mock_returncode,
            request=self,
            path=None
        )

    @property
    def operation_type(self):
        return OperationType.SHELL

class MockShellInteractiveRequest(BaseRequest):
    _require_driver = False
    def __init__(self, cmd, stdout_lines=None, stderr_lines=None, returncode=0, env=None, name=None, debug_tag=None):
        super().__init__(name=name, debug_tag=debug_tag)
        self.cmd = cmd
        self.env = env
        self.stdout_lines = list(stdout_lines) if stdout_lines is not None else []
        self.stderr_lines = list(stderr_lines) if stderr_lines is not None else []
        self.returncode = returncode
        self._output_buffer = []
        self._error_buffer = []
        self._input_history = []
        self._started = False
        self._stopped = False
        self._waited = False
        self._is_running = False
        self._result = None

    def start(self):
        self._started = True
        self._is_running = True
        self._output_buffer = list(self.stdout_lines)
        self._error_buffer = list(self.stderr_lines)
        self._input_history = []
        self._stopped = False
        self._waited = False

    def send_input(self, input_str):
        self._input_history.append(input_str)
        # 入力内容に応じて出力を模倣
        if "print(\"foo\")" in input_str:
            self._output_buffer.append("foo\n")
        elif "print(\"bar\")" in input_str:
            self._output_buffer.append("bar\n")
        elif "import sys; print(\"err" in input_str and "file=sys.stderr" in input_str:
            self._error_buffer.append("err\n")
        elif "exit()" in input_str:
            self._is_running = False
            self._stopped = True

    def read_output_line(self, timeout=None):
        if self._output_buffer:
            return self._output_buffer.pop(0)
        return None

    def read_error_line(self, timeout=None):
        if self._error_buffer:
            return self._error_buffer.pop(0)
        return None

    def is_running(self):
        return self._is_running

    def wait(self, timeout=None):
        self._waited = True
        self._is_running = False
        self._stopped = True
        # 標準出力・エラーをまとめて返す
        stdout = "".join(self.stdout_lines + [s for s in self._output_buffer if s])
        for inp in self._input_history:
            if "foo" in inp and "foo\n" not in stdout:
                stdout += "foo\n"
            if "bar" in inp and "bar\n" not in stdout:
                stdout += "bar\n"
        stderr = "".join(self.stderr_lines + [s for s in self._error_buffer if s])
        if any("err" in inp for inp in self._input_history) and "err\n" not in stderr:
            stderr += "err\n"
        self._result = OperationResult(
            stdout=stdout,
            stderr=stderr,
            returncode=self.returncode,
            request=self
        )
        return self._result

    def stop(self):
        self._is_running = False
        self._stopped = True

    @property
    def operation_type(self):
        return OperationType.SHELL

    def _execute_core(self, driver=None):
        # テスト用のダミー実装
        return None 
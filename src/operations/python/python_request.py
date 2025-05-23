import sys
import traceback
from src.operations.result import OperationResult
from src.operations.constants.operation_type import OperationType
from src.operations.base_request import BaseRequest
from src.operations.python.python_util import PythonUtil

class PythonRequest(BaseRequest):
    def __init__(self, code_or_file, cwd=None, show_output=True, name=None, debug_tag=None):
        super().__init__(name=name, debug_tag=debug_tag)
        self.code_or_file = code_or_file  # コード文字列またはファイル名
        self.cwd = cwd
        self.show_output = show_output
        self._executed = False
        self._result = None

    @property
    def operation_type(self):
        return OperationType.PYTHON

    def execute(self, driver=None):
        import os
        import time
        start_time = time.time()
        old_cwd = os.getcwd()
        try:
            if self.cwd:
                os.chdir(self.cwd)
            if PythonUtil.is_script_file(self.code_or_file):
                stdout, stderr, returncode = PythonUtil.run_script_file(self.code_or_file[0], cwd=self.cwd)
            else:
                code = "\n".join(self.code_or_file)
                stdout, stderr, returncode = PythonUtil.run_code_string(code, cwd=self.cwd)
            end_time = time.time()
            self._result = OperationResult(
                stdout=stdout,
                stderr=stderr,
                returncode=returncode,
                request=self,
                start_time=start_time,
                end_time=end_time
            )
        except Exception as e:
            end_time = time.time()
            self._result = OperationResult(
                stdout="",
                stderr=str(e),
                returncode=1,
                request=self,
                start_time=start_time,
                end_time=end_time
            )
        finally:
            os.chdir(old_cwd)
        self._executed = True
        return self._result

    def __repr__(self):
        return f"<PythonRequest code_or_file={self.code_or_file}>" 
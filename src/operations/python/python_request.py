import sys
import traceback
from src.operations.result import OperationResult
from src.operations.operation_type import OperationType
from src.operations.base_request import BaseRequest

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
        return OperationType.SHELL  # 便宜上SHELL扱い

    def execute(self, driver=None):
        import os
        import contextlib
        import io
        import runpy
        import types
        import builtins
        import importlib.util
        import subprocess
        import shlex
        import tempfile
        import pathlib
        import sys
        import traceback
        import time
        start_time = time.time()
        old_cwd = os.getcwd()
        try:
            if self.cwd:
                os.chdir(self.cwd)
            # コード文字列かファイル名か判定
            if len(self.code_or_file) == 1 and pathlib.Path(self.code_or_file[0]).is_file():
                # スクリプトファイルとして実行
                result = subprocess.run([sys.executable, self.code_or_file[0]], capture_output=True, text=True)
                stdout, stderr, returncode = result.stdout, result.stderr, result.returncode
            else:
                # コード文字列として実行
                code = "\n".join(self.code_or_file)
                buf_out = io.StringIO()
                buf_err = io.StringIO()
                with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
                    try:
                        exec(code, {})
                        returncode = 0
                    except Exception:
                        traceback.print_exc(file=buf_err)
                        returncode = 1
                stdout, stderr = buf_out.getvalue(), buf_err.getvalue()
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
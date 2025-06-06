import sys
import traceback
from src.operations.result import OperationResult
from src.operations.constants.operation_type import OperationType
from src.operations.base_request import BaseRequest
from src.operations.python.python_utils import PythonUtils

class PythonRequest(BaseRequest):
    _require_driver = True
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
        return super().execute(driver)

    def _execute_core(self, driver=None):
        import os
        import time
        start_time = time.time()
        old_cwd = os.getcwd()
        try:
            if self.cwd:
                os.chdir(self.cwd)
            
            # Check if we have a mock python driver
            if driver and hasattr(driver, 'python_driver'):
                python_driver = driver.python_driver
                if hasattr(python_driver, 'is_script_file'):
                    is_script = python_driver.is_script_file(self.code_or_file)
                else:
                    is_script = PythonUtils.is_script_file(self.code_or_file)
                
                if is_script:
                    stdout, stderr, returncode = python_driver.run_script_file(self.code_or_file[0], cwd=self.cwd)
                else:
                    if isinstance(self.code_or_file, list):
                        code = "\n".join(self.code_or_file)
                    else:
                        code = self.code_or_file
                    stdout, stderr, returncode = python_driver.run_code_string(code, cwd=self.cwd)
            # Check if we have a unified driver that can resolve python_driver
            elif driver and hasattr(driver, 'resolve') and callable(driver.resolve):
                try:
                    python_driver = driver.resolve('python_driver')
                    if hasattr(python_driver, 'is_script_file'):
                        is_script = python_driver.is_script_file(self.code_or_file)
                    else:
                        is_script = PythonUtils.is_script_file(self.code_or_file)
                    
                    if is_script:
                        stdout, stderr, returncode = python_driver.run_script_file(self.code_or_file[0], cwd=self.cwd)
                    else:
                        if isinstance(self.code_or_file, list):
                            code = "\n".join(self.code_or_file)
                        else:
                            code = self.code_or_file
                        stdout, stderr, returncode = python_driver.run_code_string(code, cwd=self.cwd)
                except:
                    # Fallback to PythonUtils if driver resolution fails
                    if PythonUtils.is_script_file(self.code_or_file):
                        stdout, stderr, returncode = PythonUtils.run_script_file(self.code_or_file[0], cwd=self.cwd)
                    else:
                        if isinstance(self.code_or_file, list):
                            code = "\n".join(self.code_or_file)
                        else:
                            code = self.code_or_file
                        stdout, stderr, returncode = PythonUtils.run_code_string(code, cwd=self.cwd)
            else:
                # Fallback to PythonUtils for backward compatibility
                if PythonUtils.is_script_file(self.code_or_file):
                    stdout, stderr, returncode = PythonUtils.run_script_file(self.code_or_file[0], cwd=self.cwd)
                else:
                    if isinstance(self.code_or_file, list):
                        code = "\n".join(self.code_or_file)
                    else:
                        code = self.code_or_file
                    stdout, stderr, returncode = PythonUtils.run_code_string(code, cwd=self.cwd)
            
            end_time = time.time()
            return OperationResult(
                stdout=stdout,
                stderr=stderr,
                returncode=returncode,
                request=self,
                cmd=self.code_or_file,
                start_time=start_time,
                end_time=end_time
            )
        except Exception as e:
            end_time = time.time()
            return OperationResult(
                stdout="",
                stderr=str(e),
                returncode=1,
                request=self,
                cmd=self.code_or_file,
                start_time=start_time,
                end_time=end_time
            )
        finally:
            os.chdir(old_cwd)

    def __repr__(self):
        return f"<PythonRequest code_or_file={self.code_or_file}>" 
"""Python code execution request."""
import time
from typing import Union, List, Optional, Any
from src.domain.requests.base.base_request import BaseRequest
from src.domain.constants.operation_type import OperationType
from src.domain.results.result import OperationResult
from src.infrastructure.drivers.python.utils.python_utils import PythonUtils


class PythonRequest(BaseRequest):
    """Request for executing Python code or scripts."""
    
    _require_driver = True
    
    def __init__(self, code_or_file: Union[str, List[str]], cwd: Optional[str] = None, 
                 show_output: bool = True, name: Optional[str] = None, 
                 debug_tag: Optional[str] = None):
        super().__init__(name=name, debug_tag=debug_tag)
        self.code_or_file = code_or_file  # Code string or filename
        self.cwd = cwd
        self.show_output = show_output

    @property
    def operation_type(self) -> OperationType:
        return OperationType.PYTHON

    def _execute_core(self, driver: Any = None) -> OperationResult:
        import os
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
                    stdout, stderr, returncode = python_driver.run_script_file(
                        self.code_or_file[0], cwd=self.cwd
                    )
                else:
                    if isinstance(self.code_or_file, list):
                        code = "\n".join(self.code_or_file)
                    else:
                        code = self.code_or_file
                    stdout, stderr, returncode = python_driver.run_code_string(
                        code, cwd=self.cwd
                    )
            
            # Check if we have a unified driver that can resolve python_driver
            elif driver and hasattr(driver, 'resolve') and callable(driver.resolve):
                try:
                    python_driver = driver.resolve('python_driver')
                    if hasattr(python_driver, 'is_script_file'):
                        is_script = python_driver.is_script_file(self.code_or_file)
                    else:
                        is_script = PythonUtils.is_script_file(self.code_or_file)
                    
                    if is_script:
                        stdout, stderr, returncode = python_driver.run_script_file(
                            self.code_or_file[0], cwd=self.cwd
                        )
                    else:
                        if isinstance(self.code_or_file, list):
                            code = "\n".join(self.code_or_file)
                        else:
                            code = self.code_or_file
                        stdout, stderr, returncode = python_driver.run_code_string(
                            code, cwd=self.cwd
                        )
                except:
                    # Fallback to PythonUtils if driver resolution fails
                    if PythonUtils.is_script_file(self.code_or_file):
                        stdout, stderr, returncode = PythonUtils.run_script_file(
                            self.code_or_file[0], cwd=self.cwd
                        )
                    else:
                        if isinstance(self.code_or_file, list):
                            code = "\n".join(self.code_or_file)
                        else:
                            code = self.code_or_file
                        stdout, stderr, returncode = PythonUtils.run_code_string(
                            code, cwd=self.cwd
                        )
            else:
                # Fallback to PythonUtils for backward compatibility
                if PythonUtils.is_script_file(self.code_or_file):
                    stdout, stderr, returncode = PythonUtils.run_script_file(
                        self.code_or_file[0], cwd=self.cwd
                    )
                else:
                    if isinstance(self.code_or_file, list):
                        code = "\n".join(self.code_or_file)
                    else:
                        code = self.code_or_file
                    stdout, stderr, returncode = PythonUtils.run_code_string(
                        code, cwd=self.cwd
                    )
            
            end_time = time.time()
            return OperationResult(
                stdout=stdout,
                stderr=stderr,
                returncode=returncode,
                request=self,
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
                start_time=start_time,
                end_time=end_time,
                error_message=str(e)
            )
        finally:
            if self.cwd:
                os.chdir(old_cwd)

    def __repr__(self) -> str:
        return f"<PythonRequest code_or_file={self.code_or_file}>"
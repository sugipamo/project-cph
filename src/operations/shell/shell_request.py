import subprocess
import time
import inspect
import os
from src.operations.result import OperationResult
from src.operations.constants.operation_type import OperationType
from src.operations.base_request import BaseRequest
from src.operations.shell.shell_utils import ShellUtils

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
        """
        シェルコマンド実行のコアロジック
        
        パフォーマンス最適化:
        - より精密な時間計測
        - インポートの最適化
        """
        start_time = time.perf_counter()  # More precise timing
        try:
            # Use the driver to run the command instead of direct subprocess
            # Check if we have a unified driver that can resolve shell_driver
            actual_driver = driver
            from src.operations.composite.unified_driver import UnifiedDriver
            if isinstance(driver, UnifiedDriver):
                actual_driver = driver._get_cached_driver("shell_driver")
            
            # Use the shell driver to run the command
            completed = actual_driver.run(
                self.cmd,
                cwd=self.cwd,
                env=self.env,
                inputdata=self.inputdata,
                timeout=self.timeout
            )
            end_time = time.perf_counter()  # Consistent timing method
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
            end_time = time.perf_counter()  # Consistent timing method
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
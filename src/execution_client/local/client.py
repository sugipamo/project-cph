from execution_client.abstract_client import AbstractExecutionClient
from execution_client.types import ExecutionResult
from typing import Any, Optional, List, Dict
import subprocess
import threading
import time

class LocalAsyncClient(AbstractExecutionClient):
    def __init__(self):
        # name -> (Popen, stdout, stderr)
        self._processes = {}
        self._lock = threading.Lock()

    def run(self, name: str, image: Optional[str] = None, command: Optional[List[str]] = None, volumes: Optional[Dict[str, str]] = None, detach: bool = True, **kwargs) -> ExecutionResult:
        if not command:
            raise ValueError("command must be specified for local execution")
        with self._lock:
            if name in self._processes:
                raise RuntimeError(f"Process with name {name} already running")
            proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self._processes[name] = proc
        # 非同期実行の場合は即返す。同期実行ならwaitして結果を返す
        if detach:
            return ExecutionResult(returncode=None, stdout=None, stderr=None, extra={"popen": proc})
        else:
            stdout, stderr = proc.communicate()
            return ExecutionResult(returncode=proc.returncode, stdout=stdout, stderr=stderr)

    def stop(self, name: str) -> bool:
        with self._lock:
            proc = self._processes.get(name)
            if not proc:
                return False
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            del self._processes[name]
        return True

    def remove(self, name: str) -> bool:
        # ローカルプロセスの場合、stopと同じ
        return self.stop(name)

    def exec_in(self, name: str, cmd: List[str], **kwargs) -> ExecutionResult:
        # 別プロセスとして即時実行
        result = subprocess.run(cmd, capture_output=True, text=True)
        return ExecutionResult(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)

    def is_running(self, name: str) -> bool:
        with self._lock:
            proc = self._processes.get(name)
            if not proc:
                return False
            return proc.poll() is None

    def list(self, all: bool = True, prefix: Optional[str] = None) -> List[str]:
        with self._lock:
            names = list(self._processes.keys())
        if prefix:
            names = [n for n in names if n.startswith(prefix)]
        return names 
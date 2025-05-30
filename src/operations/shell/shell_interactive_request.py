import subprocess
import threading
from queue import Queue, Empty
from src.operations.result import OperationResult
from src.operations.shell.shell_util import ShellUtil
from src.operations.base_request import BaseRequest
from src.operations.constants.operation_type import OperationType

class ShellInteractiveRequest(BaseRequest):
    def __init__(self, cmd, cwd=None, env=None, timeout=None, name=None, debug_tag=None):
        super().__init__(name=name, debug_tag=debug_tag)
        self.cmd = cmd
        self.cwd = cwd
        self.env = env
        self.timeout = timeout
        self._proc = None
        self._stdout_queue = Queue()
        self._stderr_queue = Queue()
        self._stdout_thread = None
        self._stderr_thread = None
        self._stdout_lines = []
        self._stderr_lines = []
        self._timeout_thread = None
        self._timeout_expired = False
        self._require_driver = False  # ドライバー不要

    @property
    def operation_type(self):
        return OperationType.SHELL_INTERACTIVE

    def _execute_core(self, driver):
        """BaseRequestの抽象メソッド実装。startを呼び出してインタラクティブセッションを開始"""
        return self.start()

    def start(self):
        self._proc = ShellUtil.start_interactive(
            self.cmd,
            cwd=self.cwd,
            env=self.env
        )
        self._stdout_thread = threading.Thread(target=ShellUtil.enqueue_output, args=(self._proc.stdout, self._stdout_queue))
        self._stderr_thread = threading.Thread(target=ShellUtil.enqueue_output, args=(self._proc.stderr, self._stderr_queue))
        self._stdout_thread.daemon = True
        self._stderr_thread.daemon = True
        self._stdout_thread.start()
        self._stderr_thread.start()
        if self.timeout is not None:
            self._timeout_thread = threading.Thread(target=ShellUtil.enforce_timeout, args=(self._proc, self.timeout, self.stop))
            self._timeout_thread.daemon = True
            self._timeout_thread.start()
        return self

    def _enforce_timeout(self):
        try:
            self._proc.wait(timeout=self.timeout)
        except subprocess.TimeoutExpired:
            self._timeout_expired = True
            self.stop(force=True)

    def is_running(self):
        return self._proc is not None and self._proc.poll() is None

    def stop(self, force=False):
        if self._proc and self.is_running():
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                if force:
                    self._proc.kill()

    def _enqueue_output(self, stream, queue):
        for line in iter(stream.readline, ''):
            queue.put(line)
        stream.close()

    def send_input(self, data):
        if self._proc and self._proc.stdin:
            self._proc.stdin.write(data)
            self._proc.stdin.flush()

    def read_output_line(self, timeout=None):
        try:
            line = self._stdout_queue.get(timeout=timeout)
            self._stdout_lines.append(line)
            return line
        except Empty:
            return None

    def read_error_line(self, timeout=None):
        try:
            line = self._stderr_queue.get(timeout=timeout)
            self._stderr_lines.append(line)
            return line
        except Empty:
            return None

    def wait(self):
        if self._proc:
            self._proc.wait()
            # 残りのqueueもdrainしてlinesに追加
            self._stdout_lines.extend(list(ShellUtil.drain_queue(self._stdout_queue)))
            self._stderr_lines.extend(list(ShellUtil.drain_queue(self._stderr_queue)))
            stdout = ''.join(self._stdout_lines)
            stderr = ''.join(self._stderr_lines)
            return OperationResult(
                stdout=stdout,
                stderr=stderr,
                returncode=self._proc.returncode,
                request=self,
                path=None
            ) 
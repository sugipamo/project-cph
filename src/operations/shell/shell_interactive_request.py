import subprocess
import threading
from queue import Queue, Empty
from .shell_result import ShellResult

class ShellInteractiveRequest:
    def __init__(self, cmd, cwd=None, env=None):
        self.cmd = cmd
        self.cwd = cwd
        self.env = env
        self._proc = None
        self._stdout_queue = Queue()
        self._stderr_queue = Queue()
        self._stdout_thread = None
        self._stderr_thread = None

    def start(self):
        self._proc = subprocess.Popen(
            self.cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.cwd,
            env=self.env,
            text=True,
            bufsize=1
        )
        self._stdout_thread = threading.Thread(target=self._enqueue_output, args=(self._proc.stdout, self._stdout_queue))
        self._stderr_thread = threading.Thread(target=self._enqueue_output, args=(self._proc.stderr, self._stderr_queue))
        self._stdout_thread.daemon = True
        self._stderr_thread.daemon = True
        self._stdout_thread.start()
        self._stderr_thread.start()
        return self

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
            return self._stdout_queue.get(timeout=timeout)
        except Empty:
            return None

    def read_error_line(self, timeout=None):
        try:
            return self._stderr_queue.get(timeout=timeout)
        except Empty:
            return None

    def wait(self):
        if self._proc:
            self._proc.wait()
            stdout = ''.join(list(self._drain_queue(self._stdout_queue)))
            stderr = ''.join(list(self._drain_queue(self._stderr_queue)))
            return ShellResult(
                stdout=stdout,
                stderr=stderr,
                returncode=self._proc.returncode,
                request=self
            )

    def _drain_queue(self, queue):
        while True:
            try:
                yield queue.get_nowait()
            except Empty:
                break 
import time
import json

class ShellResult:
    def __init__(self, stdout: str, stderr: str, returncode: int, request=None, cmd=None, start_time=None, end_time=None, error_message=None, exception=None, metadata=None):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.request = request
        self.cmd = cmd or (request.cmd if request else None)
        self.start_time = start_time
        self.end_time = end_time
        self.elapsed_time = (end_time - start_time) if start_time and end_time else None
        self.error_message = error_message
        self.exception = exception
        self.metadata = metadata or {}

    @property
    def success(self):
        return self.returncode == 0

    def is_success(self):
        return self.success

    def is_failure(self):
        return not self.success

    def raise_if_error(self):
        if self.exception:
            raise self.exception
        if not self.success:
            raise RuntimeError(f"Shell command failed: {self.cmd}\nstdout={self.stdout}\nstderr={self.stderr}")

    def to_dict(self):
        return {
            'stdout': self.stdout,
            'stderr': self.stderr,
            'returncode': self.returncode,
            'cmd': self.cmd,
            'request': str(self.request),
            'start_time': self.start_time,
            'end_time': self.end_time,
            'elapsed_time': self.elapsed_time,
            'error_message': self.error_message,
            'exception': str(self.exception) if self.exception else None,
            'metadata': self.metadata,
        }

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def summary(self):
        return f"[{'OK' if self.success else 'FAIL'}] cmd={self.cmd} code={self.returncode} time={self.elapsed_time}s\nstdout={self.stdout[:100]}\nstderr={self.stderr[:100]}" 
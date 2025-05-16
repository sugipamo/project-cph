from typing import Any, Optional
from enum import Enum

class DockerResult:
    def __init__(self, success: bool, op: Enum = None, stdout: Optional[str] = None, stderr: Optional[str] = None, returncode: Optional[int] = None, exception: Exception = None, metadata: dict = None):
        self.success = success
        self.op = op
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.exception = exception
        self.metadata = metadata or {}

    def is_success(self):
        return self.success

    def is_failure(self):
        return not self.success

    def raise_if_error(self):
        if self.exception:
            raise self.exception
        if not self.success:
            raise RuntimeError(f"Docker operation failed: {self.op}\nstdout={self.stdout}\nstderr={self.stderr}")

    def to_dict(self):
        return {
            'success': self.success,
            'op': str(self.op) if self.op else None,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'returncode': self.returncode,
            'exception': str(self.exception) if self.exception else None,
            'metadata': self.metadata,
        } 
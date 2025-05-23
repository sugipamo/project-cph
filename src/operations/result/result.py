import time
import json

class OperationResult:
    def __init__(self, success: bool = None, returncode: int = None, stdout: str = None, stderr: str = None, content: str = None, exists: bool = None, path=None, op=None, cmd=None, request=None, start_time=None, end_time=None, error_message=None, exception=None, metadata=None):
        if success is not None:
            self.success = success
        else:
            self.success = (returncode == 0) if returncode is not None else False
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.content = content
        self.exists = exists
        self.path = path if path is not None else (getattr(request, "path", None) if request is not None else None)
        self.op = op if op is not None else (getattr(request, "op", None) if request is not None else None)
        self.cmd = cmd if cmd is not None else (getattr(request, "cmd", None) if request is not None else None)
        self.request = request
        self.start_time = start_time
        self.end_time = end_time
        self.elapsed_time = (end_time - start_time) if start_time and end_time else None
        self.error_message = error_message
        self.exception = exception
        self.metadata = metadata or {}
        # operation_typeはrequestから取得できる場合のみセット
        self._operation_type = getattr(request, "operation_type", None) if request is not None else None

    @property
    def operation_type(self):
        return self._operation_type

    def is_success(self):
        return self.success

    def is_failure(self):
        return not self.success

    def raise_if_error(self):
        if self.exception:
            raise self.exception
        if not self.success:
            raise RuntimeError(f"Operation failed: {self.op or self.cmd} {self.path}\ncontent={self.content}\nstdout={self.stdout}\nstderr={self.stderr}\nerror={self.error_message}")

    def to_dict(self):
        return {
            'success': self.success,
            'returncode': self.returncode,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'content': self.content,
            'exists': self.exists,
            'path': self.path,
            'op': str(self.op) if self.op else None,
            'cmd': self.cmd,
            'request': str(self.request),
            'operation_type': str(self.operation_type) if self.operation_type else None,
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
        return f"[{'OK' if self.success else 'FAIL'}] op={self.op or self.cmd} path={self.path} code={self.returncode} time={self.elapsed_time}s\ncontent={str(self.content)[:100]}\nstdout={str(self.stdout)[:100]}\nstderr={str(self.stderr)[:100]}\nerror={self.error_message}"

    def __repr__(self):
        return (
            f"<OperationResult success={self.success} op={self.op} cmd={self.cmd} path={self.path} "
            f"returncode={self.returncode} error_message={self.error_message}>"
        ) 
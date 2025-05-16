import time
import json

class FileResult:
    def __init__(self, success: bool, content: str = None, exists: bool = None, path=None, op=None, request=None, start_time=None, end_time=None, error_message=None, exception=None, metadata=None):
        self.success = success
        self.content = content
        self.exists = exists
        self.path = path or (request.path if request else None)
        self.op = op or (request.op if request else None)
        self.request = request
        self.start_time = start_time
        self.end_time = end_time
        self.elapsed_time = (end_time - start_time) if start_time and end_time else None
        self.error_message = error_message
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
            raise RuntimeError(f"File operation failed: {self.op} {self.path}\ncontent={self.content}\nerror={self.error_message}")

    def to_dict(self):
        return {
            'success': self.success,
            'content': self.content,
            'exists': self.exists,
            'path': self.path,
            'op': str(self.op) if self.op else None,
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
        return f"[{'OK' if self.success else 'FAIL'}] op={self.op} path={self.path} time={self.elapsed_time}s\ncontent={str(self.content)[:100]}\nerror={self.error_message}" 
from .result import OperationResult

class FileResult(OperationResult):
    def __init__(self, success: bool = None, content: str = None, path=None, exists: bool = None, op=None, start_time=None, end_time=None, request=None, error_message=None, exception=None, metadata=None):
        super().__init__(success=success, exception=exception, error_message=error_message)
        self.content = content
        self.path = path
        self.exists = exists
        self.op = op
        self.start_time = start_time
        self.end_time = end_time
        self.request = request
        self.metadata = metadata or {}

    def to_dict(self):
        base = super().to_dict()
        base.update({
            'content': self.content,
            'path': self.path,
            'exists': self.exists,
            'op': str(self.op) if self.op else None,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'request': str(self.request),
            'metadata': self.metadata,
        })
        return base 
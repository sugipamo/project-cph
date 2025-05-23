from .result import OperationResult

class DockerResult(OperationResult):
    def __init__(self, success: bool = None, stdout: str = None, stderr: str = None, returncode: int = None, op=None, start_time=None, end_time=None, request=None, error_message=None, exception=None, metadata=None):
        super().__init__(success=success, exception=exception, error_message=error_message)
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.op = op
        self.start_time = start_time
        self.end_time = end_time
        self.request = request
        self.metadata = metadata or {}

    def to_dict(self):
        base = super().to_dict()
        base.update({
            'stdout': self.stdout,
            'stderr': self.stderr,
            'returncode': self.returncode,
            'op': str(self.op) if self.op else None,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'request': str(self.request),
            'metadata': self.metadata,
        })
        return base 
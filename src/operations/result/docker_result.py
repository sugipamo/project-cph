from .result import OperationResult

class DockerResult(OperationResult):
    def __init__(self, success: bool = None, stdout: str = None, stderr: str = None, returncode: int = None, op=None, error_message=None, exception=None, start_time=None, end_time=None, request=None, metadata=None):
        super().__init__(success=success, exception=exception, error_message=error_message, start_time=start_time, end_time=end_time, request=request, metadata=metadata)
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.op = op

    def to_dict(self):
        base = super().to_dict()
        base.update({
            'stdout': self.stdout,
            'stderr': self.stderr,
            'returncode': self.returncode,
            'op': str(self.op) if self.op else None,
        })
        return base 
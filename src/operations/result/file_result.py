from .result import OperationResult
from src.operations.constants.operation_type import OperationType

class FileResult(OperationResult):
    def __init__(self, success: bool = None, content: str = None, path=None, exists: bool = None, op=None, error_message=None, exception=None, start_time=None, end_time=None, request=None, metadata=None):
        super().__init__(success=success, exception=exception, error_message=error_message, start_time=start_time, end_time=end_time, request=request, metadata=metadata)
        self.content = content
        self.path = path
        self.exists = exists
        self.op = op
    
    @property 
    def operation_type(self):
        """Return the operation type for file operations"""
        return OperationType.FILE

    def to_dict(self):
        base = super().to_dict()
        base.update({
            'content': self.content,
            'path': self.path,
            'exists': self.exists,
            'op': str(self.op) if self.op else None,
        })
        return base 
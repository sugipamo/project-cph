"""File operation result class."""
from typing import Any, Optional

from src.operations.constants.operation_type import OperationType
from src.operations.results.result import OperationResult


class FileResult(OperationResult):
    """Result class for file operations."""

    def __init__(self, success: Optional[bool] = None, content: Optional[str] = None,
                 path: Optional[str] = None, exists: Optional[bool] = None,
                 op: Optional[Any] = None, error_message: Optional[str] = None,
                 exception: Optional[Exception] = None, start_time: Optional[float] = None,
                 end_time: Optional[float] = None, request: Optional[Any] = None,
                 metadata: Optional[dict[str, Any]] = None):
        """Initialize file result.

        Args:
            success: Whether the operation was successful
            content: File content (for read operations)
            path: File path
            exists: File existence flag
            op: File operation type
            error_message: Error message
            exception: Exception that occurred
            start_time: Operation start time
            end_time: Operation end time
            request: Original request object
            metadata: Additional metadata
        """
        super().__init__(
            success=success,
            exception=exception,
            error_message=error_message,
            start_time=start_time,
            end_time=end_time,
            request=request,
            metadata=metadata
        )
        self.content = content
        self.path = path
        self.exists = exists
        self.op = op

    @property
    def operation_type(self) -> OperationType:
        """Return the operation type for file operations."""
        return OperationType.FILE

    def _get_op_str(self) -> str:
        """Get op string with explicit validation."""
        if self.op is None:
            raise ValueError("File operation 'op' is required but not available")
        return str(self.op)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        base = super().to_dict()
        base.update({
            'content': self.content,
            'path': self.path,
            'exists': self.exists,
            'op': self._get_op_str(),
        })
        return base

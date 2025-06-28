"""File operation result class."""
from typing import Any, Optional

from src.operations.constants.operation_type import OperationType


class FileResult:
    """Result class for file operations."""

    def __init__(self, success: Optional[bool], content: Optional[str],
                 path: Optional[str], exists: Optional[bool],
                 op: Optional[Any], error_message: Optional[str],
                 exception: Optional[Exception], start_time: Optional[float],
                 end_time: Optional[float], request: Optional[Any],
                 metadata: Optional[dict[str, Any]]):
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
        # Store all attributes directly since OperationResult has incompatible signature
        self.success = success
        self.error_message = error_message
        self.exception = exception
        self.start_time = start_time
        self.end_time = end_time
        self.request = request
        self.metadata = metadata or {}
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
        return {
            'success': self.success,
            'content': self.content,
            'path': self.path,
            'exists': self.exists,
            'op': self._get_op_str(),
            'error_message': self.error_message,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'metadata': self.metadata
        }

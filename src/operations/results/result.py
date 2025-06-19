"""Base result class for operation results."""
from typing import Any, Optional


class OperationResult:
    """Base class for operation results."""

    def __init__(self, success: Optional[bool] = None, returncode: Optional[int] = None,
                 stdout: Optional[str] = None, stderr: Optional[str] = None,
                 content: Optional[str] = None, exists: Optional[bool] = None,
                 path: Optional[str] = None, op: Optional[Any] = None,
                 cmd: Optional[str] = None, request: Optional[Any] = None,
                 start_time: Optional[float] = None, end_time: Optional[float] = None,
                 error_message: Optional[str] = None, exception: Optional[Exception] = None,
                 metadata: Optional[dict[str, Any]] = None, skipped: bool = False):
        """Initialize operation result.

        Args:
            success: Whether the operation was successful
            returncode: Process return code
            stdout: Standard output
            stderr: Standard error
            content: Content (for file operations)
            exists: File existence flag
            path: File path
            op: Operation type
            cmd: Command executed
            request: Original request object
            start_time: Operation start time
            end_time: Operation end time
            error_message: Error message
            exception: Exception that occurred
            metadata: Additional metadata
            skipped: Whether the operation was skipped
        """
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
        self.skipped = skipped
        # operation_type is set from request if available
        self._operation_type = getattr(request, "operation_type", None) if request is not None else None

    @property
    def operation_type(self) -> Optional[Any]:
        """Get the operation type."""
        return self._operation_type

    def is_success(self) -> bool:
        """Check if operation was successful."""
        return self.success

    def is_failure(self) -> bool:
        """Check if operation failed."""
        return not self.success

    def raise_if_error(self) -> None:
        """Raise exception if operation failed."""
        if self.exception:
            raise self.exception
        if not self.success:
            raise RuntimeError(
                f"Operation failed: {self.op or self.cmd} {self.path}\n"
                f"content={self.content}\n"
                f"stdout={self.stdout}\n"
                f"stderr={self.stderr}\n"
                f"error={self.error_message}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
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
            'skipped': self.skipped,
        }

    def to_json(self, json_provider=None) -> str:
        """Convert result to JSON string.

        Args:
            json_provider: JSON provider (injected for dependency inversion)
        """
        if json_provider is None:
            # デフォルト値禁止のため、単純な文字列表現にフォールバック
            return str(self.to_dict())

        return json_provider.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def summary(self) -> str:
        """Get a summary of the result."""
        return (
            f"[{'OK' if self.success else 'FAIL'}] op={self.op or self.cmd} "
            f"path={self.path} code={self.returncode} time={self.elapsed_time}s\n"
            f"content={str(self.content)[:100]}\n"
            f"stdout={str(self.stdout)[:100]}\n"
            f"stderr={str(self.stderr)[:100]}\n"
            f"error={self.error_message}"
        )

    def __repr__(self) -> str:
        """String representation of the result."""
        return (
            f"<OperationResult success={self.success} op={self.op} cmd={self.cmd} "
            f"path={self.path} returncode={self.returncode} error_message={self.error_message}>"
        )

    def get_error_output(self) -> str:
        """Get formatted error output."""
        parts = []
        if self.error_message:
            parts.append(f"error_message: {self.error_message}")
        if self.stderr:
            parts.append(f"stderr: {self.stderr}")
        if self.stdout and not self.success:
            parts.append(f"stdout: {self.stdout}")
        if self.exception:
            parts.append(f"exception: {self.exception}")
        return "\n".join(parts) if parts else "No error output"


__all__ = ["OperationResult"]

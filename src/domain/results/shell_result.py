"""Shell operation result class."""
from typing import Any, Optional

from src.domain.results.result import OperationResult


class ShellResult(OperationResult):
    """Result class for shell operations."""

    def __init__(self, success: Optional[bool] = None, stdout: Optional[str] = None,
                 stderr: Optional[str] = None, returncode: Optional[int] = None,
                 cmd: Optional[str] = None, error_message: Optional[str] = None,
                 exception: Optional[Exception] = None, start_time: Optional[float] = None,
                 end_time: Optional[float] = None, request: Optional[Any] = None,
                 metadata: Optional[dict[str, Any]] = None):
        """Initialize shell result.

        Args:
            success: Whether the operation was successful
            stdout: Standard output
            stderr: Standard error
            returncode: Process return code
            cmd: Command that was executed
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
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.cmd = cmd

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        base = super().to_dict()
        base.update({
            'stdout': self.stdout,
            'stderr': self.stderr,
            'returncode': self.returncode,
            'cmd': self.cmd,
        })
        return base

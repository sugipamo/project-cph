"""Shell operation result class."""
from typing import Any, Optional

from src.operations.results.result import OperationResult


class ShellResult(OperationResult):
    """Result class for shell operations."""

    def __init__(self, success: Optional[bool], stdout: Optional[str],
                 stderr: Optional[str], returncode: Optional[int],
                 cmd: Optional[str], error_message: Optional[str],
                 exception: Optional[Exception], start_time: Optional[float],
                 end_time: Optional[float], request: Optional[Any],
                 metadata: Optional[dict[str, Any]]):
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
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
            content=None,
            exists=None,
            path=None,
            op=None,
            cmd=cmd,
            request=request,
            start_time=start_time,
            end_time=end_time,
            error_message=error_message,
            exception=exception,
            metadata=metadata,
            skipped=False
        )

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

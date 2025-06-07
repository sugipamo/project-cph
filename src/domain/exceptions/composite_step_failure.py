"""Exception for composite step failures."""
from typing import Any, Optional


class CompositeStepFailureError(Exception):
    """Exception raised when a composite step fails."""

    def __init__(self, message: str, result: Optional[Any] = None, original_exception: Optional[Exception] = None):
        """Initialize composite step failure exception.

        Args:
            message: Error message
            result: Result object from failed step
            original_exception: Original exception that caused the failure
        """
        super().__init__(message)
        self.result = result
        self.original_exception = original_exception

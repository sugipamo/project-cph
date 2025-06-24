"""Exception for composite step failures."""
import uuid
from typing import Any, Optional

from .error_codes import ErrorCode, ErrorSuggestion, classify_error


class CompositeStepFailureError(Exception):
    """Exception raised when a composite step fails."""

    def __init__(self, message: str, result: Optional[Any] = None, original_exception: Optional[Exception] = None,
                 error_code: Optional[ErrorCode] = None, context: str = ""):
        """Initialize composite step failure exception.

        Args:
            message: Error message
            result: Result object from failed step
            original_exception: Original exception that caused the failure
            error_code: Standardized error code
            context: Context information for error classification
        """
        super().__init__(message)
        self.result = result
        self.original_exception = original_exception
        self.error_id = str(uuid.uuid4())[:8]

        # Auto-classify error if not provided
        if error_code is None and original_exception is not None:
            self.error_code = classify_error(original_exception, context)
        else:
            self.error_code = error_code or ErrorCode.UNKNOWN_ERROR

        self.context = context

    def get_suggestion(self) -> str:
        """Get actionable suggestion for this error."""
        return ErrorSuggestion.get_suggestion(self.error_code)

    def get_formatted_message(self) -> str:
        """Get formatted error message with code and suggestion."""
        base_message = str(self)
        suggestion = self.get_suggestion()
        recovery_actions = ErrorSuggestion.get_recovery_actions(self.error_code)

        formatted = f"[{self.error_code.value}#{self.error_id}] {base_message}\n"
        formatted += f"提案: {suggestion}\n"

        if recovery_actions:
            formatted += "回復手順:\n"
            for i, action in enumerate(recovery_actions, 1):
                formatted += f"  {i}. {action}\n"

        return formatted.rstrip()

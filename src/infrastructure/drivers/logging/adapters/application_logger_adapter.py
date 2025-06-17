"""Application Logger Adapter - bridges src/logging with LoggerInterface."""

import uuid
from typing import Any, Optional

from src.operations.interfaces.logger_interface import LoggerInterface

from ..format_info import FormatInfo
from ..interfaces.output_manager_interface import OutputManagerInterface
from ..types import LogLevel


class ApplicationLoggerAdapter(LoggerInterface):
    """Adapter that implements LoggerInterface using src/logging OutputManager."""

    def __init__(self, output_manager: OutputManagerInterface, name: str = __name__):
        """Initialize adapter with output manager.

        Args:
            output_manager: The underlying output manager
            name: Logger name for session tracking
        """
        self.output_manager = output_manager
        self.name = name
        self.session_id = str(uuid.uuid4())[:8]

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        formatted_message = self._format_message(message, args)
        self.output_manager.add(
            formatted_message,
            LogLevel.DEBUG,
            formatinfo=FormatInfo(color="gray")
        )

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        formatted_message = self._format_message(message, args)
        self.output_manager.add(
            formatted_message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="cyan")
        )

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        formatted_message = self._format_message(message, args)
        self.output_manager.add(
            formatted_message,
            LogLevel.WARNING,
            formatinfo=FormatInfo(color="yellow", bold=True)
        )

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        formatted_message = self._format_message(message, args)
        self.output_manager.add(
            formatted_message,
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        formatted_message = self._format_message(message, args)
        self.output_manager.add(
            formatted_message,
            LogLevel.CRITICAL,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def log_error_with_correlation(self, error_id: str, error_code: str,
                                  message: str, context: Optional[dict] = None) -> None:
        """Log an error with correlation ID and structured context."""
        formatted_message = (
            f"[ERROR#{error_id}] [{error_code}] {message} "
            f"(session: {self.session_id})"
        )

        if context:
            formatted_message += f" Context: {context}"

        self.output_manager.add(
            formatted_message,
            LogLevel.ERROR,
            formatinfo=FormatInfo(color="red", bold=True)
        )

    def log_operation_start(self, operation_id: str, operation_type: str,
                           details: Optional[dict] = None) -> None:
        """Log the start of an operation with correlation tracking."""
        message = f"[OP#{operation_id}] {operation_type} started (session: {self.session_id})"
        if details:
            message += f" Details: {details}"

        self.output_manager.add(
            message,
            LogLevel.INFO,
            formatinfo=FormatInfo(color="blue")
        )

    def log_operation_end(self, operation_id: str, operation_type: str,
                         success: bool, details: Optional[dict] = None) -> None:
        """Log the end of an operation with correlation tracking."""
        status = "completed" if success else "failed"
        message = f"[OP#{operation_id}] {operation_type} {status} (session: {self.session_id})"
        if details:
            message += f" Details: {details}"

        level = LogLevel.INFO if success else LogLevel.ERROR
        color = "green" if success else "red"

        self.output_manager.add(
            message,
            level,
            formatinfo=FormatInfo(color=color, bold=bool(not success))
        )

    def _format_message(self, message: str, args: tuple) -> str:
        """Format message with arguments (Python logging style)."""
        if args:
            try:
                return message % args
            except (TypeError, ValueError):
                # Fallback if formatting fails
                return f"{message} {args}"
        return message

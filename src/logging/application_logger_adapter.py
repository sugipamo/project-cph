"""Application Logger Adapter - bridges src/logging with LoggerInterface."""
import contextlib
import uuid
from typing import Any, Optional
from src.infrastructure.di_container import DIContainer
from src.operations.interfaces.logger_interface import LoggerInterface
from format_info import FormatInfo
from interfaces.output_manager_interface import OutputManagerInterface
from types import LogLevel

class ApplicationLoggerAdapter(LoggerInterface):
    """Adapter that implements LoggerInterface using src/logging OutputManager."""

    def __init__(self, output_manager: OutputManagerInterface, name: str=__name__):
        """Initialize adapter with output manager.

        Args:
            output_manager: The underlying output manager
            name: Logger name for session tracking
        """
        self.output_manager = output_manager
        self.name = name
        self.session_id = str(uuid.uuid4())[:8]
        self._config_manager = None
        with contextlib.suppress(Exception):
            self._config_manager = DIContainer.resolve('config_manager')

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        formatted_message = self._format_message(message, args)
        self.output_manager.add(formatted_message, LogLevel.DEBUG, formatinfo=FormatInfo(color='gray'), realtime=False)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        formatted_message = self._format_message(message, args)
        self.output_manager.add(formatted_message, LogLevel.INFO, formatinfo=FormatInfo(color='cyan'), realtime=False)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        formatted_message = self._format_message(message, args)
        self.output_manager.add(formatted_message, LogLevel.WARNING, formatinfo=FormatInfo(color='yellow', bold=True), realtime=False)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        formatted_message = self._format_message(message, args)
        self.output_manager.add(formatted_message, LogLevel.ERROR, formatinfo=FormatInfo(color='red', bold=True), realtime=False)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        formatted_message = self._format_message(message, args)
        self.output_manager.add(formatted_message, LogLevel.CRITICAL, formatinfo=FormatInfo(color='red', bold=True), realtime=False)

    def log_error_with_correlation(self, error_id: str, error_code: str, message: str, context: Optional[dict]) -> None:
        """Log an error with correlation ID and structured context."""
        formatted_message = f'[ERROR#{error_id}] [{error_code}] {message} (session: {self.session_id})'
        if context:
            formatted_message += f' Context: {context}'
        self.output_manager.add(formatted_message, LogLevel.ERROR, formatinfo=FormatInfo(color='red', bold=True), realtime=False)

    def log_operation_start(self, operation_id: str, operation_type: str, details: Optional[dict]) -> None:
        """Log the start of an operation with correlation tracking."""
        message = f'[OP#{operation_id}] {operation_type} started (session: {self.session_id})'
        if details:
            message += f' Details: {details}'
        self.output_manager.add(message, LogLevel.INFO, formatinfo=FormatInfo(color='blue'), realtime=False)

    def log_operation_end(self, operation_id: str, operation_type: str, success: bool, details: Optional[dict]) -> None:
        """Log the end of an operation with correlation tracking."""
        try:
            if self._config_manager:
                status_success = self._config_manager.resolve_config(['logging_config', 'adapters', 'application', 'status_success'], str)
                status_failure = self._config_manager.resolve_config(['logging_config', 'adapters', 'application', 'status_failure'], str)
                color_success = self._config_manager.resolve_config(['logging_config', 'adapters', 'application', 'color_success'], str)
                color_failure = self._config_manager.resolve_config(['logging_config', 'adapters', 'application', 'color_failure'], str)
            else:
                raise KeyError('Config manager not available')
        except (KeyError, Exception) as e:
            raise ValueError('Application adapter operation status configuration not found') from e
        status = status_success if success else status_failure
        message = f'[OP#{operation_id}] {operation_type} {status} (session: {self.session_id})'
        if details:
            message += f' Details: {details}'
        level = LogLevel.INFO if success else LogLevel.ERROR
        color = color_success if success else color_failure
        self.output_manager.add(message, level, formatinfo=FormatInfo(color=color, bold=bool(not success)), realtime=False)

    def _format_message(self, message: str, args: tuple) -> str:
        """Format message with arguments (Python logging style)."""
        if args:
            try:
                return message % args
            except (TypeError, ValueError):
                return f'{message} {args}'
        return message
"""Python logging implementation."""
import logging
import uuid
from typing import Any, Optional

from src.operations.interfaces.logger_interface import LoggerInterface


class PythonLogger(LoggerInterface):
    """Python logging implementation of LoggerInterface."""

    def __init__(self, name: str = __name__):
        """Initialize with logger name."""
        self.logger = logging.getLogger(name)
        self.session_id = str(uuid.uuid4())[:8]

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        self.logger.critical(message, *args, **kwargs)

    def log_error_with_correlation(self, error_id: str, error_code: str,
                                  message: str, context: Optional[dict] = None) -> None:
        """Log an error with correlation ID and structured context."""
        log_entry = {
            'session_id': self.session_id,
            'error_id': error_id,
            'error_code': error_code,
            'message': message,
            'context': context or {}
        }

        formatted_message = (
            f"[ERROR#{error_id}] [{error_code}] {message} "
            f"(session: {self.session_id})"
        )

        if context:
            formatted_message += f" Context: {context}"

        self.logger.error(formatted_message, extra={'structured_data': log_entry})

    def log_operation_start(self, operation_id: str, operation_type: str,
                           details: Optional[dict] = None) -> None:
        """Log the start of an operation with correlation tracking."""
        log_entry = {
            'session_id': self.session_id,
            'operation_id': operation_id,
            'operation_type': operation_type,
            'status': 'started',
            'details': details or {}
        }

        message = f"[OP#{operation_id}] {operation_type} started (session: {self.session_id})"
        if details:
            message += f" Details: {details}"

        self.logger.info(message, extra={'structured_data': log_entry})

    def log_operation_end(self, operation_id: str, operation_type: str,
                         success: bool, details: Optional[dict] = None) -> None:
        """Log the end of an operation with correlation tracking."""
        status = "completed" if success else "failed"
        log_entry = {
            'session_id': self.session_id,
            'operation_id': operation_id,
            'operation_type': operation_type,
            'status': status,
            'success': success,
            'details': details or {}
        }

        message = f"[OP#{operation_id}] {operation_type} {status} (session: {self.session_id})"
        if details:
            message += f" Details: {details}"

        log_method = self.logger.info if success else self.logger.error
        log_method(message, extra={'structured_data': log_entry})

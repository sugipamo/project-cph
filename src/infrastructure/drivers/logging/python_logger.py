"""Python logging implementation."""
import logging
from typing import Any

from src.domain.interfaces.logger_interface import LoggerInterface


class PythonLogger(LoggerInterface):
    """Python logging implementation of LoggerInterface."""

    def __init__(self, name: str = __name__):
        """Initialize with logger name."""
        self.logger = logging.getLogger(name)

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

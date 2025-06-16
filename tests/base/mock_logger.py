"""Mock logger implementation for testing."""
from typing import Any, List

from src.operations.interfaces.logger_interface import LoggerInterface


class MockLogger(LoggerInterface):
    """Mock logger that captures log messages for testing."""

    def __init__(self):
        """Initialize mock logger."""
        self.messages: List[tuple[str, str]] = []  # (level, message)

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        self.messages.append(("debug", message % args if args else message))

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        self.messages.append(("info", message % args if args else message))

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        self.messages.append(("warning", message % args if args else message))

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        self.messages.append(("error", message % args if args else message))

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        self.messages.append(("critical", message % args if args else message))

    def get_messages_by_level(self, level: str) -> List[str]:
        """Get all messages for a specific level."""
        return [msg for lvl, msg in self.messages if lvl == level]

    def clear(self) -> None:
        """Clear all captured messages."""
        self.messages.clear()

    def has_message(self, level: str, message: str) -> bool:
        """Check if a specific message was logged at a level."""
        return any(msg == message for lvl, msg in self.messages if lvl == level)

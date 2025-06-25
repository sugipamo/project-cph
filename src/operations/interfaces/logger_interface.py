"""Logger interface for dependency injection."""
from abc import ABC, abstractmethod
from typing import Any


class LoggerInterface(ABC):
    """Interface for logging operations."""

    @abstractmethod
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        pass

    @abstractmethod
    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        pass

    @abstractmethod
    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        pass

    @abstractmethod
    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        pass

    @abstractmethod
    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        pass

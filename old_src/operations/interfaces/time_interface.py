"""Time operations interface for dependency injection."""
from abc import ABC, abstractmethod


class TimeInterface(ABC):
    """Interface for time operations."""

    @abstractmethod
    def current_time(self) -> float:
        """Get current time as timestamp."""
        pass

    @abstractmethod
    def sleep(self, seconds: float) -> None:
        """Sleep for specified seconds."""
        pass

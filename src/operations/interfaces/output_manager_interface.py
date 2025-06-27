"""Output manager interface for dependency injection."""
from abc import ABC, abstractmethod
from typing import List, Optional, Union

from src.utils.format_info import FormatInfo
from src.utils.types import LogEntry, LogLevel


class OutputManagerInterface(ABC):
    """Abstract interface for output management."""

    @abstractmethod
    def add(self, message: Union[str, 'OutputManagerInterface'], level: LogLevel, formatinfo: Optional[FormatInfo], realtime: bool) -> None:
        """Add a log entry."""
        pass

    @abstractmethod
    def output(self, indent: int, level: LogLevel) -> str:
        """Generate output string."""
        pass

    @abstractmethod
    def flush(self) -> None:
        """Flush output to console."""
        pass

    @abstractmethod
    def flatten(self, level: LogLevel) -> List[LogEntry]:
        """Get flattened entries."""
        pass

    @abstractmethod
    def output_sorted(self, level: LogLevel) -> str:
        """Generate sorted output string."""
        pass

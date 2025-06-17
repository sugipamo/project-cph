"""Output manager interface for dependency injection."""

from abc import ABC, abstractmethod
from typing import List, Optional, Union

from ..format_info import FormatInfo
from ..types import LogEntry, LogLevel


class OutputManagerInterface(ABC):
    """Abstract interface for output management."""

    @abstractmethod
    def add(
        self,
        message: Union[str, 'OutputManagerInterface'],
        level: LogLevel = LogLevel.INFO,
        formatinfo: Optional[FormatInfo] = None,
        realtime: bool = False
    ) -> None:
        """Add a log entry."""
        pass

    @abstractmethod
    def output(self, indent: int = 0, level: LogLevel = LogLevel.DEBUG) -> str:
        """Generate output string."""
        pass

    @abstractmethod
    def flush(self) -> None:
        """Flush output to console."""
        pass

    @abstractmethod
    def flatten(self, level: LogLevel = LogLevel.DEBUG) -> List[LogEntry]:
        """Get flattened entries."""
        pass

    @abstractmethod
    def output_sorted(self, level: LogLevel = LogLevel.DEBUG) -> str:
        """Generate sorted output string."""
        pass
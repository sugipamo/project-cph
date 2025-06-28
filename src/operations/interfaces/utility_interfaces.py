"""Consolidated utility-related interfaces."""
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Pattern, Tuple

from src.operations.results.result import OperationResult


class LoggerInterface(ABC):
    """Interface for logging operations."""

    @abstractmethod
    def debug(self, message: str) -> None:
        """Log debug message."""
        pass

    @abstractmethod
    def info(self, message: str) -> None:
        """Log info message."""
        pass

    @abstractmethod
    def warning(self, message: str) -> None:
        """Log warning message."""
        pass

    @abstractmethod
    def error(self, message: str) -> None:
        """Log error message."""
        pass

    @abstractmethod
    def critical(self, message: str) -> None:
        """Log critical message."""
        pass


class OutputManagerInterface(ABC):
    """Interface for output management."""

    @abstractmethod
    def add(self, message: str, level: str, format_info: Optional[Any] = None, execution_detail: Optional[Any] = None) -> None:
        """Add a log entry."""
        pass

    @abstractmethod
    def output(self) -> List[str]:
        """Generate output as list of strings."""
        pass

    @abstractmethod
    def output_sorted(self) -> List[str]:
        """Generate sorted output."""
        pass

    @abstractmethod
    def flush(self, use_old_format: bool = False) -> None:
        """Flush output to console."""
        pass

    @abstractmethod
    def flatten(self, depth: int = 0) -> List[Tuple[int, Any]]:
        """Get flattened log entries."""
        pass


class OutputInterface(ABC):
    """Interface for output formatting and display."""

    @abstractmethod
    def format_output(self, result: OperationResult) -> str:
        """Format operation result for display."""
        pass

    @abstractmethod
    def display_output(self, formatted_output: str) -> None:
        """Display formatted output."""
        pass


class RegexInterface(ABC):
    """Interface for regex operations."""

    @abstractmethod
    def compile_pattern(self, pattern: str) -> Pattern:
        """Compile a regex pattern."""
        pass

    @abstractmethod
    def findall(self, pattern: str, text: str) -> List[str]:
        """Find all matches of pattern in text."""
        pass

    @abstractmethod
    def search(self, pattern: str, text: str) -> Optional[Any]:
        """Search for pattern in text."""
        pass

    @abstractmethod
    def substitute(self, pattern: str, replacement: str, text: str) -> str:
        """Substitute pattern with replacement in text."""
        pass


class DIContainerInterface(ABC):
    """Interface for dependency injection container."""

    @abstractmethod
    def resolve(self, key: str) -> Any:
        """Resolve a dependency by key.
        
        Args:
            key: Dependency identifier as string
            
        Returns:
            Resolved dependency instance
        """
        pass

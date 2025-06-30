"""Regex operations interface for dependency injection."""
from abc import ABC, abstractmethod
from typing import List


class RegexInterface(ABC):
    """Interface for regex operations."""

    @abstractmethod
    def compile_pattern(self, pattern: str) -> object:
        """Compile regex pattern."""
        pass

    @abstractmethod
    def findall(self, pattern: object, text: str) -> List[str]:
        """Find all matches of pattern in text."""
        pass

    @abstractmethod
    def search(self, pattern: object, text: str) -> object:
        """Search for pattern in text."""
        pass

    @abstractmethod
    def substitute(self, pattern: object, replacement: str, text: str) -> str:
        """Substitute pattern matches with replacement."""
        pass

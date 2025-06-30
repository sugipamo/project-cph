"""Regex operations provider for dependency injection."""
import re
from typing import List

from old_src.operations.interfaces.regex_interface import RegexInterface


class RegexProvider(RegexInterface):
    """Production regex operations provider."""

    def compile_pattern(self, pattern: str) -> object:
        """Compile regex pattern."""
        return re.compile(pattern)

    def findall(self, pattern: object, text: str) -> List[str]:
        """Find all matches of pattern in text."""
        return pattern.findall(text)

    def search(self, pattern: object, text: str) -> object:
        """Search for pattern in text."""
        return pattern.search(text)

    def substitute(self, pattern: object, replacement: str, text: str) -> str:
        """Substitute pattern matches with replacement."""
        return pattern.sub(replacement, text)

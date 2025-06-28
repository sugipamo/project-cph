"""Mock regex operations provider for testing."""
import re
from typing import List

from src.operations.interfaces.utility_interfaces import RegexInterface


class MockRegexProvider(RegexInterface):
    """Mock regex operations provider for testing."""

    def __init__(self):
        self.compiled_patterns = {}
        self.findall_calls = []
        self.search_calls = []
        self.substitute_calls = []

    def compile_pattern(self, pattern: str) -> object:
        """Compile regex pattern."""
        compiled = re.compile(pattern)
        self.compiled_patterns[pattern] = compiled
        return compiled

    def findall(self, pattern: object, text: str) -> List[str]:
        """Find all matches of pattern in text."""
        result = pattern.findall(text)
        self.findall_calls.append((pattern, text, result))
        return result

    def search(self, pattern: object, text: str) -> object:
        """Search for pattern in text."""
        result = pattern.search(text)
        self.search_calls.append((pattern, text, result))
        return result

    def substitute(self, pattern: object, replacement: str, text: str) -> str:
        """Substitute pattern matches with replacement."""
        result = pattern.sub(replacement, text)
        self.substitute_calls.append((pattern, replacement, text, result))
        return result

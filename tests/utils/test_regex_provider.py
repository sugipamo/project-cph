"""Tests for RegexProvider."""
import pytest

from src.utils.regex_provider import RegexProvider


class TestRegexProvider:
    """Test RegexProvider functionality."""

    @pytest.fixture
    def provider(self):
        """Create RegexProvider instance."""
        return RegexProvider()

    def test_compile_pattern(self, provider):
        """Test pattern compilation."""
        pattern = provider.compile_pattern(r"\d+")
        assert pattern is not None
        assert hasattr(pattern, 'findall')
        assert hasattr(pattern, 'search')
        assert hasattr(pattern, 'sub')

    def test_findall(self, provider):
        """Test finding all matches."""
        pattern = provider.compile_pattern(r"\d+")
        text = "There are 123 apples and 456 oranges"
        matches = provider.findall(pattern, text)
        assert matches == ["123", "456"]

    def test_findall_no_matches(self, provider):
        """Test findall with no matches."""
        pattern = provider.compile_pattern(r"\d+")
        text = "No numbers here"
        matches = provider.findall(pattern, text)
        assert matches == []

    def test_search(self, provider):
        """Test pattern search."""
        pattern = provider.compile_pattern(r"\d+")
        text = "The answer is 42"
        match = provider.search(pattern, text)
        assert match is not None
        assert match.group() == "42"

    def test_search_no_match(self, provider):
        """Test search with no match."""
        pattern = provider.compile_pattern(r"\d+")
        text = "No numbers here"
        match = provider.search(pattern, text)
        assert match is None

    def test_substitute(self, provider):
        """Test pattern substitution."""
        pattern = provider.compile_pattern(r"\d+")
        text = "Replace 123 with X"
        result = provider.substitute(pattern, "X", text)
        assert result == "Replace X with X"

    def test_substitute_no_matches(self, provider):
        """Test substitution with no matches."""
        pattern = provider.compile_pattern(r"\d+")
        text = "No numbers to replace"
        result = provider.substitute(pattern, "X", text)
        assert result == "No numbers to replace"

    def test_complex_pattern(self, provider):
        """Test with complex regex pattern."""
        pattern = provider.compile_pattern(r"[a-zA-Z]+@[a-zA-Z]+\.[a-zA-Z]+")
        text = "Contact us at test@example.com or admin@site.org"
        matches = provider.findall(pattern, text)
        assert "test@example.com" in matches
        assert "admin@site.org" in matches
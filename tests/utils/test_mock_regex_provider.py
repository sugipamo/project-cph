"""Tests for MockRegexProvider."""
import pytest

from src.utils.mock_regex_provider import MockRegexProvider


class TestMockRegexProvider:
    """Test MockRegexProvider functionality."""

    @pytest.fixture
    def provider(self):
        """Create MockRegexProvider instance."""
        return MockRegexProvider()

    def test_init(self, provider):
        """Test initialization."""
        assert provider.compiled_patterns == {}
        assert provider.findall_calls == []
        assert provider.search_calls == []
        assert provider.substitute_calls == []

    def test_compile_pattern_tracking(self, provider):
        """Test pattern compilation tracking."""
        pattern1 = provider.compile_pattern(r"\d+")
        pattern2 = provider.compile_pattern(r"[a-z]+")
        
        assert len(provider.compiled_patterns) == 2
        assert r"\d+" in provider.compiled_patterns
        assert r"[a-z]+" in provider.compiled_patterns
        assert provider.compiled_patterns[r"\d+"] == pattern1
        assert provider.compiled_patterns[r"[a-z]+"] == pattern2

    def test_findall_tracking(self, provider):
        """Test findall call tracking."""
        pattern = provider.compile_pattern(r"\d+")
        text = "123 and 456"
        result = provider.findall(pattern, text)
        
        assert result == ["123", "456"]
        assert len(provider.findall_calls) == 1
        assert provider.findall_calls[0][0] == pattern
        assert provider.findall_calls[0][1] == text
        assert provider.findall_calls[0][2] == result

    def test_search_tracking(self, provider):
        """Test search call tracking."""
        pattern = provider.compile_pattern(r"\d+")
        text = "The answer is 42"
        result = provider.search(pattern, text)
        
        assert result is not None
        assert result.group() == "42"
        assert len(provider.search_calls) == 1
        assert provider.search_calls[0][0] == pattern
        assert provider.search_calls[0][1] == text
        assert provider.search_calls[0][2] == result

    def test_substitute_tracking(self, provider):
        """Test substitute call tracking."""
        pattern = provider.compile_pattern(r"\d+")
        text = "Replace 123 with X"
        replacement = "X"
        result = provider.substitute(pattern, replacement, text)
        
        assert result == "Replace X with X"
        assert len(provider.substitute_calls) == 1
        assert provider.substitute_calls[0][0] == pattern
        assert provider.substitute_calls[0][1] == replacement
        assert provider.substitute_calls[0][2] == text
        assert provider.substitute_calls[0][3] == result

    def test_multiple_operations_tracking(self, provider):
        """Test tracking multiple operations."""
        pattern1 = provider.compile_pattern(r"\d+")
        pattern2 = provider.compile_pattern(r"[a-z]+")
        
        # Multiple findall calls
        provider.findall(pattern1, "123 456")
        provider.findall(pattern2, "hello world")
        
        # Multiple search calls
        provider.search(pattern1, "number 789")
        provider.search(pattern2, "test 123")
        
        # Multiple substitute calls
        provider.substitute(pattern1, "X", "123 456")
        provider.substitute(pattern2, "Y", "hello world")
        
        assert len(provider.compiled_patterns) == 2
        assert len(provider.findall_calls) == 2
        assert len(provider.search_calls) == 2
        assert len(provider.substitute_calls) == 2
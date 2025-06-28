import pytest
from unittest.mock import Mock, patch

from src.presentation.formatters import (
    extract_format_keys,
    format_with_missing_keys,
    format_string_simple,
    format_with_context,
    validate_template_keys,
)


class MockRegexOps:
    """Mock regex operations provider for testing"""
    def compile_pattern(self, pattern):
        import re
        return re.compile(pattern)
    
    def findall(self, pattern, string):
        import re
        if hasattr(pattern, 'findall'):
            return pattern.findall(string)
        return re.findall(pattern, string)


class TestFormatters:
    @pytest.fixture
    def regex_ops(self):
        return MockRegexOps()
    
    def test_extract_format_keys(self, regex_ops):
        template = "Hello {name}, you have {count} messages"
        keys = extract_format_keys(template, regex_ops)
        assert keys == ['name', 'count']
        
        # Test empty template
        assert extract_format_keys("", regex_ops) == []
        
        # Test no keys
        assert extract_format_keys("Hello world", regex_ops) == []
        
        # Test duplicate keys
        template = "{name} {name} {age}"
        keys = extract_format_keys(template, regex_ops)
        assert 'name' in keys
        assert 'age' in keys

    def test_format_with_missing_keys(self, regex_ops):
        template = "Hello {name}, you have {count} messages from {sender}"
        
        # Test with all keys provided
        result, missing = format_with_missing_keys(
            template, regex_ops, name="Alice", count=5, sender="Bob"
        )
        assert result == "Hello Alice, you have 5 messages from Bob"
        assert missing == []
        
        # Test with missing keys
        result, missing = format_with_missing_keys(
            template, regex_ops, name="Alice"
        )
        assert result == "Hello Alice, you have {count} messages from {sender}"
        assert set(missing) == {'count', 'sender'}

    def test_format_string_simple(self):
        template = "Hello {name}, welcome to {place}"
        context = {"name": "Alice", "place": "Wonderland"}
        
        result = format_string_simple(template, context)
        assert result == "Hello Alice, welcome to Wonderland"
        
        # Test with missing keys
        result = format_string_simple(template, {"name": "Alice"})
        assert result == "Hello Alice, welcome to {place}"
        
        # Test with non-string template
        assert format_string_simple(123, context) == 123
        
        # Test with numeric values
        template = "Count: {count}"
        result = format_string_simple(template, {"count": 42})
        assert result == "Count: 42"

    def test_format_with_context(self, regex_ops):
        template = "Hello {name}, you are {age} years old"
        context = {"name": "Bob", "age": 25}
        
        result = format_with_context(template, context, regex_ops)
        assert result == "Hello Bob, you are 25 years old"
        
        # Test with non-string template
        assert format_with_context(None, context, regex_ops) is None
        assert format_with_context(123, context, regex_ops) == 123
        
        # Test with complex format syntax (should fall back to simple)
        template = "Price: {price:.2f}"
        context = {"price": 10.5}
        result = format_with_context(template, context, regex_ops)
        # Should fall back to simple replacement due to format spec
        assert "{price:.2f}" in result or "10.5" in result

    def test_validate_template_keys(self, regex_ops):
        template = "Hello {name}, your ID is {id}"
        
        # Test with all required keys present
        valid, missing = validate_template_keys(
            template, ["name", "id"], regex_ops
        )
        assert valid is True
        assert missing == []
        
        # Test with missing required keys
        valid, missing = validate_template_keys(
            template, ["name", "id", "email"], regex_ops
        )
        assert valid is False
        assert missing == ["email"]
        
        # Test with subset of required keys
        valid, missing = validate_template_keys(
            template, ["name"], regex_ops
        )
        assert valid is True
        assert missing == []

    def test_format_with_context_edge_cases(self, regex_ops):
        # Test with empty template
        assert format_with_context("", {"key": "value"}, regex_ops) == ""
        
        # Test with empty context
        template = "Hello {name}"
        result = format_with_context(template, {}, regex_ops)
        assert result == "Hello {name}"
        
        # Test with special characters in values
        template = "Path: {path}"
        context = {"path": "/usr/bin/python"}
        result = format_with_context(template, context, regex_ops)
        assert result == "Path: /usr/bin/python"

    def test_format_keys_caching(self, regex_ops):
        # The extract_format_keys function uses lru_cache
        # Test that it works correctly with caching
        template = "Cached {key1} and {key2}"
        
        # First call
        keys1 = extract_format_keys(template, regex_ops)
        # Second call (should hit cache)
        keys2 = extract_format_keys(template, regex_ops)
        
        assert keys1 == keys2
        assert keys1 == ['key1', 'key2']
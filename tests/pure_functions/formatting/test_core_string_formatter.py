"""
Comprehensive tests for string formatter module
"""
import pytest
from src.pure_functions.formatting.core.string_formatter import (
    extract_format_keys,
    format_with_missing_keys,
    format_with_context,
    SafeFormatter,
    # Backward compatibility aliases
    extract_template_keys,
    safe_format_template
)


class TestExtractFormatKeys:
    """Test extract_format_keys function"""
    
    def test_simple_key_extraction(self):
        """Test extracting simple keys"""
        template = "/path/{foo}/{bar}.py"
        keys = extract_format_keys(template)
        assert keys == ["foo", "bar"]
    
    def test_no_keys(self):
        """Test template with no keys"""
        template = "/path/to/file.py"
        keys = extract_format_keys(template)
        assert keys == []
    
    def test_duplicate_keys(self):
        """Test template with duplicate keys"""
        template = "{foo}/path/{bar}/{foo}"
        keys = extract_format_keys(template)
        assert keys == ["foo", "bar", "foo"]
    
    def test_empty_template(self):
        """Test empty template"""
        template = ""
        keys = extract_format_keys(template)
        assert keys == []
    
    def test_nested_braces(self):
        """Test template with nested braces (not valid Python format)"""
        template = "{foo}{{bar}}"
        keys = extract_format_keys(template)
        assert keys == ["foo"]
    
    def test_numeric_keys(self):
        """Test keys with numbers"""
        template = "{key1}/{key2}/{key3}"
        keys = extract_format_keys(template)
        assert keys == ["key1", "key2", "key3"]
    
    def test_underscore_keys(self):
        """Test keys with underscores"""
        template = "{my_key}/{another_key}"
        keys = extract_format_keys(template)
        assert keys == ["my_key", "another_key"]
    
    def test_caching_performance(self):
        """Test that results are cached (performance optimization)"""
        template = "/path/{foo}/{bar}.py"
        # First call
        keys1 = extract_format_keys(template)
        # Second call should use cache
        keys2 = extract_format_keys(template)
        assert keys1 == keys2
        assert id(keys1) == id(keys2)  # Same object due to caching


class TestFormatWithMissingKeys:
    """Test format_with_missing_keys function"""
    
    def test_full_replacement(self):
        """Test template with all keys provided"""
        template = "/path/{foo}/{bar}.py"
        result, missing = format_with_missing_keys(template, foo="A", bar="B")
        assert result == "/path/A/B.py"
        assert missing == []
    
    def test_partial_replacement(self):
        """Test template with some keys missing"""
        template = "/path/{foo}/{bar}.py"
        result, missing = format_with_missing_keys(template, foo="A")
        assert result == "/path/A/{bar}.py"
        assert missing == ["bar"]
    
    def test_no_replacement(self):
        """Test template with no keys provided"""
        template = "/path/{foo}/{bar}.py"
        result, missing = format_with_missing_keys(template)
        assert result == "/path/{foo}/{bar}.py"
        assert missing == ["foo", "bar"]
    
    def test_extra_kwargs(self):
        """Test with extra kwargs that aren't in template"""
        template = "/path/{foo}.py"
        result, missing = format_with_missing_keys(template, foo="A", bar="B", baz="C")
        assert result == "/path/A.py"
        assert missing == []
    
    def test_empty_template(self):
        """Test empty template"""
        result, missing = format_with_missing_keys("", foo="A")
        assert result == ""
        assert missing == []
    
    def test_template_without_keys(self):
        """Test template without format keys"""
        template = "/path/to/file.py"
        result, missing = format_with_missing_keys(template, foo="A")
        assert result == "/path/to/file.py"
        assert missing == []
    
    def test_special_characters_in_values(self):
        """Test values with special characters"""
        template = "{greeting}, {name}!"
        result, missing = format_with_missing_keys(
            template, 
            greeting="Hello", 
            name="World {test}"
        )
        assert result == "Hello, World {test}!"
        assert missing == []


class TestFormatWithContext:
    """Test format_with_context function"""
    
    def test_basic_formatting(self):
        """Test basic template formatting"""
        template = "/path/{foo}/{bar}.py"
        context = {"foo": "A", "bar": "B"}
        result = format_with_context(template, context)
        assert result == "/path/A/B.py"
    
    def test_missing_keys_preserved(self):
        """Test that missing keys are preserved"""
        template = "/path/{foo}/{bar}.py"
        context = {"foo": "A"}
        result = format_with_context(template, context)
        assert result == "/path/A/{bar}.py"
    
    def test_non_string_values(self):
        """Test formatting with non-string values"""
        template = "Count: {count}, Valid: {valid}"
        context = {"count": 42, "valid": True}
        result = format_with_context(template, context)
        assert result == "Count: 42, Valid: True"
    
    def test_none_values(self):
        """Test formatting with None values"""
        template = "Value: {value}"
        context = {"value": None}
        result = format_with_context(template, context)
        assert result == "Value: None"
    
    def test_non_string_template(self):
        """Test non-string template returns as-is"""
        result = format_with_context(123, {"foo": "bar"})
        assert result == 123
    
    def test_empty_context(self):
        """Test formatting with empty context"""
        template = "/path/{foo}.py"
        result = format_with_context(template, {})
        assert result == "/path/{foo}.py"
    
    def test_complex_template(self):
        """Test complex template with multiple same keys"""
        template = "{base}/{dir}/{base}.{ext}"
        context = {"base": "file", "dir": "subdir", "ext": "py"}
        result = format_with_context(template, context)
        assert result == "file/subdir/file.py"
    
    def test_fallback_mechanism(self):
        """Test fallback mechanism for edge cases"""
        # This should trigger the fallback in the except block
        template = "/path/{foo}/{bar}.py"
        context = {"foo": "A", "bar": "B"}
        result = format_with_context(template, context)
        assert result == "/path/A/B.py"


class TestSafeFormatter:
    """Test SafeFormatter class"""
    
    def test_basic_usage(self):
        """Test basic SafeFormatter usage"""
        formatter = SafeFormatter()
        result = formatter.format("{greeting}, {name}!", {"greeting": "Hello", "name": "World"})
        assert result == "Hello, World!"
    
    def test_with_default_context(self):
        """Test SafeFormatter with default context"""
        default_context = {"greeting": "Hi", "punctuation": "!"}
        formatter = SafeFormatter(default_context)
        
        # Use default values
        result = formatter.format("{greeting}, {name}{punctuation}", {"name": "Alice"})
        assert result == "Hi, Alice!"
        
        # Override default values
        result = formatter.format("{greeting}, {name}{punctuation}", 
                                {"greeting": "Hello", "name": "Bob"})
        assert result == "Hello, Bob!"
    
    def test_format_with_validation(self):
        """Test format_with_validation method"""
        formatter = SafeFormatter({"base": "default"})
        
        # All keys present
        result, missing = formatter.format_with_validation(
            "{base}/{path}", 
            {"path": "file.py"}
        )
        assert result == "default/file.py"
        assert missing == []
        
        # Missing keys
        result, missing = formatter.format_with_validation(
            "{base}/{path}/{extra}"
        )
        assert result == "default/{path}/{extra}"
        assert missing == ["path", "extra"]
    
    def test_none_context(self):
        """Test SafeFormatter with None context"""
        formatter = SafeFormatter({"foo": "default"})
        result = formatter.format("{foo}", None)
        assert result == "default"
    
    def test_empty_default_context(self):
        """Test SafeFormatter with empty default context"""
        formatter = SafeFormatter({})
        result = formatter.format("{foo}", {"foo": "bar"})
        assert result == "bar"


class TestBackwardCompatibility:
    """Test backward compatibility aliases"""
    
    def test_extract_template_keys_alias(self):
        """Test extract_template_keys is an alias for extract_format_keys"""
        assert extract_template_keys == extract_format_keys
        
        # Functional test
        template = "/path/{foo}/{bar}.py"
        keys = extract_template_keys(template)
        assert keys == ["foo", "bar"]
    
    def test_safe_format_template_alias(self):
        """Test safe_format_template is an alias for format_with_missing_keys"""
        assert safe_format_template == format_with_missing_keys
        
        # Functional test
        template = "/path/{foo}.py"
        result, missing = safe_format_template(template, foo="test")
        assert result == "/path/test.py"
        assert missing == []


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_malformed_templates(self):
        """Test handling of malformed templates"""
        # Unclosed brace
        template = "/path/{foo/{bar}.py"
        keys = extract_format_keys(template)
        assert keys == ["bar"]  # Only valid keys extracted
        
        # Empty braces
        template = "/path/{}/file.py"
        keys = extract_format_keys(template)
        assert keys == []  # No valid key
    
    def test_unicode_handling(self):
        """Test Unicode character handling"""
        template = "/path/{name}/{文件}.py"
        context = {"name": "テスト", "文件": "测试"}
        result = format_with_context(template, context)
        assert result == "/path/テスト/测试.py"
    
    def test_large_context(self):
        """Test formatting with large context dictionary"""
        template = "{key_50}"
        context = {f"key_{i}": f"value_{i}" for i in range(100)}
        result = format_with_context(template, context)
        assert result == "value_50"
    
    def test_recursive_values(self):
        """Test handling of recursive format strings in values"""
        template = "{a}"
        context = {"a": "{b}", "b": "final"}
        result = format_with_context(template, context)
        assert result == "{b}"  # Should not recursively format
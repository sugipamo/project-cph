"""
Tests for Python format engine
"""
import pytest
from src.operations.formatters.python_format_engine import PythonFormatEngine, EnhancedPythonFormatEngine
from src.operations.formatters.base_format_engine import FormatContext, FormatSyntaxType


class TestPythonFormatEngine:
    """Test PythonFormatEngine"""
    
    def setup_method(self):
        """Set up test engine"""
        self.engine = PythonFormatEngine()
    
    def test_engine_properties(self):
        """Test engine properties"""
        assert self.engine.syntax_type == FormatSyntaxType.PYTHON
        assert self.engine.name == "python_format"
    
    def test_supports_syntax_basic(self):
        """Test basic syntax support detection"""
        # Basic {key} format
        assert self.engine.supports_syntax("{name}") is True
        assert self.engine.supports_syntax("Hello {name}!") is True
        assert self.engine.supports_syntax("{foo}/{bar}") is True
        
        # No placeholders
        assert self.engine.supports_syntax("no placeholders") is False
        assert self.engine.supports_syntax("") is False
    
    def test_supports_syntax_advanced(self):
        """Test advanced syntax support detection"""
        # Advanced format specifications
        assert self.engine.supports_syntax("{value:>10}") is True
        assert self.engine.supports_syntax("{price:.2f}") is True
        assert self.engine.supports_syntax("{name!r}") is True
        assert self.engine.supports_syntax("{0}") is True
    
    def test_basic_format_success(self):
        """Test basic successful formatting"""
        template = "Hello {name}!"
        context = FormatContext(data={"name": "World"})
        
        result = self.engine.format(template, context)
        
        assert result.success is True
        assert result.formatted_text == "Hello World!"
        assert result.missing_keys == []
    
    def test_basic_format_missing_keys_strict(self):
        """Test basic formatting with missing keys in strict mode"""
        template = "Hello {name}! Welcome to {place}."
        context = FormatContext(data={"name": "World"}, strict_mode=True)
        
        result = self.engine.format(template, context)
        
        assert result.success is False
        assert result.missing_keys == ["place"]
        assert "Missing keys" in result.error_message
    
    def test_basic_format_missing_keys_non_strict(self):
        """Test basic formatting with missing keys in non-strict mode"""
        template = "Hello {name}! Welcome to {place}."
        context = FormatContext(data={"name": "World"}, strict_mode=False)
        
        result = self.engine.format(template, context)
        
        assert result.success is True
        assert result.formatted_text == "Hello World! Welcome to {place}."
        assert result.missing_keys == ["place"]
    
    def test_advanced_format_success(self):
        """Test advanced format specifications"""
        template = "{name:>10} | {value:8.2f} | {flag!r}"
        context = FormatContext(data={
            "name": "test",
            "value": 123.456,
            "flag": True
        })
        
        result = self.engine.format(template, context)
        
        assert result.success is True
        assert "test" in result.formatted_text
        assert "123.46" in result.formatted_text
        assert "True" in result.formatted_text
    
    def test_advanced_format_missing_key_strict(self):
        """Test advanced formatting with missing key in strict mode"""
        template = "{name:>10} | {missing:.2f}"
        context = FormatContext(data={"name": "test"}, strict_mode=True)
        
        result = self.engine.format(template, context)
        
        assert result.success is False
        assert result.missing_keys == ["missing"]
    
    def test_advanced_format_missing_key_non_strict(self):
        """Test advanced formatting with missing key in non-strict mode"""
        template = "{name:>10} | {missing:.2f}"
        context = FormatContext(data={"name": "test"}, strict_mode=False)
        
        result = self.engine.format(template, context)
        
        # Should use fallback
        assert result.missing_keys == ["missing"]
    
    def test_format_error_handling(self):
        """Test error handling in formatting"""
        template = "{value:invalid_spec}"
        context = FormatContext(data={"value": "text"})
        
        result = self.engine.format(template, context)
        
        assert result.success is False
        assert "Format error" in result.error_message
    
    def test_extract_all_format_keys(self):
        """Test key extraction from templates"""
        # Basic keys
        keys = self.engine._extract_all_format_keys("{name} {value}")
        assert "name" in keys
        assert "value" in keys
        
        # Advanced format specs
        keys = self.engine._extract_all_format_keys("{name:>10} {value:.2f} {flag!r}")
        assert "name" in keys
        assert "value" in keys
        assert "flag" in keys
        
        # Positional arguments should be ignored
        keys = self.engine._extract_all_format_keys("{0} {1} {name}")
        assert "name" in keys
        assert "0" not in keys
        assert "1" not in keys


class TestEnhancedPythonFormatEngine:
    """Test EnhancedPythonFormatEngine"""
    
    def setup_method(self):
        """Set up test engine"""
        self.engine = EnhancedPythonFormatEngine()
    
    def test_engine_properties(self):
        """Test enhanced engine properties"""
        assert self.engine.syntax_type == FormatSyntaxType.PYTHON
        assert self.engine.name == "enhanced_python_format"
    
    def test_basic_functionality_inherited(self):
        """Test that basic functionality is inherited"""
        template = "Hello {name}!"
        context = FormatContext(data={"name": "World"})
        
        result = self.engine.format(template, context)
        
        assert result.success is True
        assert result.formatted_text == "Hello World!"
    
    def test_custom_formatters_support(self):
        """Test custom formatters support"""
        template = "{name}"
        context = FormatContext(
            data={"name": "test"},
            extra_options={"custom_formatters": {"special": "value"}}
        )
        
        # Should still work even with custom formatters
        result = self.engine.format(template, context)
        assert result.success is True


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def setup_method(self):
        """Set up test engine"""
        self.engine = PythonFormatEngine()
    
    def test_empty_template(self):
        """Test empty template"""
        context = FormatContext(data={"key": "value"})
        result = self.engine.format("", context)
        
        assert result.success is True
        assert result.formatted_text == ""
    
    def test_empty_data(self):
        """Test empty data"""
        template = "no placeholders"
        context = FormatContext(data={})
        
        result = self.engine.format(template, context)
        
        assert result.success is True
        assert result.formatted_text == "no placeholders"
    
    def test_unicode_handling(self):
        """Test Unicode character handling"""
        template = "Hello {name}! 🎉"
        context = FormatContext(data={"name": "世界"})
        
        result = self.engine.format(template, context)
        
        assert result.success is True
        assert "世界" in result.formatted_text
        assert "🎉" in result.formatted_text
    
    def test_complex_data_types(self):
        """Test complex data types"""
        template = "{items} | {count}"
        context = FormatContext(data={
            "items": ["a", "b", "c"],
            "count": 3
        })
        
        result = self.engine.format(template, context)
        
        assert result.success is True
        assert "['a', 'b', 'c']" in result.formatted_text or "[a, b, c]" in result.formatted_text
        assert "3" in result.formatted_text
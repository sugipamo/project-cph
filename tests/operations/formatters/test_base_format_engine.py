"""
Tests for base format engine components
"""
import pytest
from src.operations.formatters.base_format_engine import (
    FormatSyntaxType,
    FormatContext,
    FormatResult,
    FormatEngine
)


class TestFormatSyntaxType:
    """Test FormatSyntaxType enum"""
    
    def test_enum_values(self):
        """Test enum values"""
        assert FormatSyntaxType.PYTHON.value == "python"
        assert FormatSyntaxType.PRINTF.value == "printf"
        assert FormatSyntaxType.JINJA2.value == "jinja2"
        assert FormatSyntaxType.TEMPLATE.value == "template"


class TestFormatContext:
    """Test FormatContext dataclass"""
    
    def test_basic_creation(self):
        """Test basic context creation"""
        data = {"name": "test", "value": 123}
        context = FormatContext(data=data)
        
        assert context.data == data
        assert context.syntax_type == FormatSyntaxType.PYTHON
        assert context.strict_mode is True
        assert context.fallback_value == ""
        assert context.extra_options is None
    
    def test_custom_options(self):
        """Test context with custom options"""
        data = {"key": "value"}
        extra_options = {"custom": "option"}
        
        context = FormatContext(
            data=data,
            syntax_type=FormatSyntaxType.JINJA2,
            strict_mode=False,
            fallback_value="N/A",
            extra_options=extra_options
        )
        
        assert context.data == data
        assert context.syntax_type == FormatSyntaxType.JINJA2
        assert context.strict_mode is False
        assert context.fallback_value == "N/A"
        assert context.extra_options == extra_options
    
    def test_immutability(self):
        """Test that context is immutable"""
        data = {"key": "value"}
        context = FormatContext(data=data)
        
        # Should not be able to modify
        with pytest.raises(AttributeError):
            context.data = {"new": "data"}


class TestFormatResult:
    """Test FormatResult class"""
    
    def test_successful_result(self):
        """Test successful format result"""
        result = FormatResult("formatted text")
        
        assert result.formatted_text == "formatted text"
        assert result.success is True
        assert result.missing_keys == []
        assert result.error_message is None
        assert result.is_success is True
        assert str(result) == "formatted text"
    
    def test_failed_result(self):
        """Test failed format result"""
        missing_keys = ["key1", "key2"]
        error_msg = "Missing keys"
        
        result = FormatResult(
            formatted_text="partial",
            success=False,
            missing_keys=missing_keys,
            error_message=error_msg
        )
        
        assert result.formatted_text == "partial"
        assert result.success is False
        assert result.missing_keys == missing_keys
        assert result.error_message == error_msg
        assert result.is_success is False
    
    def test_repr(self):
        """Test string representation"""
        result = FormatResult("short text")
        assert "short text" in repr(result)
        assert "success=True" in repr(result)
        
        # Test truncation for long text
        long_text = "a" * 100
        result_long = FormatResult(long_text)
        repr_str = repr(result_long)
        assert "..." in repr_str
        assert len(repr_str) < len(long_text) + 50


class MockFormatEngine(FormatEngine):
    """Mock format engine for testing"""
    
    def supports_syntax(self, template: str) -> bool:
        return "{" in template
    
    def format(self, template: str, context: FormatContext) -> FormatResult:
        if "error" in template:
            return FormatResult(template, success=False, error_message="Mock error")
        return FormatResult(f"formatted: {template}")
    
    @property
    def syntax_type(self) -> FormatSyntaxType:
        return FormatSyntaxType.PYTHON
    
    @property
    def name(self) -> str:
        return "mock_engine"


class TestFormatEngine:
    """Test FormatEngine abstract class"""
    
    def test_abstract_methods(self):
        """Test that FormatEngine cannot be instantiated directly"""
        with pytest.raises(TypeError):
            FormatEngine()
    
    def test_mock_engine(self):
        """Test mock engine implementation"""
        engine = MockFormatEngine()
        
        assert engine.syntax_type == FormatSyntaxType.PYTHON
        assert engine.name == "mock_engine"
        assert engine.supports_syntax("{key}") is True
        assert engine.supports_syntax("no placeholders") is False
        
        # Test successful formatting
        context = FormatContext(data={"key": "value"})
        result = engine.format("{key}", context)
        
        assert result.success is True
        assert result.formatted_text == "formatted: {key}"
        
        # Test error formatting
        error_result = engine.format("{error}", context)
        assert error_result.success is False
        assert error_result.error_message == "Mock error"
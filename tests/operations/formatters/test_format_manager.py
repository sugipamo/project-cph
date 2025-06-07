"""
Tests for format manager
"""
import pytest
from src.application.formatters.format_manager import FormatManager  # get_format_manager, format_template removed
from src.application.formatters.base.base_format_engine import FormatSyntaxType, FormatEngine, FormatContext, FormatResult


class MockFormatEngine(FormatEngine):
    """Mock format engine for testing"""
    
    def __init__(self, name: str, syntax_type: FormatSyntaxType):
        self._name = name
        self._syntax_type = syntax_type
    
    def supports_syntax(self, template: str) -> bool:
        return f"[{self._name}]" in template
    
    def format(self, template: str, context: FormatContext) -> FormatResult:
        return FormatResult(f"{self._name}: {template}")
    
    @property
    def syntax_type(self) -> FormatSyntaxType:
        return self._syntax_type
    
    @property
    def name(self) -> str:
        return self._name


class TestFormatManager:
    """Test FormatManager class"""
    
    def setup_method(self):
        """Set up fresh format manager"""
        self.manager = FormatManager()
    
    def test_initialization(self):
        """Test manager initialization"""
        # Should have default engines registered
        assert len(self.manager._engines) >= 1
        assert FormatSyntaxType.PYTHON in self.manager._engines
        assert self.manager._default_engine is not None
    
    def test_register_engine(self):
        """Test engine registration"""
        mock_engine = MockFormatEngine("test", FormatSyntaxType.PRINTF)
        
        # Register engine
        self.manager.register_engine(mock_engine)
        
        assert FormatSyntaxType.PRINTF in self.manager._engines
        assert self.manager._engines[FormatSyntaxType.PRINTF] == mock_engine
    
    def test_register_default_engine(self):
        """Test default engine registration"""
        mock_engine = MockFormatEngine("default_test", FormatSyntaxType.JINJA2)
        
        # Register as default
        self.manager.register_engine(mock_engine, is_default=True)
        
        assert self.manager._default_engine == mock_engine
    
    def test_format_with_explicit_syntax(self):
        """Test formatting with explicit syntax type"""
        template = "{name}"
        data = {"name": "test"}
        
        result = self.manager.format(
            template=template,
            data=data,
            syntax_type=FormatSyntaxType.PYTHON
        )
        
        assert result.success is True
        assert "test" in result.formatted_text
    
    def test_format_with_auto_detection(self):
        """Test formatting with auto-detection"""
        # Register mock engine
        mock_engine = MockFormatEngine("mock", FormatSyntaxType.PRINTF)
        self.manager.register_engine(mock_engine)
        
        template = "[mock] template"
        data = {"key": "value"}
        
        result = self.manager.format(template=template, data=data)
        
        assert result.success is True
        assert "mock:" in result.formatted_text
    
    def test_format_fallback_to_default(self):
        """Test fallback to default engine"""
        template = "unsupported template"
        data = {"key": "value"}
        
        result = self.manager.format(template=template, data=data)
        
        # Should use default engine
        assert result.success is True
    
    def test_format_with_options(self):
        """Test formatting with extra options"""
        template = "{name}"
        data = {"name": "test"}
        extra_option = "value"
        
        result = self.manager.format(
            template=template,
            data=data,
            strict_mode=False,
            custom_option=extra_option
        )
        
        assert result.success is True
    
    def test_get_supported_syntax_types(self):
        """Test getting supported syntax types"""
        syntax_types = self.manager.get_supported_syntax_types()
        
        assert isinstance(syntax_types, list)
        assert FormatSyntaxType.PYTHON in syntax_types
    
    def test_is_syntax_supported(self):
        """Test syntax support checking"""
        assert self.manager.is_syntax_supported(FormatSyntaxType.PYTHON) is True
        
        # Register mock engine
        mock_engine = MockFormatEngine("test", FormatSyntaxType.PRINTF)
        self.manager.register_engine(mock_engine)
        
        assert self.manager.is_syntax_supported(FormatSyntaxType.PRINTF) is True
        assert self.manager.is_syntax_supported(FormatSyntaxType.JINJA2) is False
    
    def test_detect_engine(self):
        """Test engine auto-detection"""
        # Register mock engines
        mock1 = MockFormatEngine("mock1", FormatSyntaxType.PRINTF)
        mock2 = MockFormatEngine("mock2", FormatSyntaxType.JINJA2)
        
        self.manager.register_engine(mock1)
        self.manager.register_engine(mock2)
        
        # Should detect mock1
        engine = self.manager._detect_engine("[mock1] template")
        assert engine == mock1
        
        # Should detect mock2
        engine = self.manager._detect_engine("[mock2] template")
        assert engine == mock2
        
        # Should fallback to default
        engine = self.manager._detect_engine("no special markers")
        assert engine == self.manager._default_engine


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def setup_method(self):
        """Set up format manager"""
        self.manager = FormatManager()
    
    def test_empty_engines(self):
        """Test behavior with no engines"""
        # Create fresh manager with no engines
        empty_manager = FormatManager()
        empty_manager._engines = {}
        empty_manager._default_engine = None
        
        template = "{name}"
        data = {"name": "test"}
        
        # Should handle gracefully
        with pytest.raises((IndexError, TypeError)):
            empty_manager.format(template, data)
    
    def test_engine_format_error(self):
        """Test handling of engine format errors"""
        # This test depends on the actual Python engine behavior
        template = "{value:invalid_format_spec}"
        data = {"value": "test"}
        
        result = self.manager.format(template, data)
        
        # Should handle error gracefully
        assert isinstance(result, FormatResult)
    
    def test_invalid_syntax_type(self):
        """Test with invalid syntax type"""
        template = "{name}"
        data = {"name": "test"}
        
        # Use unsupported syntax type
        result = self.manager.format(
            template=template,
            data=data,
            syntax_type=FormatSyntaxType.JINJA2  # Not registered by default
        )
        
        # Should fallback to auto-detection
        assert isinstance(result, FormatResult)
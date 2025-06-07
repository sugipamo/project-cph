"""
Tests for UnifiedFormatter module
"""
import pytest
from unittest.mock import Mock, patch

from src.application.formatters.unified_formatter import (
    UnifiedFormatter, get_unified_formatter, format_string_advanced, format_string
)
from src.application.formatters.base.base_format_engine import FormatSyntaxType


class TestUnifiedFormatter:
    """Tests for UnifiedFormatter class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.formatter = UnifiedFormatter()
    
    def test_formatter_initialization(self):
        """Test UnifiedFormatter initialization"""
        formatter = UnifiedFormatter()
        assert formatter._format_manager is not None
    
    @patch('src.application.formatters.unified_formatter.get_format_manager')
    def test_format_string_advanced_success(self, mock_get_manager):
        """Test successful advanced string formatting"""
        # Setup mock format manager
        mock_manager = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.formatted_text = "Hello, World!"
        mock_manager.format.return_value = mock_result
        mock_get_manager.return_value = mock_manager
        
        formatter = UnifiedFormatter()
        result = formatter.format_string_advanced(
            "Hello, {name}!", 
            {"name": "World"},
            FormatSyntaxType.PYTHON,
            True
        )
        
        assert result == "Hello, World!"
        mock_manager.format.assert_called_once_with(
            template="Hello, {name}!",
            data={"name": "World"},
            syntax_type=FormatSyntaxType.PYTHON,
            strict_mode=True
        )
    
    @patch('src.application.formatters.unified_formatter.get_format_manager')
    def test_format_string_advanced_failure(self, mock_get_manager):
        """Test advanced formatting failure with fallback"""
        # Setup mock format manager that fails
        mock_manager = Mock()
        mock_result = Mock()
        mock_result.success = False
        mock_manager.format.return_value = mock_result
        mock_get_manager.return_value = mock_manager
        
        formatter = UnifiedFormatter()
        result = formatter.format_string_advanced(
            "Hello, {name}!", 
            {"name": "World"}
        )
        
        # Should return original template on failure
        assert result == "Hello, {name}!"
    
    @patch('src.application.formatters.unified_formatter.get_format_manager')
    @patch('src.application.formatters.unified_formatter.format_string_pure')
    def test_format_string_advanced_exception_fallback(self, mock_format_simple, mock_get_manager):
        """Test advanced formatting exception with fallback to simple formatting"""
        # Setup mock format manager that raises exception
        mock_manager = Mock()
        mock_manager.format.side_effect = Exception("Format error")
        mock_get_manager.return_value = mock_manager
        mock_format_simple.return_value = "Hello, World!"
        
        formatter = UnifiedFormatter()
        result = formatter.format_string_advanced(
            "Hello, {name}!", 
            {"name": "World"}
        )
        
        assert result == "Hello, World!"
        mock_format_simple.assert_called_once_with("Hello, {name}!", {"name": "World"})
    
    @patch('src.application.formatters.unified_formatter.format_string_pure')  
    def test_format_string_basic_mode(self, mock_format_simple):
        """Test basic string formatting mode"""
        mock_format_simple.return_value = "Hello, World!"
        
        result = self.formatter.format_string(
            "Hello, {name}!", 
            {"name": "World"},
            use_advanced=False
        )
        
        assert result == "Hello, World!"
        mock_format_simple.assert_called_once_with("Hello, {name}!", {"name": "World"})
    
    def test_format_string_advanced_mode(self):
        """Test advanced string formatting mode"""
        with patch.object(self.formatter, 'format_string_advanced') as mock_advanced:
            mock_advanced.return_value = "Hello, World!"
            
            result = self.formatter.format_string(
                "Hello, {name}!", 
                {"name": "World"},
                use_advanced=True
            )
            
            assert result == "Hello, World!"
            mock_advanced.assert_called_once_with("Hello, {name}!", {"name": "World"})


class TestGlobalFunctions:
    """Tests for global formatting functions"""
    
    def test_get_unified_formatter_singleton(self):
        """Test that get_unified_formatter returns singleton"""
        formatter1 = get_unified_formatter()
        formatter2 = get_unified_formatter()
        
        assert formatter1 is formatter2
        assert isinstance(formatter1, UnifiedFormatter)
    
    @patch('src.application.formatters.unified_formatter._unified_formatter')
    def test_format_string_advanced_global(self, mock_formatter):
        """Test global format_string_advanced function"""
        mock_formatter.format_string_advanced.return_value = "Hello, World!"
        
        result = format_string_advanced(
            "Hello, {name}!", 
            {"name": "World"},
            FormatSyntaxType.PYTHON,
            True
        )
        
        assert result == "Hello, World!"
        mock_formatter.format_string_advanced.assert_called_once_with(
            "Hello, {name}!", {"name": "World"}, FormatSyntaxType.PYTHON, True
        )
    
    @patch('src.application.formatters.unified_formatter._unified_formatter')
    def test_format_string_global(self, mock_formatter):
        """Test global format_string function"""
        mock_formatter.format_string.return_value = "Hello, World!"
        
        result = format_string(
            "Hello, {name}!", 
            {"name": "World"},
            use_advanced=True
        )
        
        assert result == "Hello, World!"
        mock_formatter.format_string.assert_called_once_with(
            "Hello, {name}!", {"name": "World"}, True
        )


class TestIntegration:
    """Integration tests for UnifiedFormatter"""
    
    def test_real_basic_formatting(self):
        """Test real basic formatting without mocks"""
        formatter = UnifiedFormatter()
        
        # Test basic template formatting
        result = formatter.format_string(
            "Hello, {name}! Welcome to {place}.",
            {"name": "Alice", "place": "Python"},
            use_advanced=False
        )
        
        # Should work with basic Python string formatting
        assert "Alice" in result
        assert "Python" in result
    
    def test_format_syntax_types(self):
        """Test different format syntax types"""
        formatter = UnifiedFormatter()
        
        # Test with None (default) syntax type
        with patch.object(formatter, '_format_manager') as mock_manager:
            mock_result = Mock()
            mock_result.success = True
            mock_result.formatted_text = "formatted"
            mock_manager.format.return_value = mock_result
            
            formatter.format_string_advanced("template", {})
            
            # Should default to PYTHON syntax type
            call_args = mock_manager.format.call_args
            assert call_args[1]['syntax_type'] == FormatSyntaxType.PYTHON
    
    def test_strict_mode_default(self):
        """Test that strict mode defaults to True"""
        formatter = UnifiedFormatter()
        
        with patch.object(formatter, '_format_manager') as mock_manager:
            mock_result = Mock()
            mock_result.success = True
            mock_result.formatted_text = "formatted"
            mock_manager.format.return_value = mock_result
            
            formatter.format_string_advanced("template", {})
            
            # Should default to strict_mode=True
            call_args = mock_manager.format.call_args
            assert call_args[1]['strict_mode'] is True
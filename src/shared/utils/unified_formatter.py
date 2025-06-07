"""
Unified Format Utility - Advanced formatting functionality

This module provides advanced formatting capabilities that depend on
the FormatManager. For basic formatting without dependencies, use
src.shared.utils.basic_formatter.
"""
from typing import Dict, Any, Optional

# Import basic formatting functions
from src.shared.utils.basic_formatter import (
    extract_format_keys, format_with_missing_keys, format_string_simple,
    format_with_context, validate_template_keys
)

# Import the sophisticated FormatManager for advanced formatting
from src.application.formatters.format_manager import get_format_manager
from src.application.formatters.base.base_format_engine import FormatSyntaxType


class UnifiedFormatter:
    """
    Unified formatter that consolidates all formatting functionality.
    Provides backward compatibility while delegating to the most appropriate implementation.
    """
    
    def __init__(self):
        self._format_manager = get_format_manager()
    
    def extract_format_keys(self, template: str):
        """Delegate to basic formatter."""
        return extract_format_keys(template)
    
    def format_with_missing_keys(self, template: str, **kwargs):
        """Delegate to basic formatter."""
        return format_with_missing_keys(template, **kwargs)
    
    def format_string_simple(self, template: str, context_dict: Dict[str, Any]) -> str:
        """Delegate to basic formatter."""
        return format_string_simple(template, context_dict)
    
    def format_string_advanced(self, template: str, context_dict: Dict[str, Any], 
                             syntax_type: Optional[FormatSyntaxType] = None,
                             strict_mode: bool = True) -> str:
        """
        Advanced string formatting using FormatManager.
        
        Args:
            template: Template string to format
            context_dict: Variables for formatting
            syntax_type: Format syntax type (defaults to PYTHON)
            strict_mode: Whether to use strict formatting
            
        Returns:
            Formatted string
        """
        try:
            result = self._format_manager.format(
                template=template,
                data=context_dict,
                syntax_type=syntax_type or FormatSyntaxType.PYTHON,
                strict_mode=strict_mode
            )
            return result.formatted_text if result.success else template
        except Exception:
            # Fallback to simple formatting
            return format_string_simple(template, context_dict)
    
    def format_string(self, template: str, context_dict: Dict[str, Any], 
                     use_advanced: bool = False) -> str:
        """
        Universal string formatting method.
        
        Args:
            template: Template string to format
            context_dict: Variables for formatting
            use_advanced: Whether to use advanced formatting engine
            
        Returns:
            Formatted string
        """
        if use_advanced:
            return self.format_string_advanced(template, context_dict)
        else:
            return format_string_simple(template, context_dict)
    
    def format_with_context(self, template: str, context: Dict[str, Any]) -> str:
        """Delegate to basic formatter."""
        return format_with_context(template, context)
    
    def validate_template_keys(self, template: str, required_keys):
        """Delegate to basic formatter."""
        return validate_template_keys(template, required_keys)


# Global singleton instance
_unified_formatter = UnifiedFormatter()


# Re-export basic functions for backward compatibility
from src.shared.utils.basic_formatter import (
    extract_format_keys, format_with_missing_keys, format_string_simple as format_string_pure,
    format_with_context, validate_template_keys, safe_format_template, extract_template_keys
)


def get_unified_formatter() -> UnifiedFormatter:
    """Get the global unified formatter instance."""
    return _unified_formatter


# Advanced formatting functions that require the full formatter
def format_string_advanced(template: str, context_dict: Dict[str, Any], 
                         syntax_type: Optional[FormatSyntaxType] = None,
                         strict_mode: bool = True) -> str:
    """Advanced string formatting using FormatManager."""
    return _unified_formatter.format_string_advanced(template, context_dict, syntax_type, strict_mode)


def format_string(template: str, context_dict: Dict[str, Any], use_advanced: bool = False) -> str:
    """Universal string formatting method."""
    return _unified_formatter.format_string(template, context_dict, use_advanced)
"""
Unified Format Utility - Consolidates all formatting functionality

This module provides a single, unified interface for all string formatting operations
in the project, consolidating the functionality from:
- application/formatters/format_manager.py
- context/utils/format_utils.py  
- pure_functions/execution_context_formatter_pure.py
- shared/utils/pure_functions.py (format_string_pure)
"""
from typing import Dict, List, Tuple, Any, Optional
from functools import lru_cache
import re

# Import the sophisticated FormatManager for advanced formatting
from src.application.formatters.format_manager import get_format_manager
from src.application.formatters.base.base_format_engine import FormatSyntaxType


# Pre-compiled regex patterns for performance
_FORMAT_KEY_PATTERN = re.compile(r'{(\w+)}')


class UnifiedFormatter:
    """
    Unified formatter that consolidates all formatting functionality.
    Provides backward compatibility while delegating to the most appropriate implementation.
    """
    
    def __init__(self):
        self._format_manager = get_format_manager()
    
    @lru_cache(maxsize=512)
    def extract_format_keys(self, template: str) -> List[str]:
        """
        Extract format keys from template string.
        Consolidated from format_utils.extract_format_keys
        
        Args:
            template: Template string with {key} placeholders
            
        Returns:
            List of format keys found in template
        """
        return _FORMAT_KEY_PATTERN.findall(template)
    
    def format_with_missing_keys(self, template: str, **kwargs) -> Tuple[str, List[str]]:
        """
        Format template with partial data, returning missing keys.
        Consolidated from format_utils.format_with_missing_keys
        
        Args:
            template: Template string to format
            **kwargs: Format variables
            
        Returns:
            Tuple of (formatted_string, missing_keys)
        """
        keys = self.extract_format_keys(template)
        missing = [k for k in keys if k not in kwargs]
        
        class SafeDict(dict):
            def __missing__(self, key):
                return '{' + key + '}'
        
        formatted = template.format_map(SafeDict(kwargs))
        return formatted, missing
    
    def format_string_simple(self, template: str, context_dict: Dict[str, Any]) -> str:
        """
        Simple string formatting using replacement method.
        Consolidated from pure_functions.format_string_pure
        
        Args:
            template: Template string to format
            context_dict: Variables for formatting
            
        Returns:
            Formatted string
        """
        if not isinstance(template, str):
            return template
        
        result = template
        for key, val in context_dict.items():
            result = result.replace(f"{{{key}}}", str(val))
        return result
    
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
            return self.format_string_simple(template, context_dict)
    
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
            return self.format_string_simple(template, context_dict)
    
    def format_with_context(self, template: str, context: Dict[str, Any]) -> str:
        """
        Format template with context dictionary.
        Consolidated from format_utils.format_with_context
        
        Args:
            template: Template string to format
            context: Context dictionary
            
        Returns:
            Formatted string
        """
        if not isinstance(template, str):
            return template
        
        # Convert values to strings for better performance
        str_context = {k: str(v) for k, v in context.items()}
        
        class SafeDict(dict):
            def __missing__(self, key):
                return f"{{{key}}}"
        
        try:
            return template.format_map(SafeDict(str_context))
        except (KeyError, ValueError):
            # Fallback to simple replacement
            return self.format_string_simple(template, str_context)
    
    def validate_template_keys(self, template: str, required_keys: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate that template contains required keys.
        Consolidated from format_utils.validate_template_keys
        
        Args:
            template: Template string to validate
            required_keys: List of required keys
            
        Returns:
            Tuple of (is_valid, missing_keys)
        """
        template_keys = set(self.extract_format_keys(template))
        missing_keys = [key for key in required_keys if key not in template_keys]
        return len(missing_keys) == 0, missing_keys


# Global singleton instance
_unified_formatter = UnifiedFormatter()


def get_unified_formatter() -> UnifiedFormatter:
    """Get the global unified formatter instance."""
    return _unified_formatter


# Convenience functions for backward compatibility
def extract_format_keys(template: str) -> List[str]:
    """Extract format keys from template string."""
    return _unified_formatter.extract_format_keys(template)


def format_with_missing_keys(template: str, **kwargs) -> Tuple[str, List[str]]:
    """Format template with partial data, returning missing keys."""
    return _unified_formatter.format_with_missing_keys(template, **kwargs)


def format_string_pure(template: str, context_dict: Dict[str, Any]) -> str:
    """Simple string formatting (pure function)."""
    return _unified_formatter.format_string_simple(template, context_dict)


def format_with_context(template: str, context: Dict[str, Any]) -> str:
    """Format template with context dictionary."""
    return _unified_formatter.format_with_context(template, context)


def validate_template_keys(template: str, required_keys: List[str]) -> Tuple[bool, List[str]]:
    """Validate that template contains required keys."""
    return _unified_formatter.validate_template_keys(template, required_keys)


# Aliases for existing code compatibility
safe_format_template = format_with_missing_keys
extract_template_keys = extract_format_keys
"""
Minimal format utilities for internal use

This module provides only the essential formatting functions needed by 
python_format_engine.py to avoid circular imports. For general use, 
prefer src.shared.utils.unified_formatter.
"""
import re
from typing import Dict, List, Tuple, Any
from functools import lru_cache

# Pre-compiled regex patterns for performance
_FORMAT_KEY_PATTERN = re.compile(r'{(\w+)}')


@lru_cache(maxsize=512)
def extract_format_keys(s: str) -> List[str]:
    """
    Extract format keys from template string.
    
    Args:
        s: Template string with {key} placeholders
        
    Returns:
        List of format keys found in template
    """
    return _FORMAT_KEY_PATTERN.findall(s)


def format_with_missing_keys(s: str, **kwargs) -> Tuple[str, List[str]]:
    """
    Format template with partial data, returning missing keys.
    
    Args:
        s: Template string to format
        **kwargs: Format variables
        
    Returns:
        Tuple of (formatted_string, missing_keys)
    """
    keys = extract_format_keys(s)
    missing = [k for k in keys if k not in kwargs]
    
    class SafeDict(dict):
        def __missing__(self, key):
            return '{' + key + '}'
    
    formatted = s.format_map(SafeDict(kwargs))
    return formatted, missing


# Backward compatibility aliases
extract_template_keys = extract_format_keys
safe_format_template = format_with_missing_keys
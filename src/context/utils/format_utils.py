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


# Import additional function from basic_formatter for backward compatibility
from src.shared.utils.basic_formatter import format_with_context


def build_path_template(base_path: str, *parts: str) -> str:
    """
    Build path template by combining base path and path parts.
    
    Args:
        base_path: Base directory path
        *parts: Path parts to join
        
    Returns:
        Combined path template with normalized slashes
    """
    import os
    
    if not parts:
        return base_path.rstrip('/')
    
    # Normalize base path (remove trailing slash)
    normalized_base = base_path.rstrip('/')
    
    # Normalize parts (remove leading/trailing slashes, but preserve empty strings)
    normalized_parts = []
    for part in parts:
        if part == "":
            normalized_parts.append("")  # Preserve empty strings
        else:
            normalized_parts.append(part.strip('/'))
    
    # Join all parts
    if normalized_parts:
        return normalized_base + '/' + '/'.join(normalized_parts)
    else:
        return normalized_base


def validate_template_keys(template: str, required_keys: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that template contains required keys.
    
    Args:
        template: Template string to validate
        required_keys: List of required keys
        
    Returns:
        Tuple of (is_valid, missing_keys)
    """
    template_keys = set(extract_format_keys(template))
    missing_keys = [key for key in required_keys if key not in template_keys]
    return len(missing_keys) == 0, missing_keys


# Backward compatibility aliases
extract_template_keys = extract_format_keys
safe_format_template = format_with_missing_keys
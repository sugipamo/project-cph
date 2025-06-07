"""
Format utilities - delegates to basic_formatter

This module is a thin wrapper around basic_formatter to maintain
backward compatibility while avoiding code duplication.
"""
from typing import Dict, List, Tuple, Any

# Import all basic formatting functions from the canonical source
from src.shared.utils.basic_formatter import (
    extract_format_keys,
    format_with_missing_keys, 
    format_with_context,
    validate_template_keys
)


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


# Backward compatibility aliases
extract_template_keys = extract_format_keys
safe_format_template = format_with_missing_keys
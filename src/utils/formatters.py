"""Basic formatting utilities without external dependencies

This module provides core formatting functions that can be used
anywhere without causing circular imports.
"""
import re
from functools import lru_cache
from typing import Any

# Pre-compiled regex patterns for performance
_FORMAT_KEY_PATTERN = re.compile(r'{(\w+)}')


@lru_cache(maxsize=512)
def extract_format_keys(template: str) -> list[str]:
    """Extract format keys from template string.

    Args:
        template: Template string with {key} placeholders

    Returns:
        List of format keys found in template
    """
    return _FORMAT_KEY_PATTERN.findall(template)


def format_with_missing_keys(template: str, **kwargs) -> tuple[str, list[str]]:
    """Format template with partial data, returning missing keys.

    Args:
        template: Template string to format
        **kwargs: Format variables

    Returns:
        Tuple of (formatted_string, missing_keys)
    """
    keys = extract_format_keys(template)
    missing = [k for k in keys if k not in kwargs]

    class SafeDict(dict):
        def __missing__(self, key):
            return '{' + key + '}'

    formatted = template.format_map(SafeDict(kwargs))
    return formatted, missing


def format_string_simple(template: str, context_dict: dict[str, Any]) -> str:
    """Simple string formatting using replacement method.

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


def format_with_context(template: str, context: dict[str, Any]) -> str:
    """Format template with context dictionary.

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
        return format_string_simple(template, str_context)


def validate_template_keys(template: str, required_keys: list[str]) -> tuple[bool, list[str]]:
    """Validate that template contains required keys.

    Args:
        template: Template string to validate
        required_keys: List of required keys

    Returns:
        Tuple of (is_valid, missing_keys)
    """
    template_keys = set(extract_format_keys(template))
    missing_keys = [key for key in required_keys if key not in template_keys]
    return len(missing_keys) == 0, missing_keys


# Aliases for existing code compatibility
format_string_pure = format_string_simple
safe_format_template = format_with_missing_keys
extract_template_keys = extract_format_keys

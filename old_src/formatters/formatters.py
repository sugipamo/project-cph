"""Basic formatting utilities without external dependencies

This module provides core formatting functions that can be used
anywhere without causing circular imports.
"""
from functools import lru_cache
from typing import Any


@lru_cache(maxsize=512)
def extract_format_keys(template: str, regex_ops: Any) -> list[str]:
    """Extract format keys from template string.

    Args:
        template: Template string with {key} placeholders
        regex_ops: Regex operations provider for dependency injection

    Returns:
        List of format keys found in template
    """
    # regex_ops is now required parameter - no default value check needed

    pattern = regex_ops.compile_pattern(r'{(\w+)}')
    return regex_ops.findall(pattern, template)


def format_with_missing_keys(template: str, regex_ops: Any, **kwargs) -> tuple[str, list[str]]:
    """Format template with partial data, returning missing keys.

    Args:
        template: Template string to format
        regex_ops: Regex operations provider for dependency injection
        **kwargs: Format variables

    Returns:
        Tuple of (formatted_string, missing_keys)
    """
    keys = extract_format_keys(template, regex_ops)
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

    formatted_string = template
    for key, val in context_dict.items():
        formatted_string = formatted_string.replace(f"{{{key}}}", str(val))
    return formatted_string


def format_with_context(template: str, context: dict[str, Any], regex_ops: Any) -> str:
    """Format template with context dictionary.

    Args:
        template: Template string to format
        context: Context dictionary
        regex_ops: Regex operations provider for dependency injection

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

    # Check if template contains valid format syntax
    if _contains_valid_format_syntax(template, str_context, regex_ops):
        return template.format_map(SafeDict(str_context))

    # Use simple replacement if format_map would fail
    return format_string_simple(template, str_context)


def _contains_valid_format_syntax(template: str, context: dict, regex_ops: Any) -> bool:
    """Check if template contains valid format syntax that can be processed safely

    Args:
        template: Template string to check
        context: Context dictionary with available keys
        regex_ops: Regex operations provider for dependency injection

    Returns:
        bool: True if template can be safely formatted, False otherwise
    """
    # Check for basic format syntax without complex expressions
    format_pattern = regex_ops.compile_pattern(r'\{[^{}]*\}')
    format_keys = regex_ops.findall(format_pattern, template)

    # If no format keys found, safe to proceed
    if not format_keys:
        return True

    # Check if all format keys are simple (no complex expressions)
    for key in format_keys:
        # Remove braces and check content
        key_content = key[1:-1]

        # Skip if contains format specs or complex expressions
        if ':' in key_content or '!' in key_content or '.' in key_content:
            return False

        # Skip if key is not in context (will be handled by SafeDict)
        if key_content and key_content not in context:
            continue

    return True


def validate_template_keys(template: str, required_keys: list[str], regex_ops: Any) -> tuple[bool, list[str]]:
    """Validate that template contains required keys.

    Args:
        template: Template string to validate
        required_keys: List of required keys
        regex_ops: Regex operations provider for dependency injection

    Returns:
        Tuple of (is_valid, missing_keys)
    """
    template_keys = set(extract_format_keys(template, regex_ops))
    missing_keys = [key for key in required_keys if key not in template_keys]
    return len(missing_keys) == 0, missing_keys

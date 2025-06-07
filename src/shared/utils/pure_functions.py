"""
Pure function utility module

Aggregates pure functions with no side effects that always return the same output for the same input.
Follows functional programming principles to improve testability and reusability.
"""
from typing import Dict, List, Optional, Tuple, Any
import re
import os
from pathlib import Path


# =============================================================================
# String and Path Operation Pure Functions
# =============================================================================

def format_string_pure(value: str, context_dict: Dict[str, str]) -> str:
    """
    Pure function version of string formatting
    
    Args:
        value: String to format
        context_dict: Variable dictionary for formatting
        
    Returns:
        Formatted string
    
    Note: This function now delegates to the unified formatter for consistency
    """
    # Import here to avoid circular dependencies
    from src.shared.utils.unified_formatter import get_unified_formatter
    
    if not isinstance(value, str):
        return value
    
    formatter = get_unified_formatter()
    return formatter.format_string_simple(value, context_dict)


def extract_missing_keys_pure(template: str, available_keys: set) -> List[str]:
    """
    Pure function to extract unresolved keys from template string
    
    Args:
        template: Template string ({key} format)
        available_keys: Set of available keys
        
    Returns:
        List of unresolved keys
    """
    pattern = r'\{([^}]+)\}'
    found_keys = re.findall(pattern, template)
    return [key for key in found_keys if key not in available_keys]


def is_potential_script_path_pure(code_or_file: List[str], script_extensions: List[str] = None) -> bool:
    """
    Pure function to determine if input looks like a script file path
    
    Args:
        code_or_file: Input list
        script_extensions: List of script file extensions
        
    Returns:
        Boolean indicating if it looks like a script file path
    """
    if script_extensions is None:
        script_extensions = ['.py', '.js', '.sh', '.rb', '.go']
    
    return (len(code_or_file) == 1 and 
            any(code_or_file[0].endswith(ext) for ext in script_extensions))


def validate_file_path_format_pure(path: str) -> Tuple[bool, Optional[str]]:
    """
    Pure function for file path format validation
    
    Args:
        path: Path to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path:
        return False, "Path cannot be empty"
    
    # Normalize path to detect traversal attacks
    normalized = os.path.normpath(path)
    
    # Check if normalized path contains parent directory references
    if normalized.startswith('..') or '/..' in normalized:
        return False, "Path traversal detected"
    
    # Reject absolute paths containing '..'
    if os.path.isabs(path) and '..' in path:
        return False, "Absolute paths with '..' are not allowed"
    
    # Check for dangerous characters (extended version)
    dangerous_chars = ['|', ';', '&', '$', '`', '\n', '\r', '\0']
    if any(char in path for char in dangerous_chars):
        return False, f"Path contains dangerous characters: {path}"
    
    return True, None


# Docker functions have been moved to src.shared.utils.docker.docker_command_builder
# Use that module directly for all Docker command building functionality


# =============================================================================
# List and Data Processing Pure Functions
# =============================================================================

def filter_and_transform_pure(items: List[Any], filter_func, transform_func) -> List[Any]:
    """
    Pure function to filter and transform list items
    
    Args:
        items: List of items to process
        filter_func: Function to filter items
        transform_func: Function to transform items
        
    Returns:
        Filtered and transformed list
    """
    return [transform_func(item) for item in items if filter_func(item)]


def group_by_pure(items: List[Any], key_func) -> Dict[Any, List[Any]]:
    """
    Pure function to group list items by key
    
    Args:
        items: List of items to group
        key_func: Function to extract grouping key
        
    Returns:
        Dictionary with grouped items
    """
    groups = {}
    for item in items:
        key = key_func(item)
        if key not in groups:
            groups[key] = []
        groups[key].append(item)
    return groups


def merge_dicts_pure(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pure function to merge multiple dictionaries
    
    Args:
        *dicts: Dictionaries to merge
        
    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result
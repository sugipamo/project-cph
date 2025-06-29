"""String and template formatting utilities

Pure functions for string manipulation, template processing, and path validation.
All functions are stateless with no side effects.
"""
from functools import reduce
from typing import Any, Dict, Optional


def format_template_string(template_string: str, context_dict: Dict[str, str]) -> str:
    """Pure function version of string formatting

    Args:
        template_string: String to format
        context_dict: Variable dictionary for formatting

    Returns:
        Formatted string

    Note: Self-contained implementation without external dependencies
    """
    if not isinstance(template_string, str):
        return template_string

    formatted_result = template_string
    for key, val in context_dict.items():
        formatted_result = formatted_result.replace(f"{{{key}}}", str(val))
    return formatted_result


def extract_missing_template_keys(template: str, available_keys: set, regex_ops: Any) -> list[str]:
    """Pure function to extract unresolved keys from template string

    Args:
        template: Template string ({key} format)
        available_keys: Set of available keys
        regex_ops: Regex operations provider for dependency injection

    Returns:
        List of unresolved keys
    """
    pattern = regex_ops.compile_pattern(r'\{([^}]+)\}')
    found_keys = regex_ops.findall(pattern, template)
    return [key for key in found_keys if key not in available_keys]


def is_potential_script_path(code_or_file: list[str], script_extensions: Optional[list[str]]) -> bool:
    """Pure function to determine if input looks like a script file path

    Args:
        code_or_file: Input list
        script_extensions: List of script file extensions

    Returns:
        Boolean indicating if it looks like a script file path
    """
    # フォールバック処理は禁止、必要なエラーを見逃すことになる
    if script_extensions is None:
        raise ValueError("script_extensions parameter is required")

    return (len(code_or_file) == 1 and
            any(code_or_file[0].endswith(ext) for ext in script_extensions))


def validate_file_path_format(file_path: str) -> tuple[bool, Optional[str]]:
    """Pure function for file path format validation

    Args:
        file_path: Path to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path:
        return False, "Path cannot be empty"

    # Normalize path to detect traversal attacks (simple string-based implementation)
    normalized = normalize_filesystem_path(file_path)

    # Check if normalized path contains parent directory references
    if normalized.startswith('..') or '/..' in normalized:
        return False, "Path traversal detected"

    # Reject absolute paths containing '..'
    if is_absolute_filesystem_path(file_path) and '..' in file_path:
        return False, "Absolute paths with '..' are not allowed"

    # Check for dangerous characters (extended version)
    dangerous_chars = ['|', ';', '&', '$', '`', '\n', '\r', '\0']
    if any(char in file_path for char in dangerous_chars):
        return False, f"Path contains dangerous characters: {file_path}"

    return True, None


def parse_container_names(container_output: str) -> list[str]:
    """Parse container names from docker ps output (pure function)

    Args:
        container_output: Output from docker ps command

    Returns:
        List of container names
    """
    lines = container_output.strip().split('\n')
    if not lines or len(lines) < 2:  # Header + at least one container
        return []

    def extract_container_name(line: str) -> Optional[str]:
        parts = line.split()
        if len(parts) >= 1:
            return parts[-1]
        return None

    container_names = [extract_container_name(line) for line in lines[1:]]
    return [name for name in container_names if name is not None]


def normalize_filesystem_path(path: str) -> str:
    """Pure function implementation of path normalization

    Args:
        path: Path to normalize

    Returns:
        Normalized path string
    """
    if not path:
        return path

    # Split by both / and \ to handle cross-platform paths
    parts = path.replace('\\', '/').split('/')

    def process_part(acc: list, part: str) -> list:
        if part == '' or part == '.':
            return acc
        if part == '..':
            if acc and acc[-1] != '..':
                return acc[:-1]
            return [*acc, '..']
        return [*acc, part]

    normalized_parts = reduce(process_part, parts, [])
    result = '/'.join(normalized_parts)

    # Preserve leading slash for absolute paths
    if path.startswith('/'):
        result = '/' + result

    # Explicit check for empty result - don't mask normalization errors
    if not result:
        return '.'
    return result


def is_absolute_filesystem_path(path: str) -> bool:
    """Pure function implementation of absolute path detection

    Args:
        path: Path to check

    Returns:
        True if path is absolute
    """
    if not path:
        return False

    # Unix-style absolute path
    if path.startswith('/'):
        return True

    # Windows-style absolute path (C:, D:, etc.)
    return bool(len(path) >= 2 and path[1] == ':' and path[0].isalpha())

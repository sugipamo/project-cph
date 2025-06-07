"""Pure function utility module

Aggregates pure functions with no side effects that always return the same output for the same input.
Follows functional programming principles to improve testability and reusability.
"""
import os
import re
from typing import Any, Optional

# =============================================================================
# String and Path Operation Pure Functions
# =============================================================================

def format_template_string(template_string: str, context_dict: dict[str, str]) -> str:
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


def extract_missing_template_keys(template: str, available_keys: set) -> list[str]:
    """Pure function to extract unresolved keys from template string

    Args:
        template: Template string ({key} format)
        available_keys: Set of available keys

    Returns:
        List of unresolved keys
    """
    pattern = r'\{([^}]+)\}'
    found_keys = re.findall(pattern, template)
    return [key for key in found_keys if key not in available_keys]


def is_potential_script_path(code_or_file: list[str], script_extensions: Optional[list[str]] = None) -> bool:
    """Pure function to determine if input looks like a script file path

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


def validate_file_path_format(file_path: str) -> tuple[bool, Optional[str]]:
    """Pure function for file path format validation

    Args:
        file_path: Path to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path:
        return False, "Path cannot be empty"

    # Normalize path to detect traversal attacks
    normalized = os.path.normpath(file_path)

    # Check if normalized path contains parent directory references
    if normalized.startswith('..') or '/..' in normalized:
        return False, "Path traversal detected"

    # Reject absolute paths containing '..'
    if os.path.isabs(file_path) and '..' in file_path:
        return False, "Absolute paths with '..' are not allowed"

    # Check for dangerous characters (extended version)
    dangerous_chars = ['|', ';', '&', '$', '`', '\n', '\r', '\0']
    if any(char in file_path for char in dangerous_chars):
        return False, f"Path contains dangerous characters: {file_path}"

    return True, None


# =============================================================================
# Docker Command Building Pure Functions (for backward compatibility)
# =============================================================================

def build_docker_run_command_wrapper(image: str, **kwargs) -> list[str]:
    """Build docker run command (backward compatibility wrapper)

    Args:
        image: Docker image name
        **kwargs: Additional docker run options

    Returns:
        Docker run command as list
    """
    # Import here to avoid circular dependencies
    from src.infrastructure.drivers.docker.utils.docker_command_builder import build_docker_run_command
    return build_docker_run_command(image, **kwargs)


def build_docker_build_command_wrapper(context_path: str, **kwargs) -> list[str]:
    """Build docker build command (backward compatibility wrapper)

    Args:
        context_path: Build context path
        **kwargs: Additional docker build options

    Returns:
        Docker build command as list
    """
    from src.infrastructure.drivers.docker.utils.docker_command_builder import build_docker_build_command
    return build_docker_build_command(context_path, **kwargs)


def build_docker_stop_command_wrapper(container: str, **kwargs) -> list[str]:
    """Build docker stop command (backward compatibility wrapper)

    Args:
        container: Container name or ID
        **kwargs: Additional docker stop options

    Returns:
        Docker stop command as list
    """
    from src.infrastructure.drivers.docker.utils.docker_command_builder import build_docker_stop_command
    return build_docker_stop_command(container, **kwargs)


def build_docker_remove_command_wrapper(container: str, **kwargs) -> list[str]:
    """Build docker rm command (backward compatibility wrapper)

    Args:
        container: Container name or ID
        **kwargs: Additional docker rm options

    Returns:
        Docker rm command as list
    """
    from src.infrastructure.drivers.docker.utils.docker_command_builder import build_docker_remove_command
    return build_docker_remove_command(container, **kwargs)


def build_docker_ps_command_wrapper(**kwargs) -> list[str]:
    """Build docker ps command (backward compatibility wrapper)

    Args:
        **kwargs: Additional docker ps options

    Returns:
        Docker ps command as list
    """
    from src.infrastructure.drivers.docker.utils.docker_command_builder import build_docker_ps_command
    return build_docker_ps_command(**kwargs)


def build_docker_inspect_command_wrapper(container: str, **kwargs) -> list[str]:
    """Build docker inspect command (backward compatibility wrapper)

    Args:
        container: Container name or ID
        **kwargs: Additional docker inspect options

    Returns:
        Docker inspect command as list
    """
    from src.infrastructure.drivers.docker.utils.docker_command_builder import build_docker_inspect_command
    return build_docker_inspect_command(container, **kwargs)


def build_docker_cp_command_wrapper(source: str, destination: str, **kwargs) -> list[str]:
    """Build docker cp command (backward compatibility wrapper)

    Args:
        source: Source path
        destination: Destination path
        **kwargs: Additional docker cp options

    Returns:
        Docker cp command as list
    """
    from src.infrastructure.drivers.docker.utils.docker_command_builder import build_docker_cp_command
    return build_docker_cp_command(source, destination, **kwargs)


def validate_docker_image_name_wrapper(image_name: str) -> bool:
    """Validate docker image name format (backward compatibility wrapper)

    Args:
        image_name: Docker image name to validate

    Returns:
        True if valid, False otherwise
    """
    from src.infrastructure.drivers.docker.utils.docker_utils import validate_docker_image_name
    return validate_docker_image_name(image_name)


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

    container_names = []
    for line in lines[1:]:  # Skip header
        parts = line.split()
        if len(parts) >= 1:
            # Container name is typically the last column
            container_names.append(parts[-1])

    return container_names


# =============================================================================
# List and Data Processing Pure Functions
# =============================================================================

def filter_and_transform_items(items: list[Any], filter_func, transform_func) -> list[Any]:
    """Pure function to filter and transform list items

    Args:
        items: List of items to process
        filter_func: Function to filter items
        transform_func: Function to transform items

    Returns:
        Filtered and transformed list
    """
    return [transform_func(item) for item in items if filter_func(item)]


def group_items_by_key(items: list[Any], key_func) -> dict[Any, list[Any]]:
    """Pure function to group list items by key

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


def merge_dictionaries(*dicts: dict[str, Any]) -> dict[str, Any]:
    """Pure function to merge multiple dictionaries

    Args:
        *dicts: Dictionaries to merge

    Returns:
        Merged dictionary
    """
    merged_dict = {}
    for d in dicts:
        merged_dict.update(d)
    return merged_dict



"""
Pure function utility module

Aggregates pure functions with no side effects that always return the same output for the same input.
Follows functional programming principles to improve testability and reusability.
"""
from typing import Dict, List, Optional, Tuple, Any, Union
from functools import reduce
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
    """
    if not isinstance(value, str):
        return value
    
    result = value
    for key, val in context_dict.items():
        result = result.replace(f"{{{key}}}", str(val))
    return result


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


def validate_docker_image_name_pure(image_name: str) -> bool:
    """
    Pure function to validate Docker image name format
    
    Args:
        image_name: Docker image name to validate
        
    Returns:
        Boolean indicating if the image name is valid
    """
    if not image_name:
        return False
    
    # Basic Docker image name validation
    # Pattern: [registry/]name[:tag]
    pattern = r'^([a-z0-9._-]+/)*[a-z0-9._-]+(:[\w.-]+)?$'
    return bool(re.match(pattern, image_name, re.IGNORECASE))


# =============================================================================
# Docker Command Construction Pure Functions
# =============================================================================

def build_docker_run_command_pure(image: str, name: str = None, options: Dict[str, Any] = None) -> List[str]:
    """
    Pure function to build docker run command
    
    Args:
        image: Docker image name
        name: Container name
        options: Additional options
        
    Returns:
        Docker run command as list
    """
    cmd = ["docker", "run"]
    
    if name:
        cmd.extend(["--name", name])
    
    if options:
        if options.get("detach", False):
            cmd.append("-d")
        if "ports" in options:
            for port in options["ports"]:
                cmd.extend(["-p", port])
        if "volumes" in options:
            for volume in options["volumes"]:
                cmd.extend(["-v", volume])
        if "environment" in options:
            for env in options["environment"]:
                cmd.extend(["-e", env])
    
    cmd.append(image)
    return cmd


def build_docker_stop_command_pure(name: str) -> List[str]:
    """
    Pure function to build docker stop command
    
    Args:
        name: Container name
        
    Returns:
        Docker stop command as list
    """
    return ["docker", "stop", name]


def build_docker_remove_command_pure(name: str, force: bool = False) -> List[str]:
    """
    Pure function to build docker remove command
    
    Args:
        name: Container name
        force: Force removal flag
        
    Returns:
        Docker remove command as list
    """
    cmd = ["docker", "rm"]
    if force:
        cmd.append("-f")
    cmd.append(name)
    return cmd


def build_docker_build_command_pure(tag: str = None, dockerfile_text: str = None, options: Dict[str, Any] = None) -> List[str]:
    """
    Pure function to build docker build command
    
    Args:
        tag: Image tag
        dockerfile_text: Dockerfile content
        options: Additional options
        
    Returns:
        Docker build command as list
    """
    cmd = ["docker", "build"]
    
    if tag:
        cmd.extend(["-t", tag])
    
    if options:
        if "build_args" in options:
            for arg in options["build_args"]:
                cmd.extend(["--build-arg", arg])
        if "no_cache" in options and options["no_cache"]:
            cmd.append("--no-cache")
    
    cmd.extend(["-f", "-", "."])  # Read Dockerfile from stdin
    return cmd


def build_docker_ps_command_pure(all: bool = False) -> List[str]:
    """
    Pure function to build docker ps command
    
    Args:
        all: Show all containers flag
        
    Returns:
        Docker ps command as list
    """
    cmd = ["docker", "ps"]
    if all:
        cmd.append("-a")
    return cmd


def build_docker_inspect_command_pure(target: str, type_: str = None) -> List[str]:
    """
    Pure function to build docker inspect command
    
    Args:
        target: Target to inspect
        type_: Type of target
        
    Returns:
        Docker inspect command as list
    """
    cmd = ["docker", "inspect"]
    if type_:
        cmd.extend(["--type", type_])
    cmd.append(target)
    return cmd


def build_docker_cp_command_pure(src: str, dst: str, container: str, to_container: bool = True) -> List[str]:
    """
    Pure function to build docker cp command
    
    Args:
        src: Source path
        dst: Destination path
        container: Container name
        to_container: Copy to container flag
        
    Returns:
        Docker cp command as list
    """
    if to_container:
        return ["docker", "cp", src, f"{container}:{dst}"]
    else:
        return ["docker", "cp", f"{container}:{src}", dst]


def parse_container_names_pure(output: str) -> List[str]:
    """
    Pure function to parse container names from docker ps output
    
    Args:
        output: Docker ps output
        
    Returns:
        List of container names
    """
    if not output:
        return []
    
    lines = output.strip().split('\n')
    return [line.strip() for line in lines if line.strip()]


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
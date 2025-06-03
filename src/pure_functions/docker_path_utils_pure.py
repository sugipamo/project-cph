"""
Docker path utilities as pure functions
Handles path conversion between host and Docker container paths
"""
from typing import Optional, Dict


def convert_path_to_docker_mount(
    path: str,
    workspace_path: str,
    mount_path: str
) -> str:
    """
    Convert host path to Docker container mount path
    
    Args:
        path: Original path (may contain workspace references)
        workspace_path: Host workspace path
        mount_path: Docker mount path
        
    Returns:
        Converted path for use inside Docker container
    """
    # If path is exactly the workspace path or ./workspace, return mount path
    if path == "./workspace" or path == workspace_path:
        return mount_path
    
    # If path contains workspace path, replace it
    if workspace_path in path:
        return path.replace(workspace_path, mount_path)
    
    return path


def get_docker_mount_path_from_config(
    env_json: Dict,
    language: str,
    default_mount_path: str = "/workspace"
) -> str:
    """
    Extract Docker mount path from environment configuration
    
    Args:
        env_json: Environment configuration dictionary
        language: Programming language key
        default_mount_path: Default mount path if not configured
        
    Returns:
        Docker mount path
    """
    if not env_json or language not in env_json:
        return default_mount_path
    
    language_config = env_json.get(language, {})
    env_types = language_config.get('env_types', {})
    docker_config = env_types.get('docker', {})
    
    return docker_config.get('mount_path', default_mount_path)


def wrap_command_with_cwd(
    command: str,
    cwd: Optional[str],
    workspace_path: Optional[str],
    mount_path: str
) -> str:
    """
    Wrap command with cd directive for Docker execution
    
    Args:
        command: Original command to execute
        cwd: Current working directory (may be None)
        workspace_path: Host workspace path (may be None)
        mount_path: Docker mount path
        
    Returns:
        Command wrapped with bash -c and cd if needed
    """
    if not cwd:
        return command
    
    # Convert cwd to Docker path
    docker_cwd = cwd
    if workspace_path:
        docker_cwd = convert_path_to_docker_mount(cwd, workspace_path, mount_path)
    
    # Wrap with bash -c for cd support
    return f"bash -c 'cd {docker_cwd} && {command}'"


def validate_mount_path(mount_path: str) -> tuple[bool, Optional[str]]:
    """
    Validate Docker mount path
    
    Args:
        mount_path: Mount path to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not mount_path:
        return False, "Mount path cannot be empty"
    
    if not mount_path.startswith('/'):
        return False, "Mount path must be absolute (start with /)"
    
    if mount_path.endswith('/') and len(mount_path) > 1:
        return False, "Mount path should not end with /"
    
    # Check for invalid characters
    invalid_chars = ['..', ' ', '\t', '\n', '\r']
    for char in invalid_chars:
        if char in mount_path:
            return False, f"Mount path contains invalid sequence: {repr(char)}"
    
    return True, None


def should_build_custom_docker_image(image_name: str) -> bool:
    """
    Determine if a Docker image should be built locally or pulled from registry
    
    Args:
        image_name: Name of the Docker image
        
    Returns:
        True if image should be built locally, False if it should be pulled
    """
    # Custom CPH images that need to be built
    custom_image_prefixes = ['ojtools', 'cph_']
    
    for prefix in custom_image_prefixes:
        if image_name.startswith(prefix):
            return True
    
    # Check if it's a registry image (e.g., docker.io/library/python)
    # Registry images typically have format: registry/namespace/image:tag
    if '/' in image_name:
        parts = image_name.split('/')
        # Common registries
        registries = ['docker.io', 'gcr.io', 'registry.hub.docker.com', 'quay.io', 'ghcr.io']
        if parts[0] in registries or '.' in parts[0]:
            # Looks like a registry URL
            return False
    
    # Standard images without registry prefix (e.g., python:3.9, ubuntu)
    # These can be pulled from Docker Hub
    if ':' in image_name and '/' not in image_name:
        return False
    
    # Simple image names without tag (e.g., python, ubuntu, alpine)
    if '/' not in image_name and '@' not in image_name:
        return False
    
    # Everything else is considered custom
    return True
"""
Docker utilities package

Consolidated Docker functionality including:
- Command building (docker_command_builder)
- Naming conventions (docker_naming)
- General utilities (docker_utils)
"""
from .docker_command_builder import (
    # Command builders
    build_docker_run_command,
    build_docker_stop_command,
    build_docker_remove_command,
    build_docker_build_command,
    build_docker_ps_command,
    build_docker_inspect_command,
    build_docker_cp_command,
    build_docker_exec_command,
    build_docker_logs_command,
    
    # Validation and parsing
    validate_docker_image_name,
    parse_container_names,
    
    # Backward compatibility aliases
    build_docker_run_command_pure,
    build_docker_stop_command_pure,
    build_docker_remove_command_pure,
    build_docker_build_command_pure,
    build_docker_ps_command_pure,
    build_docker_inspect_command_pure,
    build_docker_cp_command_pure,
    parse_container_names_pure,
    validate_docker_image_name_pure,
)

from .docker_naming import (
    get_docker_image_name,
    get_docker_container_name,
    get_oj_image_name,
    get_oj_container_name,
)

from .docker_utils import *

__all__ = [
    # Command builders
    "build_docker_run_command",
    "build_docker_stop_command", 
    "build_docker_remove_command",
    "build_docker_build_command",
    "build_docker_ps_command",
    "build_docker_inspect_command",
    "build_docker_cp_command",
    "build_docker_exec_command",
    "build_docker_logs_command",
    
    # Validation and parsing
    "validate_docker_image_name",
    "parse_container_names",
    
    # Naming
    "get_docker_image_name",
    "get_docker_container_name",
    "get_oj_image_name", 
    "get_oj_container_name",
    
    # Backward compatibility
    "build_docker_run_command_pure",
    "build_docker_stop_command_pure",
    "build_docker_remove_command_pure",
    "build_docker_build_command_pure",
    "build_docker_ps_command_pure",
    "build_docker_inspect_command_pure",
    "build_docker_cp_command_pure",
    "parse_container_names_pure",
    "validate_docker_image_name_pure",
]
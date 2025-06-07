"""Docker utilities package

Consolidated Docker functionality including:
- Command building (docker_command_builder)
- Naming conventions (docker_naming)
- General utilities (docker_utils)
"""
from .docker_command_builder import (
    build_docker_build_command,
    build_docker_build_command_pure,
    build_docker_cp_command,
    build_docker_cp_command_pure,
    build_docker_exec_command,
    build_docker_inspect_command,
    build_docker_inspect_command_pure,
    build_docker_logs_command,
    build_docker_ps_command,
    build_docker_ps_command_pure,
    build_docker_remove_command,
    build_docker_remove_command_pure,
    # Command builders
    build_docker_run_command,
    # Backward compatibility aliases
    build_docker_run_command_pure,
    build_docker_stop_command,
    build_docker_stop_command_pure,
    parse_container_names,
    parse_container_names_pure,
    # Validation and parsing
    validate_docker_image_name,
    validate_docker_image_name_pure,
)
from .docker_naming import (
    get_docker_container_name,
    get_docker_image_name,
    get_oj_container_name,
    get_oj_image_name,
)
from .docker_utils import *

__all__ = [
    "build_docker_build_command",
    "build_docker_build_command_pure",
    "build_docker_cp_command",
    "build_docker_cp_command_pure",
    "build_docker_exec_command",
    "build_docker_inspect_command",
    "build_docker_inspect_command_pure",
    "build_docker_logs_command",
    "build_docker_ps_command",
    "build_docker_ps_command_pure",
    "build_docker_remove_command",
    "build_docker_remove_command_pure",
    # Command builders
    "build_docker_run_command",
    # Backward compatibility
    "build_docker_run_command_pure",
    "build_docker_stop_command",
    "build_docker_stop_command_pure",
    "get_docker_container_name",
    # Naming
    "get_docker_image_name",
    "get_oj_container_name",
    "get_oj_image_name",
    "parse_container_names",
    "parse_container_names_pure",
    # Validation and parsing
    "validate_docker_image_name",
    "validate_docker_image_name_pure",
]

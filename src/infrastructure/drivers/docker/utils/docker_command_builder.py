"""Docker Command Builder - Consolidated Docker command construction utilities

This module consolidates all Docker command building functionality that was previously
scattered across different modules. All pure functions for building Docker commands
are centralized here.
"""
import re
from typing import Any, Optional, Union

# Configuration manager for type-safe access to Docker options
_config_manager = None

def set_config_manager(config_manager):
    """Set configuration manager via dependency injection

    Args:
        config_manager: TypeSafeConfigNodeManager instance injected from main.py
    """
    global _config_manager
    _config_manager = config_manager

def _get_config_manager():
    """Get configuration manager (must be injected from main.py)"""
    global _config_manager
    if _config_manager is None:
        raise RuntimeError("Configuration manager not injected. Must be set via set_config_manager() from main.py")
    return _config_manager

def _get_docker_option(option_name: str, user_options: Optional[dict[str, Any]]) -> Any:
    """Get Docker option from user options or configuration

    Args:
        option_name: Name of the Docker option
        user_options: User-provided options dictionary

    Returns:
        Option value from user options or configuration

    Raises:
        KeyError: If option not found in either user options or configuration
    """
    # First check user-provided options
    if user_options and option_name in user_options:
        return user_options[option_name]

    # Then check configuration system - フォールバック処理は禁止、必要なエラーを見逃すことになる
    config_manager = _get_config_manager()
    if config_manager is None:
        raise KeyError(f"Docker option '{option_name}' not found: configuration manager not available")

    if config_manager.root_node is None:
        raise KeyError(f"Docker option '{option_name}' not found: configuration not loaded")

    return config_manager.resolve_config(['docker_defaults', 'docker_options', option_name], bool)


def validate_docker_image_name(image_name: str) -> bool:
    """Validate Docker image name format

    Args:
        image_name: Docker image name to validate

    Returns:
        Boolean indicating if the image name is valid
    """
    if not image_name:
        return False

    # Basic Docker image name validation - lowercase only per Docker standard
    # Pattern: [registry/]name[:tag]
    pattern = r'^([a-z0-9._-]+/)*[a-z0-9._-]+(:[\w.-]+)?$'
    return bool(re.match(pattern, image_name))


def _add_docker_run_flags(cmd: list[str], options: dict[str, Any]) -> None:
    """Add basic docker run flags to command."""
    # 互換性維持: .get()使用の代替として設定システム経由でアクセス
    if _get_docker_option("detach", options):
        cmd.append("-d")
    if _get_docker_option("interactive", options):
        cmd.append("-i")
    if _get_docker_option("tty", options):
        cmd.append("-t")
    if _get_docker_option("remove", options):
        cmd.append("--rm")


def _add_docker_run_ports(cmd: list[str], options: dict[str, Any]) -> None:
    """Add port mappings to docker run command."""
    if "ports" in options:
        for port in options["ports"]:
            cmd.extend(["-p", port])


def _add_docker_run_volumes(cmd: list[str], options: dict[str, Any]) -> None:
    """Add volume mounts to docker run command."""
    if "volumes" in options:
        for volume in options["volumes"]:
            cmd.extend(["-v", volume])


def _add_docker_run_environment(cmd: list[str], options: dict[str, Any]) -> None:
    """Add environment variables to docker run command."""
    if "environment" in options:
        for env in options["environment"]:
            cmd.extend(["-e", env])


def _add_docker_run_misc_options(cmd: list[str], options: dict[str, Any]) -> None:
    """Add miscellaneous options to docker run command."""
    # Working directory
    if "workdir" in options:
        cmd.extend(["-w", options["workdir"]])

    # User
    if "user" in options:
        cmd.extend(["-u", options["user"]])

    # Network
    if "network" in options:
        cmd.extend(["--network", options["network"]])

    # Additional arguments
    if "extra_args" in options:
        cmd.extend(options["extra_args"])


def build_docker_run_command(image: str, name: str, options: dict[str, Any]) -> list[str]:
    """Build docker run command

    Args:
        image: Docker image name
        name: Container name
        options: Additional options

    Returns:
        Docker run command as list
    """
    cmd = ["docker", "run"]

    cmd.extend(["--name", name])

    # Always add Docker run flags (validate options explicitly)
    _add_docker_run_flags(cmd, options)
    _add_docker_run_ports(cmd, options)
    _add_docker_run_volumes(cmd, options)
    _add_docker_run_environment(cmd, options)
    _add_docker_run_misc_options(cmd, options)

    cmd.append(image)
    _add_docker_run_command(cmd, options)
    return cmd


def _add_docker_run_command(cmd: list[str], options: Optional[dict[str, Any]]) -> None:
    """Add container command to docker run command."""
    if options and "command" in options:
        if isinstance(options["command"], list):
            cmd.extend(options["command"])
        else:
            cmd.append(options["command"])


def build_docker_stop_command(name: str, timeout: int) -> list[str]:
    """Build docker stop command

    Args:
        name: Container name
        timeout: Stop timeout in seconds

    Returns:
        Docker stop command as list
    """
    cmd = ["docker", "stop"]
    cmd.extend(["-t", str(timeout)])
    cmd.append(name)
    return cmd


def build_docker_remove_command(name: str, force: bool = False, volumes: bool = False) -> list[str]:
    """Build docker remove command

    Args:
        name: Container name
        force: Force removal flag
        volumes: Remove associated volumes

    Returns:
        Docker remove command as list
    """
    cmd = ["docker", "rm"]
    if force:
        cmd.append("-f")
    if volumes:
        cmd.append("-v")
    cmd.append(name)
    return cmd


def build_docker_build_command(tag: str, dockerfile_text: str,
                              context_path: str, options: dict[str, Any]) -> list[str]:
    """Build docker build command

    Args:
        tag: Image tag
        dockerfile_text: Dockerfile content (if None, uses Dockerfile in context)
        context_path: Build context path
        options: Additional options

    Returns:
        Docker build command as list
    """
    cmd = ["docker", "build"]

    cmd.extend(["-t", tag])

    if "build_args" in options:
        for arg in options["build_args"]:
            cmd.extend(["--build-arg", arg])
    if _get_docker_option("no_cache", options):
        cmd.append("--no-cache")
    if _get_docker_option("pull", options):
        cmd.append("--pull")
    if _get_docker_option("quiet", options):
        cmd.append("-q")

    # If dockerfile_text is provided, read from stdin
    cmd.extend(["-f", "-"])

    cmd.append(context_path)
    return cmd


def build_docker_ps_command(all: bool, filter_params: list[str],
                           format_string: str) -> list[str]:
    """Build docker ps command

    Args:
        all: Show all containers flag
        filter_params: List of filter parameters
        format_string: Custom format string

    Returns:
        Docker ps command as list
    """
    cmd = ["docker", "ps"]

    if all:
        cmd.append("-a")

    for filter_param in filter_params:
        cmd.extend(["--filter", filter_param])

    cmd.extend(["--format", format_string])

    return cmd


def build_docker_inspect_command(target: str, type_: str,
                                format_string: str) -> list[str]:
    """Build docker inspect command

    Args:
        target: Target to inspect
        type_: Type of target (container, image, network, volume)
        format_string: Custom format string

    Returns:
        Docker inspect command as list
    """
    cmd = ["docker", "inspect"]

    cmd.extend(["--type", type_])

    cmd.extend(["--format", format_string])

    cmd.append(target)
    return cmd


def build_docker_cp_command(src: str, dst: str, container: str,
                           to_container: bool = True) -> list[str]:
    """Build docker cp command

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
    return ["docker", "cp", f"{container}:{src}", dst]


def build_docker_exec_command(container: str, command: Union[str, list[str]],
                             interactive: bool, tty: bool,
                             user: str, workdir: str) -> list[str]:
    """Build docker exec command

    Args:
        container: Container name
        command: Command to execute
        interactive: Interactive mode
        tty: Allocate pseudo-TTY
        user: User to run as
        workdir: Working directory

    Returns:
        Docker exec command as list
    """
    cmd = ["docker", "exec"]

    if interactive:
        cmd.append("-i")

    if tty:
        cmd.append("-t")

    cmd.extend(["-u", user])

    cmd.extend(["-w", workdir])

    cmd.append(container)

    if isinstance(command, list):
        cmd.extend(command)
    else:
        cmd.append(command)

    return cmd


def build_docker_logs_command(container: str, follow: bool,
                             tail: int, since: str) -> list[str]:
    """Build docker logs command

    Args:
        container: Container name
        follow: Follow log output
        tail: Number of lines to show from end
        since: Show logs since timestamp

    Returns:
        Docker logs command as list
    """
    cmd = ["docker", "logs"]

    if follow:
        cmd.append("-f")

    cmd.extend(["--tail", str(tail)])

    cmd.extend(["--since", since])

    cmd.append(container)
    return cmd


def parse_container_names(output: str) -> list[str]:
    """Parse container names from docker ps output

    Args:
        output: Docker ps output

    Returns:
        List of container names
    """
    if not output:
        return []

    lines = output.strip().split('\n')
    return [line.strip() for line in lines if line.strip()]


# Backward compatibility aliases (legacy function versions)
build_docker_run_command_legacy = build_docker_run_command
build_docker_stop_command_legacy = build_docker_stop_command
build_docker_remove_command_legacy = build_docker_remove_command
build_docker_build_command_legacy = build_docker_build_command
build_docker_ps_command_legacy = build_docker_ps_command
build_docker_inspect_command_legacy = build_docker_inspect_command
build_docker_cp_command_legacy = build_docker_cp_command
parse_container_names_legacy = parse_container_names
validate_docker_image_name_legacy = validate_docker_image_name


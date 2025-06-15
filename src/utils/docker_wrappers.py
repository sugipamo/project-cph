"""Docker command wrapper utilities

Backward compatibility wrappers for Docker operations.
These functions provide a stable interface while delegating to the actual implementations.
"""


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

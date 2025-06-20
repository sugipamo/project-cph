"""Docker utility functions for container operations.
"""
from typing import Any, Optional


class DockerUtils:
    """Utility class for Docker command construction and parsing."""

    @staticmethod
    def build_docker_cmd(base_cmd: list[str], options: Optional[dict[str, Any]] = None,
                        positional_args: Optional[list[str]] = None) -> list[str]:
        """Build a Docker command with options and positional arguments.

        Args:
            base_cmd: Base command (e.g., ["docker", "run"])
            options: Dictionary of options (key -> value or None for flags)
            positional_args: List of positional arguments

        Returns:
            Complete command as list of strings
        """
        cmd = base_cmd.copy()

        if options:
            for key, value in options.items():
                if len(key) == 1:
                    # Short option
                    cmd.append(f"-{key}")
                else:
                    # Long option
                    cmd.append(f"--{key}")

                if value is not None:
                    cmd.append(str(value))

        if positional_args:
            cmd.extend(positional_args)

        return cmd

    @staticmethod
    def parse_image_tag(image_with_tag: str) -> tuple[str, Optional[str]]:
        """Parse image name and tag from image string.

        Args:
            image_with_tag: Image string (e.g., "ubuntu:20.04" or "ubuntu")

        Returns:
            Tuple of (image_name, tag) where tag is None if not specified
        """
        if ":" in image_with_tag:
            parts = image_with_tag.split(":", 1)
            return parts[0], parts[1]
        return image_with_tag, None

    @staticmethod
    def format_container_name(name: str) -> str:
        """Format container name to ensure it follows Docker naming conventions.

        Args:
            name: Container name

        Returns:
            Formatted container name
        """
        # Remove invalid characters and replace with underscores
        formatted = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)

        # Ensure it doesn't start with a number or special character
        if formatted and not formatted[0].isalpha():
            formatted = "container_" + formatted

        return formatted or "default_container"

    @staticmethod
    def validate_image_name(image: str) -> bool:
        """Validate Docker image name format.

        Args:
            image: Image name to validate

        Returns:
            True if valid, False otherwise
        """
        if not image or len(image) > 128:
            return False

        # Basic validation - no spaces, valid characters
        return all(c.isalnum() or c in "._-:/" for c in image)


def validate_docker_image_name(image: str) -> bool:
    """Validate Docker image name format (backward compatibility function).

    Args:
        image: Image name to validate

    Returns:
        True if valid, False otherwise
    """
    return DockerUtils.validate_image_name(image)

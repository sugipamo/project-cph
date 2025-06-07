"""Docker naming convention utilities
Provides consistent naming for Docker images and containers
"""
import hashlib
from typing import Optional


def calculate_dockerfile_hash(dockerfile_text: Optional[str]) -> Optional[str]:
    """Calculate short hash for dockerfile content

    Args:
        dockerfile_text: Dockerfile content as string

    Returns:
        12-character hash of dockerfile content, or None if empty
    """
    if not dockerfile_text or not dockerfile_text.strip():
        return None
    return hashlib.sha256(dockerfile_text.encode("utf-8")).hexdigest()[:12]


def get_docker_image_name(language: str, dockerfile_text: Optional[str] = None) -> str:
    """Generate Docker image name with optional content hash

    Args:
        language: Programming language (e.g., 'python', 'rust')
        dockerfile_text: Custom dockerfile content

    Returns:
        Image name in format: {language} or {language}_{hash}
    """
    if not dockerfile_text or not dockerfile_text.strip():
        return language
    hash_suffix = calculate_dockerfile_hash(dockerfile_text)
    return f"{language}_{hash_suffix}"


def get_docker_container_name(language: str, dockerfile_text: Optional[str] = None) -> str:
    """Generate Docker container name with cph_ prefix (no hash for consistency)

    Args:
        language: Programming language
        dockerfile_text: Custom dockerfile content (ignored for container names)

    Returns:
        Container name in format: cph_{language}
    """
    return f"cph_{language}"


def get_oj_image_name(oj_dockerfile_text: Optional[str] = None) -> str:
    """Generate OJ tools image name

    Args:
        oj_dockerfile_text: OJ dockerfile content

    Returns:
        OJ image name in format: ojtools or ojtools_{hash}
    """
    if not oj_dockerfile_text or not oj_dockerfile_text.strip():
        return "ojtools"
    hash_suffix = calculate_dockerfile_hash(oj_dockerfile_text)
    return f"ojtools_{hash_suffix}"


def get_oj_container_name(oj_dockerfile_text: Optional[str] = None) -> str:
    """Generate OJ tools container name (no hash for consistency)

    Args:
        oj_dockerfile_text: OJ dockerfile content (ignored for container names)

    Returns:
        OJ container name in format: cph_ojtools
    """
    return "cph_ojtools"

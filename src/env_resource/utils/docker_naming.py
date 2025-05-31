"""Docker image and container naming utilities as pure functions"""
import hashlib
from typing import Optional


def get_image_name(language: str, dockerfile_text: Optional[str] = None) -> str:
    """
    Generate Docker image name based on language and optional dockerfile content.
    
    Args:
        language: Programming language name
        dockerfile_text: Dockerfile content (optional)
        
    Returns:
        Image name with hash suffix if dockerfile provided
    """
    if not dockerfile_text:
        return language
    hash_str = hashlib.sha256(dockerfile_text.encode("utf-8")).hexdigest()[:12]
    return f"{language}_{hash_str}"


def get_container_name(language: str, dockerfile_text: Optional[str] = None) -> str:
    """
    Generate Docker container name.
    
    Args:
        language: Programming language name
        dockerfile_text: Dockerfile content (optional)
        
    Returns:
        Container name with cph_ prefix
    """
    image_name = get_image_name(language, dockerfile_text)
    return f"cph_{image_name}"


def get_oj_image_name(oj_dockerfile_text: Optional[str] = None) -> str:
    """
    Generate OJ tools Docker image name.
    
    Args:
        oj_dockerfile_text: OJ Dockerfile content (optional)
        
    Returns:
        OJ image name with hash suffix if dockerfile provided
    """
    base_name = "ojtools"
    if not oj_dockerfile_text:
        return base_name
    hash_str = hashlib.sha256(oj_dockerfile_text.encode("utf-8")).hexdigest()[:12]
    return f"{base_name}_{hash_str}"


def get_oj_container_name(oj_dockerfile_text: Optional[str] = None) -> str:
    """
    Generate OJ tools Docker container name.
    
    Args:
        oj_dockerfile_text: OJ Dockerfile content (optional)
        
    Returns:
        OJ container name with cph_ prefix
    """
    image_name = get_oj_image_name(oj_dockerfile_text)
    return f"cph_{image_name}"
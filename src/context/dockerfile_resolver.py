"""
Dockerfile resolver for delayed loading
Implements the resolver pattern for Dockerfile content management
"""
from typing import Optional, Callable, Dict, Any
from src.shared.utils.docker.docker_naming import (
    get_docker_image_name, get_docker_container_name,
    get_oj_image_name, get_oj_container_name
)


class DockerfileResolver:
    """
    Lazy Dockerfile content resolver
    
    Stores Dockerfile paths and loader functions, reads content only when needed.
    Caches content to avoid repeated file operations.
    Follows the same resolver pattern used by configuration system.
    """
    
    def __init__(self, dockerfile_path: Optional[str] = None, 
                 oj_dockerfile_path: Optional[str] = None,
                 dockerfile_loader: Optional[Callable[[str], str]] = None):
        """
        Initialize resolver with paths and loader function
        
        Args:
            dockerfile_path: Path to main Dockerfile
            oj_dockerfile_path: Path to OJ tools Dockerfile  
            dockerfile_loader: Function to load Dockerfile content from path
        """
        self._dockerfile_path = dockerfile_path
        self._oj_dockerfile_path = oj_dockerfile_path
        self._dockerfile_loader = dockerfile_loader
        
        # Content cache (None = not loaded, actual content once loaded)
        self._dockerfile_content: Optional[str] = None
        self._oj_dockerfile_content: Optional[str] = None
        self._content_loaded = {"dockerfile": False, "oj_dockerfile": False}
    
    @property
    def dockerfile(self) -> Optional[str]:
        """
        Get main Dockerfile content (lazy loaded)
        
        Returns:
            Dockerfile content or None if not available
        """
        if not self._content_loaded["dockerfile"]:
            self._load_dockerfile_content()
        return self._dockerfile_content
    
    @property
    def oj_dockerfile(self) -> Optional[str]:
        """
        Get OJ Dockerfile content (lazy loaded)
        
        Returns:
            OJ Dockerfile content or None if not available
        """
        if not self._content_loaded["oj_dockerfile"]:
            self._load_oj_dockerfile_content()
        return self._oj_dockerfile_content
    
    def get_docker_names(self, language: str) -> Dict[str, str]:
        """
        Generate Docker names using resolved Dockerfile content
        
        Args:
            language: Programming language
            
        Returns:
            Dictionary with image_name, container_name, oj_image_name, oj_container_name
        """
        return {
            "image_name": get_docker_image_name(language, self.dockerfile),
            "container_name": get_docker_container_name(language, self.dockerfile), 
            "oj_image_name": get_oj_image_name(self.oj_dockerfile),
            "oj_container_name": get_oj_container_name(self.oj_dockerfile)
        }
    
    def _load_dockerfile_content(self) -> None:
        """Load main Dockerfile content from path"""
        self._content_loaded["dockerfile"] = True
        
        if not self._dockerfile_path or not self._dockerfile_loader:
            self._dockerfile_content = None
            return
            
        try:
            self._dockerfile_content = self._dockerfile_loader(self._dockerfile_path)
        except Exception:
            self._dockerfile_content = None
    
    def _load_oj_dockerfile_content(self) -> None:
        """Load OJ Dockerfile content from path"""
        self._content_loaded["oj_dockerfile"] = True
        
        if not self._oj_dockerfile_path or not self._dockerfile_loader:
            self._oj_dockerfile_content = None
            return
            
        try:
            self._oj_dockerfile_content = self._dockerfile_loader(self._oj_dockerfile_path)
        except Exception:
            self._oj_dockerfile_content = None
    
    def invalidate_cache(self) -> None:
        """
        Invalidate content cache, forcing reload on next access
        Useful when Dockerfile files may have changed
        """
        self._dockerfile_content = None
        self._oj_dockerfile_content = None
        self._content_loaded = {"dockerfile": False, "oj_dockerfile": False}
    
    def has_dockerfile(self) -> bool:
        """Check if main Dockerfile path is configured"""
        return self._dockerfile_path is not None
    
    def has_oj_dockerfile(self) -> bool:
        """Check if OJ Dockerfile path is configured"""
        return self._oj_dockerfile_path is not None
    
    def preload(self) -> None:
        """
        Preload all Dockerfile content
        Useful for performance-critical sections where lazy loading overhead is undesirable
        """
        # Access properties to trigger loading
        _ = self.dockerfile
        _ = self.oj_dockerfile
    
    def __repr__(self) -> str:
        return (f"DockerfileResolver(dockerfile_path={self._dockerfile_path}, "
                f"oj_dockerfile_path={self._oj_dockerfile_path}, "
                f"loaded={self._content_loaded})")
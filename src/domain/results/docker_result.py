"""Docker operation result."""
from typing import Optional, Any
from src.domain.results.result import OperationResult


class DockerResult(OperationResult):
    """Result class for Docker operations."""
    
    def __init__(self, stdout: Optional[str] = None, stderr: Optional[str] = None, 
                 returncode: Optional[int] = None, container_id: Optional[str] = None,
                 image: Optional[str] = None, **kwargs):
        """Initialize Docker result.
        
        Args:
            stdout: Standard output
            stderr: Standard error
            returncode: Return code
            container_id: Container ID
            image: Docker image name
            **kwargs: Additional arguments passed to parent
        """
        super().__init__(
            stdout=stdout,
            stderr=stderr,
            returncode=returncode,
            **kwargs
        )
        self.container_id = container_id
        self.image = image
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<DockerResult success={self.success} returncode={self.returncode} "
            f"container_id={self.container_id} image={self.image}>"
        )
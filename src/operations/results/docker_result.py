"""Docker operation result."""
from typing import Optional

from src.operations.results.result import OperationResult


class DockerResult(OperationResult):
    """Result class for Docker operations."""

    def __init__(self, stdout: Optional[str], stderr: Optional[str],
                 returncode: Optional[int], container_id: Optional[str],
                 image: Optional[str], **kwargs):
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

"""Docker driver interface for domain layer

This interface defines the contract that infrastructure must implement.
Domain layer depends only on this abstraction, not on concrete implementations.
"""
from abc import ABC, abstractmethod

from src.domain.results.result import OperationResult


class DockerDriverInterface(ABC):
    """Abstract interface for Docker operations."""

    @abstractmethod
    def run_docker_container(self, image: str, **kwargs) -> OperationResult:
        """Run a Docker container."""

    @abstractmethod
    def stop(self, container: str, **kwargs) -> OperationResult:
        """Stop a Docker container."""

    @abstractmethod
    def remove(self, container: str, **kwargs) -> OperationResult:
        """Remove a Docker container."""

    @abstractmethod
    def exec(self, container: str, command: str, **kwargs) -> OperationResult:
        """Execute command in a Docker container."""

    @abstractmethod
    def logs(self, container: str, **kwargs) -> OperationResult:
        """Get logs from a Docker container."""

    @abstractmethod
    def inspect(self, container: str, **kwargs) -> OperationResult:
        """Inspect a Docker container."""

    @abstractmethod
    def build_docker_image(self, context_path: str, **kwargs) -> OperationResult:
        """Build a Docker image."""

    @abstractmethod
    def ps(self, **kwargs) -> OperationResult:
        """List Docker containers."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if Docker is available."""

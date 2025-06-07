"""
Docker driver interface for domain layer

This interface defines the contract that infrastructure must implement.
Domain layer depends only on this abstraction, not on concrete implementations.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from src.domain.results.result import OperationResult


class DockerDriverInterface(ABC):
    """Abstract interface for Docker operations."""
    
    @abstractmethod
    def run(self, image: str, **kwargs) -> OperationResult:
        """Run a Docker container."""
        pass
    
    @abstractmethod
    def stop(self, container: str, **kwargs) -> OperationResult:
        """Stop a Docker container."""
        pass
    
    @abstractmethod
    def remove(self, container: str, **kwargs) -> OperationResult:
        """Remove a Docker container."""
        pass
    
    @abstractmethod
    def exec(self, container: str, command: str, **kwargs) -> OperationResult:
        """Execute command in a Docker container."""
        pass
    
    @abstractmethod
    def logs(self, container: str, **kwargs) -> OperationResult:
        """Get logs from a Docker container."""
        pass
    
    @abstractmethod
    def inspect(self, container: str, **kwargs) -> OperationResult:
        """Inspect a Docker container."""
        pass
    
    @abstractmethod
    def build(self, context_path: str, **kwargs) -> OperationResult:
        """Build a Docker image."""
        pass
    
    @abstractmethod
    def ps(self, **kwargs) -> OperationResult:
        """List Docker containers."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if Docker is available."""
        pass
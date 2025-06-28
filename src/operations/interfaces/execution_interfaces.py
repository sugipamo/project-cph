"""Consolidated execution-related interfaces."""
from abc import ABC, abstractmethod
from typing import Any, List, Optional

from src.operations.results.result import OperationResult


class ExecutionInterface(ABC):
    """Pure interface for execution operations without side effects."""

    @abstractmethod
    def execute_request_operation(self, request: Any, logger: Any) -> Any:
        """Execute operation using provided request and logger."""
        pass


class DockerDriverInterface(ABC):
    """Interface for Docker operations."""

    @abstractmethod
    def run_docker_container(
        self,
        image: str,
        tag: str,
        container_name: str,
        commands: List[str],
        detach: bool,
        environment: dict,
        volumes: dict,
        working_dir: str,
        ports: dict
    ) -> OperationResult:
        """Run a Docker container with specified configuration."""
        pass

    @abstractmethod
    def stop(self, container_name: str) -> OperationResult:
        """Stop a running container."""
        pass

    @abstractmethod
    def remove(self, container_name: str) -> OperationResult:
        """Remove a container."""
        pass

    @abstractmethod
    def exec(self, container_name: str, commands: List[str]) -> OperationResult:
        """Execute commands in a running container."""
        pass

    @abstractmethod
    def logs(self, container_name: str) -> OperationResult:
        """Get logs from a container."""
        pass

    @abstractmethod
    def inspect(self, container_name: str) -> OperationResult:
        """Inspect a container."""
        pass

    @abstractmethod
    def build_docker_image(
        self,
        dockerfile_path: str,
        image_name: str,
        tag: str,
        build_args: dict
    ) -> OperationResult:
        """Build a Docker image from a Dockerfile."""
        pass

    @abstractmethod
    def ps(self) -> OperationResult:
        """List running containers."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if Docker is available on the system."""
        pass


class ShellExecutionInterface(ABC):
    """Interface for shell command execution."""

    @abstractmethod
    def execute_command(
        self,
        command: str,
        working_directory: Optional[str] = None,
        timeout: Optional[float] = None,
        environment: Optional[dict] = None,
        shell: Optional[bool] = None
    ) -> dict:
        """Execute a shell command."""
        pass


class PythonExecutionInterface(ABC):
    """Interface for Python code execution."""

    @abstractmethod
    def execute_python(
        self,
        script_or_code: str,
        is_script_path: bool,
        working_directory: str,
        timeout: Optional[float] = None,
        environment: Optional[dict] = None,
        python_path: Optional[str] = None
    ) -> dict:
        """Execute Python code or script."""
        pass

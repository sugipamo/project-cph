"""Pure domain interfaces for request operations."""
from abc import ABC, abstractmethod
from typing import Any, Dict


class ExecutionInterface(ABC):
    """Pure interface for execution operations without side effects."""

    @abstractmethod
    def execute_operation(self, driver: Any, logger: Any) -> Any:
        """Execute operation using provided infrastructure services."""
        pass


class FileOperationInterface(ABC):
    """Pure interface for file operations."""

    @abstractmethod
    def execute_file_operation(self, operation_type: str, path: str, **kwargs) -> Any:
        """Execute file operation with given parameters."""
        pass


class DockerOperationInterface(ABC):
    """Pure interface for Docker operations."""

    @abstractmethod
    def execute_docker_operation(self, command: str, options: Dict[str, Any]) -> Any:
        """Execute Docker operation with given command and options."""
        pass


class PythonOperationInterface(ABC):
    """Pure interface for Python operations."""

    @abstractmethod
    def execute_python_operation(self, script: str, environment: Dict[str, str]) -> Any:
        """Execute Python operation with given script and environment."""
        pass


class ShellOperationInterface(ABC):
    """Pure interface for shell operations."""

    @abstractmethod
    def execute_shell_operation(self, command: str, working_directory: str) -> Any:
        """Execute shell operation with given command and working directory."""
        pass

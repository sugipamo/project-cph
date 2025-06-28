"""Base request module combining interfaces and types for request operations."""
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict


class RequestType(Enum):
    """Enumeration of request types for type-safe identification."""

    # Core request types
    OPERATION_REQUEST_FOUNDATION = auto()
    COMPOSITE_REQUEST_FOUNDATION = auto()

    # Specific request types
    DOCKER_REQUEST = auto()
    FILE_REQUEST = auto()
    SHELL_REQUEST = auto()
    PYTHON_REQUEST = auto()
    COMPOSITE_REQUEST = auto()

    # Step types
    BUILD_STEP = auto()
    RUN_STEP = auto()
    TEST_STEP = auto()

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        return self.name.replace('_', ' ').title()

    @property
    def short_name(self) -> str:
        """Get short name for logging/display."""
        name_map = {
            self.DOCKER_REQUEST: "Docker",
            self.FILE_REQUEST: "File",
            self.SHELL_REQUEST: "Shell",
            self.PYTHON_REQUEST: "Python",
            self.COMPOSITE_REQUEST: "Composite",
            self.COMPOSITE_REQUEST_FOUNDATION: "CompositeFoundation",
            self.OPERATION_REQUEST_FOUNDATION: "OperationFoundation",
            self.BUILD_STEP: "Build",
            self.RUN_STEP: "Run",
            self.TEST_STEP: "Test",
        }
        return name_map[self]


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
    def execute_shell_operation(self, command: str) -> Any:
        """Execute shell operation with given command and working directory."""
        pass

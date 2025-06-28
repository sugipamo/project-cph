"""Request operations module."""
# Base request types and interfaces
from .base_request import (
    DockerOperationInterface,
    ExecutionInterface,
    FileOperationInterface,
    PythonOperationInterface,
    RequestType,
    ShellOperationInterface,
)

# Concrete request implementations
from .composite_request import CompositeRequest
from .execution_requests import (
    DockerOperationError,
    DockerOpType,
    DockerRequest,
    FileRequest,
    PythonRequest,
    ShellRequest,
)

# Factory
from .request_factory import RequestCreator, RequestFactory

__all__ = [
    # Types and interfaces
    "RequestType",
    "ExecutionInterface",
    "FileOperationInterface",
    "DockerOperationInterface",
    "PythonOperationInterface",
    "ShellOperationInterface",
    # Concrete implementations
    "CompositeRequest",
    "DockerRequest",
    "DockerOpType",
    "DockerOperationError",
    "FileRequest",
    "PythonRequest",
    "ShellRequest",
    # Factory
    "RequestFactory",
    "RequestCreator",
]

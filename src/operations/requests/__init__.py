"""Request operations module."""
# Base request types and interfaces
from .base_request import (
    RequestType,
    ExecutionInterface,
    FileOperationInterface,
    DockerOperationInterface,
    PythonOperationInterface,
    ShellOperationInterface,
)

# Concrete request implementations
from .composite_request import CompositeRequest
from .execution_requests import (
    DockerRequest, DockerOpType, DockerOperationError,
    FileRequest,
    PythonRequest,
    ShellRequest,
)

# Factory
from .request_factory import RequestFactory, RequestCreator

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
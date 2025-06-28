"""Consolidated operation interfaces."""
# Execution interfaces
from .execution_interfaces import (
    ExecutionInterface,
    DockerDriverInterface,
    ShellExecutionInterface,
    PythonExecutionInterface,
)

# Infrastructure interfaces
from .infrastructure_interfaces import (
    FileSystemInterface,
    PersistenceInterface,
    RepositoryInterface,
    TimeInterface,
)

# Utility interfaces
from .utility_interfaces import (
    LoggerInterface,
    OutputManagerInterface,
    OutputInterface,
    RegexInterface,
)

__all__ = [
    # Execution
    "ExecutionInterface",
    "DockerDriverInterface",
    "ShellExecutionInterface",
    "PythonExecutionInterface",
    # Infrastructure
    "FileSystemInterface",
    "PersistenceInterface",
    "RepositoryInterface",
    "TimeInterface",
    # Utility
    "LoggerInterface",
    "OutputManagerInterface",
    "OutputInterface",
    "RegexInterface",
]
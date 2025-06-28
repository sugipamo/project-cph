"""Result operations module."""
# Base results
from .base_result import InfrastructureResult, InfrastructureOperationResult
from .result import Result, OperationResult, ValidationResult

# Execution results
from .execution_results import (
    ExecutionResultBase,
    ShellResult,
    DockerResult,
    PythonResult,
    LegacyShellResult as ShellResult_Legacy,
    LegacyDockerResult as DockerResult_Legacy,
)

# Specialized results
from .file_result import FileResult
from .check_result import CheckResult, CircularImport

# Factory
from .result_factory import ResultFactory

__all__ = [
    # Base
    "InfrastructureResult",
    "InfrastructureOperationResult",
    "Result",
    "OperationResult",
    "ValidationResult",
    # Execution
    "ExecutionResultBase",
    "ShellResult",
    "DockerResult", 
    "PythonResult",
    "ShellResult_Legacy",
    "DockerResult_Legacy",
    # Specialized
    "FileResult",
    "CheckResult",
    "CircularImport",
    # Factory
    "ResultFactory",
]
"""Result operations module."""
# Base results
from .base_result import InfrastructureOperationResult, InfrastructureResult
from .check_result import CheckResult, CircularImport

# Execution results
from .execution_results import (
    DockerResult,
    ExecutionResultBase,
    PythonResult,
    ShellResult,
)
from .execution_results import (
    LegacyDockerResult as DockerResult_Legacy,
)
from .execution_results import (
    LegacyShellResult as ShellResult_Legacy,
)

# Specialized results
from .file_result import FileResult
from .result import OperationResult, Result, ValidationResult

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

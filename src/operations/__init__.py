"""Result operations module."""
# Base results
from .results.base_result import InfrastructureOperationResult, InfrastructureResult
from .results.check_result import CheckResult, CircularImport

# Execution results
from src.application.execution_results import (
    DockerResult,
    ExecutionResultBase,
    PythonResult,
    ShellResult,
)
from src.application.execution_results import (
    LegacyDockerResult as DockerResult_Legacy,
)
from src.application.execution_results import (
    LegacyShellResult as ShellResult_Legacy,
)

# Specialized results
from .results.file_result import FileResult
from .results.result import OperationResult, Result, ValidationResult

# Factory
from .results.result_factory import ResultFactory

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

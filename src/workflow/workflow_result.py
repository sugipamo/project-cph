"""Workflow execution result data structures
"""
from dataclasses import dataclass

from src.domain.results.result import OperationResult


@dataclass
class WorkflowExecutionResult:
    """Result of workflow execution"""
    success: bool
    results: list[OperationResult]
    preparation_results: list[OperationResult]
    errors: list[str]
    warnings: list[str]

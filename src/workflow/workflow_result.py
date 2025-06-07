"""
Workflow execution result data structures
"""
from typing import List
from dataclasses import dataclass
from src.domain.results.result import OperationResult


@dataclass
class WorkflowExecutionResult:
    """Result of workflow execution"""
    success: bool
    results: List[OperationResult]
    preparation_results: List[OperationResult]
    errors: List[str]
    warnings: List[str]
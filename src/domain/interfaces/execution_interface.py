"""
Execution interface for domain layer

This interface defines the contract for request execution.
Domain layer depends only on this abstraction.
"""
from abc import ABC, abstractmethod
from typing import Any
from src.domain.results.result import OperationResult


class ExecutionInterface(ABC):
    """Abstract interface for request execution."""
    
    @abstractmethod
    def execute(self, request: Any) -> OperationResult:
        """Execute a request and return the result."""
        pass


class OutputInterface(ABC):
    """Abstract interface for output management."""
    
    @abstractmethod
    def format_output(self, result: OperationResult, **kwargs) -> str:
        """Format operation result for output."""
        pass
    
    @abstractmethod
    def display_output(self, formatted_output: str, **kwargs) -> None:
        """Display formatted output."""
        pass
"""Base driver interface for all execution drivers."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseDriver(ABC):
    """Abstract base class for all drivers."""
    
    @abstractmethod
    def execute(self, request: Any) -> Any:
        """Execute a request and return the result.
        
        Args:
            request: The request object to execute
            
        Returns:
            The execution result
        """
        pass
    
    @abstractmethod
    def validate(self, request: Any) -> bool:
        """Validate if the driver can handle the request.
        
        Args:
            request: The request object to validate
            
        Returns:
            True if the driver can handle the request, False otherwise
        """
        pass
    
    def initialize(self) -> None:
        """Initialize the driver. Override if needed."""
        pass
    
    def cleanup(self) -> None:
        """Cleanup driver resources. Override if needed."""
        pass
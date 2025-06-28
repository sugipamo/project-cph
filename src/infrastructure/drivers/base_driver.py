"""Base driver implementation with common functionality."""

from typing import Any, Optional

from src.infrastructure.di_container import DIContainer
from src.infrastructure.drivers.generic.base_driver import ExecutionDriverInterface
from src.operations.interfaces.logger_interface import LoggerInterface


class BaseDriverImplementation(ExecutionDriverInterface):
    """Base implementation for drivers with common functionality."""
    
    def __init__(self, container: Optional[DIContainer] = None):
        """Initialize driver with optional dependency injection container.
        
        Args:
            container: Dependency injection container for resolving dependencies
        """
        super().__init__()
        self.container = container
        self._logger: Optional[LoggerInterface] = None
        
    @property
    def logger(self) -> LoggerInterface:
        """Get logger instance with lazy loading.
        
        Returns:
            Logger interface instance
        """
        if self._logger is None and self.container:
            from src.infrastructure.di_container import DIKey
            self._logger = self.container.resolve(DIKey.LOGGER)
        return self._logger
        
    def validate(self, request: Any) -> bool:
        """Default validation that checks if request has required attributes.
        
        Override this method to add specific validation logic.
        
        Args:
            request: The request to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Default implementation checks if request is not None
        return request is not None
        
    def log_debug(self, message: str, **kwargs) -> None:
        """Log debug message if logger is available.
        
        Args:
            message: Debug message to log
            **kwargs: Additional context for logging
        """
        if self.logger:
            self.logger.debug(message, **kwargs)
            
    def log_info(self, message: str, **kwargs) -> None:
        """Log info message if logger is available.
        
        Args:
            message: Info message to log
            **kwargs: Additional context for logging
        """
        if self.logger:
            self.logger.info(message, **kwargs)
            
    def log_error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log error message if logger is available.
        
        Args:
            message: Error message to log
            error: Optional exception that caused the error
            **kwargs: Additional context for logging
        """
        if self.logger:
            if error:
                kwargs['error'] = str(error)
                kwargs['error_type'] = type(error).__name__
            self.logger.error(message, **kwargs)
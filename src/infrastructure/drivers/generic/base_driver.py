"""Base driver interface and implementation for all execution drivers."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

from src.operations.interfaces.utility_interfaces import LoggerInterface


class ExecutionDriverInterface(ABC):
    """Abstract base class for all drivers."""

    def __init__(self):
        """Initialize driver with infrastructure defaults."""
        self._infrastructure_defaults: Optional[Dict[str, Any]] = None
        self._default_cache: Dict[str, Any] = {}

    @abstractmethod
    def execute_command(self, request: Any) -> Any:
        """Execute a request and return the result.

        Args:
            request: The request object to execute

        Returns:
            The execution result
        """

    @abstractmethod
    def validate(self, request: Any) -> bool:
        """Validate if the driver can handle the request.

        Args:
            request: The request object to validate

        Returns:
            True if the driver can handle the request, False otherwise
        """

    def initialize(self) -> None:
        """Initialize the driver. Override if needed."""

    def cleanup(self) -> None:
        """Cleanup driver resources. Override if needed."""

    def _load_infrastructure_defaults(self) -> Dict[str, Any]:
        """Load infrastructure defaults from configuration file.
        
        Returns:
            Dictionary containing infrastructure defaults
        """
        if self._infrastructure_defaults is not None:
            return self._infrastructure_defaults

        try:
            # Find config path relative to project root
            current_path = Path(__file__)
            project_root = current_path
            while project_root.name != "project-cph" and project_root.parent != project_root:
                project_root = project_root.parent

            config_path = project_root / "config" / "system" / "infrastructure_defaults.json"

            if config_path.exists():
                with open(config_path, encoding='utf-8') as f:
                    self._infrastructure_defaults = json.load(f)
            else:
                self._infrastructure_defaults = {}

        except (FileNotFoundError, json.JSONDecodeError):
            # Log error if logger is available
            self._infrastructure_defaults = {}

        return self._infrastructure_defaults

    def _get_default_value(self, key_path: str, default: Any = None) -> Any:
        """Get a default value from infrastructure defaults.
        
        Args:
            key_path: Dot-separated path to the value (e.g., "docker.network_name")
            default: Default value if key not found
            
        Returns:
            The value from defaults or the provided default
        """
        # Check cache first
        if key_path in self._default_cache:
            return self._default_cache[key_path]

        defaults = self._load_infrastructure_defaults()

        # Navigate through nested dictionaries
        keys = key_path.split('.')
        value = defaults

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                value = default
                break

        # Cache the result
        self._default_cache[key_path] = value
        return value


class BaseDriverImplementation(ExecutionDriverInterface):
    """Base implementation for drivers with common functionality."""

    def __init__(self, logger: Optional[LoggerInterface] = None):
        """Initialize driver with optional logger.
        
        Args:
            logger: Optional logger instance for logging operations
        """
        super().__init__()
        self._logger = logger

    @property
    def logger(self) -> Optional[LoggerInterface]:
        """Get logger instance.
        
        Returns:
            Logger interface instance or None if not set
        """
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


# Common utility functions for drivers
class DriverUtils:
    """Common utility functions for drivers."""

    @staticmethod
    def validate_path(path: str) -> bool:
        """Validate if a path is safe and accessible.
        
        Args:
            path: Path to validate
            
        Returns:
            True if path is valid, False otherwise
        """
        try:
            path_obj = Path(path)
            # Check if path is absolute or can be resolved
            if not path_obj.is_absolute():
                path_obj = path_obj.resolve()
            return True
        except (ValueError, OSError):
            return False

    @staticmethod
    def load_defaults(config_name: str) -> Dict[str, Any]:
        """Load default configuration from a specific config file.
        
        Args:
            config_name: Name of the configuration file (without .json extension)
            
        Returns:
            Dictionary containing configuration defaults
        """
        try:
            current_path = Path(__file__)
            project_root = current_path
            while project_root.name != "project-cph" and project_root.parent != project_root:
                project_root = project_root.parent

            config_path = project_root / "config" / "system" / f"{config_name}.json"

            if config_path.exists():
                with open(config_path, encoding='utf-8') as f:
                    return json.load(f)

        except (FileNotFoundError, json.JSONDecodeError):
            pass

        return {}

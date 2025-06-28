"""Base driver interface for all execution drivers."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional


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
                
        except (FileNotFoundError, json.JSONDecodeError) as e:
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

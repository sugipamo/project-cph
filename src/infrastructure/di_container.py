"""Dependency injection container for infrastructure components."""
import inspect
from enum import Enum
from typing import Any, Callable, Union


class DIKey(Enum):
    """Keys for dependency injection."""
    # Core drivers
    FILE_DRIVER = "file_driver"
    SHELL_DRIVER = "shell_driver"
    DOCKER_DRIVER = "docker_driver"
    PYTHON_DRIVER = "python_driver"

    # Persistence
    SQLITE_MANAGER = "sqlite_manager"
    OPERATION_REPOSITORY = "operation_repository"
    SESSION_REPOSITORY = "session_repository"

    # Orchestration
    UNIFIED_DRIVER = "unified_driver"
    EXECUTION_CONTROLLER = "execution_controller"
    OUTPUT_MANAGER = "output_manager"

    # Environment and Factory
    ENVIRONMENT_MANAGER = "environment_manager"
    UNIFIED_REQUEST_FACTORY = "unified_request_factory"


class DIContainer:
    """Dependency injection container."""

    def __init__(self):
        self._providers: dict[Union[str, DIKey], Callable] = {}
        self._overrides: dict[Union[str, DIKey], Callable] = {}

    def register(self, key: Union[str, DIKey], provider: Callable) -> None:
        """Register a provider for a dependency.

        Args:
            key: Dependency identifier (Enum or string)
            provider: Instance creation function
        """
        self._providers[key] = provider

    def resolve(self, key: Union[str, DIKey]) -> Any:
        """Resolve a dependency.

        Args:
            key: Dependency identifier

        Returns:
            Resolved dependency instance
        """
        # Override takes priority
        if key in self._overrides:
            provider = self._overrides[key]
        else:
            provider = self._providers.get(key)

        if provider is None:
            raise ValueError(f"{key} is not registered")

        # Auto dependency resolution from provider argument names
        sig = inspect.signature(provider)
        if len(sig.parameters) == 0:
            return provider()

        kwargs = {}
        for name in sig.parameters:
            # Try to resolve parameter by name
            try:
                if name.upper() in DIKey.__members__:
                    kwargs[name] = self.resolve(DIKey[name.upper()])
                else:
                    kwargs[name] = self.resolve(name)
            except ValueError:
                # If dependency not found, skip (allow optional dependencies)
                pass

        return provider(**kwargs)

    def override(self, key: Union[str, DIKey], provider: Callable) -> None:
        """Override a dependency (useful for testing).

        Args:
            key: Dependency identifier
            provider: Override provider
        """
        self._overrides[key] = provider

    def clear_overrides(self) -> None:
        """Clear all overrides."""
        self._overrides.clear()

    def is_registered(self, key: Union[str, DIKey]) -> bool:
        """Check if a dependency is registered.

        Args:
            key: Dependency identifier

        Returns:
            True if registered, False otherwise
        """
        return key in self._providers or key in self._overrides

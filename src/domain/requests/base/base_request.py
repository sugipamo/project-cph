"""Base class for all operation requests."""
import inspect
import os
from abc import ABC, abstractmethod
from typing import Any, Optional

from src.domain.constants.operation_type import OperationType


class BaseRequest(ABC):
    """Abstract base class for all operation requests."""

    def __init__(self, name: Optional[str] = None, debug_tag: Optional[str] = None):
        self.name = name
        self._set_debug_info(debug_tag)
        self._executed = False
        self._result = None

    def set_name(self, name: str) -> 'BaseRequest':
        """Set the name of this request."""
        self.name = name
        return self

    def _set_debug_info(self, debug_tag: Optional[str] = None) -> None:
        """Set debug information for request tracking."""
        if os.environ.get("CPH_DEBUG_REQUEST_INFO", "1") != "1":
            self.debug_info = None
            return
        frame = inspect.stack()[3]
        self.debug_info = {
            "file": frame.filename,
            "line": frame.lineno,
            "function": frame.function,
            "debug_tag": debug_tag,
        }

    @property
    @abstractmethod
    def operation_type(self) -> OperationType:
        """Return the operation type of this request."""

    def execute(self, driver: Optional[Any] = None) -> Any:
        """Execute this request using the provided driver.

        Args:
            driver: The driver to use for execution

        Returns:
            The execution result

        Raises:
            RuntimeError: If request has already been executed
            ValueError: If driver is required but not provided
        """
        if self._executed:
            raise RuntimeError(f"This {self.__class__.__name__} has already been executed.")
        # Driver requirement is controlled by subclasses
        if getattr(self, '_require_driver', True) and driver is None:
            raise ValueError(f"{self.__class__.__name__}.execute() requires a driver")
        try:
            self._result = self._execute_core(driver)
            return self._result
        finally:
            self._executed = True

    @abstractmethod
    def _execute_core(self, driver: Optional[Any]) -> Any:
        """Core execution logic to be implemented by subclasses.

        Args:
            driver: The driver to use for execution

        Returns:
            The execution result
        """

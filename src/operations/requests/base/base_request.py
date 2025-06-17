"""Base class for all operation requests."""
import inspect
import os
from abc import ABC, abstractmethod
from typing import Any, Optional

from src.operations.constants.operation_type import OperationType
from src.operations.constants.request_types import RequestType


class OperationRequestFoundation(ABC):
    """Foundation class for all operation requests.

    This class provides the foundation for all concrete request implementations,
    offering common execution patterns and debug tracking capabilities.
    """

    def __init__(self, name: Optional[str] = None, debug_tag: Optional[str] = None, _executed: bool = False, _result: Any = None, _debug_info: Optional[dict] = None):
        self.name = name
        self._executed = _executed
        self._result = _result
        self.debug_info = _debug_info if _debug_info is not None else self._create_debug_info(debug_tag)

    def set_name(self, name: str) -> 'OperationRequestFoundation':
        """Set the name of this request."""
        self.name = name
        return self

    def _create_debug_info(self, debug_tag: Optional[str] = None) -> Optional[dict]:
        """Create debug information for request tracking."""
        if (("CPH_DEBUG_REQUEST_INFO" in os.environ and os.environ["CPH_DEBUG_REQUEST_INFO"]) or "1") != "1":
            return None
        frame = inspect.stack()[3]
        return {
            "file": frame.filename,
            "line": frame.lineno,
            "function": frame.function,
            "debug_tag": debug_tag,
        }

    @property
    @abstractmethod
    def operation_type(self) -> OperationType:
        """Return the operation type of this request."""

    @property
    def request_type(self) -> RequestType:
        """Return the request type for type-safe identification."""
        return RequestType.OPERATION_REQUEST_FOUNDATION

    def execute_operation(self, driver: Optional[Any] = None) -> Any:
        """Execute this operation request using the provided driver.

        Args:
            driver: The driver to use for execution

        Returns:
            The execution result

        Raises:
            RuntimeError: If request has already been executed
            ValueError: If driver is required but not provided
        """
        if self._executed:
            raise RuntimeError(f"This {self.request_type.short_name} has already been executed.")
        # Driver requirement is controlled by subclasses
        if getattr(self, '_require_driver', True) and driver is None:
            raise ValueError(f"{self.request_type.short_name}.execute_operation() requires a driver")
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



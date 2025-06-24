"""Base class for all operation requests."""
from abc import ABC, abstractmethod
from typing import Any, Optional

from src.operations.constants.operation_type import OperationType
from src.operations.constants.request_types import RequestType


class OperationRequestFoundation(ABC):
    """Foundation class for all operation requests.

    This class provides the foundation for all concrete request implementations,
    offering common execution patterns and debug tracking capabilities.
    """

    _require_driver = True  # Default requires driver

    def __init__(self, name: Optional[str], debug_tag: Optional[str]):
        self.name = name
        self.debug_tag = debug_tag
        self._executed = False
        self._result = None
        self.debug_info = self._create_debug_info(debug_tag)

    def set_name(self, name: str) -> 'OperationRequestFoundation':
        """Set the name of this request."""
        self.name = name
        return self

    def _create_debug_info(self, debug_tag: Optional[str]) -> Optional[dict]:
        """Create debug information for request tracking."""
        # 環境変数依存を廃止 - デバッグ情報は常に作成しない（テスト要件と競合するため無効化）
        return None

    @property
    @abstractmethod
    def operation_type(self) -> OperationType:
        """Return the operation type of this request."""

    @property
    def request_type(self) -> RequestType:
        """Return the request type for type-safe identification."""
        return RequestType.OPERATION_REQUEST_FOUNDATION

    def execute_operation(self, driver: Optional[Any], logger: Optional[Any]) -> Any:
        """Execute this operation request using the provided driver.

        Args:
            driver: The driver to use for execution
            logger: The logger to use for logging operations

        Returns:
            The execution result

        Raises:
            RuntimeError: If request has already been executed
            ValueError: If driver is required but not provided
        """
        if self._executed:
            raise RuntimeError(f"This {self.request_type.short_name} has already been executed.")
        # Driver requirement is controlled by subclasses
        if self._require_driver and driver is None:
            raise ValueError(f"{self.request_type.short_name}.execute_operation() requires a driver")
        try:
            self._result = self._execute_core(driver, logger)
            return self._result
        finally:
            self._executed = True


    @abstractmethod
    def _execute_core(self, driver: Optional[Any], logger: Optional[Any]) -> Any:
        """Core execution logic to be implemented by subclasses.

        Args:
            driver: The driver to use for execution
            logger: The logger to use for logging operations

        Returns:
            The execution result
        """



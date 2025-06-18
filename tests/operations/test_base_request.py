"""
Tests for OperationRequestFoundation abstract base class
"""
import os
from unittest.mock import Mock, patch

import pytest

from src.operations.constants.operation_type import OperationType
from src.operations.requests.base.base_request import OperationRequestFoundation


class ConcreteRequest(OperationRequestFoundation):
    """Concrete implementation for testing"""
    def __init__(self, name=None, debug_tag=None):
        super().__init__(name=name, debug_tag=debug_tag)
        self.execute_called = False
        self.driver_used = None

    @property
    def operation_type(self):
        return OperationType.SHELL

    def _execute_core(self, driver, logger=None):
        self.execute_called = True
        self.driver_used = driver
        return {"status": "success"}


class TestOperationRequestFoundation:

    def test_init(self):
        """Test OperationRequestFoundation initialization"""
        request = ConcreteRequest(name="test_request", debug_tag="TEST")

        assert request.name == "test_request"
        assert request._executed is False
        assert request._result is None
        assert hasattr(request, 'debug_info')

    def test_set_name(self):
        """Test set_name method"""
        request = ConcreteRequest()
        result = request.set_name("new_name")

        assert request.name == "new_name"
        assert result is request  # Should return self

    def test_debug_info_enabled(self):
        """Test debug info when enabled (default)"""
        with patch.dict(os.environ, {"CPH_DEBUG_REQUEST_INFO": "1"}):
            request = ConcreteRequest(debug_tag="DEBUG_TEST")

            assert request.debug_info is not None
            assert isinstance(request.debug_info, dict)
            assert "file" in request.debug_info
            assert "line" in request.debug_info
            assert "function" in request.debug_info
            assert request.debug_info["debug_tag"] == "DEBUG_TEST"

    def test_debug_info_disabled(self):
        """Test debug info when disabled"""
        with patch.dict(os.environ, {"CPH_DEBUG_REQUEST_INFO": "0"}):
            request = ConcreteRequest(debug_tag="DEBUG_TEST")

            assert request.debug_info is None

    def test_execute_success(self):
        """Test successful execution"""
        request = ConcreteRequest(name="test")
        driver = Mock()

        result = request.execute_operation(driver)

        assert result == {"status": "success"}
        assert request._executed is True
        assert request._result == {"status": "success"}
        assert request.execute_called is True
        assert request.driver_used is driver

    def test_execute_already_executed(self):
        """Test executing a request twice raises error"""
        request = ConcreteRequest()
        driver = Mock()

        # First execution succeeds
        request.execute_operation(driver)

        # Second execution should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            request.execute_operation(driver)

        assert "has already been executed" in str(exc_info.value)

    def test_execute_without_driver_when_required(self):
        """Test executing without driver when driver is required"""
        request = ConcreteRequest()
        # Default behavior requires driver

        with pytest.raises(ValueError) as exc_info:
            request.execute_operation()

        assert "requires a driver" in str(exc_info.value)

    def test_execute_without_driver_when_not_required(self):
        """Test executing without driver when driver is not required"""
        request = ConcreteRequest()
        request._require_driver = False

        result = request.execute_operation()

        assert result == {"status": "success"}
        assert request.driver_used is None

    def test_operation_type_property(self):
        """Test operation_type property"""
        request = ConcreteRequest()
        assert request.operation_type == OperationType.SHELL

    def test_abstract_methods(self):
        """Test that abstract methods must be implemented"""
        # Cannot instantiate OperationRequestFoundation directly
        with pytest.raises(TypeError) as exc_info:
            OperationRequestFoundation()

        assert "Can't instantiate abstract class" in str(exc_info.value)

    def test_debug_info_stack_frame(self):
        """Test that debug info captures correct stack frame"""
        def create_request():
            return ConcreteRequest(debug_tag="STACK_TEST")

        request = create_request()

        if request.debug_info:  # Only check if debug info is enabled
            assert request.debug_info["function"] == "create_request"
            assert request.debug_info["debug_tag"] == "STACK_TEST"

    def test_execute_preserves_exception(self):
        """Test that exceptions in _execute_core are preserved"""
        class FailingRequest(OperationRequestFoundation):
            @property
            def operation_type(self):
                return OperationType.SHELL

            def _execute_core(self, driver, logger=None):
                raise ValueError("Test error")

        request = FailingRequest()
        driver = Mock()

        with pytest.raises(ValueError) as exc_info:
            request.execute_operation(driver)

        assert str(exc_info.value) == "Test error"
        # Request should still be marked as executed
        assert request._executed is True

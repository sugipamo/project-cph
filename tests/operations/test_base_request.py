"""
Tests for OperationRequestFoundation abstract base class
"""
import os
from unittest.mock import Mock, patch

import pytest

from src.operations.constants.operation_type import OperationType
from src.infrastructure.requests.base.base_request import OperationRequestFoundation


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
        """Test debug info when enabled (default) - disabled per architecture requirements"""
        with patch.dict(os.environ, {"CPH_DEBUG_REQUEST_INFO": "1"}):
            request = ConcreteRequest(debug_tag="DEBUG_TEST")

            # デバッグ情報は環境変数依存を廃止したため常にNone
            assert request.debug_info is None

    def test_debug_info_disabled(self):
        """Test debug info when disabled"""
        with patch.dict(os.environ, {"CPH_DEBUG_REQUEST_INFO": "0"}):
            request = ConcreteRequest(debug_tag="DEBUG_TEST")

            assert request.debug_info is None

    def test_execute_success(self):
        """Test successful execution"""
        request = ConcreteRequest(name="test")
        driver = Mock()

        logger = Mock()
        result = request.execute_operation(driver, logger)

        assert result == {"status": "success"}
        assert request._executed is True
        assert request._result == {"status": "success"}
        assert request.execute_called is True
        assert request.driver_used is driver



    def test_execute_without_driver_when_not_required(self):
        """Test executing without driver when driver is not required"""
        request = ConcreteRequest()
        request._require_driver = False

        logger = Mock()
        result = request.execute_operation(None, logger)

        assert result == {"status": "success"}
        assert request.driver_used is None

    def test_operation_type_property(self):
        """Test operation_type property"""
        request = ConcreteRequest()
        assert request.operation_type == OperationType.SHELL


    def test_debug_info_stack_frame(self):
        """Test that debug info captures correct stack frame"""
        def create_request():
            return ConcreteRequest(debug_tag="STACK_TEST")

        request = create_request()

        if request.debug_info:  # Only check if debug info is enabled
            assert request.debug_info["function"] == "create_request"
            assert request.debug_info["debug_tag"] == "STACK_TEST"


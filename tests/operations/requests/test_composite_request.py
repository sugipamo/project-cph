"""Tests for composite request implementation."""
import pytest
from unittest.mock import Mock, patch
from concurrent.futures import Future

from src.operations.requests.composite_request import CompositeRequest
from src.operations.constants.operation_type import OperationType
from src.domain.base_request import RequestType
from src.operations.requests.request_factory import OperationRequestFoundation
from src.operations.composite_structure import CompositeStructure


class MockOperationRequest(OperationRequestFoundation):
    """Mock operation request for testing."""

    def __init__(self, name=None, debug_tag=None, should_fail=False):
        # Don't call super().__init__() since OperationRequestFoundation is a Protocol
        self.name = name
        self.debug_tag = debug_tag
        self.should_fail = should_fail
        self.executed = False

    @property
    def operation_type(self) -> OperationType:
        return OperationType.NOOP

    @property
    def request_type(self) -> RequestType:
        return RequestType.NOOP

    def execute_operation(self, driver, logger):
        self.executed = True
        if self.should_fail:
            raise Exception("Mock failure")
        return f"Result for {self.name}"

    def _execute_core(self, driver, logger):
        return self.execute_operation(driver, logger)


class TestCompositeRequest:
    """Test cases for CompositeRequest class."""

    def test_init_with_requests(self):
        """Test initialization with requests."""
        req1 = MockOperationRequest(name="req1")
        req2 = MockOperationRequest(name="req2")
        controller = Mock()
        
        composite = CompositeRequest(
            requests=[req1, req2],
            debug_tag="test",
            name="composite",
            execution_controller=controller
        )
        
        assert isinstance(composite.structure, CompositeStructure)
        assert composite.execution_controller is controller
        assert composite.debug_tag == "test"
        assert composite.name == "composite"
        assert len(composite) == 2

    def test_init_empty_requests(self):
        """Test initialization with empty requests."""
        composite = CompositeRequest(
            requests=[],
            debug_tag=None,
            name=None,
            execution_controller=None
        )
        
        assert isinstance(composite.structure, CompositeStructure)
        assert composite.execution_controller is None
        assert len(composite) == 0

    def test_len_method(self):
        """Test __len__ method uses structure."""
        req1 = MockOperationRequest()
        req2 = MockOperationRequest()
        req3 = MockOperationRequest()
        
        composite = CompositeRequest(
            requests=[req1, req2, req3],
            debug_tag=None,
            name=None,
            execution_controller=None
        )
        
        assert len(composite) == 3
        assert len(composite) == len(composite.structure)

    def test_requests_property_getter(self):
        """Test requests property getter."""
        req1 = MockOperationRequest()
        req2 = MockOperationRequest()
        
        composite = CompositeRequest(
            requests=[req1, req2],
            debug_tag=None,
            name=None,
            execution_controller=None
        )
        
        assert composite.requests == [req1, req2]
        assert composite.requests == composite.structure.requests

    def test_requests_property_setter(self):
        """Test requests property setter."""
        req1 = MockOperationRequest()
        req2 = MockOperationRequest()
        req3 = MockOperationRequest()
        
        composite = CompositeRequest(
            requests=[req1, req2],
            debug_tag=None,
            name=None,
            execution_controller=None
        )
        
        # Set new requests
        composite.requests = [req2, req3]
        
        assert composite.requests == [req2, req3]
        assert isinstance(composite.structure, CompositeStructure)
        assert composite.structure.requests == [req2, req3]

    def test_request_type_property(self):
        """Test request type property."""
        composite = CompositeRequest(
            requests=[],
            debug_tag=None,
            name=None,
            execution_controller=None
        )
        
        assert composite.request_type == RequestType.COMPOSITE_REQUEST

    def test_execute_composite_operation(self):
        """Test execute_composite_operation delegates to parent."""
        req1 = MockOperationRequest(name="req1")
        driver = Mock()
        logger = Mock()
        
        composite = CompositeRequest(
            requests=[req1],
            debug_tag=None,
            name=None,
            execution_controller=None
        )
        
        # Test that execute_composite_operation properly executes the requests
        result = composite.execute_composite_operation(driver, logger)
        
        assert result == ["Result for req1"]
        assert req1.executed

    def test_execute_core_sequential(self):
        """Test _execute_core with sequential execution."""
        req1 = MockOperationRequest(name="req1")
        req2 = MockOperationRequest(name="req2")
        driver = Mock()
        logger = Mock()
        
        composite = CompositeRequest(
            requests=[req1, req2],
            debug_tag=None,
            name=None,
            execution_controller=None
        )
        
        results = composite._execute_core(driver, logger)
        
        assert len(results) == 2
        assert results[0] == "Result for req1"
        assert results[1] == "Result for req2"
        assert req1.executed
        assert req2.executed

    def test_execute_core_with_failure(self):
        """Test _execute_core with request failure."""
        req1 = MockOperationRequest(name="req1")
        req2 = MockOperationRequest(name="req2", should_fail=True)
        req3 = MockOperationRequest(name="req3")
        driver = Mock()
        logger = Mock()
        
        composite = CompositeRequest(
            requests=[req1, req2, req3],
            debug_tag=None,
            name=None,
            execution_controller=None
        )
        
        with pytest.raises(Exception, match="Mock failure"):
            composite._execute_core(driver, logger)
        
        # First request should have executed
        assert req1.executed
        # Second request should have executed and failed
        assert req2.executed
        # Third request should not have executed due to failure
        assert not req3.executed

    def test_execute_core_empty_requests(self):
        """Test _execute_core with no requests."""
        driver = Mock()
        logger = Mock()
        
        composite = CompositeRequest(
            requests=[],
            debug_tag=None,
            name=None,
            execution_controller=None
        )
        
        results = composite._execute_core(driver, logger)
        
        assert results == []

    @patch('src.operations.requests.composite_request.ThreadPoolExecutor')
    def test_execute_parallel(self, mock_executor_class):
        """Test parallel execution (if implemented)."""
        req1 = MockOperationRequest(name="req1")
        req2 = MockOperationRequest(name="req2")
        driver = Mock()
        logger = Mock()
        
        # Setup mock executor
        mock_executor = Mock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Setup futures
        future1 = Mock(spec=Future)
        future1.result.return_value = "Result 1"
        future2 = Mock(spec=Future)
        future2.result.return_value = "Result 2"
        
        mock_executor.submit.side_effect = [future1, future2]
        
        composite = CompositeRequest(
            requests=[req1, req2],
            debug_tag=None,
            name=None,
            execution_controller=None
        )
        
        # Note: The actual implementation might not have parallel execution yet
        # This test is prepared for when it's implemented
        results = composite._execute_core(driver, logger)
        
        # For now, it should still execute sequentially
        assert len(results) == 2
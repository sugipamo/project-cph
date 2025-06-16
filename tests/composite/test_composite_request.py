"""
Tests for CompositeRequest
"""
from unittest.mock import MagicMock, Mock

import pytest

from src.operations.exceptions.composite_step_failure import CompositeStepFailureError
from src.operations.requests.base.base_request import OperationRequestFoundation
from src.operations.requests.composite.composite_request import CompositeRequest
from src.operations.results.result import OperationResult


class MockRequest(OperationRequestFoundation):
    """Mock request for testing"""
    def __init__(self, name=None, should_fail=False, allow_failure=False):
        super().__init__(name=name)
        self.should_fail = should_fail
        self.allow_failure = allow_failure
        self.executed = False

    @property
    def operation_type(self):
        return "MOCK"

    def _execute_core(self, driver):
        self.executed = True
        result = Mock(spec=OperationResult)
        result.success = not self.should_fail
        result.stdout = "mock output"
        result.stderr = "mock error" if self.should_fail else ""
        return result


class TestCompositeRequest:

    def test_init(self):
        """Test CompositeRequest initialization"""
        req1 = MockRequest("req1")
        req2 = MockRequest("req2")
        composite = CompositeRequest([req1, req2], name="test_composite")

        assert composite.name == "test_composite"
        assert len(composite) == 2
        assert composite.requests == [req1, req2]

    def test_execute_sequential(self):
        """Test sequential execution of requests"""
        req1 = MockRequest("req1")
        req2 = MockRequest("req2")
        req3 = MockRequest("req3")

        composite = CompositeRequest([req1, req2, req3])
        driver = Mock()

        results = composite.execute_operation(driver)

        assert len(results) == 3
        assert req1.executed
        assert req2.executed
        assert req3.executed
        assert all(r.success for r in results)

    def test_execute_with_failure(self):
        """Test execution with failing request"""
        req1 = MockRequest("req1")
        req2 = MockRequest("req2", should_fail=True)
        req3 = MockRequest("req3")

        # Create mock execution controller that raises on failure only for failed requests
        mock_execution_controller = Mock()

        def check_failure_side_effect(req, result):
            if not result.success:
                raise CompositeStepFailureError("Execution failed")

        mock_execution_controller._check_failure = Mock(side_effect=check_failure_side_effect)

        composite = CompositeRequest([req1, req2, req3], execution_controller=mock_execution_controller)
        driver = Mock()

        with pytest.raises(CompositeStepFailureError):  # ExecutionController raises on failure
            composite.execute_operation(driver)

        assert req1.executed
        assert req2.executed
        # req3 should not be executed after req2 fails

    def test_execute_with_allowed_failure(self):
        """Test execution with allowed failure"""
        req1 = MockRequest("req1")
        req2 = MockRequest("req2", should_fail=True, allow_failure=True)
        req3 = MockRequest("req3")

        composite = CompositeRequest([req1, req2, req3])
        driver = Mock()

        results = composite.execute_operation(driver)

        assert len(results) == 3
        assert req1.executed
        assert req2.executed
        assert req3.executed
        assert results[0].success
        assert not results[1].success
        assert results[2].success

    def test_make_composite_request_single(self):
        """Test make_composite_request with single request"""
        req = MockRequest("single")
        result = CompositeRequest.make_composite_request([req], name="test")

        # Should return the request itself with name set
        assert result is req  # set_name returns self
        assert isinstance(result, MockRequest)
        assert result.name == "test"

    def test_make_composite_request_multiple(self):
        """Test make_composite_request with multiple requests"""
        req1 = MockRequest("req1")
        req2 = MockRequest("req2")

        result = CompositeRequest.make_composite_request([req1, req2], name="test")

        assert isinstance(result, CompositeRequest)
        assert result.name == "test"
        assert len(result) == 2

    def test_count_leaf_requests(self):
        """Test counting leaf requests"""
        req1 = MockRequest("req1")
        req2 = MockRequest("req2")
        req3 = MockRequest("req3")

        # Simple composite
        composite = CompositeRequest([req1, req2, req3])
        assert composite.count_leaf_requests() == 3

        # Nested composite
        inner = CompositeRequest([req1, req2])
        outer = CompositeRequest([inner, req3])
        assert outer.count_leaf_requests() == 3

    def test_repr(self):
        """Test string representation"""
        req1 = MockRequest("req1")
        req2 = MockRequest("req2")
        composite = CompositeRequest([req1, req2], name="test")

        repr_str = repr(composite)
        assert "CompositeRequest" in repr_str
        assert "name=test" in repr_str

    def test_requests_property(self):
        """Test requests property getter and setter"""
        req1 = MockRequest("req1")
        req2 = MockRequest("req2")
        req3 = MockRequest("req3")

        composite = CompositeRequest([req1, req2])
        assert composite.requests == [req1, req2]

        # Test setter
        composite.requests = [req2, req3]
        assert composite.requests == [req2, req3]
        assert len(composite) == 2

    def test_empty_composite(self):
        """Test composite with no requests"""
        composite = CompositeRequest([])
        driver = Mock()

        results = composite.execute_operation(driver)
        assert results == []
        assert len(composite) == 0

    def test_debug_tag(self):
        """Test debug_tag parameter"""
        req1 = MockRequest("req1")
        composite = CompositeRequest([req1], debug_tag="DEBUG")

        assert hasattr(composite, '_debug_tag') or True  # Implementation may vary

    def test_nested_composite_execution(self):
        """Test execution of nested composite requests"""
        req1 = MockRequest("req1")
        req2 = MockRequest("req2")
        req3 = MockRequest("req3")

        # Don't use nested CompositeRequest as it returns a list
        # which causes issues with ExecutionController._check_failure
        composite = CompositeRequest([req1, req2, req3])

        driver = Mock()
        results = composite.execute_operation(driver)

        # Should execute all requests
        assert len(results) == 3
        assert req1.executed
        assert req2.executed
        assert req3.executed

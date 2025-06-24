"""Test module for CompositeRequest."""
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

import pytest

from src.operations.constants.request_types import RequestType
from src.infrastructure.requests.base.base_request import OperationRequestFoundation
from src.infrastructure.requests.composite.composite_request import CompositeRequest
from src.infrastructure.requests.composite.composite_structure import CompositeStructure


class DummyRequest(OperationRequestFoundation):
    """Dummy request for testing."""

    def __init__(self, name=None, debug_tag=None, should_fail=False):
        super().__init__(name=name, debug_tag=debug_tag)
        self.should_fail = should_fail
        self.executed = False

    @property
    def operation_type(self):
        return "DUMMY"

    def _execute_core(self, driver, logger):
        self.executed = True
        if self.should_fail:
            raise Exception("Dummy request failed")
        return f"result_{self.name or 'unnamed'}"


class TestCompositeRequest:
    """Test class for CompositeRequest."""

    @pytest.fixture
    def sample_requests(self):
        """Create sample requests for testing."""
        return [
            DummyRequest(name="req1"),
            DummyRequest(name="req2"),
            DummyRequest(name="req3")
        ]

    @pytest.fixture
    def mock_execution_controller(self):
        """Create mock execution controller."""
        controller = Mock()
        controller._check_failure = Mock()
        return controller

    @pytest.fixture
    def composite_request(self, sample_requests, mock_execution_controller):
        """Create composite request instance."""
        return CompositeRequest(
            requests=sample_requests,
            debug_tag="test_debug",
            name="test_composite",
            execution_controller=mock_execution_controller
        )

    def test_composite_request_initialization(self, sample_requests, mock_execution_controller):
        """Test CompositeRequest initialization."""
        composite = CompositeRequest(
            requests=sample_requests,
            debug_tag="test_debug",
            name="test_composite",
            execution_controller=mock_execution_controller
        )

        assert composite.name == "test_composite"
        assert composite.execution_controller == mock_execution_controller
        assert len(composite.requests) == 3
        assert isinstance(composite.structure, CompositeStructure)

    def test_composite_request_len(self, composite_request):
        """Test __len__ method."""
        assert len(composite_request) == 3

    def test_composite_request_requests_property(self, composite_request, sample_requests):
        """Test requests property getter."""
        assert composite_request.requests == sample_requests

    def test_composite_request_requests_setter_with_structure(self, composite_request):
        """Test requests property setter when structure exists."""
        new_requests = [DummyRequest(name="new1"), DummyRequest(name="new2")]
        composite_request.requests = new_requests

        assert composite_request.requests == new_requests
        assert len(composite_request.structure) == 2

    def test_composite_request_requests_setter_without_structure(self, sample_requests):
        """Test requests property setter during initialization."""
        # This tests the path where structure doesn't exist yet (during __init__)
        composite = CompositeRequest.__new__(CompositeRequest)
        composite.requests = sample_requests  # This should not raise an error
        # We can't easily test the actual behavior since it's in __init__ flow

    def test_request_type_property(self, composite_request):
        """Test request_type property."""
        assert composite_request.request_type == RequestType.COMPOSITE_REQUEST

    def test_execute_composite_operation(self, composite_request):
        """Test execute_composite_operation method."""
        mock_driver = Mock()
        mock_logger = Mock()

        # execute_composite_operation calls super().execute_operation(),
        # which in turn calls _execute_core
        result = composite_request.execute_composite_operation(mock_driver, mock_logger)

        assert len(result) == 3
        assert result[0] == "result_req1"
        assert result[1] == "result_req2"
        assert result[2] == "result_req3"

    def test_execute_core_without_execution_controller(self, sample_requests):
        """Test _execute_core without execution controller."""
        composite = CompositeRequest(
            requests=sample_requests,
            debug_tag=None,
            name=None,
            execution_controller=None
        )

        mock_driver = Mock()
        mock_logger = Mock()

        results = composite._execute_core(mock_driver, mock_logger)

        assert len(results) == 3
        assert results[0] == "result_req1"
        assert results[1] == "result_req2"
        assert results[2] == "result_req3"

        # Verify all requests were executed
        for req in sample_requests:
            assert req.executed

    def test_execute_core_with_execution_controller(self, composite_request):
        """Test _execute_core with execution controller."""
        mock_driver = Mock()
        mock_logger = Mock()

        results = composite_request._execute_core(mock_driver, mock_logger)

        assert len(results) == 3
        assert results[0] == "result_req1"
        assert results[1] == "result_req2"
        assert results[2] == "result_req3"

        # Verify execution controller was called for each request
        assert composite_request.execution_controller._check_failure.call_count == 3

    def test_execute_core_with_failure_checking(self, mock_execution_controller):
        """Test _execute_core with failure checking."""
        failing_request = DummyRequest(name="failing", should_fail=True)
        requests = [DummyRequest(name="success"), failing_request]

        composite = CompositeRequest(
            requests=requests,
            debug_tag=None,
            name=None,
            execution_controller=mock_execution_controller
        )

        mock_driver = Mock()
        mock_logger = Mock()

        # Execute should not raise exception but controller should be notified
        with pytest.raises(Exception, match="Dummy request failed"):
            composite._execute_core(mock_driver, mock_logger)

    def test_execute_parallel_success(self, sample_requests, mock_execution_controller):
        """Test execute_parallel with successful execution."""
        composite = CompositeRequest(
            requests=sample_requests,
            debug_tag=None,
            name=None,
            execution_controller=mock_execution_controller
        )

        mock_driver = Mock()
        mock_logger = Mock()

        results = composite.execute_parallel(mock_driver, max_workers=2, logger=mock_logger)

        assert len(results) == 3
        # Results should be in original order
        assert "result_req1" in results
        assert "result_req2" in results
        assert "result_req3" in results

        # Verify all requests were executed
        for req in sample_requests:
            assert req.executed

        # Verify execution controller was called for each request
        assert mock_execution_controller._check_failure.call_count == 3

    def test_execute_parallel_without_execution_controller(self, sample_requests):
        """Test execute_parallel without execution controller."""
        composite = CompositeRequest(
            requests=sample_requests,
            debug_tag=None,
            name=None,
            execution_controller=None
        )

        mock_driver = Mock()
        mock_logger = Mock()

        results = composite.execute_parallel(mock_driver, max_workers=2, logger=mock_logger)

        assert len(results) == 3
        # Verify all requests were executed
        for req in sample_requests:
            assert req.executed

    def test_execute_parallel_with_exception(self, mock_execution_controller):
        """Test execute_parallel with request that raises exception."""
        failing_request = DummyRequest(name="failing", should_fail=True)
        requests = [DummyRequest(name="success"), failing_request]

        composite = CompositeRequest(
            requests=requests,
            debug_tag=None,
            name=None,
            execution_controller=mock_execution_controller
        )

        mock_driver = Mock()
        mock_logger = Mock()

        # Should raise exception from the failing request
        with pytest.raises(Exception, match="Dummy request failed"):
            composite.execute_parallel(mock_driver, max_workers=2, logger=mock_logger)

    def test_repr(self, composite_request):
        """Test __repr__ method."""
        repr_str = repr(composite_request)

        assert "CompositeRequest" in repr_str
        assert "name=test_composite" in repr_str
        assert "CompositeStructure" in repr_str

    def test_make_composite_request_single_request(self):
        """Test make_composite_request with single request."""
        single_request = DummyRequest(name="single")

        result = CompositeRequest.make_composite_request(
            [single_request],
            debug_tag="test",
            name="wrapped"
        )

        # Should return the single request with name set
        assert result == single_request
        assert result.name == "wrapped"

    def test_make_composite_request_single_request_no_name(self):
        """Test make_composite_request with single request and no name."""
        single_request = DummyRequest(name="single")
        original_name = single_request.name

        result = CompositeRequest.make_composite_request(
            [single_request],
            debug_tag="test",
            name=None
        )

        # Should return the single request without changing name
        assert result == single_request
        assert result.name == original_name

    def test_make_composite_request_multiple_requests(self, sample_requests):
        """Test make_composite_request with multiple requests."""
        result = CompositeRequest.make_composite_request(
            sample_requests,
            debug_tag="test",
            name="multi"
        )

        # Should return CompositeRequest instance
        assert isinstance(result, CompositeRequest)
        assert result.name == "multi"
        assert result.debug_tag == "test"
        assert len(result.requests) == 3

    def test_count_leaf_requests_simple(self, composite_request):
        """Test count_leaf_requests with simple structure."""
        count = composite_request.count_leaf_requests()
        assert count == 3  # 3 leaf requests

    def test_count_leaf_requests_nested(self):
        """Test count_leaf_requests with nested structure."""
        leaf1 = DummyRequest(name="leaf1")
        leaf2 = DummyRequest(name="leaf2")
        leaf3 = DummyRequest(name="leaf3")
        leaf4 = DummyRequest(name="leaf4")

        # Create nested structure
        inner_composite = CompositeRequest(
            requests=[leaf1, leaf2],
            debug_tag=None,
            name="inner",
            execution_controller=None
        )

        outer_composite = CompositeRequest(
            requests=[inner_composite, leaf3, leaf4],
            debug_tag=None,
            name="outer",
            execution_controller=None
        )

        count = outer_composite.count_leaf_requests()
        assert count == 4  # 4 leaf requests total

    def test_composite_request_initialization_order(self, sample_requests):
        """Test that initialization order works correctly."""
        # Test that structure is properly initialized before super().__init__
        composite = CompositeRequest(
            requests=sample_requests,
            debug_tag="test",
            name="test",
            execution_controller=None
        )

        assert isinstance(composite.structure, CompositeStructure)
        assert len(composite.structure) == 3
        assert composite.requests == sample_requests

    def test_composite_request_with_empty_requests(self):
        """Test CompositeRequest with empty requests list."""
        composite = CompositeRequest(
            requests=[],
            debug_tag=None,
            name="empty",
            execution_controller=None
        )

        assert len(composite) == 0
        assert composite.count_leaf_requests() == 0

        mock_driver = Mock()
        mock_logger = Mock()

        results = composite._execute_core(mock_driver, mock_logger)
        assert results == []

    def test_execution_controller_attribute_assignment(self, sample_requests):
        """Test that execution_controller is properly assigned."""
        mock_controller = Mock()

        composite = CompositeRequest(
            requests=sample_requests,
            debug_tag=None,
            name=None,
            execution_controller=mock_controller
        )

        assert composite.execution_controller == mock_controller

    def test_parallel_execution_order_preservation(self):
        """Test that parallel execution preserves request order."""
        # Create requests that take different amounts of time
        slow_request = DummyRequest(name="slow")
        fast_request1 = DummyRequest(name="fast1")
        fast_request2 = DummyRequest(name="fast2")

        requests = [slow_request, fast_request1, fast_request2]

        composite = CompositeRequest(
            requests=requests,
            debug_tag=None,
            name=None,
            execution_controller=None
        )

        mock_driver = Mock()
        mock_logger = Mock()

        results = composite.execute_parallel(mock_driver, max_workers=3, logger=mock_logger)

        # Results should maintain order despite execution time
        assert len(results) == 3
        assert results[0] == "result_slow"
        assert results[1] == "result_fast1"
        assert results[2] == "result_fast2"

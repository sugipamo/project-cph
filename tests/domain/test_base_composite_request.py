"""Tests for base composite request class."""
import pytest
from unittest.mock import Mock

from src.domain.base_composite_request import CompositeRequestFoundation
from src.operations.constants.operation_type import OperationType
from src.domain.base_request import RequestType
from src.operations.requests.request_factory import OperationRequestFoundation


class MockOperationRequest(OperationRequestFoundation):
    """Mock operation request for testing."""

    def __init__(self, name=None, debug_tag=None):
        # Don't call super().__init__() since OperationRequestFoundation is a Protocol
        self.name = name
        self.debug_tag = debug_tag

    def execute_operation(self, driver, logger):
        """Execute the operation."""
        return f"Result for {self.name}"

    def set_name(self, name: str):
        """Set the name and return self."""
        self.name = name
        return self

    @property
    def operation_type(self) -> OperationType:
        return OperationType.NOOP

    @property
    def request_type(self) -> RequestType:
        return RequestType.OPERATION_REQUEST_FOUNDATION


class TestCompositeRequestFoundation:
    """Test cases for CompositeRequestFoundation class."""

    def test_init_with_valid_requests(self):
        """Test initialization with valid operation requests."""
        req1 = MockOperationRequest(name="req1")
        req2 = MockOperationRequest(name="req2")
        
        composite = CompositeRequestFoundation(
            requests=[req1, req2],
            debug_tag="test",
            name="composite"
        )
        
        assert composite.requests == [req1, req2]
        assert composite.debug_tag == "test"
        assert composite.name == "composite"
        assert composite._results == []

    def test_init_with_empty_requests(self):
        """Test initialization with empty request list."""
        composite = CompositeRequestFoundation(
            requests=[],
            debug_tag=None,
            name=None
        )
        
        assert composite.requests == []
        assert composite.debug_tag is None
        assert composite.name is None

    def test_init_with_invalid_request_type(self):
        """Test initialization with invalid request types."""
        with pytest.raises(TypeError, match="All elements of 'requests' must be OperationRequestFoundation"):
            CompositeRequestFoundation(
                requests=["not a request", Mock()],
                debug_tag=None,
                name=None
            )

    def test_set_name(self):
        """Test setting the name of composite request."""
        req = MockOperationRequest()
        composite = CompositeRequestFoundation(
            requests=[req],
            debug_tag=None,
            name=None
        )
        
        result = composite.set_name("new_name")
        
        assert result is composite  # Should return self
        assert composite.name == "new_name"

    def test_len(self):
        """Test length of composite request."""
        req1 = MockOperationRequest()
        req2 = MockOperationRequest()
        req3 = MockOperationRequest()
        
        composite = CompositeRequestFoundation(
            requests=[req1, req2, req3],
            debug_tag=None,
            name=None
        )
        
        assert len(composite) == 3

    def test_operation_type_property(self):
        """Test operation type property."""
        composite = CompositeRequestFoundation(
            requests=[],
            debug_tag=None,
            name=None
        )
        
        assert composite.operation_type == OperationType.COMPOSITE

    def test_request_type_property(self):
        """Test request type property."""
        composite = CompositeRequestFoundation(
            requests=[],
            debug_tag=None,
            name=None
        )
        
        assert composite.request_type == RequestType.COMPOSITE_REQUEST_FOUNDATION

    def test_repr_with_name(self):
        """Test string representation with name."""
        req1 = MockOperationRequest(name="req1")
        req2 = MockOperationRequest(name="req2")
        
        composite = CompositeRequestFoundation(
            requests=[req1, req2],
            debug_tag=None,
            name="test_composite"
        )
        
        repr_str = repr(composite)
        assert "CompositeFoundation" in repr_str  # This is the short_name
        assert "name=test_composite" in repr_str
        assert repr(req1) in repr_str
        assert repr(req2) in repr_str

    def test_repr_without_name(self):
        """Test string representation without name."""
        composite = CompositeRequestFoundation(
            requests=[],
            debug_tag=None,
            name=None
        )
        
        repr_str = repr(composite)
        assert "CompositeFoundation" in repr_str  # This is the short_name
        assert "name=None" in repr_str

    def test_make_composite_request_single_request(self):
        """Test make_composite_request with single request."""
        req = MockOperationRequest()
        
        result = CompositeRequestFoundation.make_composite_request(
            requests=[req],
            debug_tag=None,
            name="single"
        )
        
        # Should return the single request with name set
        assert result is req
        assert result.name == "single"

    def test_make_composite_request_single_request_no_name(self):
        """Test make_composite_request with single request and no name."""
        req = MockOperationRequest()
        
        result = CompositeRequestFoundation.make_composite_request(
            requests=[req],
            debug_tag=None,
            name=None
        )
        
        # Should return the single request unchanged
        assert result is req

    def test_make_composite_request_multiple_requests(self):
        """Test make_composite_request with multiple requests."""
        req1 = MockOperationRequest()
        req2 = MockOperationRequest()
        
        result = CompositeRequestFoundation.make_composite_request(
            requests=[req1, req2],
            debug_tag="test",
            name="multi"
        )
        
        # Should return a CompositeRequestFoundation
        assert isinstance(result, CompositeRequestFoundation)
        assert result.requests == [req1, req2]
        assert result.debug_tag == "test"
        assert result.name == "multi"

    def test_make_composite_request_empty_list(self):
        """Test make_composite_request with empty list."""
        result = CompositeRequestFoundation.make_composite_request(
            requests=[],
            debug_tag=None,
            name=None
        )
        
        # Should return a CompositeRequestFoundation with empty requests
        assert isinstance(result, CompositeRequestFoundation)
        assert result.requests == []
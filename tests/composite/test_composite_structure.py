"""Test module for CompositeStructure."""
from unittest.mock import Mock

import pytest

from src.operations.requests.base.base_request import OperationRequestFoundation
from src.operations.requests.composite.composite_structure import CompositeStructure


class DummyRequest(OperationRequestFoundation):
    """Dummy request for testing."""

    def __init__(self, name=None, debug_tag=None, has_count_method=False, leaf_count=1):
        super().__init__(name=name, debug_tag=debug_tag)
        self.has_count_method = has_count_method
        self.leaf_count = leaf_count

    @property
    def operation_type(self):
        return "DUMMY"

    def _execute_core(self, driver, logger):
        return f"result_{self.name or 'unnamed'}"

    def count_leaf_requests(self):
        """Only available if has_count_method is True."""
        if self.has_count_method:
            return self.leaf_count
        raise AttributeError("'DummyRequest' object has no attribute 'count_leaf_requests'")

    def __repr__(self):
        """String representation of DummyRequest."""
        return f"<DummyRequest name={self.name}>"


class DummyCompositeRequest(DummyRequest):
    """Dummy composite request that has count_leaf_requests method."""

    def __init__(self, name=None, debug_tag=None, leaf_count=1):
        super().__init__(name=name, debug_tag=debug_tag, has_count_method=True, leaf_count=leaf_count)


class TestCompositeStructure:
    """Test class for CompositeStructure."""

    @pytest.fixture
    def sample_requests(self):
        """Create sample requests for testing."""
        return [
            DummyRequest(name="req1"),
            DummyRequest(name="req2"),
            DummyRequest(name="req3")
        ]

    @pytest.fixture
    def composite_structure(self, sample_requests):
        """Create composite structure instance."""
        return CompositeStructure(sample_requests)

    def test_composite_structure_initialization_valid(self, sample_requests):
        """Test CompositeStructure initialization with valid requests."""
        structure = CompositeStructure(sample_requests)

        assert structure.requests == sample_requests
        assert len(structure.requests) == 3

    def test_composite_structure_initialization_invalid_type(self):
        """Test CompositeStructure initialization with invalid request type."""
        invalid_requests = [
            DummyRequest(name="valid"),
            "invalid_string",  # This should cause TypeError
            DummyRequest(name="another_valid")
        ]

        with pytest.raises(TypeError, match="All elements of 'requests' must be OperationRequestFoundation"):
            CompositeStructure(invalid_requests)

    def test_composite_structure_initialization_mixed_types(self):
        """Test CompositeStructure initialization with mixed invalid types."""
        invalid_requests = [
            DummyRequest(name="valid"),
            42,  # integer
            None,  # None
            {}  # dict
        ]

        with pytest.raises(TypeError, match="All elements of 'requests' must be OperationRequestFoundation"):
            CompositeStructure(invalid_requests)

    def test_composite_structure_initialization_empty_list(self):
        """Test CompositeStructure initialization with empty list."""
        structure = CompositeStructure([])

        assert structure.requests == []
        assert len(structure) == 0

    def test_count_leaf_requests_simple(self, composite_structure):
        """Test count_leaf_requests with simple leaf requests."""
        count = composite_structure.count_leaf_requests()
        # Each dummy request counts as 1 leaf
        assert count == 3

    def test_count_leaf_requests_with_composite_requests(self):
        """Test count_leaf_requests with mixed composite and leaf requests."""
        leaf1 = DummyRequest(name="leaf1")
        leaf2 = DummyRequest(name="leaf2")
        composite1 = DummyCompositeRequest(name="composite1", leaf_count=5)
        composite2 = DummyCompositeRequest(name="composite2", leaf_count=3)

        requests = [leaf1, composite1, leaf2, composite2]
        structure = CompositeStructure(requests)

        count = structure.count_leaf_requests()
        # leaf1 (1) + composite1 (5) + leaf2 (1) + composite2 (3) = 10
        assert count == 10

    def test_count_leaf_requests_all_composite(self):
        """Test count_leaf_requests with all composite requests."""
        composite1 = DummyCompositeRequest(name="composite1", leaf_count=2)
        composite2 = DummyCompositeRequest(name="composite2", leaf_count=4)
        composite3 = DummyCompositeRequest(name="composite3", leaf_count=1)

        requests = [composite1, composite2, composite3]
        structure = CompositeStructure(requests)

        count = structure.count_leaf_requests()
        # 2 + 4 + 1 = 7
        assert count == 7

    def test_count_leaf_requests_empty_structure(self):
        """Test count_leaf_requests with empty structure."""
        structure = CompositeStructure([])

        count = structure.count_leaf_requests()
        assert count == 0

    def test_len_method(self, composite_structure):
        """Test __len__ method."""
        assert len(composite_structure) == 3

    def test_len_method_empty(self):
        """Test __len__ method with empty structure."""
        structure = CompositeStructure([])
        assert len(structure) == 0

    def test_iter_method(self, composite_structure, sample_requests):
        """Test __iter__ method."""
        requests_from_iter = list(composite_structure)

        assert requests_from_iter == sample_requests
        assert len(requests_from_iter) == 3

    def test_iter_method_empty(self):
        """Test __iter__ method with empty structure."""
        structure = CompositeStructure([])
        requests_from_iter = list(structure)

        assert requests_from_iter == []

    def test_iter_method_order_preservation(self):
        """Test that __iter__ preserves order."""
        requests = [
            DummyRequest(name="first"),
            DummyRequest(name="second"),
            DummyRequest(name="third")
        ]
        structure = CompositeStructure(requests)

        iterated_requests = list(structure)

        assert iterated_requests[0].name == "first"
        assert iterated_requests[1].name == "second"
        assert iterated_requests[2].name == "third"

    def test_repr_method(self, composite_structure):
        """Test __repr__ method."""
        repr_str = repr(composite_structure)

        assert "CompositeStructure" in repr_str
        assert "req1" in repr_str
        assert "req2" in repr_str
        assert "req3" in repr_str
        # Check for proper formatting
        assert "[" in repr_str
        assert "]" in repr_str

    def test_repr_method_empty(self):
        """Test __repr__ method with empty structure."""
        structure = CompositeStructure([])
        repr_str = repr(structure)

        assert "CompositeStructure" in repr_str
        assert "[\n]" in repr_str or "[]" in repr_str.replace('\n', '').replace(' ', '')

    def test_repr_method_single_request(self):
        """Test __repr__ method with single request."""
        request = DummyRequest(name="single")
        structure = CompositeStructure([request])
        repr_str = repr(structure)

        assert "CompositeStructure" in repr_str
        assert "single" in repr_str

    def test_make_optimal_structure_single_request(self):
        """Test make_optimal_structure with single request."""
        single_request = DummyRequest(name="single")

        result = CompositeStructure.make_optimal_structure([single_request], name=None)

        # Should return the single request as-is
        assert result == single_request
        assert result.name == "single"

    def test_make_optimal_structure_single_request_with_name(self):
        """Test make_optimal_structure with single request and name."""
        single_request = DummyRequest(name="original")

        result = CompositeStructure.make_optimal_structure([single_request], name="new_name")

        # Should return the request with updated name
        assert result == single_request
        assert result.name == "new_name"

    def test_make_optimal_structure_multiple_requests(self, sample_requests):
        """Test make_optimal_structure with multiple requests."""
        result = CompositeStructure.make_optimal_structure(sample_requests, name=None)

        # Should return CompositeStructure instance
        assert isinstance(result, CompositeStructure)
        assert result.requests == sample_requests

    def test_make_optimal_structure_multiple_requests_with_name(self, sample_requests):
        """Test make_optimal_structure with multiple requests and name."""
        result = CompositeStructure.make_optimal_structure(sample_requests, name="multi")

        # Should return CompositeStructure instance
        # Note: CompositeStructure doesn't have a name attribute, so name is ignored for multiple requests
        assert isinstance(result, CompositeStructure)
        assert result.requests == sample_requests

    def test_make_optimal_structure_empty_list(self):
        """Test make_optimal_structure with empty list."""
        result = CompositeStructure.make_optimal_structure([], name=None)

        # Should return CompositeStructure instance even for empty list
        assert isinstance(result, CompositeStructure)
        assert len(result) == 0

    def test_count_leaf_requests_duck_typing(self):
        """Test count_leaf_requests uses duck typing correctly."""
        # Create a mock object that has count_leaf_requests method
        mock_request = Mock(spec=OperationRequestFoundation)
        mock_request.count_leaf_requests = Mock(return_value=7)

        # Create a normal request without the method
        normal_request = DummyRequest(name="normal")

        requests = [mock_request, normal_request]
        structure = CompositeStructure(requests)

        count = structure.count_leaf_requests()

        # mock_request contributes 7, normal_request contributes 1
        assert count == 8
        mock_request.count_leaf_requests.assert_called_once()

    def test_count_leaf_requests_callable_check(self):
        """Test count_leaf_requests checks if method is callable."""
        # Create a mock with non-callable count_leaf_requests
        mock_request = Mock(spec=OperationRequestFoundation)
        mock_request.count_leaf_requests = "not_callable"  # Not callable

        normal_request = DummyRequest(name="normal")

        requests = [mock_request, normal_request]
        structure = CompositeStructure(requests)

        count = structure.count_leaf_requests()

        # Since count_leaf_requests is not callable, mock_request should count as 1
        assert count == 2

    def test_requests_attribute_immutability(self, composite_structure, sample_requests):
        """Test that requests attribute is properly set."""
        assert composite_structure.requests == sample_requests

        # Verify we can access individual requests
        assert composite_structure.requests[0].name == "req1"
        assert composite_structure.requests[1].name == "req2"
        assert composite_structure.requests[2].name == "req3"

    def test_structure_with_subclassed_requests(self):
        """Test CompositeStructure with subclassed OperationRequestFoundation."""
        class CustomRequest(OperationRequestFoundation):
            def __init__(self, name=None):
                super().__init__(name=name, debug_tag=None)

            @property
            def operation_type(self):
                return "CUSTOM"

            def _execute_core(self, driver, logger):
                return "custom_result"

        custom_requests = [
            CustomRequest(name="custom1"),
            CustomRequest(name="custom2"),
            DummyRequest(name="dummy")  # Mix with other types
        ]

        structure = CompositeStructure(custom_requests)

        assert len(structure) == 3
        assert structure.requests == custom_requests
        assert structure.count_leaf_requests() == 3

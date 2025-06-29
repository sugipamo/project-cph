"""Tests for CompositeStructure class."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.operations.composite_structure import CompositeStructure


# Create a concrete class that implements the protocol
class MockRequest:
    """Mock request implementing OperationRequestFoundation protocol."""
    def __init__(self, name="MockRequest"):
        self.name = name
    
    def execute_operation(self, driver, logger):
        return f"{self.name} executed"
    
    def set_name(self, name):
        self.name = name
        return self
    
    def __repr__(self):
        return self.name


class TestCompositeStructure:
    """Test suite for CompositeStructure."""
    
    def create_structure(self, requests):
        """Helper to create CompositeStructure with patched validation."""
        with patch('src.operations.composite_structure.all', return_value=True):
            return CompositeStructure(requests)
    
    def test_init_valid_requests(self):
        """Test initialization with valid OperationRequestFoundation objects."""
        req1 = MockRequest("req1")
        req2 = MockRequest("req2")
        req3 = MockRequest("req3")
        
        structure = self.create_structure([req1, req2, req3])
        
        assert structure.requests == [req1, req2, req3]
    
    def test_init_invalid_requests(self):
        """Test initialization with invalid request types."""
        req1 = MockRequest("req1")
        req2 = "not a request"  # Invalid type
        
        # Patch all() to return False for invalid request
        with patch('src.operations.composite_structure.all', return_value=False):
            with pytest.raises(TypeError, match="All elements of 'requests' must be OperationRequestFoundation"):
                CompositeStructure([req1, req2])
    
    def test_count_leaf_requests_simple(self):
        """Test counting leaf requests (no nested composites)."""
        req1 = MockRequest()
        req2 = MockRequest()
        req3 = MockRequest()
        
        # These don't have count_leaf_requests method, so they're leaves
        structure = self.create_structure([req1, req2, req3])
        
        assert structure.count_leaf_requests() == 3
    
    def test_count_leaf_requests_nested(self):
        """Test counting leaf requests with nested composite structures."""
        # Create leaf requests
        leaf1 = MockRequest()
        leaf2 = MockRequest()
        leaf3 = MockRequest()
        
        # Create a nested composite request that has count_leaf_requests
        nested = MockRequest()
        nested.count_leaf_requests = Mock(return_value=2)
        
        structure = self.create_structure([leaf1, nested, leaf3])
        
        assert structure.count_leaf_requests() == 4  # 1 + 2 + 1
    
    def test_count_leaf_requests_with_attribute_error(self):
        """Test counting when a request has the method but it raises AttributeError."""
        req1 = MockRequest()
        
        # Create a request with count_leaf_requests that raises AttributeError
        req2 = MockRequest()
        req2.count_leaf_requests = Mock(side_effect=AttributeError)
        
        structure = self.create_structure([req1, req2])
        
        assert structure.count_leaf_requests() == 2  # Both treated as leaves
    
    def test_len(self):
        """Test __len__ method."""
        req1 = MockRequest()
        req2 = MockRequest()
        
        structure = self.create_structure([req1, req2])
        
        assert len(structure) == 2
    
    def test_iter(self):
        """Test __iter__ method."""
        req1 = MockRequest()
        req2 = MockRequest()
        req3 = MockRequest()
        
        structure = self.create_structure([req1, req2, req3])
        
        requests_list = list(structure)
        assert requests_list == [req1, req2, req3]
        
        # Test with for loop
        count = 0
        for req in structure:
            count += 1
            assert isinstance(req, MockRequest)
        assert count == 3
    
    def test_repr(self):
        """Test __repr__ method."""
        req1 = MockRequest("Request1")
        
        req2 = MockRequest("Request2")
        
        structure = self.create_structure([req1, req2])
        
        repr_str = repr(structure)
        assert "CompositeStructure" in repr_str
        assert "Request1" in repr_str
        assert "Request2" in repr_str
    
    def test_make_optimal_structure_single_request(self):
        """Test make_optimal_structure with single request."""
        req = MockRequest()
        
        result = CompositeStructure.make_optimal_structure([req], None)
        
        assert result == req  # Returns the single request directly
    
    def test_make_optimal_structure_single_request_with_name(self):
        """Test make_optimal_structure with single request and name."""
        req = MockRequest()
        
        result = CompositeStructure.make_optimal_structure([req], "test_name")
        
        assert result == req
        assert result.name == "test_name"
    
    def test_make_optimal_structure_multiple_requests(self):
        """Test make_optimal_structure with multiple requests."""
        req1 = MockRequest()
        req2 = MockRequest()
        req3 = MockRequest()
        
        with patch('src.operations.composite_structure.all', return_value=True):
            result = CompositeStructure.make_optimal_structure([req1, req2, req3], None)
        
        assert isinstance(result, CompositeStructure)
        assert result.requests == [req1, req2, req3]
    
    def test_make_optimal_structure_multiple_requests_with_name(self):
        """Test make_optimal_structure with multiple requests and name."""
        req1 = MockRequest()
        req2 = MockRequest()
        
        with patch('src.operations.composite_structure.all', return_value=True):
            result = CompositeStructure.make_optimal_structure([req1, req2], "composite_name")
        
        assert isinstance(result, CompositeStructure)
        assert result.requests == [req1, req2]
        # Note: When multiple requests, name is not used in current implementation
    
    def test_empty_structure(self):
        """Test with empty request list."""
        structure = self.create_structure([])
        
        assert len(structure) == 0
        assert structure.count_leaf_requests() == 0
        assert list(structure) == []
    
    def test_deeply_nested_structure(self):
        """Test with deeply nested composite structures."""
        # Create leaf requests
        leaf1 = MockRequest()
        leaf2 = MockRequest()
        
        # Create nested composites
        nested1 = MockRequest()
        nested1.count_leaf_requests = Mock(return_value=3)
        
        nested2 = MockRequest()
        nested2.count_leaf_requests = Mock(return_value=5)
        
        structure = self.create_structure([leaf1, nested1, leaf2, nested2])
        
        assert structure.count_leaf_requests() == 10  # 1 + 3 + 1 + 5
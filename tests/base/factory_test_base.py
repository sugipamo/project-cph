"""
Base test class for factory testing
"""
import pytest
from .base_test import BaseTest


class FactoryTestBase(BaseTest):
    """Base class for factory tests with common patterns"""
    
    def setup_test(self):
        """Setup for factory tests"""
        super().setup_test()
        self.factory = None  # Override in subclasses
    
    def test_factory_initialization(self):
        """Test that factory can be initialized"""
        assert self.factory is not None, "Factory should be initialized"
    
    def assert_creates_valid_request(self, request):
        """Assert that factory creates a valid request"""
        assert request is not None, "Factory should create a non-None request"
        assert hasattr(request, 'execute'), "Request should have execute method"
    
    def test_factory_with_empty_config(self):
        """Test factory behavior with empty configuration"""
        # Override in subclasses if needed
        pass
    
    def test_factory_with_invalid_config(self):
        """Test factory behavior with invalid configuration"""
        # Override in subclasses if needed
        pass
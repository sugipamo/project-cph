"""
Base test class for driver testing
"""
import pytest
from .base_test import BaseTest


class DriverTestBase(BaseTest):
    """Base class for driver tests with common patterns"""
    
    def setup_test(self):
        """Setup for driver tests"""
        super().setup_test()
        self.driver = None  # Override in subclasses
    
    def test_driver_initialization(self):
        """Test that driver can be initialized"""
        assert self.driver is not None, "Driver should be initialized"
    
    def create_test_request(self, **kwargs):
        """Create a test request - override in subclasses"""
        raise NotImplementedError("Subclasses must implement create_test_request")
    
    def assert_successful_execution(self, result):
        """Assert that execution was successful"""
        assert hasattr(result, 'success'), "Result should have success attribute"
        if hasattr(result, 'success'):
            assert result.success, f"Execution should be successful, got: {result}"
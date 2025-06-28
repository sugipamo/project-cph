"""Tests for the base driver interface."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from src.infrastructure.drivers.generic.base_driver import ExecutionDriverInterface


class ConcreteDriver(ExecutionDriverInterface):
    """Concrete implementation for testing."""
    
    def execute_command(self, request):
        return f"Executed: {request}"
    
    def validate(self, request):
        return request is not None


class TestExecutionDriverInterface:
    """Test cases for ExecutionDriverInterface."""
    
    def test_initialization(self):
        """Test driver initialization."""
        driver = ConcreteDriver()
        assert driver._infrastructure_defaults is None
        assert driver._default_cache == {}
    
    def test_abstract_methods_implemented(self):
        """Test that concrete class implements abstract methods."""
        driver = ConcreteDriver()
        assert hasattr(driver, 'execute_command')
        assert hasattr(driver, 'validate')
        
        # Test implementations
        assert driver.execute_command("test") == "Executed: test"
        assert driver.validate("test") is True
        assert driver.validate(None) is False
    
    def test_initialize_and_cleanup(self):
        """Test initialize and cleanup methods."""
        driver = ConcreteDriver()
        # Should not raise exceptions
        driver.initialize()
        driver.cleanup()
    
    def test_load_infrastructure_defaults_success(self):
        """Test loading infrastructure defaults successfully."""
        driver = ConcreteDriver()
        mock_data = {"docker": {"network_name": "test_network"}}
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(mock_data))):
                defaults = driver._load_infrastructure_defaults()
                
        assert defaults == mock_data
        assert driver._infrastructure_defaults == mock_data
    
    def test_load_infrastructure_defaults_cached(self):
        """Test that infrastructure defaults are cached."""
        driver = ConcreteDriver()
        mock_data = {"test": "value"}
        driver._infrastructure_defaults = mock_data
        
        # Should return cached value without loading file
        with patch('builtins.open', side_effect=Exception("Should not be called")):
            defaults = driver._load_infrastructure_defaults()
            
        assert defaults == mock_data
    
    def test_load_infrastructure_defaults_file_not_found(self):
        """Test loading defaults when file doesn't exist."""
        driver = ConcreteDriver()
        
        with patch('pathlib.Path.exists', return_value=False):
            defaults = driver._load_infrastructure_defaults()
            
        assert defaults == {}
        assert driver._infrastructure_defaults == {}
    
    def test_load_infrastructure_defaults_json_error(self):
        """Test loading defaults with JSON decode error."""
        driver = ConcreteDriver()
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data="invalid json")):
                defaults = driver._load_infrastructure_defaults()
                
        assert defaults == {}
        assert driver._infrastructure_defaults == {}
    
    def test_get_default_value_simple(self):
        """Test getting a simple default value."""
        driver = ConcreteDriver()
        driver._infrastructure_defaults = {"key": "value"}
        
        assert driver._get_default_value("key") == "value"
        assert driver._get_default_value("missing", "default") == "default"
    
    def test_get_default_value_nested(self):
        """Test getting nested default values."""
        driver = ConcreteDriver()
        driver._infrastructure_defaults = {
            "docker": {
                "network": {
                    "name": "test_network"
                }
            }
        }
        
        assert driver._get_default_value("docker.network.name") == "test_network"
        assert driver._get_default_value("docker.network") == {"name": "test_network"}
        assert driver._get_default_value("docker.missing.key", "default") == "default"
    
    def test_get_default_value_cached(self):
        """Test that default values are cached."""
        driver = ConcreteDriver()
        driver._infrastructure_defaults = {"key": "value"}
        
        # First call
        value1 = driver._get_default_value("key")
        assert value1 == "value"
        assert "key" in driver._default_cache
        
        # Modify defaults
        driver._infrastructure_defaults = {"key": "new_value"}
        
        # Should return cached value
        value2 = driver._get_default_value("key")
        assert value2 == "value"  # Still the cached value
    
    def test_get_default_value_loads_defaults(self):
        """Test that get_default_value loads defaults if needed."""
        driver = ConcreteDriver()
        mock_data = {"test": {"nested": "value"}}
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(mock_data))):
                value = driver._get_default_value("test.nested")
                
        assert value == "value"
    
    def test_get_default_value_non_dict_navigation(self):
        """Test navigation through non-dict values."""
        driver = ConcreteDriver()
        driver._infrastructure_defaults = {
            "key": "string_value"
        }
        
        # Trying to navigate into a string
        assert driver._get_default_value("key.nested", "default") == "default"
    
    def test_path_resolution_to_project_root(self):
        """Test finding project root from file path."""
        driver = ConcreteDriver()
        
        # Mock the path resolution
        with patch('pathlib.Path.exists') as mock_exists:
            # Make config file exist
            mock_exists.return_value = True
            
            with patch('builtins.open', mock_open(read_data="{}")):
                defaults = driver._load_infrastructure_defaults()
                
        assert defaults == {}
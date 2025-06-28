"""Tests for JSON provider implementations."""
import json
import pytest
from io import StringIO
from unittest.mock import Mock, mock_open

from src.infrastructure.json_provider import SystemJsonProvider, MockJsonProvider


class TestSystemJsonProvider:
    """Tests for SystemJsonProvider."""
    
    def test_dumps_simple_dict(self):
        """Test converting dict to JSON string."""
        provider = SystemJsonProvider()
        data = {"key": "value", "number": 42}
        result = provider.dumps(data)
        
        assert result == '{"key": "value", "number": 42}'
        assert json.loads(result) == data
    
    def test_dumps_with_indent(self):
        """Test dumps with formatting options."""
        provider = SystemJsonProvider()
        data = {"a": 1, "b": 2}
        result = provider.dumps(data, indent=2)
        
        assert "{\n  \"a\": 1,\n  \"b\": 2\n}" == result
    
    def test_loads_simple_string(self):
        """Test converting JSON string to object."""
        provider = SystemJsonProvider()
        json_str = '{"test": "data", "count": 5}'
        result = provider.loads(json_str)
        
        assert result == {"test": "data", "count": 5}
    
    def test_loads_invalid_json(self):
        """Test loads with invalid JSON raises error."""
        provider = SystemJsonProvider()
        
        with pytest.raises(json.JSONDecodeError):
            provider.loads("invalid json{")
    
    def test_dump_to_file(self):
        """Test writing JSON to file object."""
        provider = SystemJsonProvider()
        data = {"test": "value"}
        file_obj = StringIO()
        
        provider.dump(data, file_obj)
        file_obj.seek(0)
        
        assert file_obj.read() == '{"test": "value"}'
    
    def test_load_from_file(self):
        """Test reading JSON from file object."""
        provider = SystemJsonProvider()
        file_obj = StringIO('{"loaded": "data", "num": 123}')
        
        result = provider.load(file_obj)
        
        assert result == {"loaded": "data", "num": 123}


class TestMockJsonProvider:
    """Tests for MockJsonProvider."""
    
    def test_dumps_loads_compatibility(self):
        """Test that dumps and loads work together correctly."""
        provider = MockJsonProvider()
        data = {"mock": "test", "nested": {"value": 42}}
        
        json_str = provider.dumps(data)
        result = provider.loads(json_str)
        
        assert result == data
    
    def test_mock_file_operations(self):
        """Test mock file dump and load."""
        provider = MockJsonProvider()
        data = {"file": "data"}
        
        # Mock file object with name attribute
        mock_file = Mock()
        mock_file.name = "test.json"
        
        # Dump data
        provider.dump(data, mock_file)
        
        # Load data back
        result = provider.load(mock_file)
        
        assert result == data
    
    def test_add_mock_data(self):
        """Test adding mock data directly."""
        provider = MockJsonProvider()
        test_data = {"pre": "loaded"}
        
        provider.add_mock_data("config.json", test_data)
        
        # Create mock file with matching name
        mock_file = Mock()
        mock_file.name = "config.json"
        
        result = provider.load(mock_file)
        assert result == test_data
    
    def test_load_nonexistent_file_falls_back(self):
        """Test loading non-mocked file falls back to real load."""
        provider = MockJsonProvider()
        file_obj = StringIO('{"real": "file"}')
        
        # No mock data added, should fall back to actual json.load
        result = provider.load(file_obj)
        
        assert result == {"real": "file"}
    
    def test_normalized_path_matching(self):
        """Test that paths are normalized for matching."""
        provider = MockJsonProvider()
        data = {"normalized": True}
        
        # Add data with one path format
        provider.add_mock_data("./some/path/file.json", data)
        
        # Load with different but equivalent path
        mock_file = Mock()
        mock_file.name = "some/path/file.json"
        
        result = provider.load(mock_file)
        assert result == data
    
    def test_dumps_with_special_types(self):
        """Test dumps handles various data types."""
        provider = MockJsonProvider()
        
        # Test with None, lists, nested structures
        test_cases = [
            None,
            [],
            [1, 2, 3],
            {"list": [1, 2], "null": None, "bool": True},
            "simple string"
        ]
        
        for data in test_cases:
            json_str = provider.dumps(data)
            result = provider.loads(json_str)
            assert result == data
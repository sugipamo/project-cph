"""Tests for ResultFactory."""
import pytest
from unittest.mock import Mock, patch
from src.operations.results.result_factory import ResultFactory
from src.operations.error_converter import ErrorConverter


class TestResultFactory:
    """Test cases for ResultFactory."""
    
    def test_create_shell_result_success(self):
        """Test creating a successful shell result."""
        error_converter = Mock(spec=ErrorConverter)
        factory = ResultFactory(error_converter)
        
        result = factory.create_shell_result(
            success=True,
            stdout="Hello, world!",
            stderr="",
            command="echo Hello, world!",
            working_directory="/test"
        )
        
        assert result.success is True
        assert result.stdout == "Hello, world!"
        assert result.stderr == ""
        assert result.command == "echo Hello, world!"
        assert result.returncode == 0
    
    def test_create_shell_result_failure(self):
        """Test creating a failed shell result."""
        error_converter = Mock(spec=ErrorConverter)
        factory = ResultFactory(error_converter)
        
        error = Exception("Command failed")
        result = factory.create_shell_result(
            success=False,
            stdout="",
            stderr="Error: Command not found",
            command="invalid_command",
            working_directory="/test",
            error=error
        )
        
        assert result.success is False
        assert result.stdout == ""
        assert result.stderr == "Error: Command not found"
        assert result.command == "invalid_command"
        assert result.returncode == 1
        assert result.error == "Command failed"
    
    def test_create_shell_result_with_metadata(self):
        """Test creating shell result with metadata."""
        error_converter = Mock(spec=ErrorConverter)
        factory = ResultFactory(error_converter)
        
        result = factory.create_shell_result(
            success=True,
            stdout="Output",
            stderr="",
            command="test",
            working_directory="/test",
            metadata={"key": "value"},
            start_time=1.0,
            end_time=2.0
        )
        
        assert result.metadata == {"key": "value"}
        assert result.start_time == 1.0
        assert result.end_time == 2.0
    
    def test_load_infrastructure_defaults(self):
        """Test loading infrastructure defaults."""
        error_converter = Mock(spec=ErrorConverter)
        
        # Test with successful file load
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = '{"infrastructure_defaults": {"test": "value"}}'
            factory = ResultFactory(error_converter)
            assert factory._infrastructure_defaults == {"infrastructure_defaults": {"test": "value"}}
    
    def test_load_infrastructure_defaults_file_not_found(self):
        """Test loading infrastructure defaults when file not found."""
        error_converter = Mock(spec=ErrorConverter)
        
        with patch('builtins.open', side_effect=FileNotFoundError):
            factory = ResultFactory(error_converter)
            # Should use default values
            assert 'infrastructure_defaults' in factory._infrastructure_defaults
    
    def test_get_default_value(self):
        """Test getting default values from infrastructure defaults."""
        error_converter = Mock(spec=ErrorConverter)
        factory = ResultFactory(error_converter)
        factory._infrastructure_defaults = {
            'infrastructure_defaults': {
                'result': {
                    'path': '/default/path',
                    'op': 'default_op'
                }
            }
        }
        
        # Test getting nested value
        value = factory._get_default_value(['infrastructure_defaults', 'result', 'path'], str)
        assert value == '/default/path'
        
        # Test getting value with wrong type
        value = factory._get_default_value(['infrastructure_defaults', 'result', 'path'], int)
        assert value is None
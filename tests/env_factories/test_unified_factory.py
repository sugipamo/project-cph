"""
Tests for the unified factory pattern
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.env_factories.unified_factory import UnifiedCommandRequestFactory
from src.env_factories.unified_selector import UnifiedFactorySelector
from src.env_factories.command_types import CommandType
from src.operations.shell.shell_request import ShellRequest
from src.operations.file.file_request import FileRequest, FileOpType
from src.operations.python.python_request import PythonRequest


class TestUnifiedCommandRequestFactory:
    """Test the unified command request factory"""
    
    @pytest.fixture
    def mock_controller(self):
        """Create mock controller"""
        controller = Mock()
        controller.env_context = Mock()
        controller.env_context.contest_name = "test_contest"
        controller.env_context.problem_name = "test_problem"
        controller.format_string = Mock(side_effect=lambda x: x)  # Pass-through for testing
        return controller
    
    @pytest.fixture
    def factory(self, mock_controller):
        """Create unified factory instance"""
        factory = UnifiedCommandRequestFactory(mock_controller)
        # Mock format_string method
        factory.format_string = Mock(side_effect=lambda x: x)
        factory.format_value = Mock(side_effect=lambda value, node: value)
        return factory
    
    def test_factory_initialization(self, factory):
        """Test factory initializes correctly"""
        assert factory.builder_registry is not None
        assert factory.supports_command_type(CommandType.SHELL)
        assert factory.supports_command_type(CommandType.COPY)
        assert factory.supports_command_type(CommandType.PYTHON)
    
    def test_get_supported_types(self, factory):
        """Test getting supported types"""
        supported_types = factory.get_supported_types()
        assert CommandType.SHELL in supported_types
        assert CommandType.COPY in supported_types
        assert CommandType.MKDIR in supported_types
        assert CommandType.PYTHON in supported_types
    
    def test_create_shell_request_from_kwargs(self, factory):
        """Test creating shell request from kwargs"""
        request = factory.create_request_by_type(
            CommandType.SHELL,
            cmd=["echo", "hello"],
            cwd="/tmp",
            show_output=True
        )
        
        assert isinstance(request, ShellRequest)
        assert request.cmd == ["echo", "hello"]
        assert request.cwd == "/tmp"
        assert request.show_output is True
    
    def test_create_file_request_from_kwargs(self, factory):
        """Test creating file request from kwargs"""
        request = factory.create_request_by_type(
            CommandType.COPY,
            src="/tmp/source.txt",
            dst="/tmp/dest.txt"
        )
        
        assert isinstance(request, FileRequest)
        assert request.path == "/tmp/source.txt"
        assert request.dst_path == "/tmp/dest.txt"
        assert request.op == FileOpType.COPY
    
    def test_create_mkdir_request_from_kwargs(self, factory):
        """Test creating mkdir request from kwargs"""
        request = factory.create_request_by_type(
            CommandType.MKDIR,
            path="/tmp/new_dir"
        )
        
        assert isinstance(request, FileRequest)
        assert request.path == "/tmp/new_dir"
        assert request.op == FileOpType.MKDIR
    
    def test_create_python_request_from_kwargs(self, factory):
        """Test creating python request from kwargs"""
        request = factory.create_request_by_type(
            CommandType.PYTHON,
            code_or_file=["print('hello')"],
            cwd="/tmp"
        )
        
        assert isinstance(request, PythonRequest)
        assert request.code_or_file == ["print('hello')"]
        assert request.cwd == "/tmp"
    
    def test_create_request_from_node_shell(self, factory):
        """Test creating shell request from node"""
        mock_node = Mock()
        mock_node.value = {
            "type": "shell",
            "cmd": ["echo", "hello"],
            "cwd": "/tmp",
            "show_output": True,
            "allow_failure": False
        }
        mock_node.next_nodes = []
        
        request = factory.create_request_from_node(mock_node)
        
        assert isinstance(request, ShellRequest)
        assert request.allow_failure is False
    
    def test_create_request_from_node_copy(self, factory):
        """Test creating copy request from node"""
        mock_node = Mock()
        mock_node.value = {
            "type": "copy",
            "cmd": ["/tmp/src.txt", "/tmp/dst.txt"],
            "allow_failure": True
        }
        mock_node.next_nodes = []
        
        request = factory.create_request_from_node(mock_node)
        
        assert isinstance(request, FileRequest)
        assert request.op == FileOpType.COPY
        assert request.allow_failure is True
    
    def test_unsupported_command_type(self, factory):
        """Test handling of unsupported command type"""
        with pytest.raises(ValueError, match="Unsupported command type"):
            factory.create_request_by_type("unsupported_type")
    
    def test_invalid_node_value(self, factory):
        """Test handling of invalid node value"""
        mock_node = Mock()
        mock_node.value = None
        
        with pytest.raises(ValueError, match="Invalid node value"):
            factory.create_request_from_node(mock_node)
    
    def test_missing_type_field(self, factory):
        """Test handling of missing type field in node"""
        mock_node = Mock()
        mock_node.value = {"cmd": ["echo", "hello"]}  # Missing 'type' field
        
        with pytest.raises(ValueError, match="Missing 'type' field"):
            factory.create_request_from_node(mock_node)


class TestUnifiedFactorySelector:
    """Test the unified factory selector"""
    
    @pytest.fixture
    def mock_controller(self):
        """Create mock controller"""
        controller = Mock()
        controller.env_context = Mock()
        return controller
    
    @pytest.fixture 
    def selector(self):
        """Create factory selector"""
        return UnifiedFactorySelector()
    
    def test_get_factory(self, selector, mock_controller):
        """Test getting factory instance"""
        factory = selector.get_factory(mock_controller)
        
        assert isinstance(factory, UnifiedCommandRequestFactory)
        assert factory.controller == mock_controller
    
    def test_factory_caching(self, selector, mock_controller):
        """Test that factory instances are cached"""
        factory1 = selector.get_factory(mock_controller)
        factory2 = selector.get_factory(mock_controller)
        
        assert factory1 is factory2  # Same instance should be returned
    
    def test_get_factory_for_step_type(self, selector, mock_controller):
        """Test getting factory for specific step type"""
        factory = selector.get_factory_for_step_type("shell", mock_controller)
        
        assert isinstance(factory, UnifiedCommandRequestFactory)
        assert factory.supports_command_type(CommandType.SHELL)
    
    def test_unsupported_step_type(self, selector, mock_controller):
        """Test handling of unsupported step type"""
        with pytest.raises(ValueError, match="Unsupported step type"):
            selector.get_factory_for_step_type("invalid_type", mock_controller)
    
    def test_create_request_for_type(self, selector, mock_controller):
        """Test creating request directly by type"""
        # Mock the controller's format methods
        mock_controller.format_string = Mock(side_effect=lambda x: x)
        
        request = selector.create_request_for_type(
            "shell",
            mock_controller,
            cmd=["echo", "test"],
            cwd="/tmp"
        )
        
        assert isinstance(request, ShellRequest)
        assert request.cmd == ["echo", "test"]
        assert request.cwd == "/tmp"
    
    def test_get_supported_types(self, selector, mock_controller):
        """Test getting supported types"""
        supported_types = selector.get_supported_types(mock_controller)
        
        assert CommandType.SHELL in supported_types
        assert CommandType.COPY in supported_types
        assert CommandType.PYTHON in supported_types
    
    def test_clear_cache(self, selector, mock_controller):
        """Test clearing factory cache"""
        factory1 = selector.get_factory(mock_controller)
        selector.clear_cache()
        factory2 = selector.get_factory(mock_controller)
        
        assert factory1 is not factory2  # Different instances after cache clear
"""Tests for unified driver"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.infrastructure.specialized_drivers.unified_driver import UnifiedDriver
from src.operations.requests.request_types import RequestType
from src.infrastructure.di_container import DIKey


class TestUnifiedDriver:
    """Test suite for unified driver"""
    
    def setup_method(self):
        """Set up test driver before each test"""
        # Create mocks before patching
        self.mock_container = Mock()
        self.mock_logger = Mock()
        self.mock_config_provider = Mock()
        
        # Patch the _load_infrastructure_defaults method directly
        with patch.object(UnifiedDriver, '_load_infrastructure_defaults', return_value={
            "infrastructure_defaults": {
                "unified": {"request_type_name_fallback": "UnknownRequest"},
                "docker": {"container_id": None, "image_id": None}
            }
        }):
            self.driver = UnifiedDriver(self.mock_container, self.mock_logger, self.mock_config_provider)
    
    def test_initialization(self):
        """Test driver initialization"""
        assert self.driver.infrastructure == self.mock_container
        assert self.driver.logger == self.mock_logger
        assert self.driver._config_provider == self.mock_config_provider
        assert self.driver._docker_driver is None
        assert self.driver._file_driver is None
        assert self.driver._shell_python_driver is None
    
    def test_docker_driver_property(self):
        """Test lazy loading of docker driver"""
        mock_driver = Mock()
        self.mock_container.resolve.return_value = mock_driver
        
        # First access should resolve from container
        result = self.driver.docker_driver
        
        assert result == mock_driver
        assert self.driver._docker_driver == mock_driver
        self.mock_container.resolve.assert_called_once_with(DIKey.DOCKER_DRIVER)
        
        # Second access should use cached value
        self.mock_container.reset_mock()
        result2 = self.driver.docker_driver
        assert result2 == mock_driver
        self.mock_container.resolve.assert_not_called()
    
    def test_file_driver_property(self):
        """Test lazy loading of file driver"""
        mock_driver = Mock()
        self.mock_container.resolve.return_value = mock_driver
        
        result = self.driver.file_driver
        
        assert result == mock_driver
        assert self.driver._file_driver == mock_driver
        self.mock_container.resolve.assert_called_once_with(DIKey.FILE_DRIVER)
    
    def test_execute_docker_request(self):
        """Test executing a docker request"""
        mock_docker_driver = Mock()
        mock_driver_result = Mock()
        mock_driver_result.output = "output"
        mock_driver_result.error = ""
        mock_driver_result.success = True
        mock_driver_result.container_id = "container123"
        mock_driver_result.image_id = "image123"
        
        mock_docker_driver.build.return_value = mock_driver_result
        self.driver._docker_driver = mock_docker_driver
        
        mock_request = Mock()
        mock_request.request_type = RequestType.DOCKER_REQUEST
        mock_request.op = "build"
        mock_request.context_path = "/path"
        mock_request.tag = "test:latest"
        mock_request.dockerfile = "Dockerfile"
        
        result = self.driver.execute_operation_request(mock_request)
        
        assert result.success is True
        assert result.stdout == "output"
        mock_docker_driver.build.assert_called_once()
    
    def test_execute_shell_request(self):
        """Test executing a shell request"""
        mock_shell_driver = Mock()
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        
        mock_shell_driver.execute_command.return_value = mock_result
        self.driver._shell_python_driver = mock_shell_driver
        
        mock_request = Mock()
        mock_request.request_type = RequestType.SHELL_REQUEST
        mock_request.cmd = "echo test"
        
        result = self.driver.execute_operation_request(mock_request)
        
        assert result.success is True
        assert result.stdout == "output"
        mock_shell_driver.execute_command.assert_called_once_with(mock_request)
    
    def test_execute_python_request(self):
        """Test executing a python request"""
        mock_python_driver = Mock()
        mock_python_driver.execute_command.return_value = ("output", "", 0)
        self.driver._shell_python_driver = mock_python_driver
        
        mock_request = Mock()
        mock_request.request_type = RequestType.PYTHON_REQUEST
        mock_request.code_or_file = "print('test')"
        
        result = self.driver.execute_operation_request(mock_request)
        
        assert result.success is True
        assert result.stdout == "output"
        assert result.returncode == 0
        mock_python_driver.execute_command.assert_called_once_with(mock_request)
    
    def test_execute_file_request(self):
        """Test executing a file request"""
        from src.infrastructure.requests.file.file_op_type import FileOpType
        
        mock_file_driver = Mock()
        mock_driver_result = Mock()
        mock_driver_result.success = True
        mock_driver_result.output = "file content"
        mock_driver_result.error = ""
        
        mock_file_driver.mkdir.return_value = mock_driver_result
        self.driver._file_driver = mock_file_driver
        
        mock_request = Mock()
        mock_request.request_type = RequestType.FILE_REQUEST
        mock_request.op = FileOpType.MKDIR
        mock_request.get_absolute_source.return_value = "/test/dir"
        
        result = self.driver.execute_operation_request(mock_request)
        
        assert result.success is True
        assert result.content == "file content"
        mock_file_driver.mkdir.assert_called_once_with("/test/dir")
    
    def test_execute_unsupported_operation(self):
        """Test executing an unsupported operation type"""
        mock_request = Mock()
        mock_request.request_type = "UNSUPPORTED"
        
        with pytest.raises(ValueError, match="Unsupported request type: UNSUPPORTED"):
            self.driver.execute_operation_request(mock_request)
    
    def test_file_operation_delegation(self):
        """Test file operation delegation methods"""
        mock_file_driver = Mock()
        self.driver._file_driver = mock_file_driver
        
        # Test mkdir
        self.driver.mkdir("/test/dir")
        mock_file_driver.mkdir.assert_called_once_with("/test/dir")
        
        # Test rmtree
        self.driver.rmtree("/test/dir")
        mock_file_driver.rmtree.assert_called_once_with("/test/dir")
        
        # Test touch
        self.driver.touch("/test/file")
        mock_file_driver.touch.assert_called_once_with("/test/file")
        
        # Test copy
        self.driver.copy("/src", "/dst")
        mock_file_driver.copy.assert_called_once_with("/src", "/dst")
        
        # Test remove
        self.driver.remove("/test/file")
        mock_file_driver.remove.assert_called_once_with("/test/file")
    
    def test_resolve_method(self):
        """Test resolve method for compatibility"""
        mock_driver = Mock()
        self.mock_container.resolve.return_value = mock_driver
        
        # Test resolving python_driver
        self.driver._shell_python_driver = mock_driver
        result = self.driver.resolve('python_driver')
        assert result == mock_driver
        
        # Test resolving other drivers
        result = self.driver.resolve('some_driver')
        self.mock_container.resolve.assert_called_with('some_driver')
    
    def test_shell_and_python_driver_properties(self):
        """Test shell_driver and python_driver compatibility properties"""
        mock_driver = Mock()
        self.driver._shell_python_driver = mock_driver
        
        assert self.driver.shell_driver == mock_driver
        assert self.driver.python_driver == mock_driver
import pytest
from unittest.mock import Mock, MagicMock
from src.infrastructure.requests.file.file_op_type import FileOpType
from src.operations.constants.operation_type import OperationType
from src.operations.results.file_result import FileResult


class MockTimeOps:
    """Mock time operations for testing"""
    def __init__(self):
        self.time_counter = 0
        
    def current_time(self):
        self.time_counter += 1
        return self.time_counter


class TestFileRequestSimple:
    """Simplified tests for FileRequest that test individual methods"""
    
    @pytest.fixture
    def time_ops(self):
        return MockTimeOps()
        
    def test_dispatch_file_operation_read(self, time_ops):
        # Import inside test to avoid module-level issues
        from src.application.execution_requests import FileRequest
        
        # Create a real FileRequest instance
        request = FileRequest(
            operation=FileOpType.READ,
            path="/test/file.txt",
            time_ops=time_ops,
            name=None,
            content=None,
            destination=None,
            encoding='utf-8',
            allow_failure=False,
            debug_tag=None
        )
        
        # Mock the _execute_read method
        mock_result = Mock(success=True)
        request._execute_read = Mock(return_value=mock_result)
        
        # Test the dispatch method
        result = request._dispatch_file_operation(Mock(), Mock())
        request._execute_read.assert_called_once()
        assert result == mock_result
        
    def test_dispatch_file_operation_write(self, time_ops):
        from src.application.execution_requests import FileRequest
        
        request = FileRequest(
            operation=FileOpType.WRITE,
            path="/test/file.txt",
            time_ops=time_ops,
            name=None,
            content="test content",
            destination=None,
            encoding='utf-8',
            allow_failure=False,
            debug_tag=None
        )
        
        mock_result = Mock(success=True)
        request._execute_write = Mock(return_value=mock_result)
        
        result = request._dispatch_file_operation(Mock(), Mock())
        request._execute_write.assert_called_once()
        assert result == mock_result
        
    def test_dispatch_file_operation_exists(self, time_ops):
        from src.application.execution_requests import FileRequest
        
        request = FileRequest(
            operation=FileOpType.EXISTS,
            path="/test/file.txt",
            time_ops=time_ops,
            name=None,
            content=None,
            destination=None,
            encoding='utf-8',
            allow_failure=False,
            debug_tag=None
        )
        
        mock_result = Mock(success=True)
        request._execute_exists = Mock(return_value=mock_result)
        
        result = request._dispatch_file_operation(Mock(), Mock())
        request._execute_exists.assert_called_once()
        assert result == mock_result
        
    def test_dispatch_file_operation_move(self, time_ops):
        from src.application.execution_requests import FileRequest
        
        request = FileRequest(
            operation=FileOpType.MOVE,
            path="/test/file.txt",
            time_ops=time_ops,
            name=None,
            content=None,
            destination="/test/new_file.txt",
            encoding='utf-8',
            allow_failure=False,
            debug_tag=None
        )
        
        mock_result = Mock(success=True)
        request._execute_move = Mock(return_value=mock_result)
        
        result = request._dispatch_file_operation(Mock(), Mock())
        request._execute_move.assert_called_once()
        assert result == mock_result
        
    def test_dispatch_file_operation_single_path_ops(self, time_ops):
        from src.application.execution_requests import FileRequest
        
        for op in [FileOpType.REMOVE, FileOpType.MKDIR]:
            request = FileRequest(
                operation=op,
                path="/test/path",
                time_ops=time_ops,
                name=None,
                content=None,
                destination=None,
                encoding='utf-8',
                allow_failure=False,
                debug_tag=None
            )
            
            mock_result = Mock(success=True)
            if op == FileOpType.REMOVE:
                request._execute_delete = Mock(return_value=mock_result)
            elif op == FileOpType.MKDIR:
                request._execute_mkdir = Mock(return_value=mock_result)
            
            result = request._dispatch_file_operation(Mock(), Mock())
            
            if op == FileOpType.REMOVE:
                request._execute_delete.assert_called_once()
            elif op == FileOpType.MKDIR:
                request._execute_mkdir.assert_called_once()
            
            assert result == mock_result
            
    def test_dispatch_file_operation_invalid(self, time_ops):
        from src.application.execution_requests import FileRequest
        
        # We can't set invalid operation in constructor, so we'll modify after creation
        request = FileRequest(
            operation=FileOpType.READ,
            path="/test/file.txt",
            time_ops=time_ops,
            name=None,
            content=None,
            destination=None,
            encoding='utf-8',
            allow_failure=False,
            debug_tag=None
        )
        
        # Override the operation with invalid value
        request.operation = "INVALID_OP"
        
        with pytest.raises(ValueError, match="Unsupported file operation"):
            request._dispatch_file_operation(Mock(), Mock())
            
    def test_resolve_driver_direct(self):
        from src.application.execution_requests import FileRequest
        
        direct_driver = Mock()
        # Ensure the driver doesn't have _get_cached_driver attribute
        if hasattr(direct_driver, '_get_cached_driver'):
            del direct_driver._get_cached_driver
        request = Mock(spec=FileRequest)
        
        result = FileRequest._resolve_driver(request, direct_driver)
        assert result == direct_driver
        
        
    def test_handle_file_error_raise_exception(self, time_ops):
        from src.application.execution_requests import FileRequest
        
        request = FileRequest(
            operation=FileOpType.READ,
            path="/test/path",
            time_ops=time_ops,
            name=None,
            content=None,
            destination=None,
            encoding='utf-8',
            allow_failure=False,
            debug_tag=None
        )
        
        error = Exception("Test error")
        start_time = 1.0
        
        # The _handle_file_error method raises the exception when allow_failure=False
        with pytest.raises(Exception, match="Test error"):
            request._handle_file_error(error, start_time, Mock())
            
    def test_property_operation_type(self):
        from src.application.execution_requests import FileRequest
        
        # Test that operation_type property returns correct value
        assert FileRequest.operation_type.fget(Mock()) == OperationType.FILE
        
    def test_property_request_type(self):
        from src.application.execution_requests import FileRequest
        from src.domain.base_request import RequestType
        
        # Test that request_type property returns correct value
        assert FileRequest.request_type.fget(Mock()) == RequestType.FILE_REQUEST
"""Extended tests for ResultFactory to improve coverage."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import time
from src.operations.results.result_factory import ResultFactory
from src.operations.error_converter import ErrorConverter
from src.operations.results.base_result import InfrastructureResult


class TestResultFactoryExtended:
    """Extended test cases for ResultFactory."""
    
    @pytest.fixture
    def error_converter(self):
        """Create a mock error converter."""
        return Mock(spec=ErrorConverter)
    
    @pytest.fixture
    def factory(self, error_converter):
        """Create a ResultFactory instance."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            return ResultFactory(error_converter)
    
    def test_create_operation_success_result_basic(self, factory):
        """Test creating basic successful operation result."""
        result = factory.create_operation_success_result(
            success=True,
            returncode=0,
            stdout="output",
            stderr="",
            content=None,
            exists=None,
            path="/test/path",
            op="test_op",
            cmd="test_cmd",
            request=None,
            start_time=1.0,
            end_time=2.0,
            metadata={"key": "value"},
            skipped=False
        )
        
        assert result['success'] is True
        assert result['returncode'] == 0
        assert result['stdout'] == "output"
        assert result['stderr'] == ""
        assert result['path'] == "/test/path"
        assert result['op'] == "test_op"
        assert result['cmd'] == "test_cmd"
        assert result['elapsed_time'] == 1.0
        assert result['metadata'] == {"key": "value"}
        assert result['skipped'] is False
    
    def test_create_operation_success_result_with_request(self, factory):
        """Test creating operation result with request object."""
        request = Mock()
        request.path = "/request/path"
        request.op = "request_op"
        request.cmd = "request_cmd"
        request.operation_type = "test_operation"
        
        result = factory.create_operation_success_result(
            success=True,
            returncode=0,
            stdout="output",
            stderr="",
            content=None,
            exists=None,
            path=None,  # Should use request.path
            op=None,    # Should use request.op
            cmd=None,   # Should use request.cmd
            request=request,
            start_time=None,
            end_time=None,
            metadata=None,
            skipped=False
        )
        
        assert result['path'] == "/request/path"
        assert result['op'] == "request_op"
        assert result['cmd'] == "request_cmd"
        assert result['operation_type'] == "test_operation"
        assert result['elapsed_time'] is None
        assert result['metadata'] == {}
    
    def test_create_operation_success_result_returncode_only(self, factory):
        """Test creating result with returncode only (no explicit success)."""
        result = factory.create_operation_success_result(
            success=None,
            returncode=0,
            stdout=None,
            stderr=None,
            content=None,
            exists=None,
            path=None,
            op=None,
            cmd=None,
            request=None,
            start_time=None,
            end_time=None,
            metadata=None,
            skipped=True
        )
        
        assert result['success'] is True  # Inferred from returncode
        assert result['skipped'] is True
    
    def test_create_operation_success_result_missing_values_error(self, factory):
        """Test error when neither success nor returncode provided."""
        with pytest.raises(ValueError, match="Either success or returncode must be provided"):
            factory.create_operation_success_result(
                success=None,
                returncode=None,
                stdout=None,
                stderr=None,
                content=None,
                exists=None,
                path=None,
                op=None,
                cmd=None,
                request=None,
                start_time=None,
                end_time=None,
                metadata=None,
                skipped=False
            )
    
    def test_create_operation_error_result_basic(self, factory):
        """Test creating basic error operation result."""
        exception = ValueError("Test error")
        
        result = factory.create_operation_error_result(
            exception=exception,
            driver=Mock(),
            logger=Mock(),
            start_time=1.0,
            end_time=3.0,
            path="/error/path",
            op="error_op",
            cmd="error_cmd",
            request=None,
            metadata={"error": "data"}
        )
        
        assert result['success'] is False
        assert result['error_message'] == "Test error"
        assert result['exception'] == exception
        assert result['elapsed_time'] == 2.0
        assert result['path'] == "/error/path"
        assert result['metadata'] == {"error": "data"}
    
    def test_create_operation_error_result_with_request(self, factory):
        """Test creating error result with request object."""
        exception = RuntimeError("Runtime error")
        request = Mock()
        request.path = "/request/error/path"
        request.op = "request_error_op"
        request.cmd = "request_error_cmd"
        request.operation_type = "error_operation"
        
        result = factory.create_operation_error_result(
            exception=exception,
            driver=None,
            logger=None,
            start_time=None,
            end_time=None,
            path=None,
            op=None,
            cmd=None,
            request=request,
            metadata=None
        )
        
        assert result['path'] == "/request/error/path"
        assert result['op'] == "request_error_op"
        assert result['cmd'] == "request_error_cmd"
        assert result['operation_type'] == "error_operation"
        assert result['metadata'] == {}
    
    def test_create_shell_result_data(self, factory):
        """Test creating shell result data from completed process."""
        completed_process = Mock()
        completed_process.returncode = 0
        completed_process.stdout = "Shell output"
        completed_process.stderr = ""
        
        request = Mock()
        request.cmd = "echo test"
        
        result = factory.create_shell_result_data(
            completed_process=completed_process,
            start_time=1.0,
            end_time=2.0,
            request=request
        )
        
        assert result['success'] is True
        assert result['returncode'] == 0
        assert result['stdout'] == "Shell output"
        assert result['stderr'] == ""
        assert result['cmd'] == "echo test"
        assert result['elapsed_time'] == 1.0
    
    def test_create_docker_result_data(self, factory):
        """Test creating docker result data."""
        docker_response = Mock()
        docker_response.stdout = "Docker output"
        docker_response.stderr = ""
        
        request = Mock()
        request.cmd = "docker run test"
        
        result = factory.create_docker_result_data(
            docker_response=docker_response,
            start_time=1.0,
            end_time=3.0,
            request=request,
            container_id="abc123",
            image="test:latest"
        )
        
        assert result['success'] is True
        assert result['stdout'] == "Docker output"
        assert result['container_id'] == "abc123"
        assert result['image'] == "test:latest"
        assert result['elapsed_time'] == 2.0
    
    def test_create_docker_result_data_no_stdout(self, factory):
        """Test creating docker result without stdout attribute."""
        docker_response = Mock(spec=[])  # No attributes
        
        result = factory.create_docker_result_data(
            docker_response=docker_response,
            start_time=1.0,
            end_time=2.0,
            request=None,
            container_id="xyz789",
            image="alpine"
        )
        
        assert result['stdout'] is None  # Uses default
        assert result['stderr'] is None  # Uses default
    
    def test_create_file_result_data(self, factory):
        """Test creating file result data."""
        file_operation_result = Mock()
        file_operation_result.content = "File content"
        file_operation_result.exists = True
        
        request = Mock()
        request.path = "/test/file.txt"
        
        result = factory.create_file_result_data(
            file_operation_result=file_operation_result,
            start_time=1.0,
            end_time=1.5,
            request=request
        )
        
        assert result['success'] is True
        assert result['content'] == "File content"
        assert result['exists'] is True
        assert result['path'] == "/test/file.txt"
        assert result['elapsed_time'] == 0.5
    
    def test_create_file_result_data_no_attributes(self, factory):
        """Test creating file result without attributes."""
        file_operation_result = Mock(spec=[])  # No attributes
        
        result = factory.create_file_result_data(
            file_operation_result=file_operation_result,
            start_time=1.0,
            end_time=2.0,
            request=None
        )
        
        assert result['content'] is None  # Uses default
        assert result['exists'] is None   # Uses default
    
    def test_execute_operation_with_result_creation_success(self, factory):
        """Test executing operation with successful result creation."""
        # Mock the operation function
        operation_func = Mock(return_value="operation_result")
        
        # Mock result creator
        result_creator = Mock(return_value={"result": "data"})
        
        # Mock error converter to return success
        success_result = InfrastructureResult.success("operation_result")
        factory.error_converter.execute_with_conversion.return_value = success_result
        
        # Execute
        with patch('time.perf_counter', side_effect=[1.0, 2.0]):
            result = factory.execute_operation_with_result_creation(
                operation_func=operation_func,
                result_creator=result_creator
            )
        
        assert result.is_success()
        assert result.get_value() == {"result": "data"}
        result_creator.assert_called_once_with("operation_result", 1.0, 2.0)
    
    def test_execute_operation_with_result_creation_operation_error(self, factory):
        """Test executing operation that fails."""
        # Mock the operation function
        operation_func = Mock()
        
        # Mock error converter to return error
        error = ValueError("Operation failed")
        error_result = InfrastructureResult.failure(error)
        factory.error_converter.execute_with_conversion.return_value = error_result
        
        # Execute
        with patch('time.perf_counter', side_effect=[1.0, 2.0]):
            result = factory.execute_operation_with_result_creation(
                operation_func=operation_func,
                result_creator=Mock()
            )
        
        assert result.is_success()  # Still returns success
        error_data = result.get_value()
        assert error_data['success'] is False
        assert error_data['error_message'] == "Operation failed"
        assert error_data['exception'] == error
    
    def test_execute_operation_with_result_creation_creator_error(self, factory):
        """Test when result creator raises exception."""
        # Mock the operation function
        operation_func = Mock(return_value="operation_result")
        
        # Mock result creator to raise exception
        creator_error = RuntimeError("Creator failed")
        result_creator = Mock(side_effect=creator_error)
        
        # Mock error converter to return success
        success_result = InfrastructureResult.success("operation_result")
        factory.error_converter.execute_with_conversion.return_value = success_result
        
        # Execute
        with patch('time.perf_counter', side_effect=[1.0, 2.0]):
            result = factory.execute_operation_with_result_creation(
                operation_func=operation_func,
                result_creator=result_creator
            )
        
        assert result.is_success()  # Still returns success
        error_data = result.get_value()
        assert error_data['success'] is False
        assert error_data['error_message'] == "Creator failed"
        assert error_data['exception'] == creator_error
    
    def test_load_infrastructure_defaults_json_error(self, error_converter):
        """Test loading defaults with JSON decode error."""
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "invalid json"
            factory = ResultFactory(error_converter)
            # Should use default values
            assert 'infrastructure_defaults' in factory._infrastructure_defaults
    
    def test_create_shell_result_with_request(self, factory):
        """Test create_shell_result with request parameter."""
        request = Mock()
        result = factory.create_shell_result(
            success=True,
            stdout="output",
            stderr="",
            command="test",
            working_directory="/dir",
            request=request
        )
        
        assert result.request == request
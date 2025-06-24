"""Tests for ResultFactory"""
import time
from unittest.mock import Mock, patch

import pytest

from src.infrastructure.result.base_result import InfrastructureResult
from src.infrastructure.result.result_factory import ResultFactory


class TestResultFactory:
    """Test suite for ResultFactory"""

    @pytest.fixture
    def mock_error_converter(self):
        """Create mock error converter"""
        return Mock()

    @pytest.fixture
    def factory(self, mock_error_converter):
        """Create ResultFactory instance"""
        return ResultFactory(mock_error_converter)

    def test_init(self, mock_error_converter):
        """Test ResultFactory initialization"""
        factory = ResultFactory(mock_error_converter)
        assert factory.error_converter == mock_error_converter


class TestCreateOperationSuccessResult:
    """Test create_operation_success_result method"""

    @pytest.fixture
    def factory(self):
        """Create ResultFactory instance"""
        return ResultFactory(Mock())

    def test_create_success_result_all_params(self, factory):
        """Test creating success result with all parameters"""
        start_time = 1000.0
        end_time = 1002.5
        metadata = {"test": "value"}

        result = factory.create_operation_success_result(
            success=True,
            returncode=0,
            stdout="output",
            stderr="error",
            content="file content",
            exists=True,
            path="/test/path",
            op="READ",
            cmd="cat file",
            request=None,
            start_time=start_time,
            end_time=end_time,
            metadata=metadata,
            skipped=False
        )

        assert result['success'] is True
        assert result['returncode'] == 0
        assert result['stdout'] == "output"
        assert result['stderr'] == "error"
        assert result['content'] == "file content"
        assert result['exists'] is True
        assert result['path'] == "/test/path"
        assert result['op'] == "READ"
        assert result['cmd'] == "cat file"
        assert result['request'] is None
        assert result['start_time'] == start_time
        assert result['end_time'] == end_time
        assert result['elapsed_time'] == 2.5
        assert result['error_message'] is None
        assert result['exception'] is None
        assert result['metadata'] == metadata
        assert result['skipped'] is False

    def test_create_success_result_minimal_params(self, factory):
        """Test creating success result with minimal parameters"""
        result = factory.create_operation_success_result(
            success=True,
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

        assert result['success'] is True
        assert result['returncode'] is None
        assert result['elapsed_time'] is None
        assert result['metadata'] == {}

    def test_create_success_result_from_returncode(self, factory):
        """Test deriving success from returncode"""
        # Test success from returncode 0
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
            skipped=False
        )

        assert result['success'] is True

        # Test failure from returncode 1
        result = factory.create_operation_success_result(
            success=None,
            returncode=1,
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

        assert result['success'] is False

    def test_create_success_result_no_success_no_returncode_raises(self, factory):
        """Test that missing both success and returncode raises ValueError"""
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

    def test_create_success_result_with_request_attributes(self, factory):
        """Test extracting attributes from request object"""
        mock_request = Mock()
        mock_request.path = "/request/path"
        mock_request.op = "WRITE"
        mock_request.cmd = "echo test"
        mock_request.operation_type = "SHELL"

        result = factory.create_operation_success_result(
            success=True,
            returncode=0,
            stdout=None,
            stderr=None,
            content=None,
            exists=None,
            path=None,
            op=None,
            cmd=None,
            request=mock_request,
            start_time=None,
            end_time=None,
            metadata=None,
            skipped=False
        )

        assert result['path'] == "/request/path"
        assert result['op'] == "WRITE"
        assert result['cmd'] == "echo test"
        assert result['operation_type'] == "SHELL"
        assert result['request'] == mock_request

    def test_create_success_result_explicit_params_override_request(self, factory):
        """Test that explicit parameters override request attributes"""
        mock_request = Mock()
        mock_request.path = "/request/path"
        mock_request.op = "WRITE"
        mock_request.cmd = "echo test"

        result = factory.create_operation_success_result(
            success=True,
            returncode=0,
            stdout=None,
            stderr=None,
            content=None,
            exists=None,
            path="/explicit/path",
            op="READ",
            cmd="cat file",
            request=mock_request,
            start_time=None,
            end_time=None,
            metadata=None,
            skipped=False
        )

        assert result['path'] == "/explicit/path"
        assert result['op'] == "READ"
        assert result['cmd'] == "cat file"


class TestCreateOperationErrorResult:
    """Test create_operation_error_result method"""

    @pytest.fixture
    def factory(self):
        """Create ResultFactory instance"""
        return ResultFactory(Mock())

    def test_create_error_result_all_params(self, factory):
        """Test creating error result with all parameters"""
        exception = ValueError("Test error")
        start_time = 1000.0
        end_time = 1002.5
        metadata = {"error": "context"}

        result = factory.create_operation_error_result(
            exception=exception,
            driver=Mock(),
            logger=Mock(),
            start_time=start_time,
            end_time=end_time,
            path="/error/path",
            op="FAILED_OP",
            cmd="failed command",
            request=None,
            metadata=metadata
        )

        assert result['success'] is False
        assert result['returncode'] is None
        assert result['stdout'] is None
        assert result['stderr'] is None
        assert result['content'] is None
        assert result['exists'] is None
        assert result['path'] == "/error/path"
        assert result['op'] == "FAILED_OP"
        assert result['cmd'] == "failed command"
        assert result['request'] is None
        assert result['start_time'] == start_time
        assert result['end_time'] == end_time
        assert result['elapsed_time'] == 2.5
        assert result['error_message'] == "Test error"
        assert result['exception'] == exception
        assert result['metadata'] == metadata
        assert result['skipped'] is False

    def test_create_error_result_minimal_params(self, factory):
        """Test creating error result with minimal parameters"""
        exception = RuntimeError("Minimal error")

        result = factory.create_operation_error_result(
            exception=exception,
            driver=None,
            logger=None,
            start_time=None,
            end_time=None,
            path=None,
            op=None,
            cmd=None,
            request=None,
            metadata=None
        )

        assert result['success'] is False
        assert result['elapsed_time'] is None
        assert result['error_message'] == "Minimal error"
        assert result['exception'] == exception
        assert result['metadata'] == {}

    def test_create_error_result_with_request_attributes(self, factory):
        """Test extracting attributes from request object for error result"""
        mock_request = Mock()
        mock_request.path = "/request/error/path"
        mock_request.op = "FAILED_WRITE"
        mock_request.cmd = "rm -rf /"
        mock_request.operation_type = "FILE"

        exception = PermissionError("Access denied")

        result = factory.create_operation_error_result(
            exception=exception,
            driver=None,
            logger=None,
            start_time=None,
            end_time=None,
            path=None,
            op=None,
            cmd=None,
            request=mock_request,
            metadata=None
        )

        assert result['path'] == "/request/error/path"
        assert result['op'] == "FAILED_WRITE"
        assert result['cmd'] == "rm -rf /"
        assert result['operation_type'] == "FILE"
        assert result['request'] == mock_request


class TestCreateShellResultData:
    """Test create_shell_result_data method"""

    @pytest.fixture
    def factory(self):
        """Create ResultFactory instance"""
        return ResultFactory(Mock())

    def test_create_shell_result_data_success(self, factory):
        """Test creating shell result data for successful process"""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "Hello World"
        mock_process.stderr = ""

        mock_request = Mock()
        mock_request.cmd = ["echo", "Hello World"]

        start_time = 1000.0
        end_time = 1001.5

        result = factory.create_shell_result_data(
            completed_process=mock_process,
            start_time=start_time,
            end_time=end_time,
            request=mock_request
        )

        assert result['success'] is True
        assert result['returncode'] == 0
        assert result['stdout'] == "Hello World"
        assert result['stderr'] == ""
        assert result['cmd'] == ["echo", "Hello World"]
        assert result['start_time'] == start_time
        assert result['end_time'] == end_time
        assert result['elapsed_time'] == 1.5

    def test_create_shell_result_data_failure(self, factory):
        """Test creating shell result data for failed process"""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_process.stderr = "Command not found"

        result = factory.create_shell_result_data(
            completed_process=mock_process,
            start_time=1000.0,
            end_time=1001.0,
            request=None
        )

        assert result['success'] is False
        assert result['returncode'] == 1
        assert result['stderr'] == "Command not found"
        assert result['cmd'] is None

    def test_create_shell_result_data_no_request(self, factory):
        """Test creating shell result data without request"""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "output"
        mock_process.stderr = ""

        result = factory.create_shell_result_data(
            completed_process=mock_process,
            start_time=1000.0,
            end_time=1001.0,
            request=None
        )

        assert result['cmd'] is None
        assert result['request'] is None


class TestCreateDockerResultData:
    """Test create_docker_result_data method"""

    @pytest.fixture
    def factory(self):
        """Create ResultFactory instance"""
        return ResultFactory(Mock())

    def test_create_docker_result_data(self, factory):
        """Test creating docker result data"""
        mock_response = Mock()
        mock_response.stdout = "Container started"
        mock_response.stderr = ""

        mock_request = Mock()
        mock_request.cmd = ["docker", "run", "nginx"]

        start_time = 1000.0
        end_time = 1005.0

        result = factory.create_docker_result_data(
            docker_response=mock_response,
            start_time=start_time,
            end_time=end_time,
            request=mock_request,
            container_id="abc123",
            image="nginx:latest"
        )

        assert result['success'] is True
        assert result['returncode'] == 0
        assert result['stdout'] == "Container started"
        assert result['stderr'] == ""
        assert result['cmd'] == ["docker", "run", "nginx"]
        assert result['container_id'] == "abc123"
        assert result['image'] == "nginx:latest"
        assert result['start_time'] == start_time
        assert result['end_time'] == end_time
        assert result['elapsed_time'] == 5.0

    def test_create_docker_result_data_no_request(self, factory):
        """Test creating docker result data without request"""
        mock_response = Mock()
        mock_response.stdout = "Success"
        mock_response.stderr = None

        result = factory.create_docker_result_data(
            docker_response=mock_response,
            start_time=1000.0,
            end_time=1001.0,
            request=None,
            container_id=None,
            image="test:latest"
        )

        assert result['cmd'] is None
        assert result['request'] is None
        assert result['container_id'] is None
        assert result['image'] == "test:latest"

    def test_create_docker_result_data_no_attributes(self, factory):
        """Test creating docker result data when response lacks attributes"""
        mock_response = Mock(spec=[])  # No stdout/stderr attributes

        result = factory.create_docker_result_data(
            docker_response=mock_response,
            start_time=1000.0,
            end_time=1001.0,
            request=None,
            container_id="def456",
            image="alpine"
        )

        assert result['stdout'] is None
        assert result['stderr'] is None
        assert result['container_id'] == "def456"
        assert result['image'] == "alpine"


class TestCreateFileResultData:
    """Test create_file_result_data method"""

    @pytest.fixture
    def factory(self):
        """Create ResultFactory instance"""
        return ResultFactory(Mock())

    def test_create_file_result_data(self, factory):
        """Test creating file result data"""
        mock_file_result = Mock()
        mock_file_result.content = "File content"
        mock_file_result.exists = True

        mock_request = Mock()
        mock_request.path = "/test/file.txt"

        start_time = 1000.0
        end_time = 1000.5

        result = factory.create_file_result_data(
            file_operation_result=mock_file_result,
            start_time=start_time,
            end_time=end_time,
            request=mock_request
        )

        assert result['success'] is True
        assert result['returncode'] is None
        assert result['content'] == "File content"
        assert result['exists'] is True
        assert result['path'] == "/test/file.txt"
        assert result['start_time'] == start_time
        assert result['end_time'] == end_time
        assert result['elapsed_time'] == 0.5

    def test_create_file_result_data_no_request(self, factory):
        """Test creating file result data without request"""
        mock_file_result = Mock()
        mock_file_result.content = None
        mock_file_result.exists = False

        result = factory.create_file_result_data(
            file_operation_result=mock_file_result,
            start_time=1000.0,
            end_time=1000.1,
            request=None
        )

        assert result['path'] is None
        assert result['request'] is None
        assert result['content'] is None
        assert result['exists'] is False

    def test_create_file_result_data_no_attributes(self, factory):
        """Test creating file result data when result lacks attributes"""
        mock_file_result = Mock(spec=[])  # No content/exists attributes

        result = factory.create_file_result_data(
            file_operation_result=mock_file_result,
            start_time=1000.0,
            end_time=1000.1,
            request=None
        )

        assert result['content'] is None
        assert result['exists'] is None


class TestExecuteOperationWithResultCreation:
    """Test execute_operation_with_result_creation method"""

    @pytest.fixture
    def mock_error_converter(self):
        """Create mock error converter"""
        return Mock()

    @pytest.fixture
    def factory(self, mock_error_converter):
        """Create ResultFactory instance"""
        return ResultFactory(mock_error_converter)

    @patch('src.infrastructure.result.result_factory.time.perf_counter')
    def test_execute_operation_success(self, mock_time, factory):
        """Test successful operation execution"""
        mock_time.side_effect = [1000.0, 1002.0]

        # Mock successful operation
        operation_func = Mock(return_value="operation result")

        # Mock successful error converter result
        mock_success_result = Mock()
        mock_success_result.is_success.return_value = True
        mock_success_result.get_value.return_value = "operation result"
        factory.error_converter.execute_with_conversion.return_value = mock_success_result

        # Mock result creator
        result_creator = Mock(return_value={"test": "data"})

        result = factory.execute_operation_with_result_creation(operation_func, result_creator)

        assert result.is_success()
        assert result.get_value() == {"test": "data"}

        factory.error_converter.execute_with_conversion.assert_called_once_with(operation_func)
        result_creator.assert_called_once_with("operation result", 1000.0, 1002.0)

    @patch('src.infrastructure.result.result_factory.time.perf_counter')
    def test_execute_operation_with_operation_error(self, mock_time, factory):
        """Test operation execution with operation error"""
        mock_time.side_effect = [1000.0, 1001.0]

        operation_func = Mock()

        # Mock failed error converter result
        operation_error = RuntimeError("Operation failed")
        mock_error_result = Mock()
        mock_error_result.is_success.return_value = False
        mock_error_result.get_error.return_value = operation_error
        factory.error_converter.execute_with_conversion.return_value = mock_error_result

        result_creator = Mock()

        result = factory.execute_operation_with_result_creation(operation_func, result_creator)

        assert result.is_success()  # Always returns success wrapper with error data
        result_data = result.get_value()
        assert result_data['success'] is False
        assert result_data['error_message'] == "Operation failed"
        assert result_data['exception'] == operation_error

        result_creator.assert_not_called()

    @patch('src.infrastructure.result.result_factory.time.perf_counter')
    def test_execute_operation_with_result_creation_error(self, mock_time, factory):
        """Test operation execution with result creation error"""
        mock_time.side_effect = [1000.0, 1001.5]

        operation_func = Mock()

        # Mock successful operation
        mock_success_result = Mock()
        mock_success_result.is_success.return_value = True
        mock_success_result.get_value.return_value = "operation result"
        factory.error_converter.execute_with_conversion.return_value = mock_success_result

        # Mock result creator that raises exception
        result_creation_error = ValueError("Result creation failed")
        result_creator = Mock(side_effect=result_creation_error)

        result = factory.execute_operation_with_result_creation(operation_func, result_creator)

        assert result.is_success()  # Always returns success wrapper with error data
        result_data = result.get_value()
        assert result_data['success'] is False
        assert result_data['error_message'] == "Result creation failed"
        assert result_data['exception'] == result_creation_error

        result_creator.assert_called_once_with("operation result", 1000.0, 1001.5)

    def test_execute_operation_calls_error_converter(self, factory):
        """Test that execute_operation_with_result_creation calls error converter"""
        operation_func = Mock()
        result_creator = Mock()

        # Mock error converter result
        mock_result = Mock()
        mock_result.is_success.return_value = True
        mock_result.get_value.return_value = "test"
        factory.error_converter.execute_with_conversion.return_value = mock_result

        # Mock result creator
        result_creator.return_value = {"data": "test"}

        factory.execute_operation_with_result_creation(operation_func, result_creator)

        factory.error_converter.execute_with_conversion.assert_called_once_with(operation_func)

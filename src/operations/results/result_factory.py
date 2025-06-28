"""Result factory service for creating standardized result objects."""
import json
import time
from pathlib import Path
from typing import Any, Optional

from src.operations.error_converter import ErrorConverter
from src.operations.results.base_result import InfrastructureResult


class ResultFactory:
    """Factory service for creating standardized result objects.

    This service centralizes result creation logic in the infrastructure layer,
    ensuring consistent result structure and avoiding scattered result creation code.
    """

    def __init__(self, error_converter: ErrorConverter):
        """Initialize result factory.

        Args:
            error_converter: Error conversion service for exception handling
        """
        self.error_converter = error_converter
        self._infrastructure_defaults = self._load_infrastructure_defaults()

    def _load_infrastructure_defaults(self) -> dict[str, Any]:
        """Load infrastructure defaults from config file."""
        try:
            config_path = Path(__file__).parents[3] / 'config' / 'system' / 'infrastructure_defaults.json'
            with open(config_path, encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {'infrastructure_defaults': {'result': {'path': None, 'op': None, 'cmd': None, 'operation_type': 'unknown'}, 'docker': {'stdout': None, 'stderr': None}, 'file': {'content': None, 'exists': None}}}

    def _get_default_value(self, path: list[str], default_type: type) -> Any:
        """Get default value from infrastructure defaults."""
        current = self._infrastructure_defaults
        for key in path:
            current = current[key]
        return current if isinstance(current, default_type) else None

    def create_operation_success_result(self, success: bool, returncode: Optional[int], stdout: Optional[str], stderr: Optional[str], content: Optional[str], exists: Optional[bool], path: Optional[str], op: Optional[Any], cmd: Optional[str], request: Optional[Any], start_time: Optional[float], end_time: Optional[float], metadata: Optional[dict[str, Any]], skipped: bool) -> dict[str, Any]:
        """Create successful operation result data.

        Args:
            All parameters for OperationResult creation

        Returns:
            Dictionary containing operation result data
        """
        if start_time is not None and end_time is not None:
            elapsed_time = end_time - start_time
        else:
            elapsed_time = None
        if metadata is not None:
            result_metadata = metadata
        else:
            result_metadata = {}
        if request is not None:
            if hasattr(request, 'path'):
                result_path = path or request.path
            else:
                result_path = path or self._get_default_value(['infrastructure_defaults', 'result', 'path'], type(None))
            if hasattr(request, 'op'):
                result_op = op or request.op
            else:
                result_op = op or self._get_default_value(['infrastructure_defaults', 'result', 'op'], type(None))
            if hasattr(request, 'cmd'):
                result_cmd = cmd or request.cmd
            else:
                result_cmd = cmd or self._get_default_value(['infrastructure_defaults', 'result', 'cmd'], type(None))
            if hasattr(request, 'operation_type'):
                operation_type = request.operation_type
            else:
                operation_type = self._get_default_value(['infrastructure_defaults', 'result', 'operation_type'], str) or 'unknown'
        else:
            result_path = path
            result_op = op
            result_cmd = cmd
            operation_type = self._get_default_value(['infrastructure_defaults', 'result', 'operation_type'], str)
        if success is None:
            if returncode is None:
                raise ValueError('Either success or returncode must be provided')
            result_success = returncode == 0
        else:
            result_success = success
        return {'success': result_success, 'returncode': returncode, 'stdout': stdout, 'stderr': stderr, 'content': content, 'exists': exists, 'path': result_path, 'op': result_op, 'cmd': result_cmd, 'request': request, 'start_time': start_time, 'end_time': end_time, 'elapsed_time': elapsed_time, 'error_message': None, 'exception': None, 'metadata': result_metadata, 'skipped': skipped, 'operation_type': operation_type}

    def create_operation_error_result(self, exception: Exception, driver: Any, logger: Any, start_time: Optional[float], end_time: Optional[float], path: Optional[str], op: Optional[Any], cmd: Optional[str], request: Optional[Any], metadata: Optional[dict[str, Any]]) -> dict[str, Any]:
        """Create error operation result data.

        Args:
            exception: The exception that occurred
            driver: Driver instance (for context)
            logger: Logger instance (for context)
            start_time: Operation start time
            end_time: Operation end time
            path: File path (if applicable)
            op: Operation type
            cmd: Command executed (if applicable)
            request: Original request object
            metadata: Additional metadata

        Returns:
            Dictionary containing error operation result data
        """
        if start_time is not None and end_time is not None:
            elapsed_time = end_time - start_time
        else:
            elapsed_time = None
        if metadata is not None:
            result_metadata = metadata
        else:
            result_metadata = {}
        if request is not None:
            if hasattr(request, 'path'):
                result_path = path or request.path
            else:
                result_path = path or self._get_default_value(['infrastructure_defaults', 'result', 'path'], type(None))
            if hasattr(request, 'op'):
                result_op = op or request.op
            else:
                result_op = op or self._get_default_value(['infrastructure_defaults', 'result', 'op'], type(None))
            if hasattr(request, 'cmd'):
                result_cmd = cmd or request.cmd
            else:
                result_cmd = cmd or self._get_default_value(['infrastructure_defaults', 'result', 'cmd'], type(None))
            if hasattr(request, 'operation_type'):
                operation_type = request.operation_type
            else:
                operation_type = self._get_default_value(['infrastructure_defaults', 'result', 'operation_type'], str) or 'unknown'
        else:
            result_path = path
            result_op = op
            result_cmd = cmd
            operation_type = self._get_default_value(['infrastructure_defaults', 'result', 'operation_type'], str)
        return {'success': False, 'returncode': None, 'stdout': None, 'stderr': None, 'content': None, 'exists': None, 'path': result_path, 'op': result_op, 'cmd': result_cmd, 'request': request, 'start_time': start_time, 'end_time': end_time, 'elapsed_time': elapsed_time, 'error_message': str(exception), 'exception': exception, 'metadata': result_metadata, 'skipped': False, 'operation_type': operation_type}

    def create_shell_result_data(self, completed_process: Any, start_time: float, end_time: float, request: Optional[Any]) -> dict[str, Any]:
        """Create shell operation result data from completed process.

        Args:
            completed_process: Completed process object
            start_time: Operation start time
            end_time: Operation end time
            request: Original shell request

        Returns:
            Dictionary containing shell result data
        """
        return self.create_operation_success_result(success=None, returncode=completed_process.returncode, stdout=completed_process.stdout, stderr=completed_process.stderr, content=None, exists=None, path=None, op=None, cmd=request.cmd if request and hasattr(request, 'cmd') else self._get_default_value(['infrastructure_defaults', 'result', 'cmd'], type(None)), request=request, start_time=start_time, end_time=end_time, metadata=None, skipped=False)

    def create_docker_result_data(self, docker_response: Any, start_time: float, end_time: float, request: Optional[Any], container_id: Optional[str], image: Optional[str]) -> dict[str, Any]:
        """Create docker operation result data.

        Args:
            docker_response: Docker operation response
            start_time: Operation start time
            end_time: Operation end time
            request: Original docker request
            container_id: Docker container ID
            image: Docker image name

        Returns:
            Dictionary containing docker result data
        """
        base_data = self.create_operation_success_result(success=True, returncode=0, stdout=docker_response.stdout if hasattr(docker_response, 'stdout') else self._get_default_value(['infrastructure_defaults', 'docker', 'stdout'], type(None)), stderr=docker_response.stderr if hasattr(docker_response, 'stderr') else self._get_default_value(['infrastructure_defaults', 'docker', 'stderr'], type(None)), content=None, exists=None, path=None, op=None, cmd=request.cmd if request and hasattr(request, 'cmd') else self._get_default_value(['infrastructure_defaults', 'result', 'cmd'], type(None)), request=request, start_time=start_time, end_time=end_time, metadata=None, skipped=False)
        base_data['container_id'] = container_id
        base_data['image'] = image
        return base_data

    def create_file_result_data(self, file_operation_result: Any, start_time: float, end_time: float, request: Optional[Any]) -> dict[str, Any]:
        """Create file operation result data.

        Args:
            file_operation_result: File operation result
            start_time: Operation start time
            end_time: Operation end time
            request: Original file request

        Returns:
            Dictionary containing file result data
        """
        return self.create_operation_success_result(success=True, returncode=None, stdout=None, stderr=None, content=file_operation_result.content if hasattr(file_operation_result, 'content') else self._get_default_value(['infrastructure_defaults', 'file', 'content'], type(None)), exists=file_operation_result.exists if hasattr(file_operation_result, 'exists') else self._get_default_value(['infrastructure_defaults', 'file', 'exists'], type(None)), path=request.path if request and hasattr(request, 'path') else self._get_default_value(['infrastructure_defaults', 'result', 'path'], type(None)), op=None, cmd=None, request=request, start_time=start_time, end_time=end_time, metadata=None, skipped=False)

    def execute_operation_with_result_creation(self, operation_func: callable, result_creator: callable) -> InfrastructureResult[dict[str, Any], Exception]:
        """Execute operation and create result using provided creator function.

        Args:
            operation_func: Function to execute
            result_creator: Function to create result data from operation result

        Returns:
            InfrastructureResult containing created result data or exception
        """
        start_time = time.perf_counter()
        operation_result = self.error_converter.execute_with_conversion(operation_func)
        end_time = time.perf_counter()
        if operation_result.is_success():
            try:
                result_data = result_creator(operation_result.get_value(), start_time, end_time)
                return InfrastructureResult.success(result_data)
            except Exception as e:
                error_data = self.create_operation_error_result(exception=e, driver=None, logger=None, start_time=start_time, end_time=end_time, path=None, op=None, cmd=None, request=None, metadata=None)
                return InfrastructureResult.success(error_data)
        else:
            error_data = self.create_operation_error_result(exception=operation_result.get_error(), driver=None, logger=None, start_time=start_time, end_time=end_time, path=None, op=None, cmd=None, request=None, metadata=None)
            return InfrastructureResult.success(error_data)
    def create_shell_result(self, success: bool, stdout: str, stderr: str, 
                          command: str, working_directory: str, 
                          error: Optional[Exception] = None, **kwargs) -> Any:
        """Create a shell result object.
        
        Args:
            success: Whether the operation succeeded
            stdout: Standard output
            stderr: Standard error
            command: Command that was executed  
            working_directory: Working directory used
            error: Optional error/exception
            **kwargs: Additional arguments
            
        Returns:
            LegacyShellResult object
        """
        from src.operations.results.execution_results import LegacyShellResult
        
        return LegacyShellResult(
            success=success,
            stdout=stdout,
            stderr=stderr,
            returncode=0 if success else 1,
            cmd=command,
            error_message=str(error) if error else None,
            exception=error,
            start_time=kwargs.get('start_time'),
            end_time=kwargs.get('end_time'),
            request=kwargs.get('request'),
            metadata=kwargs.get('metadata', {}),
            op=None
        )

__all__ = ['ResultFactory']

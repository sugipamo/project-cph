"""Result factory service for creating standardized result objects."""
import time
from typing import TYPE_CHECKING, Any, Optional

from .base_result import InfrastructureResult

if TYPE_CHECKING:
    from .error_converter import ErrorConverter


class ResultFactory:
    """Factory service for creating standardized result objects.

    This service centralizes result creation logic in the infrastructure layer,
    ensuring consistent result structure and avoiding scattered result creation code.
    """

    def __init__(self, error_converter: 'ErrorConverter'):
        """Initialize result factory.

        Args:
            error_converter: Error conversion service for exception handling
        """
        self.error_converter = error_converter

    def create_operation_success_result(self, success: bool, returncode: Optional[int],
                                        stdout: Optional[str], stderr: Optional[str],
                                        content: Optional[str], exists: Optional[bool],
                                        path: Optional[str], op: Optional[Any],
                                        cmd: Optional[str], request: Optional[Any],
                                        start_time: Optional[float], end_time: Optional[float],
                                        metadata: Optional[dict[str, Any]], skipped: bool) -> dict[str, Any]:
        """Create successful operation result data.

        Args:
            All parameters for OperationResult creation

        Returns:
            Dictionary containing operation result data
        """
        # Calculate elapsed time with explicit validation
        if start_time is not None and end_time is not None:
            elapsed_time = end_time - start_time
        else:
            elapsed_time = None

        # Initialize metadata with explicit validation
        if metadata is not None:
            result_metadata = metadata
        else:
            result_metadata = {}

        # Extract operation information from request if available
        if request is not None:
            result_path = path or getattr(request, "path", None)
            result_op = op or getattr(request, "op", None)
            result_cmd = cmd or getattr(request, "cmd", None)
            operation_type = getattr(request, "operation_type", None)
        else:
            result_path = path
            result_op = op
            result_cmd = cmd
            operation_type = None

        # Determine success status with explicit validation
        if success is None:
            if returncode is None:
                raise ValueError("Either success or returncode must be provided")
            result_success = returncode == 0
        else:
            result_success = success

        return {
            'success': result_success,
            'returncode': returncode,
            'stdout': stdout,
            'stderr': stderr,
            'content': content,
            'exists': exists,
            'path': result_path,
            'op': result_op,
            'cmd': result_cmd,
            'request': request,
            'start_time': start_time,
            'end_time': end_time,
            'elapsed_time': elapsed_time,
            'error_message': None,
            'exception': None,
            'metadata': result_metadata,
            'skipped': skipped,
            'operation_type': operation_type
        }

    def create_operation_error_result(self, exception: Exception, driver: Any, logger: Any,
                                      start_time: Optional[float], end_time: Optional[float],
                                      path: Optional[str], op: Optional[Any], cmd: Optional[str],
                                      request: Optional[Any], metadata: Optional[dict[str, Any]]) -> dict[str, Any]:
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
        # Calculate elapsed time
        if start_time is not None and end_time is not None:
            elapsed_time = end_time - start_time
        else:
            elapsed_time = None

        # Initialize metadata
        if metadata is not None:
            result_metadata = metadata
        else:
            result_metadata = {}

        # Extract operation information from request if available
        if request is not None:
            result_path = path or getattr(request, "path", None)
            result_op = op or getattr(request, "op", None)
            result_cmd = cmd or getattr(request, "cmd", None)
            operation_type = getattr(request, "operation_type", None)
        else:
            result_path = path
            result_op = op
            result_cmd = cmd
            operation_type = None

        return {
            'success': False,
            'returncode': None,
            'stdout': None,
            'stderr': None,
            'content': None,
            'exists': None,
            'path': result_path,
            'op': result_op,
            'cmd': result_cmd,
            'request': request,
            'start_time': start_time,
            'end_time': end_time,
            'elapsed_time': elapsed_time,
            'error_message': str(exception),
            'exception': exception,
            'metadata': result_metadata,
            'skipped': False,
            'operation_type': operation_type
        }

    def create_shell_result_data(self, completed_process: Any, start_time: float, end_time: float,
                                 request: Optional[Any]) -> dict[str, Any]:
        """Create shell operation result data from completed process.

        Args:
            completed_process: Completed process object
            start_time: Operation start time
            end_time: Operation end time
            request: Original shell request

        Returns:
            Dictionary containing shell result data
        """
        return self.create_operation_success_result(
            success=None,  # Will be derived from returncode
            returncode=completed_process.returncode,
            stdout=completed_process.stdout,
            stderr=completed_process.stderr,
            content=None,
            exists=None,
            path=None,
            op=None,
            cmd=getattr(request, 'cmd', None) if request else None,
            request=request,
            start_time=start_time,
            end_time=end_time,
            metadata=None,
            skipped=False
        )

    def create_docker_result_data(self, docker_response: Any, start_time: float, end_time: float,
                                  request: Optional[Any], container_id: Optional[str],
                                  image: Optional[str]) -> dict[str, Any]:
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
        base_data = self.create_operation_success_result(
            success=True,
            returncode=0,
            stdout=getattr(docker_response, 'stdout', None),
            stderr=getattr(docker_response, 'stderr', None),
            content=None,
            exists=None,
            path=None,
            op=None,
            cmd=getattr(request, 'cmd', None) if request else None,
            request=request,
            start_time=start_time,
            end_time=end_time,
            metadata=None,
            skipped=False
        )

        # Add Docker-specific fields
        base_data['container_id'] = container_id
        base_data['image'] = image

        return base_data

    def create_file_result_data(self, file_operation_result: Any, start_time: float, end_time: float,
                                request: Optional[Any]) -> dict[str, Any]:
        """Create file operation result data.

        Args:
            file_operation_result: File operation result
            start_time: Operation start time
            end_time: Operation end time
            request: Original file request

        Returns:
            Dictionary containing file result data
        """
        return self.create_operation_success_result(
            success=True,
            returncode=None,
            stdout=None,
            stderr=None,
            content=getattr(file_operation_result, 'content', None),
            exists=getattr(file_operation_result, 'exists', None),
            path=getattr(request, 'path', None) if request else None,
            op=None,
            cmd=None,
            request=request,
            start_time=start_time,
            end_time=end_time,
            metadata=None,
            skipped=False
        )

    def execute_operation_with_result_creation(self, operation_func: callable,
                                               result_creator: callable) -> InfrastructureResult[dict[str, Any], Exception]:
        """Execute operation and create result using provided creator function.

        Args:
            operation_func: Function to execute
            result_creator: Function to create result data from operation result

        Returns:
            InfrastructureResult containing created result data or exception
        """
        start_time = time.perf_counter()

        # Use error converter for exception handling
        operation_result = self.error_converter.execute_with_conversion(operation_func)

        end_time = time.perf_counter()

        if operation_result.is_success():
            # Create success result data
            try:
                result_data = result_creator(operation_result.get_value(), start_time, end_time)
                return InfrastructureResult.success(result_data)
            except Exception as e:
                # Handle result creation errors
                error_data = self.create_operation_error_result(
                    exception=e,
                    driver=None,
                    logger=None,
                    start_time=start_time,
                    end_time=end_time,
                    path=None,
                    op=None,
                    cmd=None,
                    request=None,
                    metadata=None
                )
                return InfrastructureResult.success(error_data)
        else:
            # Create error result data
            error_data = self.create_operation_error_result(
                exception=operation_result.get_error(),
                driver=None,
                logger=None,
                start_time=start_time,
                end_time=end_time,
                path=None,
                op=None,
                cmd=None,
                request=None,
                metadata=None
            )
            return InfrastructureResult.success(error_data)


__all__ = ["ResultFactory"]

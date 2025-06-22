"""Base result class for operation results."""
from typing import Any, Optional

from src.infrastructure.result.base_result import InfrastructureResult


class OperationResult:
    """Base class for operation results.

    This class now integrates with the infrastructure layer for consistent
    result handling while maintaining backward compatibility.
    """

    def __init__(self, success: Optional[bool], returncode: Optional[int],
                 stdout: Optional[str], stderr: Optional[str],
                 content: Optional[str], exists: Optional[bool],
                 path: Optional[str], op: Optional[Any],
                 cmd: Optional[str], request: Optional[Any],
                 start_time: Optional[float], end_time: Optional[float],
                 error_message: Optional[str], exception: Optional[Exception],
                 metadata: Optional[dict[str, Any]], skipped: bool):
        """Initialize operation result.

        Args:
            success: Whether the operation was successful
            returncode: Process return code
            stdout: Standard output
            stderr: Standard error
            content: Content (for file operations)
            exists: File existence flag
            path: File path
            op: Operation type
            cmd: Command executed
            request: Original request object
            start_time: Operation start time
            end_time: Operation end time
            error_message: Error message
            exception: Exception that occurred
            metadata: Additional metadata
            skipped: Whether the operation was skipped
        """
        if success is None:
            if returncode is None:
                raise ValueError("Either success or returncode must be provided")
            self.success = returncode == 0
        else:
            self.success = success

        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.content = content
        self.exists = exists
        # Initialize path, op, and cmd with explicit validation
        if path is not None:
            self.path = path
        elif request is not None:
            self.path = request.path if hasattr(request, "path") else None
        else:
            self.path = None

        if op is not None:
            self.op = op
        elif request is not None:
            self.op = request.op if hasattr(request, "op") else None
        else:
            self.op = None

        if cmd is not None:
            self.cmd = cmd
        elif request is not None:
            self.cmd = request.cmd if hasattr(request, "cmd") else None
        else:
            self.cmd = None
        self.request = request
        self.start_time = start_time
        self.end_time = end_time
        # Calculate elapsed time with explicit validation
        if start_time is not None and end_time is not None:
            self.elapsed_time = end_time - start_time
        else:
            self.elapsed_time = None
        self.error_message = error_message
        self.exception = exception
        # Initialize metadata with explicit validation
        if metadata is not None:
            self.metadata = metadata
        else:
            self.metadata = {}
        self.skipped = skipped
        # Initialize operation_type with explicit validation
        if request is not None:
            self._operation_type = request.operation_type if hasattr(request, "operation_type") else None
        else:
            self._operation_type = None

        # Create infrastructure result for compatibility and future migration
        self._infrastructure_result = self._create_infrastructure_result()

    @property
    def operation_type(self) -> Optional[Any]:
        """Get the operation type."""
        return self._operation_type

    def is_success(self) -> bool:
        """Check if operation was successful."""
        return self.success

    def is_failure(self) -> bool:
        """Check if operation failed."""
        return not self.success

    def raise_if_error(self) -> None:
        """Raise exception if operation failed."""
        if self.exception:
            raise self.exception
        if not self.success:
            raise RuntimeError(
                f"Operation failed: {self.op or self.cmd} {self.path}\n"
                f"content={self.content}\n"
                f"stdout={self.stdout}\n"
                f"stderr={self.stderr}\n"
                f"error={self.error_message}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'success': self.success,
            'returncode': self.returncode,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'content': self.content,
            'exists': self.exists,
            'path': self.path,
            'op': self._get_op_str(),
            'cmd': self.cmd,
            'request': str(self.request),
            'operation_type': self._get_operation_type_str(),
            'start_time': self.start_time,
            'end_time': self.end_time,
            'elapsed_time': self.elapsed_time,
            'error_message': self.error_message,
            'exception': self._get_exception_str(),
            'metadata': self.metadata,
            'skipped': self.skipped,
        }

    def to_json(self, json_provider) -> str:
        """Convert result to JSON string.

        Args:
            json_provider: JSON provider (injected for dependency inversion)
        """
        if json_provider is None:
            raise ValueError("json_provider is required")

        return json_provider.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def _get_operation_identifier(self) -> str:
        """Get operation identifier.

        Returns:
            Operation identifier in priority order

        Raises:
            ValueError: If no operation identifier is available
        """
        if self.op is not None:
            return str(self.op)
        if self.cmd is not None:
            return str(self.cmd)
        raise ValueError("Operation identifier (op or cmd) is required but not available")

    def summary(self) -> str:
        """Get a summary of the result."""
        if self.success:
            status = "OK"
        else:
            status = "FAIL"
        return (
            f"[{status}] op={self._get_operation_identifier()} "
            f"path={self.path} code={self.returncode} time={self.elapsed_time}s\n"
            f"content={str(self.content)[:100]}\n"
            f"stdout={str(self.stdout)[:100]}\n"
            f"stderr={str(self.stderr)[:100]}\n"
            f"error={self.error_message}"
        )

    def __repr__(self) -> str:
        """String representation of the result."""
        return (
            f"<OperationResult success={self.success} op={self.op} cmd={self.cmd} "
            f"path={self.path} returncode={self.returncode} error_message={self.error_message}>"
        )

    def _get_op_str(self) -> str:
        """Get op string with explicit validation."""
        if self.op is None:
            return ""
        return str(self.op)

    def _get_operation_type_str(self) -> str:
        """Get operation_type string with explicit validation."""
        if self.operation_type is None:
            return ""
        return str(self.operation_type)

    def _get_exception_str(self) -> str:
        """Get exception string with explicit validation."""
        if self.exception is None:
            return ""
        return str(self.exception)

    def get_error_output(self) -> str:
        """Get formatted error output."""
        parts = []
        if self.error_message:
            parts.append(f"error_message: {self.error_message}")
        if self.stderr:
            parts.append(f"stderr: {self.stderr}")
        if self.stdout and not self.success:
            parts.append(f"stdout: {self.stdout}")
        if self.exception:
            parts.append(f"exception: {self.exception}")
        # Return formatted error output with explicit validation
        if parts:
            return "\n".join(parts)
        return "No error output"

    def _create_infrastructure_result(self) -> InfrastructureResult[dict[str, Any], Exception]:
        """Create infrastructure result representation.

        This method creates an InfrastructureResult that wraps the operation data,
        providing a bridge to the infrastructure layer result system.

        Returns:
            InfrastructureResult containing operation data or exception
        """
        if self.success:
            # Create success result with operation data
            operation_data = self.to_dict()
            return InfrastructureResult.success(operation_data)
        # Create failure result with exception
        if self.exception:
            return InfrastructureResult.failure(self.exception)
        # Create generic exception if no specific exception is available
        error_details = f"Operation failed: {self.error_message or 'Unknown error'}"
        generic_exception = RuntimeError(error_details)
        return InfrastructureResult.failure(generic_exception)

    def get_infrastructure_result(self) -> InfrastructureResult[dict[str, Any], Exception]:
        """Get infrastructure result representation.

        Returns:
            InfrastructureResult wrapping this operation result
        """
        return self._infrastructure_result

    @classmethod
    def from_infrastructure_result(cls, infrastructure_result: InfrastructureResult[dict[str, Any], Exception]) -> 'OperationResult':
        """Create OperationResult from InfrastructureResult.

        This factory method enables creation of OperationResult instances
        from infrastructure layer results, supporting the migration path.

        Args:
            infrastructure_result: InfrastructureResult containing operation data

        Returns:
            OperationResult instance
        """
        if infrastructure_result.is_success():
            data = infrastructure_result.get_value()
            return cls(
                success=data['success'],
                returncode=data['returncode'],
                stdout=data['stdout'],
                stderr=data['stderr'],
                content=data['content'],
                exists=data['exists'],
                path=data['path'],
                op=data['op'],
                cmd=data['cmd'],
                request=data['request'],
                start_time=data['start_time'],
                end_time=data['end_time'],
                error_message=data['error_message'],
                exception=data['exception'],
                metadata=data['metadata'],
                skipped=data['skipped']
            )
        # Create error result from infrastructure failure
        error = infrastructure_result.get_error()
        return cls(
            success=False,
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
            error_message=str(error),
            exception=error,
            metadata={},
            skipped=False
        )


__all__ = ["OperationResult"]

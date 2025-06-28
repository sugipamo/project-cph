"""Consolidated execution result implementations."""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ExecutionResultBase:
    """Base class for all execution results with common fields."""
    success: bool
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'success': self.success,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'error': self.error,
            'metadata': self.metadata
        }


@dataclass
class ShellResult(ExecutionResultBase):
    """Result class for shell command execution."""
    stdout: str = ""
    stderr: str = ""
    returncode: Optional[int] = None
    command: Optional[str] = None
    working_directory: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        result = super().to_dict()
        result.update({
            'stdout': self.stdout,
            'stderr': self.stderr,
            'returncode': self.returncode,
            'command': self.command,
            'working_directory': self.working_directory
        })
        return result


@dataclass
class DockerResult(ExecutionResultBase):
    """Result class for Docker operations."""
    operation: str = ""
    container_id: Optional[str] = None
    image_id: Optional[str] = None
    output: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        result = super().to_dict()
        result.update({
            'operation': self.operation,
            'container_id': self.container_id,
            'image_id': self.image_id,
            'output': self.output
        })
        return result


@dataclass
class PythonResult(ExecutionResultBase):
    """Result class for Python code execution."""
    output: str = ""
    exception: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        result = super().to_dict()
        result.update({
            'output': self.output,
            'exception': self.exception
        })
        return result


# Legacy compatibility wrappers to maintain existing interfaces
class LegacyShellResult:
    """Legacy wrapper for ShellResult to maintain compatibility."""

    def __init__(self, success: Optional[bool], stdout: Optional[str],
                 stderr: Optional[str], returncode: Optional[int],
                 cmd: Optional[str], error_message: Optional[str],
                 exception: Optional[Exception], start_time: Optional[float],
                 end_time: Optional[float], request: Optional[Any],
                 metadata: Optional[dict[str, Any]], op: Optional[str],
                 **kwargs):
        """Initialize shell result with legacy interface."""
        self.result = ShellResult(
            success=success if success is not None else False,
            stdout=stdout or "",
            stderr=stderr or "",
            returncode=returncode,
            command=cmd,
            start_time=start_time,
            end_time=end_time,
            error=error_message or (str(exception) if exception else None),
            metadata=metadata or {}
        )
        # Store additional legacy fields
        self.request = request
        self.op = op
        self.exception = exception

        # Make attributes accessible directly
        for key, value in self.result.__dict__.items():
            setattr(self, key, value)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.result.to_dict()


class LegacyDockerResult:
    """Legacy wrapper for DockerResult to maintain compatibility."""

    def __init__(self, stdout: Optional[str] = None, stderr: Optional[str] = None,
                 returncode: Optional[int] = None, container_id: Optional[str] = None,
                 image: Optional[str] = None, success: Optional[bool] = None,
                 operation: Optional[str] = None, error: Optional[str] = None,
                 image_id: Optional[str] = None, output: Optional[str] = None,
                 **kwargs):
        """Initialize Docker result with legacy interface."""
        self.result = DockerResult(
            success=success if success is not None else (returncode == 0 if returncode is not None else False),
            operation=operation or "",
            container_id=container_id,
            image_id=image_id or image,
            output=output or stdout or "",
            error=error or (stderr if stderr and returncode != 0 else None),
            metadata=kwargs
        )

        # Store additional legacy fields
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.image = image

        # Make attributes accessible directly
        for key, value in self.result.__dict__.items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<DockerResult success={self.success} returncode={self.returncode} "
            f"container_id={self.container_id} image={self.image_id}>"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.result.to_dict()

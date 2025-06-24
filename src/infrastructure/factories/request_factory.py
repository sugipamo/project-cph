"""Infrastructure implementation of request factory."""
from src.infrastructure.requests.docker.docker_request import DockerRequest
from src.infrastructure.requests.file.file_op_type import FileOpType
from src.infrastructure.requests.file.file_request import FileRequest
from src.infrastructure.requests.python.python_request import PythonRequest
from src.infrastructure.requests.shell.shell_request import ShellRequest


class InfrastructureRequestFactory:
    """Infrastructure implementation for creating request objects."""

    def create_file_request(self, operation_type: str, file_path: str, **kwargs):
        """Create file request with Infrastructure layer implementation."""
        if isinstance(operation_type, str):
            operation_type = FileOpType(operation_type.upper())
        return FileRequest(operation_type, file_path, **kwargs)

    def create_docker_request(self, command: str, **kwargs):
        """Create Docker request with Infrastructure layer implementation."""
        return DockerRequest(command, **kwargs)

    def create_python_request(self, script: str, **kwargs):
        """Create Python request with Infrastructure layer implementation."""
        return PythonRequest(script, **kwargs)

    def create_shell_request(self, command: str, **kwargs):
        """Create shell request with Infrastructure layer implementation."""
        return ShellRequest(command, **kwargs)

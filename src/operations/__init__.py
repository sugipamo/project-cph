"""
Operations package - Request implementations and execution
"""
try:
    from .base_request import BaseRequest
except ImportError:
    BaseRequest = None

try:
    from .composite.composite_request import CompositeRequest
    from .composite.driver_bound_request import DriverBoundRequest  
    from .composite.parallel_composite_request import ParallelCompositeRequest
except ImportError:
    CompositeRequest = DriverBoundRequest = ParallelCompositeRequest = None

try:
    from .file.file_request import FileRequest
    from .file.local_file_driver import LocalFileDriver
except ImportError:
    FileRequest = LocalFileDriver = None

try:
    from .shell.shell_request import ShellRequest
    from .shell.local_shell_driver import LocalShellDriver
except ImportError:
    ShellRequest = LocalShellDriver = None

try:
    from .docker.docker_request import DockerRequest
    from .docker.docker_driver import DockerDriver
except ImportError:
    DockerRequest = DockerDriver = None

try:
    from .python.python_request import PythonRequest
except ImportError:
    PythonRequest = None

try:
    from .result.result import OperationResult
    from .result.docker_result import DockerResult
    from .result.file_result import FileResult
    from .result.shell_result import ShellResult
except ImportError:
    OperationResult = DockerResult = FileResult = ShellResult = None

try:
    from .constants.operation_type import OperationType
except ImportError:
    OperationType = None

# Filter out None values for __all__
_exports = {
    'BaseRequest': BaseRequest,
    'CompositeRequest': CompositeRequest,
    'DriverBoundRequest': DriverBoundRequest, 
    'ParallelCompositeRequest': ParallelCompositeRequest,
    'FileRequest': FileRequest,
    'ShellRequest': ShellRequest,
    'DockerRequest': DockerRequest,
    'PythonRequest': PythonRequest,
    'LocalFileDriver': LocalFileDriver,
    'LocalShellDriver': LocalShellDriver,
    'DockerDriver': DockerDriver,
    'OperationResult': OperationResult,
    'DockerResult': DockerResult,
    'FileResult': FileResult,
    'ShellResult': ShellResult,
    'OperationType': OperationType
}

__all__ = [name for name, obj in _exports.items() if obj is not None]
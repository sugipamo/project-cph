"""Unified driver for executing different types of requests"""
import json
from pathlib import Path
from typing import Any

# 互換性維持: configuration層への逆方向依存を削除、依存性注入で解決
from src.infrastructure.di_container import DIContainer, DIKey
from src.infrastructure.requests.file.file_op_type import FileOpType
from src.operations.interfaces.utility_interfaces import LoggerInterface
from src.operations.requests.base_request import RequestType
from src.domain.base_request import OperationRequestFoundation
from src.operations.results.execution_results import LegacyDockerResult as DockerResult
from src.operations.results.execution_results import LegacyShellResult as ShellResult
from src.operations.results.file_result import FileResult
from src.operations.results.result import OperationResult


class UnifiedDriver:
    """Unified driver that routes requests to appropriate specialized drivers"""

    def __init__(self, infrastructure: DIContainer, logger: LoggerInterface, config_provider):
        """Initialize unified driver with infrastructure container

        Args:
            infrastructure: DI container for resolving drivers
            logger: Logger instance
            config_provider: Configuration provider instance
        """
        self.infrastructure = infrastructure
        self.logger = logger
        self._config_provider = config_provider
        # 互換性維持: 設定システムでgetattr()デフォルト値を管理
        self._infrastructure_defaults = self._load_infrastructure_defaults()

        # Lazy load drivers as needed
        self._docker_driver = None
        self._file_driver = None
        self._shell_python_driver = None

    def _load_infrastructure_defaults(self) -> dict[str, Any]:
        """Load infrastructure defaults from config file."""
        try:
            config_path = Path(__file__).parents[4] / "config" / "system" / "infrastructure_defaults.json"
            with open(config_path, encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # フォールバック: デフォルト値をハードコード
            return {
                "infrastructure_defaults": {
                    "unified": {"request_type_name_fallback": "UnknownRequest"},
                    "docker": {"container_id": None, "image_id": None}
                }
            }

    def _get_default_value(self, path: list[str], default_type: type) -> Any:
        """Get default value from infrastructure defaults."""
        current = self._infrastructure_defaults
        for key in path:
            current = current[key]
        if isinstance(current, default_type):
            return current
        return None

    @property
    def docker_driver(self):
        """Lazy load docker driver"""
        if self._docker_driver is None:
            self._docker_driver = self.infrastructure.resolve(DIKey.DOCKER_DRIVER)
        return self._docker_driver

    @property
    def file_driver(self):
        """Lazy load file driver"""
        if self._file_driver is None:
            self._file_driver = self.infrastructure.resolve(DIKey.FILE_DRIVER)
        return self._file_driver

    @property
    def shell_python_driver(self):
        """Lazy load shell/python driver"""
        if self._shell_python_driver is None:
            self._shell_python_driver = self.infrastructure.resolve(DIKey.SHELL_PYTHON_DRIVER)
        return self._shell_python_driver

    @property
    def shell_driver(self):
        """Compatibility property for shell driver"""
        return self.shell_python_driver

    @property
    def python_driver(self):
        """Compatibility property for python driver"""
        return self.shell_python_driver

    def resolve(self, key):
        """Resolve a driver by key for compatibility with PythonRequest"""
        if key == 'python_driver':
            return self.python_driver
        return self.infrastructure.resolve(key)


    def execute_operation_request(self, request: OperationRequestFoundation) -> OperationResult:
        """Execute a request using the appropriate driver

        Args:
            request: Request to execute

        Returns:
            ExecutionResult from the driver
        """
        # Log request execution
        # 互換性維持: hasattr()によるgetattr()デフォルト値の代替
        if hasattr(request.request_type, 'name'):
            request_type_name = request.request_type.name
        else:
            request_type_name = self._get_default_value(['infrastructure_defaults', 'unified', 'request_type_name_fallback'], str) or str(request.request_type)
        self.logger.debug(f"Executing {request_type_name} request")

        # Route to appropriate driver based on request type
        if request.request_type == RequestType.DOCKER_REQUEST:
            return self._execute_docker_request(request)
        if request.request_type == RequestType.FILE_REQUEST:
            return self._execute_file_request(request)
        if request.request_type == RequestType.SHELL_REQUEST:
            return self._execute_shell_request(request)
        if request.request_type == RequestType.PYTHON_REQUEST:
            return self._execute_python_request(request)
        raise ValueError(f"Unsupported request type: {request.request_type}")

    def _execute_docker_request(self, request: Any) -> OperationResult:
        """Execute docker request"""
        # Check if request has DockerRequest-like attributes
        if not hasattr(request, 'op'):
            raise TypeError(f"Expected DockerRequest with 'op' attribute, got {type(request)}")

        try:
            # Route to appropriate docker operation
            if request.op == "build":
                result = self.docker_driver.build(
                    context_path=request.context_path,
                    tag=request.tag,
                    dockerfile=request.dockerfile
                )
            elif request.op == "run":
                result = self.docker_driver.run(
                    image=request.image,
                    cmd=request.cmd,
                    name=request.container,
                    volumes=request.volumes,
                    environment=request.environment,
                    detach=request.detach
                )
            elif request.op == "exec":
                result = self.docker_driver.exec(
                    container=request.container,
                    cmd=request.cmd,
                    workdir=request.workdir
                )
            elif request.op == "commit":
                result = self.docker_driver.commit(
                    container=request.container,
                    repository=request.image,
                    tag=request.tag
                )
            elif request.op == "rm":
                result = self.docker_driver.rm(
                    container=request.container,
                    force=request.force
                )
            elif request.op == "rmi":
                result = self.docker_driver.rmi(
                    image=request.image,
                    force=request.force
                )
            else:
                raise ValueError(f"Unsupported docker operation: {request.op}")

            # Convert driver result to DockerResult
            return DockerResult(
                stdout=result.output,
                stderr=result.error,
                returncode=0 if result.success else 1,
                # 互換性維持: hasattr()によるgetattr()デフォルト値の代替
                container_id=result.container_id if hasattr(result, 'container_id') else self._get_default_value(['infrastructure_defaults', 'docker', 'container_id'], type(None)),
                image=result.image_id if hasattr(result, 'image_id') else self._get_default_value(['infrastructure_defaults', 'docker', 'image_id'], type(None)),
                success=result.success,
                request=request
            )

        except Exception as e:
            self.logger.error(f"Docker operation failed: {e}")
            return DockerResult(
                stdout="",
                stderr=str(e),
                returncode=1,
                container_id=None,
                image=None,
                success=False,
                request=request
            )

    def _execute_file_request(self, request: Any) -> OperationResult:
        """Execute file request"""
        # Check if request has FileRequest-like attributes
        if not hasattr(request, 'op'):
            raise TypeError(f"Expected FileRequest with 'op' attribute, got {type(request)}")

        try:
            # Route to appropriate file operation
            if request.op == FileOpType.MKDIR:
                result = self.file_driver.mkdir(request.get_absolute_source())
            elif request.op == FileOpType.TOUCH:
                result = self.file_driver.touch(request.get_absolute_source())
            elif request.op == FileOpType.COPY:
                result = self.file_driver.copy(
                    request.get_absolute_source(),
                    request.get_absolute_target()
                )
            elif request.op == FileOpType.MOVE:
                result = self.file_driver.move(
                    request.get_absolute_source(),
                    request.get_absolute_target()
                )
            elif request.op == FileOpType.REMOVE:
                result = self.file_driver.remove(request.get_absolute_source())
            elif request.op == FileOpType.RMTREE:
                result = self.file_driver.rmtree(request.get_absolute_source())
            elif request.op == FileOpType.CHMOD:
                result = self.file_driver.chmod(
                    request.get_absolute_source(),
                    request.mode
                )
            else:
                raise ValueError(f"Unsupported file operation: {request.op}")

            # Convert driver result to FileResult
            return FileResult(
                success=result.success,
                content=result.output,
                path=request.get_absolute_source(),
                exists=None,
                op=request.op,
                error_message=result.error,
                exception=None,
                start_time=0.0,
                end_time=0.0,
                request=request,
                metadata={}
            )

        except Exception as e:
            self.logger.error(f"File operation failed: {e}")
            return FileResult(
                success=False,
                content="",
                path=request.get_absolute_source(),
                exists=None,
                # 互換性維持: hasattr()によるgetattr()デフォルト値の代替
                op=request.op if hasattr(request, 'op') else self._get_default_value(['infrastructure_defaults', 'result', 'op'], type(None)),
                error_message=str(e),
                exception=e,
                start_time=0.0,
                end_time=0.0,
                request=request,
                metadata={}
            )

    def _execute_shell_request(self, request: Any) -> OperationResult:
        """Execute shell request"""
        # Check if request has ShellRequest-like attributes
        if not hasattr(request, 'cmd'):
            raise TypeError(f"Expected ShellRequest with 'cmd' attribute, got {type(request)}")

        try:
            # Execute shell command via execute_command
            result = self.shell_driver.execute_command(request)

            # Convert CompletedProcess result to ShellResult
            return ShellResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                cmd=request.cmd,
                error_message=None,
                exception=None,
                start_time=0.0,
                end_time=0.0,
                request=request,
                metadata={},
                op="shell_operation"
            )

        except Exception as e:
            self.logger.error(f"Shell operation failed: {e}")
            return ShellResult(
                success=False,
                stdout="",
                stderr=str(e),
                returncode=1,
                cmd=request.cmd,
                error_message=str(e),
                exception=e,
                start_time=0.0,
                end_time=0.0,
                request=request,
                metadata={},
                op="shell_operation"
            )

    def _execute_python_request(self, request: Any) -> ShellResult:
        """Execute python request"""
        if not hasattr(request, 'code_or_file'):
            raise TypeError(f"Expected PythonRequest with 'code_or_file' attribute, got {type(request)}")

        try:
            stdout, stderr, returncode = self.python_driver.execute_command(request)

            return ShellResult(
                success=returncode == 0,
                returncode=returncode,
                stdout=stdout,
                stderr=stderr,
                start_time=0.0,
                end_time=0.0,
                error_message=stderr if returncode != 0 else None,
                exception=None,
                request=request,
                metadata={},
                cmd=getattr(request, 'code_or_file', 'python_code'),
                op="python_operation"
            )

        except Exception as e:
            self.logger.error(f"Python operation failed: {e}")
            return ShellResult(
                success=False,
                returncode=1,
                stdout="",
                stderr=str(e),
                start_time=0.0,
                end_time=0.0,
                error_message=str(e),
                exception=e,
                request=request,
                metadata={},
                cmd=getattr(request, 'code_or_file', 'python_code'),
                op="python_operation"
            )

    # File operation delegation methods - route to file driver
    def mkdir(self, path):
        """Create directory - delegate to file driver"""
        return self.file_driver.mkdir(path)

    def rmtree(self, path):
        """Remove directory tree - delegate to file driver"""
        return self.file_driver.rmtree(path)

    def touch(self, path):
        """Create empty file - delegate to file driver"""
        return self.file_driver.touch(path)

    def copy(self, src, dst):
        """Copy file or directory - delegate to file driver"""
        return self.file_driver.copy(src, dst)

    def remove(self, path):
        """Remove file - delegate to file driver"""
        return self.file_driver.remove(path)


"""Unified driver for executing different types of requests"""
from typing import Any

from src.configuration.config_manager import TypeSafeConfigNodeManager
from src.infrastructure.di_container import DIContainer, DIKey
from src.operations.constants.request_types import RequestType
from src.operations.interfaces.logger_interface import LoggerInterface
from src.operations.requests.base.base_request import OperationRequestFoundation
from src.operations.requests.file.file_op_type import FileOpType
from src.operations.results.docker_result import DockerResult
from src.operations.results.file_result import FileResult
from src.operations.results.result import OperationResult
from src.operations.results.shell_result import ShellResult


class UnifiedDriver:
    """Unified driver that routes requests to appropriate specialized drivers"""

    def __init__(self, infrastructure: DIContainer, logger: LoggerInterface, config_manager: TypeSafeConfigNodeManager):
        """Initialize unified driver with infrastructure container

        Args:
            infrastructure: DI container for resolving drivers
            logger: Logger instance
            config_manager: Configuration manager instance
        """
        self.infrastructure = infrastructure
        self.logger = logger
        self._config_manager = config_manager

        # Lazy load drivers as needed
        self._docker_driver = None
        self._file_driver = None
        self._shell_driver = None

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
    def shell_driver(self):
        """Lazy load shell driver"""
        if self._shell_driver is None:
            self._shell_driver = self.infrastructure.resolve(DIKey.SHELL_DRIVER)
        return self._shell_driver


    def execute_operation_request(self, request: OperationRequestFoundation) -> OperationResult:
        """Execute a request using the appropriate driver

        Args:
            request: Request to execute

        Returns:
            ExecutionResult from the driver
        """
        # Log request execution
        request_type_name = getattr(request.request_type, 'name', str(request.request_type))
        self.logger.debug(f"Executing {request_type_name} request")

        # Route to appropriate driver based on request type
        if request.request_type == RequestType.DOCKER_REQUEST:
            return self._execute_docker_request(request)
        if request.request_type == RequestType.FILE_REQUEST:
            return self._execute_file_request(request)
        if request.request_type == RequestType.SHELL_REQUEST:
            return self._execute_shell_request(request)
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
                container_id=getattr(result, 'container_id', None),
                image=getattr(result, 'image_id', None),
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
                op=getattr(request, 'op', None),
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
            # Execute shell command
            result = self.shell_driver.run(
                cmd=request.cmd,
                cwd=request.cwd,
                env=request.env,
                timeout=request.timeout
            )

            # Convert driver result to ShellResult
            # Get exit code from result if available, otherwise determine from success status
            if hasattr(result, 'exit_code') and result.exit_code is not None:
                exit_code = result.exit_code
            else:
                try:
                    success_code = self._config_manager.resolve_config(['execution_defaults', 'exit_codes', 'success'], int)
                    failure_code = self._config_manager.resolve_config(['execution_defaults', 'exit_codes', 'failure'], int)
                    exit_code = success_code if result.success else failure_code
                except KeyError as e:
                    raise ValueError("Exit code not available and no default exit codes found in configuration") from e

            return ShellResult(
                success=result.success,
                stdout=result.output,
                stderr=result.error,
                returncode=exit_code,
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


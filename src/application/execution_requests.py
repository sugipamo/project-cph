"""Consolidated execution request implementations."""
from enum import Enum, auto
from typing import Any, List, Optional, Union

from src.domain.base_request import OperationRequestFoundation
from src.infrastructure.json_provider import JsonProvider
from src.infrastructure.os_provider import OsProvider
from src.infrastructure.registry_provider import SystemRegistryProvider
from src.infrastructure.requests.file.file_op_type import FileOpType
from src.infrastructure.time_provider import TimeProvider
from src.operations.constants.operation_type import OperationType
from src.operations.error_converter import ErrorConverter
from src.operations.requests.base_request import RequestType
from src.operations.requests.composite_request import CompositeRequest
from src.operations.results.execution_results import LegacyDockerResult as DockerResult
from src.operations.results.execution_results import LegacyShellResult as ShellResult
from src.operations.results.execution_results import PythonResult
from src.operations.results.file_result import FileResult
from src.operations.results.result_factory import ResultFactory
from src.utils.python_utils import PythonUtils


class ShellRequest(OperationRequestFoundation):
    """Request for executing shell commands."""

    def __init__(
        self,
        command: str,
        working_directory: str,
        error_converter: ErrorConverter,
        result_factory: ResultFactory,
        name: Optional[str] = None,
        timeout: Optional[float] = None,
        environment: Optional[dict] = None,
        shell: Optional[bool] = None,
        retry_config: Optional[dict] = None,
        debug_tag: Optional[str] = None
    ):
        """Initialize shell request with provided parameters."""
        super().__init__(name or command, debug_tag)
        self.command = command
        self.working_directory = working_directory
        self.timeout = timeout
        self.environment = environment
        self.shell = shell
        self.retry_config = retry_config
        self._error_converter = error_converter
        self._result_factory = result_factory

    @property
    def operation_type(self) -> OperationType:
        """Return the operation type."""
        return OperationType.SHELL

    @property
    def request_type(self) -> RequestType:
        """Return the request type for type-safe identification."""
        return RequestType.SHELL_REQUEST

    def _execute_core(self, driver: Optional[Any], logger: Optional[Any]) -> ShellResult:
        """Execute shell command with retry support."""
        if logger:
            cmd_preview = self.command if len(self.command) <= 50 else self.command[:47] + "..."
            logger.info(f"Executing shell command: {cmd_preview}")

        error = None
        stdout, stderr = "", ""

        max_attempts = 1
        if self.retry_config:
            max_attempts = self.retry_config.get('max_attempts', 1)

        for attempt in range(max_attempts):
            try:
                # Execute command through driver
                result = driver.execute_command(
                    command=self.command,
                    timeout=self.timeout,
                    environment=self.environment,
                    shell=self.shell,
                    working_directory=self.working_directory
                )

                stdout = result.get('stdout', '')
                stderr = result.get('stderr', '')

                # Check for execution errors
                if not result.get('success', False):
                    error = self._error_converter.convert_error(
                        result.get('error') or Exception(f"Command failed: {stderr}")
                    )
                    if logger and attempt < max_attempts - 1:
                        logger.warning(f"Command failed (attempt {attempt + 1}/{max_attempts}), retrying...")
                    continue

                # Success case
                if logger:
                    logger.info("Shell command executed successfully")

                return self._result_factory.create_shell_result(
                    success=True,
                    stdout=stdout,
                    stderr=stderr,
                    command=self.command,
                    working_directory=self.working_directory
                )

            except Exception as e:
                error = self._error_converter.convert_error(e)
                if logger and attempt < max_attempts - 1:
                    logger.warning(f"Command failed with exception (attempt {attempt + 1}/{max_attempts}), retrying...")

        # All attempts failed
        if logger:
            logger.error(f"Shell command failed after {max_attempts} attempts: {error}")

        return self._result_factory.create_shell_result(
            success=False,
            stdout=stdout,
            stderr=stderr,
            error=error,
            command=self.command,
            working_directory=self.working_directory
        )


class PythonRequest(OperationRequestFoundation):
    """Request for executing Python code or scripts."""

    def __init__(
        self,
        script_or_code: str,
        is_script_path: bool,
        working_directory: str,
        os_provider: OsProvider,
        python_utils: PythonUtils,
        time_ops: TimeProvider,
        name: Optional[str] = None,
        timeout: Optional[float] = None,
        environment: Optional[dict] = None,
        python_path: Optional[str] = None,
        debug_tag: Optional[str] = None
    ):
        """Initialize Python request with provided parameters."""
        super().__init__(name or script_or_code, debug_tag)
        self.script_or_code = script_or_code
        self.is_script_path = is_script_path
        self.working_directory = working_directory
        self.timeout = timeout
        self.environment = environment
        self.python_path = python_path
        self._os_provider = os_provider
        self._python_utils = python_utils
        self._time_ops = time_ops

    @property
    def operation_type(self) -> OperationType:
        """Return the operation type."""
        return OperationType.PYTHON

    @property
    def request_type(self) -> RequestType:
        """Return the request type for type-safe identification."""
        return RequestType.PYTHON_REQUEST

    def _execute_core(self, driver: Optional[Any], logger: Optional[Any]) -> PythonResult:
        """Execute Python code or script."""
        start_time = self._time_ops.now()

        try:
            if logger:
                operation_desc = "script" if self.is_script_path else "code"
                logger.info(f"Executing Python {operation_desc}")

            # Prepare execution parameters
            execution_params = {
                'script_or_code': self.script_or_code,
                'is_script_path': self.is_script_path,
                'working_directory': self.working_directory,
                'timeout': self.timeout,
                'environment': self._prepare_environment(),
                'python_path': self.python_path
            }

            # Execute through driver
            result = driver.execute_python(**execution_params)

            if result['success']:
                if logger:
                    logger.info("Python execution completed successfully")
                return PythonResult(
                    success=True,
                    output=result.get('output', ''),
                    start_time=start_time,
                    end_time=self._time_ops.now()
                )
            error_msg = result.get('error', 'Unknown error')
            if logger:
                logger.error(f"Python execution failed: {error_msg}")
            return PythonResult(
                success=False,
                error=error_msg,
                start_time=start_time,
                end_time=self._time_ops.now()
            )

        except Exception as e:
            if logger:
                logger.error(f"Python execution failed with exception: {e!s}")
            return PythonResult(
                success=False,
                error=str(e),
                start_time=start_time,
                end_time=self._time_ops.now()
            )

    def _prepare_environment(self) -> dict:
        """Prepare environment variables for Python execution."""
        env = self._os_provider.environ.copy()
        if self.environment:
            env.update(self.environment)
        # Ensure PYTHONPATH includes working directory
        python_path = env.get('PYTHONPATH', '')
        if self.working_directory and self.working_directory not in python_path:
            env['PYTHONPATH'] = self._python_utils.join_paths(python_path, self.working_directory)
        return env


class DockerOpType(Enum):
    """Types of Docker operations."""
    BUILD = auto()
    RUN = auto()
    EXEC = auto()
    STOP = auto()
    REMOVE = auto()
    PULL = auto()
    PUSH = auto()


class DockerOperationError(Exception):
    """Custom exception for Docker operation errors."""
    pass


class DockerRequest(OperationRequestFoundation):
    """Request for Docker operations."""

    def __init__(
        self,
        operation: DockerOpType,
        json_provider: JsonProvider,
        working_directory: str,
        name: Optional[str] = None,
        image_name: Optional[str] = None,
        container_name: Optional[str] = None,
        dockerfile_path: Optional[str] = None,
        build_args: Optional[dict] = None,
        run_args: Optional[dict] = None,
        command: Optional[Union[str, List[str]]] = None,
        environment: Optional[dict] = None,
        volumes: Optional[dict] = None,
        ports: Optional[dict] = None,
        network: Optional[str] = None,
        debug_tag: Optional[str] = None
    ):
        """Initialize Docker request with provided parameters."""
        super().__init__(name or f"Docker {operation.name}", debug_tag)
        self.operation = operation
        self.working_directory = working_directory
        self.image_name = image_name
        self.container_name = container_name
        self.dockerfile_path = dockerfile_path
        self.build_args = build_args or {}
        self.run_args = run_args or {}
        self.command = command
        self.environment = environment or {}
        self.volumes = volumes or {}
        self.ports = ports or {}
        self.network = network
        self._json_provider = json_provider

    @property
    def operation_type(self) -> OperationType:
        """Return the operation type."""
        return OperationType.DOCKER

    @property
    def request_type(self) -> RequestType:
        """Return the request type for type-safe identification."""
        return RequestType.DOCKER_REQUEST

    def _execute_core(self, driver: Optional[Any], logger: Optional[Any]) -> DockerResult:
        """Execute Docker operation."""
        if logger:
            logger.info(f"Executing Docker operation: {self.operation.name}")

        try:
            # Dispatch to appropriate operation method
            if self.operation == DockerOpType.BUILD:
                return self._execute_build(driver, logger)
            if self.operation == DockerOpType.RUN:
                return self._execute_run(driver, logger)
            if self.operation == DockerOpType.STOP:
                return self._execute_stop(driver, logger)
            if self.operation == DockerOpType.REMOVE:
                return self._execute_remove(driver, logger)
            raise DockerOperationError(f"Unsupported Docker operation: {self.operation}")

        except Exception as e:
            if logger:
                logger.error(f"Docker operation failed: {e!s}")
            return DockerResult(
                success=False,
                operation=self.operation.name,
                error=str(e)
            )

    def _execute_build(self, driver: Any, logger: Optional[Any]) -> DockerResult:
        """Execute Docker build operation."""
        if not self.image_name:
            raise DockerOperationError("Image name is required for build operation")

        build_params = {
            'context': self.working_directory,
            'dockerfile': self.dockerfile_path,
            'tag': self.image_name,
            'buildargs': self._json_provider.dumps(self.build_args) if self.build_args else None
        }

        result = driver.execute_docker_operation('build', build_params)

        if result.get('success'):
            if logger:
                logger.info(f"Docker image built successfully: {self.image_name}")
            return DockerResult(
                success=True,
                operation='BUILD',
                image_id=result.get('image_id'),
                output=result.get('output')
            )
        return DockerResult(
            success=False,
            operation='BUILD',
            error=result.get('error', 'Build failed')
        )

    def _execute_run(self, driver: Any, logger: Optional[Any]) -> DockerResult:
        """Execute Docker run operation."""
        if not self.image_name:
            raise DockerOperationError("Image name is required for run operation")

        # Build run command with all parameters
        run_params = {
            'image': self.image_name,
            'name': self.container_name,
            'command': self.command,
            'environment': self.environment,
            'volumes': self.volumes,
            'ports': self.ports,
            'network': self.network,
            **self.run_args
        }

        # Create composite request for complex run operations
        requests = []

        # Pull image if needed
        error_converter = ErrorConverter()
        result_factory = ResultFactory(error_converter)

        pull_request = ShellRequest(
            command=f"docker pull {self.image_name}",
            working_directory=self.working_directory,
            error_converter=error_converter,
            result_factory=result_factory,
            name=f"Pull {self.image_name}"
        )
        requests.append(pull_request)

        # Run container
        run_command = self._build_run_command(run_params)
        run_request = ShellRequest(
            command=run_command,
            working_directory=self.working_directory,
            error_converter=error_converter,
            result_factory=result_factory,
            name=f"Run {self.image_name}"
        )
        requests.append(run_request)

        # Execute as composite
        composite = CompositeRequest(
            requests=requests,
            name="Docker Run",
            debug_tag=None,
            execution_controller=None
        )
        try:
            result = composite.execute_operation(driver, logger)
            
            # Composite request returns a list of results
            # Check if all operations succeeded
            if hasattr(result, '__iter__') and not isinstance(result, str):
                # It's a list or iterable
                all_success = all(getattr(r, 'success', False) for r in result)
            else:
                all_success = getattr(result, 'success', False)
        except Exception as e:
            if logger:
                logger.error(f"Docker run operation failed: {e}")
            return DockerResult(
                success=False,
                operation='RUN',
                error=str(e)
            )

        if all_success:
            return DockerResult(
                success=True,
                operation='RUN',
                container_id=self.container_name,
                output="Container started successfully"
            )
        # Extract error from composite results
        error_msg = "Failed to run container"
        if isinstance(result, list):
            for r in result:
                if hasattr(r, 'error') and r.error:
                    error_msg = r.error
                    break
        elif hasattr(result, 'error') and result.error:
            error_msg = result.error

        return DockerResult(
            success=False,
            operation='RUN',
            error=error_msg
        )

    def _execute_stop(self, driver: Any, logger: Optional[Any]) -> DockerResult:
        """Execute Docker stop operation."""
        if not self.container_name:
            raise DockerOperationError("Container name is required for stop operation")

        result = driver.execute_docker_operation('stop', {'container': self.container_name})

        if result.get('success'):
            if logger:
                logger.info(f"Docker container stopped: {self.container_name}")
            return DockerResult(
                success=True,
                operation='STOP',
                container_id=self.container_name
            )
        return DockerResult(
            success=False,
            operation='STOP',
            error=result.get('error', 'Stop failed')
        )

    def _execute_remove(self, driver: Any, logger: Optional[Any]) -> DockerResult:
        """Execute Docker remove operation."""
        if not self.container_name:
            raise DockerOperationError("Container name is required for remove operation")

        result = driver.execute_docker_operation('rm', {'container': self.container_name})

        if result.get('success'):
            if logger:
                logger.info(f"Docker container removed: {self.container_name}")
            return DockerResult(
                success=True,
                operation='REMOVE',
                container_id=self.container_name
            )
        return DockerResult(
            success=False,
            operation='REMOVE',
            error=result.get('error', 'Remove failed')
        )

    def _build_run_command(self, params: dict) -> str:
        """Build docker run command from parameters."""
        cmd_parts = ['docker', 'run']

        if params.get('name'):
            cmd_parts.extend(['--name', params['name']])

        for key, value in params.get('environment', {}).items():
            cmd_parts.extend(['-e', f'{key}={value}'])

        for host_path, container_path in params.get('volumes', {}).items():
            cmd_parts.extend(['-v', f'{host_path}:{container_path}'])

        for host_port, container_port in params.get('ports', {}).items():
            cmd_parts.extend(['-p', f'{host_port}:{container_port}'])

        if params.get('network'):
            cmd_parts.extend(['--network', params['network']])

        cmd_parts.append(params['image'])

        if params.get('command'):
            if isinstance(params['command'], list):
                cmd_parts.extend(params['command'])
            else:
                cmd_parts.append(params['command'])

        return ' '.join(cmd_parts)


class FileRequest(OperationRequestFoundation):
    """Request for file system operations."""

    def __init__(
        self,
        operation: FileOpType,
        path: str,
        time_ops: TimeProvider,
        name: Optional[str] = None,
        content: Optional[str] = None,
        destination: Optional[str] = None,
        encoding: Optional[str] = None,
        allow_failure: bool = False,
        debug_tag: Optional[str] = None
    ):
        """Initialize file request with provided parameters."""
        super().__init__(name or f"{operation.value} {path}", debug_tag)
        self.operation = operation
        self.path = path
        self.content = content
        self.destination = destination
        self.encoding = encoding or 'utf-8'
        self.allow_failure = allow_failure
        self._time_ops = time_ops

    @property
    def operation_type(self) -> OperationType:
        """Return the operation type."""
        return OperationType.FILE

    @property
    def request_type(self) -> RequestType:
        """Return the request type for type-safe identification."""
        return RequestType.FILE_REQUEST

    def _execute_core(self, driver: Optional[Any], logger: Optional[Any]) -> FileResult:
        """Execute file operation."""
        start_time = self._time_ops.now()

        if logger:
            logger.info(f"Executing file operation: {self.operation.value} on {self.path}")

        try:
            # Get appropriate driver
            file_driver = self._resolve_driver(driver)

            # Dispatch to appropriate operation
            result = self._dispatch_file_operation(file_driver, logger)

            if result.success:
                if logger:
                    logger.info("File operation completed successfully")
            else:
                if logger:
                    logger.error(f"File operation failed: {result.error}")

            return result

        except Exception as e:
            return self._handle_file_error(e, start_time, logger)

    def _resolve_driver(self, driver: Any) -> Any:
        """Resolve the appropriate driver for file operations."""
        # If driver has file operation capability, use it directly
        if hasattr(driver, 'read_file') or hasattr(driver, 'write_file'):
            return driver

        # Otherwise try to get file driver from registry
        try:
            registry = SystemRegistryProvider()
            return registry.get_driver('file')
        except Exception:
            # Fallback to using the provided driver
            return driver

    def _dispatch_file_operation(self, driver: Any, logger: Optional[Any]) -> FileResult:
        """Dispatch to the appropriate file operation method."""
        operation_map = {
            FileOpType.READ: self._execute_read,
            FileOpType.WRITE: self._execute_write,
            FileOpType.EXISTS: self._execute_exists,
            FileOpType.REMOVE: self._execute_delete,
            FileOpType.RMTREE: self._execute_rmtree,
            FileOpType.COPY: self._execute_copy,
            FileOpType.MOVE: self._execute_move,
            FileOpType.MKDIR: self._execute_mkdir,
            FileOpType.TOUCH: self._execute_touch,
        }

        operation_func = operation_map.get(self.operation)
        if not operation_func:
            raise ValueError(f"Unsupported file operation: {self.operation}")

        return operation_func(driver, logger)

    def _execute_read(self, driver: Any, logger: Optional[Any]) -> FileResult:
        """Execute file read operation."""
        content = driver.read_file(self.path, encoding=self.encoding)
        return FileResult(
            success=True,
            content=content,
            path=self.path,
            exists=None,
            op=self.operation,
            error_message=None,
            exception=None,
            start_time=self._time_ops.now(),
            end_time=self._time_ops.now(),
            request=self,
            metadata=None
        )

    def _execute_write(self, driver: Any, logger: Optional[Any]) -> FileResult:
        """Execute file write operation."""
        if self.content is None:
            raise ValueError("Content is required for write operation")

        driver.write_file(self.path, self.content, encoding=self.encoding)
        return FileResult(
            success=True,
            content=None,
            path=self.path,
            exists=True,
            op=self.operation,
            error_message=None,
            exception=None,
            start_time=self._time_ops.now(),
            end_time=self._time_ops.now(),
            request=self,
            metadata={}
        )

    def _execute_exists(self, driver: Any, logger: Optional[Any]) -> FileResult:
        """Execute file exists check."""
        exists = driver.file_exists(self.path)
        return FileResult(
            success=True,
            content=None,
            path=self.path,
            exists=exists,
            op=self.operation,
            error_message=None,
            exception=None,
            start_time=self._time_ops.now(),
            end_time=self._time_ops.now(),
            request=self,
            metadata={}
        )

    def _execute_delete(self, driver: Any, logger: Optional[Any]) -> FileResult:
        """Execute file delete operation."""
        driver.delete_file(self.path)
        return FileResult(
            success=True,
            content=None,
            path=self.path,
            exists=False,
            op=self.operation,
            error_message=None,
            exception=None,
            start_time=self._time_ops.now(),
            end_time=self._time_ops.now(),
            request=self,
            metadata={}
        )

    def _execute_copy(self, driver: Any, logger: Optional[Any]) -> FileResult:
        """Execute file copy operation."""
        if not self.destination:
            raise ValueError("Destination is required for copy operation")

        driver.copy_file(self.path, self.destination)
        return FileResult(
            success=True,
            content=None,
            path=self.path,
            exists=True,
            op=self.operation,
            error_message=None,
            exception=None,
            start_time=self._time_ops.now(),
            end_time=self._time_ops.now(),
            request=self,
            metadata={'destination': self.destination}
        )

    def _execute_move(self, driver: Any, logger: Optional[Any]) -> FileResult:
        """Execute file move operation."""
        if not self.destination:
            raise ValueError("Destination is required for move operation")

        driver.move_file(self.path, self.destination)
        return FileResult(
            success=True,
            content=None,
            path=self.path,
            exists=True,
            op=self.operation,
            error_message=None,
            exception=None,
            start_time=self._time_ops.now(),
            end_time=self._time_ops.now(),
            request=self,
            metadata={'destination': self.destination}
        )

    def _execute_mkdir(self, driver: Any, logger: Optional[Any]) -> FileResult:
        """Execute directory creation."""
        driver.create_directory(self.path)
        return FileResult(
            success=True,
            content=None,
            path=self.path,
            exists=True,
            op=self.operation,
            error_message=None,
            exception=None,
            start_time=self._time_ops.now(),
            end_time=self._time_ops.now(),
            request=self,
            metadata={}
        )

    def _execute_rmtree(self, driver: Any, logger: Optional[Any]) -> FileResult:
        """Execute recursive directory removal."""
        driver.remove_directory(self.path)
        return FileResult(
            success=True,
            content=None,
            path=self.path,
            exists=False,
            op=self.operation,
            error_message=None,
            exception=None,
            start_time=self._time_ops.now(),
            end_time=self._time_ops.now(),
            request=self,
            metadata={}
        )

    def _execute_touch(self, driver: Any, logger: Optional[Any]) -> FileResult:
        """Execute file touch operation."""
        driver.touch_file(self.path)
        return FileResult(
            success=True,
            content=None,
            path=self.path,
            exists=True,
            op=self.operation,
            error_message=None,
            exception=None,
            start_time=self._time_ops.now(),
            end_time=self._time_ops.now(),
            request=self,
            metadata={}
        )

    def _execute_list(self, driver: Any, logger: Optional[Any]) -> FileResult:
        """Execute directory listing."""
        items = driver.list_directory(self.path)
        return FileResult(
            success=True,
            content=None,
            path=self.path,
            exists=True,
            op=self.operation,
            error_message=None,
            exception=None,
            start_time=self._time_ops.now(),
            end_time=self._time_ops.now(),
            request=self,
            metadata={'items': items}
        )

    def _handle_file_error(self, error: Exception, start_time: Any, logger: Optional[Any]) -> FileResult:
        """Handle file operation errors."""
        error_msg = str(error)

        if self.allow_failure:
            if logger:
                logger.warning(f"File operation failed (allowed): {error_msg}")
            return FileResult(
                success=True,  # Mark as success since failure is allowed
                content=None,
                path=self.path,
                exists=None,
                op=self.operation,
                error_message=error_msg,
                exception=error,
                start_time=start_time,
                end_time=self._time_ops.now(),
                request=self,
                metadata={}
            )
        if logger:
            logger.error(f"File operation failed: {error_msg}")
        raise error

"""Docker request implementation for container operations."""
from enum import Enum, auto
from typing import Any, Optional, Union

from src.operations.constants.operation_type import OperationType
from src.operations.constants.request_types import RequestType
from src.operations.interfaces.docker_interface import DockerDriverInterface
from src.operations.requests.base.base_request import OperationRequestFoundation
from src.operations.requests.composite.composite_request import CompositeRequest
from src.operations.results.result import OperationResult


class DockerOperationError(Exception):
    """Docker操作のエラー"""
    pass


class DockerOpType(Enum):
    """Docker operation types."""
    RUN = auto()
    STOP = auto()
    REMOVE = auto()
    EXEC = auto()
    LOGS = auto()
    INSPECT = auto()
    BUILD = auto()
    CP = auto()


class DockerRequest(OperationRequestFoundation):
    """Request for Docker container operations."""

    def __init__(self, op: DockerOpType, image: Optional[str], container: Optional[str],
                 command: Optional[Union[str, list[str]]], options: Optional[dict[str, Any]],
                 debug_tag, name, show_output: bool, dockerfile_text,
                 json_provider: Any):
        """Initialize Docker request.

        Args:
            op: Docker operation type
            image: Docker image name
            container: Container name
            command: Command to execute
            options: Additional options
            debug_tag: Debug tag for logging
            name: Request name
            show_output: Whether to show output
            dockerfile_text: Dockerfile content for build operations
            json_provider: JSON provider injected from main.py
        """
        super().__init__(name=name, debug_tag=debug_tag)
        self.op = op
        self.image = image
        self.container = container
        self.command = command
        if options is None:
            raise ValueError("Options must be explicitly provided (pass empty dict {} if no options)")
        self.options = options
        self.show_output = show_output
        self._executed = False
        self._result = None
        self.dockerfile_text = dockerfile_text

        # Infrastructure services injected from main.py
        self._json_provider = json_provider

    def _get_json_provider(self, driver):
        """Get JSON provider from injected dependency."""
        return self._json_provider

    @property
    def operation_type(self):
        """Get operation type."""
        return OperationType.DOCKER

    @property
    def request_type(self) -> RequestType:
        """Return the request type for type-safe identification."""
        return RequestType.DOCKER_REQUEST

    def execute_docker_operation(self, driver):
        """Execute the Docker operation request."""
        return super().execute_operation(driver)


    def _execute_core(self, driver: DockerDriverInterface, logger: Optional[Any]):
        """Core execution logic for Docker operations."""
        if logger:
            logger.debug(f"Executing Docker operation: {self.op} for container: {self.container}")

        # Get JSON provider for container status parsing
        json_provider = self._get_json_provider(driver)

        # Handle RUN operations with container state checking
        if self.op == DockerOpType.RUN and hasattr(driver, 'ps') and self.container:
            return self._handle_run_operation(driver, logger, json_provider)

        # Handle normal single request operations
        return self._execute_single_operation(driver, logger)

    def _handle_run_operation(self, driver: DockerDriverInterface, logger: Optional[Any], json_provider):
        """Handle RUN operation with container state checking."""
        # Check if container exists
        container_names = driver.ps(all=True, show_output=False, names_only=True)
        if self.container not in container_names:
            # If doesn't exist, just run
            return driver.run_container(self.image, name=self.container, options=self.options, show_output=self.show_output)

        # Check container status and handle accordingly
        return self._handle_existing_container(driver, logger, json_provider)

    def _handle_existing_container(self, driver: DockerDriverInterface, logger: Optional[Any], json_provider):
        """Handle existing container based on its current status."""
        inspect_result = driver.inspect(self.container, type_=None, show_output=False)
        try:
            inspect_data = json_provider.loads(inspect_result.stdout)
            if isinstance(inspect_data, list) and len(inspect_data) > 0:
                if "State" not in inspect_data[0]:
                    return driver.run_container(self.image, name=self.container, options=self.options, show_output=self.show_output)
                state = inspect_data[0]["State"]
                status = state["Status"]
                return self._process_container_status(driver, status, logger)
        except Exception as e:
            raise DockerOperationError(f"Docker container inspection failed: {e}") from e

    def _process_container_status(self, driver: DockerDriverInterface, status: str, logger: Optional[Any]):
        """Process container based on its current status."""
        if status == "running":
            # Already running, reuse
            return OperationResult(success=True, op=self.op, stdout="already running", stderr=None, returncode=0)

        if status in ("exited", "created", "dead", "paused"):
            # Stopped, remove first then run
            return self._remove_and_run_container(driver)

        # For other statuses, just run
        return driver.run_container(self.image, name=self.container, options=self.options, show_output=self.show_output)

    def _remove_and_run_container(self, driver: DockerDriverInterface):
        """Remove existing container and run a new one."""
        reqs = [
            DockerRequest(DockerOpType.REMOVE, image=None, container=self.container, command=None, options={}, debug_tag=None, name=None, show_output=False, dockerfile_text=None, json_provider=self.json_provider),
            DockerRequest(DockerOpType.RUN, image=self.image, container=self.container, command=None,
                         options=self.options, debug_tag=None, name=None, show_output=self.show_output, dockerfile_text=None, json_provider=self.json_provider)
        ]
        results = CompositeRequest.make_composite_request(reqs, debug_tag=None, name=None).execute_operation(driver, logger=None)
        if isinstance(results, list) and results:
            return results[-1]
        return results

    def _execute_single_operation(self, driver: DockerDriverInterface, logger: Optional[Any]):
        """Execute single Docker operation."""
        try:
            result = self._dispatch_operation(driver)
            return self._create_operation_result(result)
        except Exception as e:
            if logger:
                logger.error(f"Docker operation failed: {self.op} for container: {self.container}: {e}")
            return self._handle_operation_error(e)

    def _dispatch_operation(self, driver: DockerDriverInterface):
        """Dispatch to appropriate driver method based on operation type."""
        if self.op == DockerOpType.RUN:
            return driver.run_container(self.image, name=self.container, options=self.options, show_output=self.show_output)
        if self.op == DockerOpType.STOP:
            return driver.stop_container(self.container, show_output=self.show_output)
        if self.op == DockerOpType.REMOVE:
            if not self.options:
                raise ValueError("Options cannot be empty for REMOVE operation with 'f' flag check")
            force = 'f' in self.options and self.options['f'] is not None
            return driver.remove_container(self.container, force=force, show_output=self.show_output)
        if self.op == DockerOpType.INSPECT:
            return driver.inspect(self.container, type_=None, show_output=self.show_output)
        if self.op == DockerOpType.EXEC:
            return driver.exec_in_container(self.container, self.command, show_output=self.show_output)
        if self.op == DockerOpType.LOGS:
            return driver.get_logs(self.container, show_output=self.show_output)
        if self.op == DockerOpType.BUILD:
            return self._handle_build_operation(driver)
        if self.op == DockerOpType.CP:
            return self._handle_copy_operation(driver)
        raise ValueError(f"Unknown DockerOpType: {self.op}")

    def _handle_build_operation(self, driver: DockerDriverInterface):
        """Handle Docker build operation."""
        tag = self.options['t']
        return driver.build_docker_image(self.dockerfile_text, tag=tag, options=self.options, show_output=self.show_output)

    def _handle_copy_operation(self, driver: DockerDriverInterface):
        """Handle Docker copy operation."""
        local_path = self.options['local_path']
        remote_path = self.options['remote_path']
        to_container = self.options['to_container']

        if to_container:
            return driver.cp(local_path, remote_path, self.container, to_container=True, show_output=self.show_output)
        return driver.cp(remote_path, local_path, self.container, to_container=False, show_output=self.show_output)

    def _create_operation_result(self, result):
        """Create OperationResult from driver result."""
        return OperationResult(
            op=self.op,
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode
        )

    def _handle_operation_error(self, e: Exception):
        """Handle operation errors with proper error classification."""
        formatted_error = f"Docker operation failed: {e}"

        return OperationResult(success=False, op=self.op, stdout=None, stderr=formatted_error, returncode=None)

    def __repr__(self):
        """String representation."""
        return f"<DockerRequest op={self.op} container={self.container} command={self.command}>"

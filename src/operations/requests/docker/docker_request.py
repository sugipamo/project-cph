"""Docker request implementation for container operations."""
from enum import Enum, auto
from typing import Any, Optional, Union

from src.operations.constants.operation_type import OperationType
from src.operations.constants.request_types import RequestType
from src.operations.interfaces.docker_interface import DockerDriverInterface
from src.operations.requests.base.base_request import OperationRequestFoundation
from src.operations.requests.composite.composite_request import CompositeRequest
from src.operations.results.result import OperationResult


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

    def __init__(self, op: DockerOpType, image: Optional[str] = None, container: Optional[str] = None,
                 command: Optional[Union[str, list[str]]] = None, options: Optional[dict[str, Any]] = None,
                 debug_tag=None, name=None, show_output=True, dockerfile_text=None):
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
        """
        super().__init__(name=name, debug_tag=debug_tag)
        self.op = op
        self.image = image
        self.container = container
        self.command = command
        self.options = options or {}
        self.show_output = show_output
        self._executed = False
        self._result = None
        self.dockerfile_text = dockerfile_text

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


    def _execute_core(self, driver: DockerDriverInterface, logger: Optional[Any] = None):
        """Core execution logic for Docker operations."""
        if logger:
            logger.debug(f"Executing Docker operation: {self.op} for container: {self.container}")

        # Handle RUN operations with container state checking
        if self.op == DockerOpType.RUN and hasattr(driver, 'ps') and self.container:
            return self._handle_run_operation(driver, logger)

        # Handle normal single request operations
        return self._execute_single_operation(driver, logger)

    def _handle_run_operation(self, driver: DockerDriverInterface, logger: Optional[Any] = None):
        """Handle RUN operation with container state checking."""
        # Check if container exists
        container_names = driver.ps(all=True, show_output=False, names_only=True)
        if self.container not in container_names:
            # If doesn't exist, just run
            return driver.run_container(self.image, self.container, self.options, show_output=self.show_output)

        # Check container status and handle accordingly
        return self._handle_existing_container(driver, logger)

    def _handle_existing_container(self, driver: DockerDriverInterface, logger: Optional[Any] = None):
        """Handle existing container based on its current status."""
        inspect_result = driver.inspect(self.container, show_output=False)
        import json
        try:
            inspect_data = json.loads(inspect_result.stdout)
            if isinstance(inspect_data, list) and len(inspect_data) > 0:
                if "State" not in inspect_data[0]:
                    return driver.run_container(self.image, self.container, self.options, show_output=self.show_output)
                state = inspect_data[0]["State"]
                status = state["Status"]
                return self._process_container_status(driver, status, logger)
        except Exception:
            # If inspect fails, just run
            return driver.run_container(self.image, self.container, self.options, show_output=self.show_output)

    def _process_container_status(self, driver: DockerDriverInterface, status: str, logger: Optional[Any] = None):
        """Process container based on its current status."""
        if status == "running":
            # Already running, reuse
            return OperationResult(success=True, op=self.op, stdout="already running", stderr=None, returncode=0)

        if status in ("exited", "created", "dead", "paused"):
            # Stopped, remove first then run
            return self._remove_and_run_container(driver)

        # For other statuses, just run
        return driver.run_container(self.image, self.container, self.options, show_output=self.show_output)

    def _remove_and_run_container(self, driver: DockerDriverInterface):
        """Remove existing container and run a new one."""
        reqs = [
            DockerRequest(DockerOpType.REMOVE, container=self.container, show_output=False),
            DockerRequest(DockerOpType.RUN, image=self.image, container=self.container,
                         options=self.options, show_output=self.show_output)
        ]
        results = CompositeRequest.make_composite_request(reqs).execute_operation(driver)
        if isinstance(results, list) and results:
            return results[-1]
        return results

    def _execute_single_operation(self, driver: DockerDriverInterface, logger: Optional[Any] = None):
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
            return driver.run_container(self.image, self.container, self.options, show_output=self.show_output)
        if self.op == DockerOpType.STOP:
            return driver.stop_container(self.container, show_output=self.show_output)
        if self.op == DockerOpType.REMOVE:
            force = ('f' in self.options and self.options['f'] is not None) if self.options else False
            return driver.remove_container(self.container, force=force, show_output=self.show_output)
        if self.op == DockerOpType.INSPECT:
            return driver.inspect(self.container, show_output=self.show_output)
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
            stdout=getattr(result, 'stdout', None),
            stderr=getattr(result, 'stderr', None),
            returncode=getattr(result, 'returncode', None)
        )

    def _handle_operation_error(self, e: Exception):
        """Handle operation errors with proper error classification."""
        formatted_error = f"Docker operation failed: {e}"

        return OperationResult(success=False, op=self.op, stdout=None, stderr=formatted_error, returncode=None)

    def __repr__(self):
        """String representation."""
        return f"<DockerRequest op={self.op} container={self.container} command={self.command}>"

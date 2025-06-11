"""Docker request implementation for container operations."""
from enum import Enum, auto
from typing import Any, Optional, Union

from src.domain.constants.operation_type import OperationType
from src.domain.interfaces.docker_interface import DockerDriverInterface
from src.domain.requests.base.base_request import BaseRequest
from src.domain.requests.composite.composite_request import CompositeRequest
from src.domain.results.result import OperationResult


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


class DockerRequest(BaseRequest):
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

    def execute(self, driver):
        """Execute the Docker request."""
        return super().execute(driver)

    def _execute_core(self, driver: DockerDriverInterface):
        """Core execution logic for Docker operations."""
        # Pre-processing for RUN operations
        if self.op == DockerOpType.RUN and hasattr(driver, 'ps') and self.container:
                # Check if container exists
                container_names = driver.ps(all=True, show_output=False, names_only=True)
                if self.container not in container_names:
                    # If doesn't exist, just run
                    return driver.run_container(self.image, self.container, self.options, show_output=self.show_output)

                # Check container status
                inspect_result = driver.inspect(self.container, show_output=False)
                import json
                try:
                    inspect_data = json.loads(inspect_result.stdout)
                    if isinstance(inspect_data, list) and len(inspect_data) > 0:
                        state = inspect_data[0].get("State", {})
                        status = state.get("Status", "")
                        reqs = []
                        if status == "running":
                            # Already running, reuse
                            return OperationResult(success=True, op=self.op, stdout="already running", stderr=None, returncode=0)
                        if status in ("exited", "created", "dead", "paused"):
                            # Stopped, remove first
                            reqs.append(DockerRequest(DockerOpType.REMOVE, container=self.container, show_output=False))
                        # Run container
                        reqs.append(DockerRequest(DockerOpType.RUN, image=self.image, container=self.container, options=self.options, show_output=self.show_output))
                        results = CompositeRequest.make_composite_request(reqs).execute(driver)
                        if isinstance(results, list) and results:
                            return results[-1]
                        return results
                except Exception:
                    # If inspect fails, just run
                    return driver.run_container(self.image, self.container, self.options, show_output=self.show_output)

        # Normal single request operations
        try:
            if self.op == DockerOpType.RUN:
                result = driver.run_container(self.image, self.container, self.options, show_output=self.show_output)
            elif self.op == DockerOpType.STOP:
                result = driver.stop_container(self.container, show_output=self.show_output)
            elif self.op == DockerOpType.REMOVE:
                force = self.options.get('f') is not None if self.options else False
                result = driver.remove_container(self.container, force=force, show_output=self.show_output)
            elif self.op == DockerOpType.INSPECT:
                result = driver.inspect(self.container, show_output=self.show_output)
            elif self.op == DockerOpType.EXEC:
                result = driver.exec_in_container(self.container, self.command, show_output=self.show_output)
            elif self.op == DockerOpType.LOGS:
                result = driver.get_logs(self.container, show_output=self.show_output)
            elif self.op == DockerOpType.BUILD:
                # BUILD operation
                tag = self.options.get('t')
                result = driver.build(self.dockerfile_text, tag=tag, options=self.options, show_output=self.show_output)
            elif self.op == DockerOpType.CP:
                # CP operation
                local_path = self.options.get('local_path')
                remote_path = self.options.get('remote_path')
                to_container = self.options.get('to_container', True)
                if to_container:
                    result = driver.cp(local_path, remote_path, self.container, to_container=True, show_output=self.show_output)
                else:
                    result = driver.cp(remote_path, local_path, self.container, to_container=False, show_output=self.show_output)
            else:
                raise ValueError(f"Unknown DockerOpType: {self.op}")

            return OperationResult(
                op=self.op,
                stdout=getattr(result, 'stdout', None),
                stderr=getattr(result, 'stderr', None),
                returncode=getattr(result, 'returncode', None)
            )
        except Exception as e:
            from src.domain.exceptions.error_codes import ErrorSuggestion, classify_error
            error_code = classify_error(e, "docker operation")
            suggestion = ErrorSuggestion.get_suggestion(error_code)
            formatted_error = f"Docker operation failed: {e}\nError Code: {error_code.value}\nSuggestion: {suggestion}"

            return OperationResult(success=False, op=self.op, stdout=None, stderr=formatted_error, returncode=None)

    def __repr__(self):
        """String representation."""
        return f"<DockerRequest op={self.op} container={self.container} command={self.command}>"

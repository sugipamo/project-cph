"""Mock docker driver for testing."""
from typing import Any, Optional

from src.domain.results.docker_result import DockerResult
from src.infrastructure.drivers.docker.docker_driver import DockerDriver


class MockDockerDriver(DockerDriver):
    """Mock implementation of docker driver for testing."""

    def __init__(self):
        """Initialize mock docker driver."""
        self._operations_executed = []
        self._container_states = {}  # container_name -> state
        self._images = set()
        self._default_result = DockerResult(
            stdout="mock docker output",
            stderr="",
            returncode=0
        )

    def run_container(self, image: str, container_name: Optional[str] = None,
                     options: Optional[dict[str, Any]] = None,
                     show_output: bool = True) -> DockerResult:
        """Run a container (mocked).

        Args:
            image: Docker image name
            container_name: Container name
            options: Additional options
            show_output: Whether to show output

        Returns:
            Mocked docker result
        """
        self._operations_executed.append({
            'operation': 'run',
            'image': image,
            'container': container_name,
            'options': options,
            'show_output': show_output
        })

        if container_name:
            self._container_states[container_name] = 'running'

        return DockerResult(
            stdout=f"Mock: Started container {container_name or 'unnamed'} from {image}",
            stderr="",
            returncode=0
        )

    def stop_container(self, container_name: str, show_output: bool = True) -> DockerResult:
        """Stop a container (mocked).

        Args:
            container_name: Container name
            show_output: Whether to show output

        Returns:
            Mocked docker result
        """
        self._operations_executed.append({
            'operation': 'stop',
            'container': container_name,
            'show_output': show_output
        })

        self._container_states[container_name] = 'exited'

        return DockerResult(
            stdout=f"Mock: Stopped container {container_name}",
            stderr="",
            returncode=0
        )

    def remove_container(self, container_name: str, force: bool = False,
                        show_output: bool = True) -> DockerResult:
        """Remove a container (mocked).

        Args:
            container_name: Container name
            force: Force removal
            show_output: Whether to show output

        Returns:
            Mocked docker result
        """
        self._operations_executed.append({
            'operation': 'remove',
            'container': container_name,
            'force': force,
            'show_output': show_output
        })

        if container_name in self._container_states:
            del self._container_states[container_name]

        return DockerResult(
            stdout=f"Mock: Removed container {container_name}",
            stderr="",
            returncode=0
        )

    def exec_in_container(self, container_name: str, command: str,
                         show_output: bool = True) -> DockerResult:
        """Execute command in container (mocked).

        Args:
            container_name: Container name
            command: Command to execute
            show_output: Whether to show output

        Returns:
            Mocked docker result
        """
        self._operations_executed.append({
            'operation': 'exec',
            'container': container_name,
            'command': command,
            'show_output': show_output
        })

        return DockerResult(
            stdout=f"Mock: Executed '{command}' in {container_name}",
            stderr="",
            returncode=0
        )

    def inspect(self, container_name: str, show_output: bool = True) -> DockerResult:
        """Inspect container (mocked).

        Args:
            container_name: Container name
            show_output: Whether to show output

        Returns:
            Mocked docker result with JSON inspection data
        """
        self._operations_executed.append({
            'operation': 'inspect',
            'container': container_name,
            'show_output': show_output
        })

        state = self._container_states.get(container_name, 'not_found')
        mock_inspect_data = [{
            "State": {
                "Status": state,
                "Running": state == 'running',
                "ExitCode": 0 if state == 'running' else 1
            },
            "Name": f"/{container_name}",
            "Config": {
                "Image": "mock_image:latest"
            }
        }]

        import json
        return DockerResult(
            stdout=json.dumps(mock_inspect_data),
            stderr="",
            returncode=0
        )

    def ps(self, all: bool = False, show_output: bool = True,
           names_only: bool = False) -> DockerResult:
        """List containers (mocked).

        Args:
            all: Include stopped containers
            show_output: Whether to show output
            names_only: Return only names

        Returns:
            Mocked docker result
        """
        self._operations_executed.append({
            'operation': 'ps',
            'all': all,
            'show_output': show_output,
            'names_only': names_only
        })

        if names_only:
            containers = list(self._container_states.keys()) if all else [
                name for name, state in self._container_states.items()
                if state == 'running'
            ]
            return containers

        # Return mock container list
        return DockerResult(
            stdout="CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    NAMES\n" +
                   "mock_id        mock      mock      mock      mock      mock_container",
            stderr="",
            returncode=0
        )

    def get_executed_operations(self) -> list[dict]:
        """Get list of executed operations.

        Returns:
            List of operation details
        """
        return self._operations_executed.copy()

    def clear_history(self) -> None:
        """Clear operation execution history."""
        self._operations_executed.clear()
        self._container_states.clear()

    def set_container_state(self, container_name: str, state: str) -> None:
        """Set container state for testing.

        Args:
            container_name: Container name
            state: Container state ('running', 'exited', etc.)
        """
        self._container_states[container_name] = state

    # Abstract methods from DockerDriver base class
    def build(self, tag: Optional[str] = None, options: Optional[dict[str, Any]] = None, show_output: bool = True, dockerfile_text: Optional[str] = None):
        """Build Docker image (mocked)."""
        self._operations_executed.append({
            'operation': 'build',
            'tag': tag,
            'options': options,
            'show_output': show_output,
            'dockerfile_text': dockerfile_text
        })
        return self._default_result

    def image_ls(self):
        """List Docker images (mocked)."""
        self._operations_executed.append({'operation': 'image_ls'})
        return self._default_result

    def image_rm(self, image: str):
        """Remove Docker image (mocked)."""
        self._operations_executed.append({
            'operation': 'image_rm',
            'image': image
        })
        return self._default_result

    def cp(self, src: str, dst: str, container: str, to_container: bool = True):
        """Copy files to/from container (mocked)."""
        self._operations_executed.append({
            'operation': 'cp',
            'src': src,
            'dst': dst,
            'container': container,
            'to_container': to_container
        })
        return self._default_result

    def get_logs(self, name: str, show_output: bool = True):
        """Get container logs (mocked)."""
        self._operations_executed.append({
            'operation': 'logs',
            'container': name,
            'show_output': show_output
        })
        return DockerResult(
            stdout=f"Mock logs for {name}",
            stderr="",
            returncode=0
        )

    def execute_command(self, request: Any) -> Any:
        """Execute a Docker request (mocked)."""
        self._operations_executed.append({
            'operation': 'execute',
            'request': str(request)
        })
        return self._default_result

    def validate(self, request: Any) -> bool:
        """Validate if this driver can handle the request (mocked)."""
        return True

"""Environment inspection for Docker containers and file system state
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from unittest.mock import MagicMock

from src.domain.requests.file.file_op_type import FileOpType
from src.domain.requests.file.file_request import FileRequest


class ResourceType(Enum):
    """Resource types that can be inspected"""
    DOCKER_CONTAINER = "docker_container"
    DOCKER_IMAGE = "docker_image"
    DIRECTORY = "directory"
    FILE = "file"


@dataclass
class ResourceRequirement:
    """Represents a resource requirement for workflow execution"""
    resource_type: ResourceType
    identifier: str  # container name, image name, file path, etc.
    required_state: str  # "running", "exists", "available", etc.
    context_info: Optional[dict] = None


@dataclass
class ResourceStatus:
    """Current status of a resource"""
    resource_type: ResourceType
    identifier: str
    current_state: str  # "running", "stopped", "missing", etc.
    exists: bool
    needs_preparation: bool
    preparation_actions: list[str]  # Actions needed to reach required state


class EnvironmentInspector:
    """Inspects current environment state against workflow requirements"""

    def __init__(self, operations):
        """Initialize with operations container for Docker and file operations

        Args:
            operations: Operations container providing docker_driver and file_driver
        """
        self.operations = operations
        self._docker_driver = operations.resolve("docker_driver")
        self._file_driver = operations.resolve("file_driver")

    def inspect_docker_containers(self, required_containers: list[str]) -> dict[str, ResourceStatus]:
        """Inspect Docker container states

        Args:
            required_containers: List of container names that should be running

        Returns:
            Dict mapping container name to ResourceStatus
        """
        results = {}

        # Get all containers (including stopped ones)
        # Use direct driver method instead of DockerRequest for ps operation
        try:
            container_names = self._docker_driver.ps(all=True, names_only=False, show_output=False)
            ps_result = MagicMock()
            ps_result.success = True
            # Convert container names to container info format
            ps_result.container_info = []
            for name in container_names:
                # Get inspect info for each container
                inspect_result = self._docker_driver.inspect(name.lstrip('/'), show_output=False)
                if inspect_result:
                    ps_result.container_info.append({
                        "name": name,
                        "state": {"status": inspect_result.get("State", {}).get("Status", "unknown")}
                    })
        except Exception:
            # Fallback to mock result if driver method fails
            ps_result = MagicMock()
            ps_result.success = True
            ps_result.container_info = []

        # Parse container information
        running_containers = set()
        stopped_containers = set()

        if ps_result.success and ps_result.container_info:
            for container_info in ps_result.container_info:
                name = container_info.get("name", "").lstrip("/")
                state = container_info.get("state", {}).get("status", "")

                if state.lower() == "running":
                    running_containers.add(name)
                else:
                    stopped_containers.add(name)

        # Check each required container
        for container_name in required_containers:
            if container_name in running_containers:
                # Container is running - no preparation needed
                status = ResourceStatus(
                    resource_type=ResourceType.DOCKER_CONTAINER,
                    identifier=container_name,
                    current_state="running",
                    exists=True,
                    needs_preparation=False,
                    preparation_actions=[]
                )
            elif container_name in stopped_containers:
                # Container exists but stopped - needs restart
                status = ResourceStatus(
                    resource_type=ResourceType.DOCKER_CONTAINER,
                    identifier=container_name,
                    current_state="stopped",
                    exists=True,
                    needs_preparation=True,
                    preparation_actions=["remove_stopped_container", "run_new_container"]
                )
            else:
                # Container doesn't exist - needs creation
                status = ResourceStatus(
                    resource_type=ResourceType.DOCKER_CONTAINER,
                    identifier=container_name,
                    current_state="missing",
                    exists=False,
                    needs_preparation=True,
                    preparation_actions=["run_new_container"]
                )

            results[container_name] = status

        return results

    def inspect_directories(self, required_directories: list[str]) -> dict[str, ResourceStatus]:
        """Inspect directory existence

        Args:
            required_directories: List of directory paths that should exist

        Returns:
            Dict mapping directory path to ResourceStatus
        """
        results = {}

        for dir_path in required_directories:
            # Check if directory exists
            exists_request = FileRequest(op=FileOpType.EXISTS, path=dir_path)
            exists_result = self._file_driver.execute(exists_request)

            if exists_result.success and exists_result.exists:
                # Directory exists - no preparation needed
                status = ResourceStatus(
                    resource_type=ResourceType.DIRECTORY,
                    identifier=dir_path,
                    current_state="exists",
                    exists=True,
                    needs_preparation=False,
                    preparation_actions=[]
                )
            else:
                # Directory doesn't exist - needs creation
                status = ResourceStatus(
                    resource_type=ResourceType.DIRECTORY,
                    identifier=dir_path,
                    current_state="missing",
                    exists=False,
                    needs_preparation=True,
                    preparation_actions=["create_directory"]
                )

            results[dir_path] = status

        return results

    def inspect_docker_images(self, required_images: list[str]) -> dict[str, ResourceStatus]:
        """Inspect Docker image existence

        Args:
            required_images: List of image names that should exist

        Returns:
            Dict mapping image name to ResourceStatus
        """
        results = {}

        # Get all available images
        try:
            image_ls_result = self._docker_driver.image_ls(show_output=False)
            available_images = set()

            if hasattr(image_ls_result, 'stdout') and image_ls_result.stdout:
                # Parse docker image ls output to extract image names
                lines = image_ls_result.stdout.strip().split('\n')
                for line in lines[1:]:  # Skip header line
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            # Format: REPOSITORY TAG
                            repo = parts[0]
                            tag = parts[1]
                            if tag != '<none>':
                                available_images.add(f"{repo}:{tag}")
                                if tag == 'latest':
                                    available_images.add(repo)  # Also add without :latest
                            else:
                                available_images.add(repo)
        except Exception:
            # Fallback - assume no images available
            available_images = set()

        # Check each required image
        for image_name in required_images:
            # Normalize image name (add :latest if no tag specified)
            normalized_name = image_name if ':' in image_name else f"{image_name}:latest"

            if image_name in available_images or normalized_name in available_images:
                # Image exists - no preparation needed
                status = ResourceStatus(
                    resource_type=ResourceType.DOCKER_IMAGE,
                    identifier=image_name,
                    current_state="available",
                    exists=True,
                    needs_preparation=False,
                    preparation_actions=[]
                )
            else:
                # Image doesn't exist - needs building or pulling
                status = ResourceStatus(
                    resource_type=ResourceType.DOCKER_IMAGE,
                    identifier=image_name,
                    current_state="missing",
                    exists=False,
                    needs_preparation=True,
                    preparation_actions=["build_or_pull_image"]
                )

            results[image_name] = status

        return results

    def extract_requirements_from_workflow_tasks(self, workflow_tasks: list) -> list[ResourceRequirement]:
        """Extract resource requirements from workflow tasks

        Args:
            workflow_tasks: List of workflow task objects or dicts

        Returns:
            List of ResourceRequirement objects
        """
        requirements = []

        for task in workflow_tasks:
            # Handle different task formats (dict, object, etc.)
            task_data = task if isinstance(task, dict) else getattr(task, '__dict__', {})

            # Extract Docker exec/cp requirements
            if self._is_docker_exec_task(task_data):
                container_name = self._extract_container_name_from_exec(task_data)
                if container_name:
                    requirements.append(ResourceRequirement(
                        resource_type=ResourceType.DOCKER_CONTAINER,
                        identifier=container_name,
                        required_state="running",
                        context_info={"task_type": "docker_exec"}
                    ))

            elif self._is_docker_cp_task(task_data):
                container_name = self._extract_container_name_from_cp(task_data)
                dest_dir = self._extract_destination_directory_from_cp(task_data)

                if container_name:
                    requirements.append(ResourceRequirement(
                        resource_type=ResourceType.DOCKER_CONTAINER,
                        identifier=container_name,
                        required_state="running",
                        context_info={"task_type": "docker_cp"}
                    ))

                if dest_dir:
                    requirements.append(ResourceRequirement(
                        resource_type=ResourceType.DIRECTORY,
                        identifier=dest_dir,
                        required_state="exists",
                        context_info={"task_type": "docker_cp_destination"}
                    ))

            # Extract Docker image requirements
            elif self._is_docker_run_task(task_data):
                image_name = self._extract_image_name_from_run(task_data)
                if image_name:
                    requirements.append(ResourceRequirement(
                        resource_type=ResourceType.DOCKER_IMAGE,
                        identifier=image_name,
                        required_state="available",
                        context_info={"task_type": "docker_run"}
                    ))

        return requirements

    def _is_docker_exec_task(self, task_data: dict) -> bool:
        """Check if task is a docker exec task"""
        # Check request type first (more reliable)
        request_type = task_data.get('request_type', '')
        if request_type == 'docker' and task_data.get('operation') == 'exec':
            return True

        # Fallback: Look for docker exec patterns in command
        if isinstance(task_data.get('command'), str):
            return 'docker exec' in task_data['command']

        return False

    def _is_docker_cp_task(self, task_data: dict) -> bool:
        """Check if task is a docker cp task"""
        # Check request type first (more reliable)
        request_type = task_data.get('request_type', '')
        if request_type == 'docker' and task_data.get('operation') == 'cp':
            return True

        # Fallback: Look for docker cp patterns in command
        if isinstance(task_data.get('command'), str):
            return 'docker cp' in task_data['command']

        return False

    def _extract_container_name_from_exec(self, task_data: dict) -> Optional[str]:
        """Extract container name from docker exec task"""
        command = task_data.get('command', '')
        if isinstance(command, str) and 'docker exec' in command:
            # Parse: docker exec <container_name> <command>
            parts = command.split()
            if len(parts) >= 3 and parts[0] == 'docker' and parts[1] == 'exec':
                return parts[2]

        # Check direct container specification
        return task_data.get('container_name')

    def _extract_container_name_from_cp(self, task_data: dict) -> Optional[str]:
        """Extract container name from docker cp task"""
        command = task_data.get('command', '')
        if isinstance(command, str) and 'docker cp' in command:
            # Parse: docker cp <src> <container>:<dest> or docker cp <container>:<src> <dest>
            parts = command.split()
            if len(parts) >= 4 and parts[0] == 'docker' and parts[1] == 'cp':
                # Check both source and destination for container:path format
                for part in parts[2:4]:
                    if ':' in part:
                        return part.split(':')[0]

        # Check direct container specification
        return task_data.get('container_name')

    def _extract_destination_directory_from_cp(self, task_data: dict) -> Optional[str]:
        """Extract destination directory from docker cp task"""
        command = task_data.get('command', '')
        if isinstance(command, str) and 'docker cp' in command:
            # Parse: docker cp <src> <container>:<dest> or docker cp <container>:<src> <dest>
            parts = command.split()
            if len(parts) >= 4 and parts[0] == 'docker' and parts[1] == 'cp':
                # Check if copying TO container (second path has container:path format)
                if ':' in parts[3]:
                    dest_path = parts[3].split(':', 1)[1]
                    # Return parent directory
                    return '/'.join(dest_path.split('/')[:-1]) if '/' in dest_path else '/'
                # Copying FROM container to local path
                return '/'.join(parts[3].split('/')[:-1]) if '/' in parts[3] else '.'

        # Check direct destination specification
        return task_data.get('destination_directory')

    def _is_docker_run_task(self, task_data: dict) -> bool:
        """Check if task is a docker run task"""
        # Check request type first (more reliable)
        request_type = task_data.get('request_type', '')
        if request_type == 'docker' and task_data.get('operation') == 'run':
            return True

        # Fallback: Look for docker run patterns in command
        if isinstance(task_data.get('command'), str):
            return 'docker run' in task_data['command']

        return False

    def _extract_image_name_from_run(self, task_data: dict) -> Optional[str]:
        """Extract image name from docker run task"""
        # Check direct image specification
        if 'image' in task_data:
            return task_data['image']

        command = task_data.get('command', '')
        if isinstance(command, str) and 'docker run' in command:
            # Parse: docker run [options] image [command]
            parts = command.split()
            if len(parts) >= 3 and parts[0] == 'docker' and parts[1] == 'run':
                # Find the image name (first argument that doesn't start with -)
                for i in range(2, len(parts)):
                    if not parts[i].startswith('-'):
                        # Skip option values
                        if i > 2 and parts[i-1].startswith('-') and not parts[i-1].startswith('--'):
                            continue
                        return parts[i]

        return None

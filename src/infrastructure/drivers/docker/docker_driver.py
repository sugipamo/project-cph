"""Consolidated Docker driver implementation with optional tracking."""
import contextlib
import hashlib
import shlex
import time
from abc import abstractmethod
from typing import Any, Optional, Union

from src.infrastructure.drivers.docker.utils.docker_naming import (
    build_docker_build_command,
    build_docker_remove_command,
    build_docker_run_command,
    build_docker_stop_command,
    parse_container_names,
)
from src.infrastructure.drivers.file.local_file_driver import LocalFileDriver
from src.infrastructure.drivers.generic.base_driver import ExecutionDriverInterface
from src.infrastructure.di_container import DIKey
from src.operations.requests.shell_request import ShellRequest
from src.operations.results.__init__ import LocalShellDriver


class DockerDriver(ExecutionDriverInterface):
    """Consolidated Docker driver with optional SQLite tracking."""

    def __init__(self, file_driver: LocalFileDriver, di_container: Optional[Any] = None):
        """Initialize Docker driver.
        
        Args:
            file_driver: File driver for filesystem operations
            di_container: Optional DI container for enabling tracking features
        """
        super().__init__()
        self.shell_driver = LocalShellDriver(file_driver)
        self.di_container = di_container
        self._container_repo = None
        self._image_repo = None
        self._tracking_enabled = di_container is not None

    @property
    def container_repo(self):
        """Lazy load container repository."""
        if self._container_repo is None and self.di_container:
            self._container_repo = self.di_container.resolve(DIKey.DOCKER_CONTAINER_REPOSITORY)
        return self._container_repo

    @property
    def image_repo(self):
        """Lazy load image repository."""
        if self._image_repo is None and self.di_container:
            self._image_repo = self.di_container.resolve(DIKey.DOCKER_IMAGE_REPOSITORY)
        return self._image_repo

    def execute_command(self, request: Any) -> Any:
        """Execute a Docker request."""
        # This method is for compatibility with ExecutionDriverInterface
        # Actual execution happens in specific methods
        pass

    def validate(self, request: Any) -> bool:
        """Validate if this driver can handle the request."""
        return True

    def initialize(self) -> None:
        """Initialize the driver."""
        pass

    def cleanup(self) -> None:
        """Clean up resources."""
        pass

    def run_container(self, image: str, name: Optional[str], options: dict[str, Any], show_output: bool = True):
        """Run container with optional tracking."""
        cmd = build_docker_run_command(image, name, options)
        req = ShellRequest(cmd, cwd=".", env={}, inputdata="", timeout=300, 
                          debug_tag="docker_run", name="docker_run_request", 
                          show_output=show_output, allow_failure=False)
        result = req.execute_operation(driver=self.shell_driver, logger=None)

        # Track if enabled
        if self._tracking_enabled and result.success and name:
            with contextlib.suppress(Exception):
                self.container_repo.update_container_status(name, "running", "started_at")
                self.container_repo.add_lifecycle_event(
                    name, "started", {"image": image, "options": options}
                )
                # Update container ID if available
                if result.stdout:
                    container_id = result.stdout.strip()
                    if len(container_id) == 64:  # Docker container ID length
                        self.container_repo.update_container_id(name, container_id)

        return result

    def stop_container(self, name: str, timeout: int = 10, show_output: bool = True):
        """Stop container with optional tracking."""
        cmd = build_docker_stop_command(name, timeout)
        req = ShellRequest(cmd, cwd=".", env={}, inputdata="", timeout=300,
                          debug_tag="docker_stop", name="docker_stop_request",
                          show_output=show_output, allow_failure=False)
        result = req.execute_operation(driver=self.shell_driver, logger=None)

        # Track if enabled
        if self._tracking_enabled and result.success:
            with contextlib.suppress(Exception):
                self.container_repo.update_container_status(name, "stopped", "stopped_at")
                self.container_repo.add_lifecycle_event(name, "stopped", None)

        return result

    def remove_container(self, name: str, force: bool = False, show_output: bool = True):
        """Remove container with optional tracking."""
        cmd = build_docker_remove_command(name, force=force)
        req = ShellRequest(cmd, cwd=".", env={}, inputdata="", timeout=300,
                          debug_tag="docker_rm", name="docker_rm_request",
                          show_output=show_output, allow_failure=False)
        result = req.execute_operation(driver=self.shell_driver, logger=None)

        # Track if enabled
        if self._tracking_enabled and result.success:
            with contextlib.suppress(Exception):
                self.container_repo.mark_container_removed(name)
                self.container_repo.add_lifecycle_event(name, "removed", {"force": force})

        return result

    def exec_in_container(self, name: str, command: Union[str, list[str]], show_output: bool = True):
        """Execute command in container."""
        if isinstance(command, list):
            cmd_str = " ".join(shlex.quote(arg) for arg in command)
        else:
            cmd_str = command
        
        cmd = f"docker exec {name} {cmd_str}"
        req = ShellRequest(cmd, cwd=".", env={}, inputdata="", timeout=300,
                          debug_tag="docker_exec", name="docker_exec_request",
                          show_output=show_output, allow_failure=False)
        return req.execute_operation(driver=self.shell_driver, logger=None)

    def get_logs(self, name: str, show_output: bool = True):
        """Get container logs."""
        cmd = f"docker logs {name}"
        req = ShellRequest(cmd, cwd=".", env={}, inputdata="", timeout=300,
                          debug_tag="docker_logs", name="docker_logs_request",
                          show_output=show_output, allow_failure=False)
        return req.execute_operation(driver=self.shell_driver, logger=None)

    def build_docker_image(self, dockerfile_text: str, tag: Optional[str], 
                          options: dict[str, Any], show_output: bool = True):
        """Build Docker image with optional tracking."""
        # Calculate Dockerfile hash
        dockerfile_hash = hashlib.sha256(dockerfile_text.encode('utf-8')).hexdigest()[:12]

        # Track build start if enabled
        if self._tracking_enabled and tag:
            with contextlib.suppress(Exception):
                self.image_repo.create_or_update_image(
                    name=tag, tag="latest", dockerfile_hash=dockerfile_hash,
                    build_command=f"docker build -t {tag}",
                    build_status="building"
                )

        # Create temp dockerfile and build
        start_time = time.time()
        cmd = build_docker_build_command(dockerfile_text, tag, options)
        req = ShellRequest(cmd, cwd=".", env={}, inputdata="", timeout=600,
                          debug_tag="docker_build", name="docker_build_request",
                          show_output=show_output, allow_failure=False)
        result = req.execute_operation(driver=self.shell_driver, logger=None)
        build_time_ms = int((time.time() - start_time) * 1000)

        # Track build result if enabled
        if self._tracking_enabled and tag:
            with contextlib.suppress(Exception):
                if result.success:
                    # Try to extract image ID
                    image_id = None
                    if result.stdout:
                        for line in result.stdout.split('\n'):
                            if 'Successfully built' in line:
                                parts = line.split()
                                if len(parts) > 2:
                                    image_id = parts[-1]
                                    break

                    self.image_repo.update_image_build_result(
                        name=tag, tag="latest", image_id=image_id,
                        build_status="success", build_time_ms=build_time_ms,
                        size_bytes=None
                    )
                else:
                    self.image_repo.update_image_build_result(
                        name=tag, tag="latest", image_id=None,
                        build_status="failed", build_time_ms=build_time_ms,
                        size_bytes=None
                    )

        return result

    def image_ls(self, show_output: bool = True):
        """List Docker images."""
        cmd = "docker images"
        req = ShellRequest(cmd, cwd=".", env={}, inputdata="", timeout=300,
                          debug_tag="docker_images", name="docker_images_request",
                          show_output=show_output, allow_failure=False)
        return req.execute_operation(driver=self.shell_driver, logger=None)

    def image_rm(self, image: str, show_output: bool = True):
        """Remove Docker image with optional tracking."""
        cmd = f"docker rmi {image}"
        req = ShellRequest(cmd, cwd=".", env={}, inputdata="", timeout=300,
                          debug_tag="docker_rmi", name="docker_rmi_request",
                          show_output=show_output, allow_failure=False)
        result = req.execute_operation(driver=self.shell_driver, logger=None)

        # Track if enabled
        if self._tracking_enabled and result.success:
            with contextlib.suppress(Exception):
                # Parse image name and tag
                if ':' in image:
                    name, tag = image.split(':', 1)
                else:
                    name, tag = image, "latest"
                self.image_repo.delete_image(name, tag)

        return result

    def ps(self, all: bool = False, show_output: bool = True, names_only: bool = False):
        """List Docker containers."""
        cmd = "docker ps"
        if all:
            cmd += " -a"
        if names_only:
            cmd += " --format '{{.Names}}'"
            
        req = ShellRequest(cmd, cwd=".", env={}, inputdata="", timeout=300,
                          debug_tag="docker_ps", name="docker_ps_request",
                          show_output=show_output, allow_failure=False)
        result = req.execute_operation(driver=self.shell_driver, logger=None)

        if names_only and result.success:
            result.names = parse_container_names(result.stdout)

        return result

    def inspect(self, target: str, type_: Optional[str] = None):
        """Inspect Docker object."""
        cmd = f"docker inspect {target}"
        if type_:
            cmd = f"docker inspect --type={type_} {target}"
            
        req = ShellRequest(cmd, cwd=".", env={}, inputdata="", timeout=300,
                          debug_tag="docker_inspect", name="docker_inspect_request",
                          show_output=False, allow_failure=False)
        return req.execute_operation(driver=self.shell_driver, logger=None)

    def cp(self, src: str, dst: str, container: str, to_container: bool = True):
        """Copy files to/from container."""
        if to_container:
            cmd = f"docker cp {src} {container}:{dst}"
        else:
            cmd = f"docker cp {container}:{src} {dst}"
            
        req = ShellRequest(cmd, cwd=".", env={}, inputdata="", timeout=300,
                          debug_tag="docker_cp", name="docker_cp_request",
                          show_output=True, allow_failure=False)
        return req.execute_operation(driver=self.shell_driver, logger=None)
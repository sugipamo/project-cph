"""Consolidated Docker driver with integrated command building."""
import contextlib
import re
import shlex
from typing import Any, Dict, List, Optional, Union

from src.infrastructure.di_container import DIContainer, DIKey
from src.infrastructure.drivers.base_driver import BaseDriverImplementation
from src.infrastructure.drivers.execution_driver import ExecutionDriver
from src.infrastructure.drivers.file_driver import FileDriver
from src.operations.requests.execution_requests import ShellRequest


class DockerDriver(BaseDriverImplementation):
    """Consolidated Docker driver with command building and optional tracking."""

    def __init__(self,
                 file_driver: FileDriver,
                 execution_driver: ExecutionDriver,
                 container: Optional[DIContainer] = None):
        """Initialize Docker driver.
        
        Args:
            file_driver: File driver for filesystem operations
            execution_driver: Shell/Python execution driver
            container: Optional DI container for dependency resolution
        """
        super().__init__(container)
        self.file_driver = file_driver
        self.execution_driver = execution_driver
        self._container_repo = None
        self._image_repo = None
        self._tracking_enabled = container is not None

    @property
    def container_repo(self):
        """Lazy load container repository if tracking is enabled."""
        if self._container_repo is None and self.container:
            self._container_repo = self.container.resolve(DIKey.DOCKER_CONTAINER_REPOSITORY)
        return self._container_repo

    @property
    def image_repo(self):
        """Lazy load image repository if tracking is enabled."""
        if self._image_repo is None and self.container:
            self._image_repo = self.container.resolve(DIKey.DOCKER_IMAGE_REPOSITORY)
        return self._image_repo

    def execute_command(self, request: Any) -> Any:
        """Execute a Docker request.
        
        Routes to appropriate method based on request type.
        """
        if hasattr(request, 'operation'):
            operation = request.operation
            if operation == 'run':
                return self.run_container(
                    request.image,
                    getattr(request, 'name', None),
                    getattr(request, 'options', {}),
                    getattr(request, 'show_output', True)
                )
            if operation == 'stop':
                return self.stop_container(
                    request.name,
                    getattr(request, 'timeout', 10),
                    getattr(request, 'show_output', True)
                )
            if operation == 'build':
                return self.build_docker_image(
                    request.image_name,
                    request.dockerfile_path,
                    getattr(request, 'build_args', {}),
                    getattr(request, 'show_output', True)
                )

        raise ValueError("Invalid Docker request")

    def validate(self, request: Any) -> bool:
        """Validate if this driver can handle the request."""
        return hasattr(request, 'operation') and request.operation in [
            'run', 'stop', 'remove', 'build', 'exec', 'ps', 'logs', 'inspect'
        ]

    # Command Building Methods (integrated from docker_command_utils)

    @staticmethod
    def validate_docker_image_name(image_name: str) -> bool:
        """Validate Docker image name format."""
        if not image_name:
            return False
        # Pattern: [registry/]name[:tag]
        pattern = r'^([a-z0-9._-]+/)*[a-z0-9._-]+(:[\w.-]+)?$'
        return bool(re.match(pattern, image_name))

    def _build_docker_run_command(self, image: str, name: Optional[str],
                                  options: Dict[str, Any]) -> List[str]:
        """Build docker run command."""
        cmd = ["docker", "run"]

        # Add container name if provided
        if name:
            cmd.extend(["--name", name])

        # Add flags
        if options.get("detach"):
            cmd.append("-d")
        if options.get("interactive"):
            cmd.append("-i")
        if options.get("tty"):
            cmd.append("-t")
        if options.get("remove"):
            cmd.append("--rm")

        # Add network
        if "network" in options:
            cmd.extend(["--network", options["network"]])

        # Add ports
        if "ports" in options:
            for port in options["ports"]:
                cmd.extend(["-p", port])

        # Add volumes
        if "volumes" in options:
            for volume in options["volumes"]:
                cmd.extend(["-v", volume])

        # Add environment variables
        if "env" in options:
            for key, value in options["env"].items():
                cmd.extend(["-e", f"{key}={value}"])

        # Add working directory
        if "workdir" in options:
            cmd.extend(["-w", options["workdir"]])

        # Add image
        cmd.append(image)

        # Add command if provided
        if "command" in options:
            if isinstance(options["command"], str):
                cmd.extend(shlex.split(options["command"]))
            else:
                cmd.extend(options["command"])

        return cmd

    def _build_docker_stop_command(self, name: str, timeout: int = 10) -> List[str]:
        """Build docker stop command."""
        return ["docker", "stop", "-t", str(timeout), name]

    def _build_docker_remove_command(self, name: str, force: bool = False) -> List[str]:
        """Build docker remove command."""
        cmd = ["docker", "rm"]
        if force:
            cmd.append("-f")
        cmd.append(name)
        return cmd

    def _build_docker_build_command(self, image_name: str, dockerfile_path: str,
                                    build_args: Dict[str, str]) -> List[str]:
        """Build docker build command."""
        cmd = ["docker", "build", "-t", image_name]

        # Add build arguments
        for key, value in build_args.items():
            cmd.extend(["--build-arg", f"{key}={value}"])

        # Add dockerfile if not default
        if dockerfile_path != "Dockerfile":
            cmd.extend(["-f", dockerfile_path])

        # Add build context (current directory)
        cmd.append(".")

        return cmd

    # Container Operations

    def run_container(self, image: str, name: Optional[str],
                      options: Dict[str, Any], show_output: bool = True):
        """Run a Docker container with optional tracking."""
        self.log_info(f"Running container from image: {image}", name=name)

        cmd = self._build_docker_run_command(image, name, options)
        req = ShellRequest(
            cmd=cmd,
            cwd=self._get_default_value("infrastructure_defaults.docker.cwd", "."),
            env={},
            inputdata="",
            timeout=self._get_default_value("infrastructure_defaults.docker.timeout", 300),
            debug_tag="docker_run",
            name="docker_run_request",
            show_output=show_output,
            allow_failure=False
        )

        result = req.execute_operation(driver=self.execution_driver, logger=self.logger)

        # Track if enabled
        if self._tracking_enabled and result.success and name:
            self._track_container_start(name, image, options, result)

        return result

    def stop_container(self, name: str, timeout: int = 10, show_output: bool = True):
        """Stop a Docker container with optional tracking."""
        self.log_info(f"Stopping container: {name}", timeout=timeout)

        cmd = self._build_docker_stop_command(name, timeout)
        req = ShellRequest(
            cmd=cmd,
            cwd=self._get_default_value("infrastructure_defaults.docker.cwd", "."),
            env={},
            inputdata="",
            timeout=self._get_default_value("infrastructure_defaults.docker.timeout", 300),
            debug_tag="docker_stop",
            name="docker_stop_request",
            show_output=show_output,
            allow_failure=False
        )

        result = req.execute_operation(driver=self.execution_driver, logger=self.logger)

        # Track if enabled
        if self._tracking_enabled and result.success:
            self._track_container_stop(name)

        return result

    def remove_container(self, name: str, force: bool = False, show_output: bool = True):
        """Remove a Docker container."""
        self.log_info(f"Removing container: {name}", force=force)

        cmd = self._build_docker_remove_command(name, force)
        req = ShellRequest(
            cmd=cmd,
            cwd=self._get_default_value("infrastructure_defaults.docker.cwd", "."),
            env={},
            inputdata="",
            timeout=self._get_default_value("infrastructure_defaults.docker.timeout", 300),
            debug_tag="docker_rm",
            name="docker_rm_request",
            show_output=show_output,
            allow_failure=False
        )

        result = req.execute_operation(driver=self.execution_driver, logger=self.logger)

        # Track if enabled
        if self._tracking_enabled and result.success:
            self._track_container_removal(name)

        return result

    def build_docker_image(self, image_name: str, dockerfile_path: str,
                          build_args: Dict[str, str] = None, show_output: bool = True):
        """Build a Docker image."""
        if not self.validate_docker_image_name(image_name):
            raise ValueError(f"Invalid Docker image name: {image_name}")

        self.log_info(f"Building Docker image: {image_name}", dockerfile=dockerfile_path)

        build_args = build_args or {}
        cmd = self._build_docker_build_command(image_name, dockerfile_path, build_args)

        req = ShellRequest(
            cmd=cmd,
            cwd=self._get_default_value("infrastructure_defaults.docker.build_cwd", "."),
            env={},
            inputdata="",
            timeout=self._get_default_value("infrastructure_defaults.docker.build_timeout", 600),
            debug_tag="docker_build",
            name="docker_build_request",
            show_output=show_output,
            allow_failure=False
        )

        result = req.execute_operation(driver=self.execution_driver, logger=self.logger)

        # Track if enabled
        if self._tracking_enabled and result.success:
            self._track_image_build(image_name, dockerfile_path, build_args)

        return result

    def exec_in_container(self, container_name: str, command: Union[str, List[str]],
                          interactive: bool = False, tty: bool = False,
                          show_output: bool = True):
        """Execute a command in a running container."""
        self.log_info(f"Executing command in container: {container_name}")

        cmd = ["docker", "exec"]
        if interactive:
            cmd.append("-i")
        if tty:
            cmd.append("-t")

        cmd.append(container_name)

        if isinstance(command, str):
            cmd.extend(shlex.split(command))
        else:
            cmd.extend(command)

        req = ShellRequest(
            cmd=cmd,
            cwd=self._get_default_value("infrastructure_defaults.docker.cwd", "."),
            env={},
            inputdata="",
            timeout=self._get_default_value("infrastructure_defaults.docker.exec_timeout", 300),
            debug_tag="docker_exec",
            name="docker_exec_request",
            show_output=show_output,
            allow_failure=False
        )

        return req.execute_operation(driver=self.execution_driver, logger=self.logger)

    def get_logs(self, container_name: str, follow: bool = False,
                 tail: Optional[int] = None, show_output: bool = True):
        """Get logs from a container."""
        cmd = ["docker", "logs"]
        if follow:
            cmd.append("-f")
        if tail is not None:
            cmd.extend(["--tail", str(tail)])

        cmd.append(container_name)

        req = ShellRequest(
            cmd=cmd,
            cwd=self._get_default_value("infrastructure_defaults.docker.cwd", "."),
            env={},
            inputdata="",
            timeout=30 if not follow else None,
            debug_tag="docker_logs",
            name="docker_logs_request",
            show_output=show_output,
            allow_failure=False
        )

        return req.execute_operation(driver=self.execution_driver, logger=self.logger)

    def ps(self, all_containers: bool = False, show_output: bool = True):
        """List Docker containers."""
        cmd = ["docker", "ps"]
        if all_containers:
            cmd.append("-a")

        req = ShellRequest(
            cmd=cmd,
            cwd=self._get_default_value("infrastructure_defaults.docker.cwd", "."),
            env={},
            inputdata="",
            timeout=30,
            debug_tag="docker_ps",
            name="docker_ps_request",
            show_output=show_output,
            allow_failure=False
        )

        return req.execute_operation(driver=self.execution_driver, logger=self.logger)

    # Tracking Helper Methods

    def _track_container_start(self, name: str, image: str, options: Dict[str, Any], result):
        """Track container start event."""
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

    def _track_container_stop(self, name: str):
        """Track container stop event."""
        with contextlib.suppress(Exception):
            self.container_repo.update_container_status(name, "stopped", "stopped_at")
            self.container_repo.add_lifecycle_event(name, "stopped", {})

    def _track_container_removal(self, name: str):
        """Track container removal event."""
        with contextlib.suppress(Exception):
            self.container_repo.update_container_status(name, "removed", "removed_at")
            self.container_repo.add_lifecycle_event(name, "removed", {})

    def _track_image_build(self, image_name: str, dockerfile_path: str,
                          build_args: Dict[str, str]):
        """Track image build event."""
        with contextlib.suppress(Exception):
            self.image_repo.record_image_build(
                image_name,
                dockerfile_path,
                build_args,
                "success"
            )


# Utility functions for Docker naming conventions

def get_docker_image_name(contest_name: str, env_name: str, language: str) -> str:
    """Generate Docker image name following naming convention."""
    normalized_contest = contest_name.lower().replace(" ", "_")
    normalized_env = env_name.lower()
    normalized_lang = language.lower()
    return f"cph_{normalized_contest}_{normalized_env}_{normalized_lang}"


def get_docker_container_name(contest_name: str, env_name: str, language: str) -> str:
    """Generate Docker container name following naming convention."""
    return f"{get_docker_image_name(contest_name, env_name, language)}_container"


def get_docker_network_name(contest_name: str) -> str:
    """Generate Docker network name following naming convention."""
    normalized_contest = contest_name.lower().replace(" ", "_")
    return f"cph_{normalized_contest}_network"

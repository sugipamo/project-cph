"""Docker driver implementation for container operations.
"""
import shlex
from abc import abstractmethod
from typing import Any, Optional, Union

from src.infrastructure.drivers.base.base_driver import ExecutionDriverInterface
from src.infrastructure.drivers.docker.utils import (
    build_docker_build_command,
    build_docker_remove_command,
    build_docker_run_command,
    build_docker_stop_command,
    parse_container_names,
)
from src.infrastructure.drivers.file.local_file_driver import LocalFileDriver
from src.infrastructure.drivers.shell.local_shell_driver import LocalShellDriver
from src.operations.requests.shell.shell_request import ShellRequest


class DockerDriver(ExecutionDriverInterface):
    """Abstract base class for Docker operations."""

    @abstractmethod
    def run_container(self, image: str, name: Optional[str] = None, options: Optional[dict[str, Any]] = None):
        pass

    @abstractmethod
    def stop_container(self, name: str):
        pass

    @abstractmethod
    def remove_container(self, name: str, force: bool = False):
        pass

    @abstractmethod
    def exec_in_container(self, name: str, command: Union[str, list[str]]):
        pass

    @abstractmethod
    def get_logs(self, name: str):
        pass

    @abstractmethod
    def build_docker_image(self, tag: Optional[str] = None, options: Optional[dict[str, Any]] = None, show_output: bool = True, dockerfile_text: Optional[str] = None):
        pass

    @abstractmethod
    def image_ls(self):
        pass

    @abstractmethod
    def image_rm(self, image: str):
        pass

    @abstractmethod
    def ps(self, all: bool = False, show_output: bool = True, names_only: bool = False):
        pass

    @abstractmethod
    def inspect(self, target: str, type_: Optional[str] = None):
        pass

    @abstractmethod
    def cp(self, src: str, dst: str, container: str, to_container: bool = True):
        pass


class LocalDockerDriver(DockerDriver):
    """Local Docker driver implementation using shell commands."""

    def __init__(self, file_driver: LocalFileDriver):
        super().__init__()
        self.shell_driver = LocalShellDriver(file_driver)

    def execute_command(self, request: Any) -> Any:
        """Execute a Docker request."""
        # This method is for compatibility with BaseDriver
        # Actual execution happens in specific methods

    def validate(self, request: Any) -> bool:
        """Validate if this driver can handle the request."""
        # For now, always return True for Docker requests
        return True

    def run_container(self, image: str, name: Optional[str] = None, options: Optional[dict[str, Any]] = None, show_output: bool = True):
        cmd = build_docker_run_command(image, name, options)
        req = ShellRequest(cmd, cwd=None, env=None, inputdata=None, timeout=None, debug_tag=None, name=None, show_output=show_output, allow_failure=False)
        result = req.execute_operation(driver=self.shell_driver, logger=None)
        return result

    def stop_container(self, name: str, show_output: bool = True):
        cmd = build_docker_stop_command(name)
        req = ShellRequest(cmd, cwd=None, env=None, inputdata=None, timeout=None, debug_tag=None, name=None, show_output=show_output, allow_failure=False)
        result = req.execute_operation(driver=self.shell_driver, logger=None)
        return result

    def remove_container(self, name: str, force: bool = False, show_output: bool = True):
        cmd = build_docker_remove_command(name, force=force)
        req = ShellRequest(cmd, cwd=None, env=None, inputdata=None, timeout=None, debug_tag=None, name=None, show_output=show_output, allow_failure=False)
        result = req.execute_operation(driver=self.shell_driver, logger=None)
        return result

    def exec_in_container(self, name: str, command: Union[str, list[str]], show_output: bool = True):
        if isinstance(command, list):
            cmd = ["docker", "exec", name, *command]
        elif isinstance(command, str):
            cmd_parts = shlex.split(command)
            cmd = ["docker", "exec", name, *cmd_parts]
        else:
            raise ValueError(f"Invalid command type: {type(command)}")

        req = ShellRequest(cmd, cwd=None, env=None, inputdata=None, timeout=None, debug_tag=None, name=None, show_output=show_output, allow_failure=False)
        result = req.execute_operation(driver=self.shell_driver, logger=None)
        return result

    def get_logs(self, name: str, show_output: bool = True):
        cmd = ["docker", "logs", name]
        req = ShellRequest(cmd, cwd=None, env=None, inputdata=None, timeout=None, debug_tag=None, name=None, show_output=show_output, allow_failure=False)
        result = req.execute_operation(driver=self.shell_driver, logger=None)
        return result

    def build_docker_image(self, dockerfile_text: str, tag: Optional[str] = None, options: Optional[dict[str, Any]] = None, show_output: bool = True):
        if not dockerfile_text or dockerfile_text is None:
            raise ValueError("dockerfile_text is None. Dockerfile内容が正しく渡っていません。")

        cmd = build_docker_build_command(tag, dockerfile_text, options)
        req = ShellRequest(cmd, cwd=None, env=None, inputdata=dockerfile_text, timeout=None, debug_tag=None, name=None, show_output=show_output, allow_failure=False)
        result = req.execute_operation(driver=self.shell_driver, logger=None)
        return result


    def image_ls(self, show_output: bool = True):
        cmd = ["docker", "image", "ls"]
        req = ShellRequest(cmd, cwd=None, env=None, inputdata=None, timeout=None, debug_tag=None, name=None, show_output=show_output, allow_failure=False)
        result = req.execute_operation(driver=self.shell_driver, logger=None)
        return result

    def image_rm(self, image: str, show_output: bool = True):
        cmd = ["docker", "image", "rm", image]
        req = ShellRequest(cmd, cwd=None, env=None, inputdata=None, timeout=None, debug_tag=None, name=None, show_output=show_output, allow_failure=False)
        result = req.execute_operation(driver=self.shell_driver, logger=None)
        return result

    def ps(self, all: bool = False, show_output: bool = True, names_only: bool = False):
        if names_only:
            cmd = ["docker", "ps", "-a", "--format", "{{.Names}}"]
            req = ShellRequest(cmd, cwd=None, env=None, inputdata=None, timeout=None, debug_tag=None, name=None, show_output=show_output, allow_failure=False)
            result = req.execute_operation(driver=self.shell_driver, logger=None)
            stdout_value = result.stdout
            if stdout_value is None:
                raise ValueError("Docker command returned None stdout - this indicates a critical error")
            return parse_container_names(stdout_value)
        cmd = ["docker", "ps"]
        if all:
            cmd.append("-a")
        req = ShellRequest(cmd, cwd=None, env=None, inputdata=None, timeout=None, debug_tag=None, name=None, show_output=show_output, allow_failure=False)
        result = req.execute_operation(driver=self.shell_driver, logger=None)
        return result

    def inspect(self, target: str, type_: Optional[str] = None, show_output: bool = True):
        cmd = ["docker", "inspect"]
        if type_:
            cmd += ["--type", type_]
        cmd.append(target)
        req = ShellRequest(cmd, cwd=None, env=None, inputdata=None, timeout=None, debug_tag=None, name=None, show_output=show_output, allow_failure=False)
        result = req.execute_operation(driver=self.shell_driver, logger=None)
        return result

    def cp(self, src: str, dst: str, container: str, to_container: bool = True, show_output: bool = True):
        if to_container:
            cp_src = str(src)
            cp_dst = f"{container}:{dst}"
        else:
            cp_src = f"{container}:{src}"
            cp_dst = str(dst)
        cmd = ["docker", "cp", cp_src, cp_dst]
        req = ShellRequest(cmd, cwd=None, env=None, inputdata=None, timeout=None, debug_tag=None, name=None, show_output=show_output, allow_failure=False)
        result = req.execute_operation(driver=self.shell_driver, logger=None)
        return result

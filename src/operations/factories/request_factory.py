"""Request factory for creating request objects from steps"""
from typing import Any, Optional

from src.operations.requests.base.base_request import OperationRequestFoundation
from src.operations.requests.docker.docker_request import DockerOpType, DockerRequest
from src.operations.requests.file.file_op_type import FileOpType
from src.operations.requests.file.file_request import FileRequest
from src.operations.requests.python.python_request import PythonRequest
from src.operations.requests.shell.shell_request import ShellRequest

# Removed direct import of workflow layer - StepType will be passed as parameter


class RequestFactory:
    """Factory class for creating request objects from steps"""

    def __init__(self, config_manager, error_converter: Any, result_factory: Any,
                 os_provider: Any, python_utils: Any, json_provider: Any):
        """Initialize RequestFactory with injected dependencies

        Args:
            config_manager: Configuration manager for resolving default values
            error_converter: Error converter for handling exceptions
            result_factory: Result factory for creating results
            os_provider: OS provider for system operations
            python_utils: Python utilities for script operations
            json_provider: JSON provider for parsing JSON data
        """
        self.config_manager = config_manager
        self._error_converter = error_converter
        self._result_factory = result_factory
        self._os_provider = os_provider
        self._python_utils = python_utils
        self._json_provider = json_provider

    def create_request_from_step(self, step: Any, context: Any, env_manager: Any) -> Optional[OperationRequestFoundation]:
        """Create a request object from a step

        Args:
            step: Any object to convert
            context: Execution context containing configuration
            env_manager: Environment manager for workspace paths

        Returns:
            Request object or None if step type is not supported
        """
        # Use step type as string to avoid dependency on workflow layer
        if not hasattr(step, 'type'):
            raise ValueError("Step object must have 'type' attribute")
        step_type = step.type
        if hasattr(step_type, 'name'):
            step_type_name = step_type.name
        else:
            step_type_name = str(step_type)

        if step_type_name == "DOCKER_BUILD":
            return self._create_docker_build_request(step, context, env_manager)
        if step_type_name == "DOCKER_RUN":
            return self._create_docker_run_request(step, context, env_manager)
        if step_type_name == "DOCKER_EXEC":
            return self._create_docker_exec_request(step, context, env_manager)
        if step_type_name == "DOCKER_COMMIT":
            return self._create_docker_commit_request(step, context)
        if step_type_name == "DOCKER_RM":
            return self._create_docker_rm_request(step, context)
        if step_type_name == "DOCKER_RMI":
            return self._create_docker_rmi_request(step, context)
        if step_type_name == "MKDIR":
            return self._create_mkdir_request(step, context, env_manager)
        if step_type_name == "TOUCH":
            return self._create_touch_request(step, context, env_manager)
        if step_type_name == "COPY":
            return self._create_copy_request(step, context, env_manager)
        if step_type_name == "MOVE":
            return self._create_move_request(step, context, env_manager)
        if step_type_name == "REMOVE":
            return self._create_remove_request(step, context, env_manager)
        if step_type_name == "RMTREE":
            return self._create_rmtree_request(step, context, env_manager)
        if step_type_name == "CHMOD":
            return self._create_chmod_request(step, context, env_manager)
        if step_type_name == "RUN":
            return self._create_run_request(step, context, env_manager)
        if step_type_name == "PYTHON":
            return self._create_python_request(step, context, env_manager)
        return None

    def _create_docker_build_request(self, step: Any, context: Any, env_manager: Any) -> DockerRequest:
        """Create docker build request"""

        # Extract tag from build command
        tag = None
        if "-t" in step.cmd:
            tag_idx = step.cmd.index("-t") + 1
            if tag_idx < len(step.cmd):
                tag = step.cmd[tag_idx]

        return DockerRequest(
            op=DockerOpType.BUILD,
            image=tag,
            container=None,
            command=None,
            options={
                "context_path": env_manager.get_workspace_root(),
                "tag": tag
            },
            debug_tag=f"docker_build_{context.problem_name}",
            name=None,
            show_output=True,
            dockerfile_text=None,
            json_provider=self._json_provider
        )

    def _create_docker_run_request(self, step: Any, context: Any, env_manager: Any) -> DockerRequest:
        """Create docker run request"""

        # Extract container name and image from run command
        container_name = None
        image = None

        if "--name" in step.cmd:
            name_idx = step.cmd.index("--name") + 1
            if name_idx < len(step.cmd):
                container_name = step.cmd[name_idx]

        # Image is typically the last argument
        if step.cmd:
            image = step.cmd[-1]

        return DockerRequest(
            op=DockerOpType.RUN,
            image=image,
            container=container_name,
            command=step.cmd,
            options={
                "workspace_mount": env_manager.get_workspace_root()
            },
            debug_tag=f"docker_run_{context.problem_name}",
            name=None,
            show_output=True,
            dockerfile_text=None,
            json_provider=self._json_provider
        )

    def _create_docker_exec_request(self, step: Any, context: Any, env_manager: Any) -> DockerRequest:
        """Create docker exec request"""

        # Container name is typically the first argument after exec
        if not step.cmd:
            if self.config_manager:
                container_name = self.config_manager.resolve_config(
                    ['request_factory_defaults', 'docker', 'container_name_fallback'], type(None)
                )
            else:
                raise ValueError("No command provided for docker exec and no config manager available")
        else:
            container_name = step.cmd[0]

        if len(step.cmd) <= 1:
            if self.config_manager:
                exec_cmd = self.config_manager.resolve_config(
                    ['request_factory_defaults', 'docker', 'exec_cmd_fallback'], list
                )
            else:
                raise ValueError("No exec command provided for docker exec and no config manager available")
        else:
            exec_cmd = step.cmd[1:]

        return DockerRequest(
            op=DockerOpType.EXEC,
            image=None,
            container=container_name,
            command=exec_cmd,
            options={},
            debug_tag=f"docker_exec_{context.problem_name}",
            name=None,
            show_output=True,
            dockerfile_text=None,
            json_provider=self._json_provider
        )

    def _create_docker_commit_request(self, step: Any, context: Any) -> DockerRequest:
        """Create docker commit request"""

        # Container and image are typically the first two arguments
        if not step.cmd:
            if self.config_manager:
                container_name = self.config_manager.resolve_config(
                    ['request_factory_defaults', 'docker', 'container_name_fallback'], type(None)
                )
            else:
                raise ValueError("No command provided for docker commit and no config manager available")
        else:
            container_name = step.cmd[0]

        if len(step.cmd) <= 1:
            if self.config_manager:
                image = self.config_manager.resolve_config(
                    ['request_factory_defaults', 'docker', 'image_fallback'], type(None)
                )
            else:
                raise ValueError("No image provided for docker commit and no config manager available")
        else:
            image = step.cmd[1]

        return DockerRequest(
            op=DockerOpType.BUILD,  # Commit is similar to build in DockerOpType
            image=image,
            container=container_name,
            command=None,
            options={},
            debug_tag=f"docker_commit_{context.problem_name}",
            name=None,
            show_output=True,
            dockerfile_text=None,
            json_provider=self._json_provider
        )

    def _create_docker_rm_request(self, step: Any, context: Any) -> DockerRequest:
        """Create docker rm request"""

        if not step.cmd:
            if self.config_manager:
                container_name = self.config_manager.resolve_config(
                    ['request_factory_defaults', 'docker', 'container_name_fallback'], type(None)
                )
            else:
                raise ValueError("No command provided for docker remove and no config manager available")
        else:
            container_name = step.cmd[0]

        return DockerRequest(
            op=DockerOpType.REMOVE,
            image=None,
            container=container_name,
            command=None,
            options={},
            debug_tag=f"docker_rm_{context.problem_name}",
            name=None,
            show_output=True,
            dockerfile_text=None,
            json_provider=self._json_provider
        )

    def _create_docker_rmi_request(self, step: Any, context: Any) -> DockerRequest:
        """Create docker rmi request"""

        if not step.cmd:
            if self.config_manager:
                image = self.config_manager.resolve_config(
                    ['request_factory_defaults', 'docker', 'image_fallback'], type(None)
                )
            else:
                raise ValueError("No command provided for docker rmi and no config manager available")
        else:
            image = step.cmd[0]

        return DockerRequest(
            op=DockerOpType.REMOVE,  # Use REMOVE for image removal as well
            image=image,
            container=None,
            command=None,
            options={},
            debug_tag=f"docker_rmi_{context.problem_name}",
            name=None,
            show_output=True,
            dockerfile_text=None,
            json_provider=self._json_provider
        )

    def _create_mkdir_request(self, step: Any, context: Any, env_manager: Any) -> FileRequest:
        """Create mkdir request"""
        if not step.cmd:
            if self.config_manager:
                path = self.config_manager.resolve_config(
                    ['request_factory_defaults', 'file', 'path_fallback'], str
                )
            else:
                raise ValueError("No command provided for mkdir and no config manager available")
        else:
            path = step.cmd[0]

        return FileRequest(
            op=FileOpType.MKDIR,
            path=path,
            content=None,
            dst_path=None,
            debug_tag=f"mkdir_{context.problem_name}",
            name=None
        )

    def _create_touch_request(self, step: Any, context: Any, env_manager: Any) -> FileRequest:
        """Create touch request"""
        if not step.cmd:
            if self.config_manager:
                path = self.config_manager.resolve_config(
                    ['request_factory_defaults', 'file', 'path_fallback'], str
                )
            else:
                raise ValueError("No command provided for touch and no config manager available")
        else:
            path = step.cmd[0]

        return FileRequest(
            op=FileOpType.TOUCH,
            path=path,
            content=None,
            dst_path=None,
            debug_tag=f"touch_{context.problem_name}",
            name=None
        )

    def _create_copy_request(self, step: Any, context: Any, env_manager: Any) -> FileRequest:
        """Create copy request"""
        if not step.cmd:
            if self.config_manager:
                source = self.config_manager.resolve_config(
                    ['request_factory_defaults', 'file', 'path_fallback'], str
                )
            else:
                raise ValueError("No command provided for copy source and no config manager available")
        else:
            source = step.cmd[0]

        if len(step.cmd) <= 1:
            if self.config_manager:
                target = self.config_manager.resolve_config(
                    ['request_factory_defaults', 'file', 'path_fallback'], str
                )
            else:
                raise ValueError("No target provided for copy and no config manager available")
        else:
            target = step.cmd[1]

        return FileRequest(
            op=FileOpType.COPY,
            path=source,
            content=None,
            dst_path=target,
            debug_tag=f"copy_{context.problem_name}",
            name=None
        )

    def _create_move_request(self, step: Any, context: Any, env_manager: Any) -> FileRequest:
        """Create move request"""
        if not step.cmd:
            raise ValueError("Copy command requires source path")
        source = step.cmd[0]
        if len(step.cmd) < 2:
            raise ValueError("Copy command requires both source and target paths")
        target = step.cmd[1]

        return FileRequest(
            op=FileOpType.MOVE,
            path=source,
            content=None,
            dst_path=target,
            debug_tag=f"move_{context.problem_name}",
            name=None
        )

    def _create_remove_request(self, step: Any, context: Any, env_manager: Any) -> FileRequest:
        """Create remove request"""
        if not step.cmd:
            raise ValueError("Remove command requires path")
        path = step.cmd[0]

        return FileRequest(
            op=FileOpType.REMOVE,
            path=path,
            content=None,
            dst_path=None,
            debug_tag=f"remove_{context.problem_name}",
            name=None
        )

    def _create_rmtree_request(self, step: Any, context: Any, env_manager: Any) -> FileRequest:
        """Create rmtree request"""
        if not step.cmd:
            raise ValueError("rmtree command requires path")
        path = step.cmd[0]

        return FileRequest(
            op=FileOpType.RMTREE,
            path=path,
            content=None,
            dst_path=None,
            debug_tag=f"rmtree_{context.problem_name}",
            name=None
        )

    def _create_chmod_request(self, step: Any, context: Any, env_manager: Any) -> ShellRequest:
        """Create chmod request using shell command"""
        # chmod is not supported by FileRequest, use ShellRequest instead
        return ShellRequest(
            cmd=step.cmd,
            cwd=env_manager.get_workspace_root(),
            env={},
            inputdata="",
            timeout=30,
            debug_tag=f"chmod_{context.problem_name}",
            name=None,
            show_output=True,
            allow_failure=False,
            error_converter=self._error_converter,
            result_factory=self._result_factory
        )

    def _create_run_request(self, step: Any, context: Any, env_manager: Any) -> ShellRequest:
        """Create run (shell) request"""
        return ShellRequest(
            cmd=step.cmd,
            cwd=env_manager.get_workspace_root(),
            env={},
            inputdata="",
            timeout=30,
            debug_tag=f"run_{context.problem_name}",
            name=None,
            show_output=True,
            allow_failure=step.allow_failure,
            error_converter=self._error_converter,
            result_factory=self._result_factory
        )

    def _create_python_request(self, step: Any, context: Any, env_manager: Any) -> PythonRequest:
        """Create python request"""
        # For Python steps, cmd contains Python code lines
        code_or_file = step.cmd

        return PythonRequest(
            code_or_file=code_or_file,
            cwd=env_manager.get_workspace_root(),
            show_output=True,
            name=None,
            debug_tag=f"python_{context.problem_name}",
            allow_failure=step.allow_failure,
            os_provider=self._os_provider,
            python_utils=self._python_utils
        )


# Backward compatibility factory instance - deprecated
# All dependencies set to None, proper injection should be used
_factory_instance = RequestFactory(
    config_manager=None,
    error_converter=None,
    result_factory=None,
    os_provider=None,
    python_utils=None,
    json_provider=None
)


def create_request(step: Any, context: Any) -> Optional[OperationRequestFoundation]:
    """Create a request from a step using the default factory

    This function maintains backward compatibility with the old API
    """

    # この関数は廃止予定 - 新しいファクトリでは依存性注入が必要

    # この関数は廃止予定 - 代わりにRequestFactoryを直接使用してください
    # contextとenv_managerが必要な場合は、呼び出し元で直接RequestFactoryを使用
    return None

"""Request factory for creating request objects from steps"""
from typing import Any, Optional

from src.operations.requests.base.base_request import OperationRequestFoundation
from src.operations.requests.docker.docker_request import DockerRequest
from src.operations.requests.file.file_op_type import FileOpType
from src.operations.requests.file.file_request import FileRequest
from src.operations.requests.python.python_request import PythonRequest
from src.operations.requests.shell.shell_request import ShellRequest
from src.workflow.step.step import Step, StepType


class RequestFactory:
    """Factory class for creating request objects from steps"""

    def create_request_from_step(self, step: Step, context: Any, env_manager: Any) -> Optional[OperationRequestFoundation]:
        """Create a request object from a step

        Args:
            step: Step object to convert
            context: Execution context containing configuration
            env_manager: Environment manager for workspace paths

        Returns:
            Request object or None if step type is not supported
        """
        if step.type == StepType.DOCKER_BUILD:
            return self._create_docker_build_request(step, context, env_manager)
        if step.type == StepType.DOCKER_RUN:
            return self._create_docker_run_request(step, context, env_manager)
        if step.type == StepType.DOCKER_EXEC:
            return self._create_docker_exec_request(step, context, env_manager)
        if step.type == StepType.DOCKER_COMMIT:
            return self._create_docker_commit_request(step, context)
        if step.type == StepType.DOCKER_RM:
            return self._create_docker_rm_request(step, context)
        if step.type == StepType.DOCKER_RMI:
            return self._create_docker_rmi_request(step, context)
        if step.type == StepType.MKDIR:
            return self._create_mkdir_request(step, context, env_manager)
        if step.type == StepType.TOUCH:
            return self._create_touch_request(step, context, env_manager)
        if step.type == StepType.COPY:
            return self._create_copy_request(step, context, env_manager)
        if step.type == StepType.MOVE:
            return self._create_move_request(step, context, env_manager)
        if step.type == StepType.REMOVE:
            return self._create_remove_request(step, context, env_manager)
        if step.type == StepType.RMTREE:
            return self._create_rmtree_request(step, context, env_manager)
        if step.type == StepType.CHMOD:
            return self._create_chmod_request(step, context, env_manager)
        if step.type == StepType.RUN:
            return self._create_run_request(step, context, env_manager)
        if step.type == StepType.PYTHON:
            return self._create_python_request(step, context, env_manager)
        return None

    def _create_docker_build_request(self, step: Step, context: Any, env_manager: Any) -> DockerRequest:
        """Create docker build request"""
        # Extract tag from build command
        tag = None
        if "-t" in step.cmd:
            tag_idx = step.cmd.index("-t") + 1
            if tag_idx < len(step.cmd):
                tag = step.cmd[tag_idx]

        return DockerRequest(
            op="build",
            context_path=env_manager.get_workspace_root(),
            tag=tag,
            debug_tag=f"docker_build_{context.problem_name}"
        )

    def _create_docker_run_request(self, step: Step, context: Any, env_manager: Any) -> DockerRequest:
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
            op="run",
            image=image,
            container=container_name,
            cmd=step.cmd,
            workspace_mount=env_manager.get_workspace_root(),
            debug_tag=f"docker_run_{context.problem_name}"
        )

    def _create_docker_exec_request(self, step: Step, context: Any, env_manager: Any) -> DockerRequest:
        """Create docker exec request"""
        # Container name is typically the first argument after exec
        container_name = step.cmd[0] if step.cmd else None
        exec_cmd = step.cmd[1:] if len(step.cmd) > 1 else []

        return DockerRequest(
            op="exec",
            container=container_name,
            cmd=exec_cmd,
            debug_tag=f"docker_exec_{context.problem_name}"
        )

    def _create_docker_commit_request(self, step: Step, context: Any) -> DockerRequest:
        """Create docker commit request"""
        # Container and image are typically the first two arguments
        container_name = step.cmd[0] if step.cmd else None
        image = step.cmd[1] if len(step.cmd) > 1 else None

        return DockerRequest(
            op="commit",
            container=container_name,
            image=image,
            debug_tag=f"docker_commit_{context.problem_name}"
        )

    def _create_docker_rm_request(self, step: Step, context: Any) -> DockerRequest:
        """Create docker rm request"""
        container_name = step.cmd[0] if step.cmd else None

        return DockerRequest(
            op="rm",
            container=container_name,
            debug_tag=f"docker_rm_{context.problem_name}"
        )

    def _create_docker_rmi_request(self, step: Step, context: Any) -> DockerRequest:
        """Create docker rmi request"""
        image = step.cmd[0] if step.cmd else None

        return DockerRequest(
            op="rmi",
            image=image,
            debug_tag=f"docker_rmi_{context.problem_name}"
        )

    def _create_mkdir_request(self, step: Step, context: Any, env_manager: Any) -> FileRequest:
        """Create mkdir request"""
        path = step.cmd[0] if step.cmd else ""

        return FileRequest(
            op=FileOpType.MKDIR,
            source=path,
            workspace_path=env_manager.get_workspace_root(),
            debug_tag=f"mkdir_{context.problem_name}"
        )

    def _create_touch_request(self, step: Step, context: Any, env_manager: Any) -> FileRequest:
        """Create touch request"""
        path = step.cmd[0] if step.cmd else ""

        return FileRequest(
            op=FileOpType.TOUCH,
            source=path,
            workspace_path=env_manager.get_workspace_root(),
            debug_tag=f"touch_{context.problem_name}"
        )

    def _create_copy_request(self, step: Step, context: Any, env_manager: Any) -> FileRequest:
        """Create copy request"""
        source = step.cmd[0] if step.cmd else ""
        target = step.cmd[1] if len(step.cmd) > 1 else ""

        return FileRequest(
            op=FileOpType.COPY,
            source=source,
            target=target,
            workspace_path=env_manager.get_workspace_root(),
            debug_tag=f"copy_{context.problem_name}"
        )

    def _create_move_request(self, step: Step, context: Any, env_manager: Any) -> FileRequest:
        """Create move request"""
        source = step.cmd[0] if step.cmd else ""
        target = step.cmd[1] if len(step.cmd) > 1 else ""

        return FileRequest(
            op=FileOpType.MOVE,
            source=source,
            target=target,
            workspace_path=env_manager.get_workspace_root(),
            debug_tag=f"move_{context.problem_name}"
        )

    def _create_remove_request(self, step: Step, context: Any, env_manager: Any) -> FileRequest:
        """Create remove request"""
        path = step.cmd[0] if step.cmd else ""

        return FileRequest(
            op=FileOpType.REMOVE,
            source=path,
            workspace_path=env_manager.get_workspace_root(),
            debug_tag=f"remove_{context.problem_name}"
        )

    def _create_rmtree_request(self, step: Step, context: Any, env_manager: Any) -> FileRequest:
        """Create rmtree request"""
        path = step.cmd[0] if step.cmd else ""

        return FileRequest(
            op=FileOpType.RMTREE,
            source=path,
            workspace_path=env_manager.get_workspace_root(),
            debug_tag=f"rmtree_{context.problem_name}"
        )

    def _create_chmod_request(self, step: Step, context: Any, env_manager: Any) -> FileRequest:
        """Create chmod request"""
        mode = step.cmd[0] if step.cmd else "755"
        path = step.cmd[1] if len(step.cmd) > 1 else ""

        return FileRequest(
            op=FileOpType.CHMOD,
            source=path,
            mode=mode,
            workspace_path=env_manager.get_workspace_root(),
            debug_tag=f"chmod_{context.problem_name}"
        )

    def _create_run_request(self, step: Step, context: Any, env_manager: Any) -> ShellRequest:
        """Create run (shell) request"""
        return ShellRequest(
            cmd=step.cmd,
            cwd=env_manager.get_workspace_root(),
            allow_failure=getattr(step, 'allow_failure', False),
            debug_tag=f"run_{context.problem_name}"
        )

    def _create_python_request(self, step: Step, context: Any, env_manager: Any) -> PythonRequest:
        """Create python request"""
        script = step.cmd[0] if step.cmd else ""
        args = step.cmd[1:] if len(step.cmd) > 1 else []

        return PythonRequest(
            script=script,
            args=args,
            cwd=env_manager.get_workspace_root(),
            debug_tag=f"python_{context.problem_name}"
        )


# Create a singleton instance for backward compatibility
_factory_instance = RequestFactory()


def create_request(step: Step, context: Any) -> Optional[OperationRequestFoundation]:
    """Create a request from a step using the default factory

    This function maintains backward compatibility with the old API
    """
    from src.infrastructure.di_container import DIKey
    env_manager = context.infrastructure.resolve(DIKey.ENVIRONMENT_MANAGER)
    return _factory_instance.create_request_from_step(step, context, env_manager)

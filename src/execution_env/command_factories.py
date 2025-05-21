from src.operations.shell.shell_request import ShellRequest
from src.operations.file.file_request import FileRequest, FileOpType
from src.operations.docker.docker_request import DockerRequest, DockerOpType
from src.execution_env.run_step_shell import ShellRunStep
from src.execution_env.run_step_copy import CopyRunStep
from src.execution_env.run_step_oj import OjRunStep

class BaseCommandRequestFactory:
    def __init__(self, controller):
        self.controller = controller

    def create_request(self, run_step):
        raise NotImplementedError

class ShellCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, ShellRunStep):
            raise TypeError(f"ShellCommandRequestFactory expects ShellRunStep, got {type(run_step).__name__}")
        cmd = [self.controller.const_handler.parse(arg) for arg in run_step.cmd]
        return ShellRequest(cmd)

class DockerCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, ShellRunStep):
            raise TypeError(f"DockerCommandRequestFactory expects ShellRunStep, got {type(run_step).__name__}")
        cmd = [self.controller.const_handler.parse(arg) for arg in run_step.cmd]
        container_name = self.controller.const_handler.container_name
        return DockerRequest(
            DockerOpType.EXEC,
            container=container_name,
            command=" ".join(cmd)
        )

class CopyCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, CopyRunStep):
            raise TypeError(f"CopyCommandRequestFactory expects CopyRunStep, got {type(run_step).__name__}")
        if len(run_step.cmd) < 2:
            raise ValueError("CopyRunStep: cmdにはsrcとdstの2つが必要です")
        src = self.controller.const_handler.parse(run_step.cmd[0])
        dst = self.controller.const_handler.parse(run_step.cmd[1])
        return FileRequest(FileOpType.COPY, src, dst_path=dst)

class OjCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, OjRunStep):
            raise TypeError(f"OjCommandRequestFactory expects OjRunStep, got {type(run_step).__name__}")
        if not run_step.cmd:
            raise ValueError("OjRunStep: cmdは必須です")
        cmd = [self.controller.const_handler.parse(arg) for arg in run_step.cmd]
        container_name = self.controller.const_handler.oj_container_name
        return DockerRequest(
            DockerOpType.EXEC,
            container=container_name,
            command=" ".join(cmd)
        ) 
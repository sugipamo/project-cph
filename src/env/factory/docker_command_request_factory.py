from src.env.factory.base_command_request_factory import BaseCommandRequestFactory
from src.env.step.run_step_shell import ShellRunStep
from src.operations.docker.docker_request import DockerRequest, DockerOpType

class DockerCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, ShellRunStep):
            raise TypeError(f"DockerCommandRequestFactory expects ShellRunStep, got {type(run_step).__name__}")
        cmd = [self.controller.const_handler.parse(arg) for arg in run_step.cmd]
        container_name = self.controller.const_handler.container_name
        return DockerRequest(
            DockerOpType.EXEC,
            container=container_name,
            command=" ".join(cmd),
            show_output=getattr(run_step, 'show_output', True)
        ) 
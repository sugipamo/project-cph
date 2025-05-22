from src.env.factory.base_command_request_factory import BaseCommandRequestFactory
from src.env.step.run_step_oj import OjRunStep
from src.operations.docker.docker_request import DockerRequest, DockerOpType
from src.operations.shell.shell_request import ShellRequest

class OjCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, OjRunStep):
            raise TypeError(f"OjCommandRequestFactory expects OjRunStep, got {type(run_step).__name__}")
        if not run_step.cmd:
            raise ValueError("OjRunStep: cmdは必須です")
        cmd = [self.controller.const_handler.parse(arg) for arg in run_step.cmd]
        env_type = self.controller.env_context.env_type.lower()
        if env_type == "docker":
            container_name = self.controller.const_handler.oj_container_name
            return DockerRequest(
                DockerOpType.EXEC,
                container=container_name,
                command=" ".join(cmd),
                show_output=getattr(run_step, 'show_output', True)
            )
        else:
            return ShellRequest(cmd, show_output=getattr(run_step, 'show_output', True)) 
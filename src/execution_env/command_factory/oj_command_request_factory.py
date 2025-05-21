from src.execution_env.command_factory.base_command_request_factory import BaseCommandRequestFactory
from src.execution_env.run_step.run_step_oj import OjRunStep
from src.operations.docker.docker_request import DockerRequest, DockerOpType

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
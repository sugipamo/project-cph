from src.env.factory.base_command_request_factory import BaseCommandRequestFactory
from src.env.step.run_step_oj import OjRunStep
from src.operations.docker.docker_request import DockerRequest, DockerOpType
from src.operations.shell.shell_request import ShellRequest
from src.operations.composite.composite_request import CompositeRequest

class OjCommandRequestFactory(BaseCommandRequestFactory):
    def __init__(self, controller, DockerRequestClass, DockerOpTypeClass):
        super().__init__(controller)
        self.DockerRequest = DockerRequestClass
        self.DockerOpType = DockerOpTypeClass

    def create_request(self, run_step):
        if not isinstance(run_step, OjRunStep):
            raise TypeError(f"OjCommandRequestFactory expects OjRunStep, got {type(run_step).__name__}")
        if not run_step.cmd:
            raise ValueError("OjRunStep: cmdは必須です")
        cmd = [self.controller.const_handler.parse(arg) for arg in run_step.cmd]
        cwd = self.controller.const_handler.parse(run_step.cwd) if getattr(run_step, 'cwd', None) else None
        env_type = self.controller.env_context.env_type.lower()
        if env_type == "docker":
            container_name = self.controller.const_handler.oj_container_name
            image_name = self.controller.const_handler.oj_image_name
            temp_path = str(self.controller.const_handler.contest_temp_path)
            dockerfile_text = self.controller.const_handler.oj_dockerfile_text
            # BUILDリクエスト
            build_req = self.DockerRequest(
                self.DockerOpType.BUILD,
                image=image_name,
                options={"f": "-", "t": image_name, "inputdata": dockerfile_text},
            )
            # RUNリクエスト
            run_req = self.DockerRequest(
                self.DockerOpType.RUN,
                image=image_name,
                container=container_name,
                options={}
            )
            # EXECリクエスト
            exec_req = self.DockerRequest(
                self.DockerOpType.EXEC,
                container=container_name,
                command=" ".join(cmd),
                show_output=getattr(run_step, 'show_output', True)
            )
            return CompositeRequest.make_composite_request([build_req, run_req, exec_req])
        else:
            return ShellRequest(cmd, cwd=cwd, show_output=getattr(run_step, 'show_output', True)) 